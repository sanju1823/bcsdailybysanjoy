import feedparser
import json
import os
import re
from datetime import datetime
import pytz

# --- NOTUN SDK ---
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY pai nai")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

RSS_FEEDS = {
    "প্রথম আলো": "https://www.prothomalo.com/feed/",
    "ডেইলি স্টার": "https://www.thedailystar.net/frontpage/rss.xml",
    "যুগান্তর": "https://www.jugantor.com/feed/",
    "বিবিসি বাংলা": "https://feeds.bbci.co.uk/bengali/rss.xml"
}

print("Fetching news...")
news_text = ""
count = 0
for name, url in RSS_FEEDS.items():
    try:
        feed = feedparser.parse(url)
        if not feed.entries:
            print(f"⚠️ {name} khali")
            continue
        for entry in feed.entries[:6]:
            title = getattr(entry, 'title', '').strip()
            link = getattr(entry, 'link', '')
            if title and link:
                news_text += f"- [{name}] {title} | Link: {link}\n"
                count += 1
                print(f"✓ {name}: {title[:60]}")
    except Exception as e:
        print(f"❌ {name} error: {e}")
        continue

if count < 3:
    print("❌ News khub kom, exit")
    exit(1)

bd_time = datetime.now(pytz.timezone('Asia/Dhaka'))
today_str = bd_time.strftime("%d %B %Y")
today_iso = bd_time.strftime("%Y-%m-%d")

prompt = f"""
Tumi ekjon BCS expert. Ajker tarikh {today_str}.
Nicher news gulo theke BCS er jonno 20 ta samprotik MCQ banaw.

NEWS:
{news_text}

JSON format e sudhu JSON diba:
{{
  "date": "{today_str}",
  "questions": [ {{"id":1, "category":"সংবিধান", "question":"...", "options":["ক) ...","খ) ...","গ) ...","ঘ) ..."], "answer":"ক) ...", "explanation":"2 line", "source":"প্রথম আলো", "sourceUrl":"asol link"}} ],
  "vocabulary": [ {{"word":"word","bangla":"অর্থ","pronunciation":"...","example":"..."}} ]
}}
Rules: 20 Q + 10 vocab must, sourceUrl e uporer asol link, valid JSON only, markdown chara
"""

print("\nGenerating with Gemini (new SDK)...")
# Model fallback - Google ekhon bar bar model name change kore
models_to_try = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash", "gemini-flash-latest"]

raw_text = None
for model_name in models_to_try:
    try:
        print(f"Trying model: {model_name}...")
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        raw_text = response.text
        print(f"✅ Success with {model_name}")
        break
    except Exception as e:
        print(f"⚠️ {model_name} failed: {e}")
        continue

if not raw_text:
    print("❌ All models failed")
    exit(1)

clean_json = raw_text.replace("```json","").replace("```","").strip()
m = re.search(r'\{.*\}', clean_json, re.DOTALL)
if m:
    clean_json = m.group(0)

try:
    data = json.loads(clean_json)
except Exception as e:
    print(f"❌ JSON parse failed: {e}")
    print(clean_json[:1500])
    with open("gemini_raw.txt","w",encoding="utf-8") as f:
        f.write(raw_text)
    exit(1)

with open("data.json","w",encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Done! {len(data.get('questions',[]))} Q")

sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url><loc>https://bcsdailybysanjoy.netlify.app/</loc><lastmod>' + today_iso + '</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>\n  <url><loc>https://bcsdailybysanjoy.netlify.app/archive/</loc><lastmod>' + today_iso + '</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>\n</urlset>'

with open("sitemap.xml","w",encoding="utf-8") as f:
    f.write(sitemap_content)

print("✅ sitemap.xml updated")
