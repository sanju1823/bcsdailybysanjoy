import feedparser
import json
import os
import google.generativeai as genai
from datetime import datetime
import pytz
import re

# 1. API Key check
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY pai nai! GitHub Secrets e add koro")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)
# 2.0-flash stable, 1.5-flash majhe majhe 404 dey
model = genai.GenerativeModel("gemini-2.0-flash")

RSS_FEEDS = {
    "প্রথম আলো": "https://www.prothomalo.com/feed/",
    "ডেইলি স্টার": "https://www.thedailystar.net/frontpage/rss.xml",
    "যুগান্তর": "https://www.jugantor.com/feed/",
    "বিবিসি বাংলা": "https://feeds.bbci.co.uk/bengali/rss.xml"
}

print("Fetching news...")
news_items = []
news_text = ""
for name, url in RSS_FEEDS.items():
    try:
        feed = feedparser.parse(url)
        if not feed.entries:
            print(f"⚠️ {name} khali")
            continue
        for entry in feed.entries[:7]:
            title = entry.title.strip()
            link = entry.link
            news_items.append({"source": name, "title": title, "link": link})
            news_text += f"- [{name}] {title} | Link: {link}\n"
    except Exception as e:
        print(f"❌ {name} error: {e}")
        continue

if len(news_items) < 5:
    print("❌ News kom, exit")
    exit(1)

bd_time = datetime.now(pytz.timezone('Asia/Dhaka'))
today_str = bd_time.strftime("%d %B %Y")
today_iso = bd_time.strftime("%Y-%m-%d")

prompt = f"""
Tumi ekjon BCS expert. Ajker tarikh {today_str}.
Nicher news gulo theke BCS er jonno 20 ta samprotik MCQ banaw. Prottek proshno er sourceUrl e NICHER DEYA ASOL LINK TAI USE KORBA, fake link banaba na.

NEWS LIST:
{news_text}

Format JSON e hobe, sudhu JSON:
{{
  "date": "{today_str}",
  "questions": [ {{ "id": 1, "category": "সংবিধান", "question": "...", "options": ["ক) ...", "খ) ...", "গ) ...", "ঘ) ..."], "answer": "ক) ...", "explanation": "2 line", "source": "প্রথম আলো", "sourceUrl": "asol link" }} ],
  "vocabulary": [ {{ "word": "word", "bangla": "অর্থ", "pronunciation": "...", "example": "..." }} ]
}}
Rules: 20 question + 10 vocab must, sourceUrl e uporer asol link diba, valid JSON only
"""

print("\nGenerating with Gemini...")
try:
    response = model.generate_content(prompt)
    raw_text = response.text
except Exception as e:
    print(f"❌ Gemini API error: {e}")
    exit(1)

clean_json = raw_text.replace("```json", "").replace("```", "").strip()
m = re.search(r'\{.*\}', clean_json, re.DOTALL)
if m:
    clean_json = m.group(0)

try:
    data = json.loads(clean_json)
except Exception as e:
    print(f"❌ JSON parse failed: {e}")
    print(clean_json[:1000])
    with open("gemini_raw.txt", "w", encoding="utf-8") as f:
        f.write(raw_text)
    exit(1)

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Done! {len(data.get('questions', []))} Q saved")

# sitemap update - choto hater e
sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url>\n    <loc>https://bcsdailybysanjoy.netlify.app/</loc>\n    <lastmod>' + today_iso + '</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>1.0</priority>\n  </url>\n  <url>\n    <loc>https://bcsdailybysanjoy.netlify.app/archive/</loc>\n    <lastmod>' + today_iso + '</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>0.8</priority>\n  </url>\n</urlset>'

with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap_content)

print("✅ sitemap.xml updated")
