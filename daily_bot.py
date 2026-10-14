import feedparser
import json
import os
from google import genai
from datetime import datetime
import pytz

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found!")

client = genai.Client(api_key=GEMINI_API_KEY)

RSS_FEEDS = {
    "প্রথম আলো": "https://www.prothomalo.com/feed/",
    "ডেইলি স্টার": "https://www.thedailystar.net/frontpage/rss.xml",
    "যুগান্তর": "https://www.jugantor.com/feed/",
    "বিবিসি বাংলা": "https://www.bbc.com/bengali/index.xml"
}

print("Fetching news...")
news_text = ""
for name, url in RSS_FEEDS.items():
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:7]:
            news_text += f"- {name}: {entry.title}\n"
    except Exception as e:
        print(f"Failed {name}: {e}")
        continue

if not news_text.strip():
    news_text = "Recent Bangladesh and international news for BCS preparation"

bd_time = datetime.now(pytz.timezone('Asia/Dhaka'))
today_str = bd_time.strftime("%d %B %Y")

prompt = f"""
Tumi ekjon BCS expert. Ajker tarikh {today_str}.
Nicher news gulo theke BCS er jonno 20 ta samprotik proshno banaw:

{news_text}

Format JSON e hobe:
{{
  "date": "{today_str}",
  "questions": [
    {{
      "id": 1,
      "category": "সংবিধান / অর্থনীতি / বিজ্ঞান / আন্তর্জাতিক / ভূগোল / যোগাযোগ / ICT er jekono ekta",
      "question": "Proshno Bangla te",
      "options": ["ক) ...", "খ) ...", "গ) ...", "ঘ) ..."],
      "answer": "ক) ...",
      "explanation": "2 line bekkha Bangla te",
      "source": "【entity-Prothom Alo¦canonical_name=Prothom Alo】 / 【entity-Daily Star¦canonical_name=Daily Star】"
    }}
  ],
  "vocabulary": [
    {{
      "word": "English word",
      "bangla": "বাংলা অর্থ",
      "pronunciation": "pronunciation",
      "example": "English example with Bangla translation"
    }}
  ]
}}
20 ta question + 10 ta vocabulary must. Shob Bangla te, source soho. Valid JSON only.
"""

import time

models_to_try = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-2.5-flash", "gemini-flash-latest"]

response = None
for model_name in models_to_try:
    try:
        print(f"Trying model: {model_name}...")
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        print(f"Success with {model_name}")
        break
    except Exception as e:
        print(f"Failed {model_name}: {e}")
        time.sleep(3)
        continue

if response is None:
    raise Exception("All Gemini models are busy, try again later")

clean_json = response.text.replace("```json", "").replace("```", "").strip()
data = json.loads(clean_json)

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

sitemap_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://bcsdailybysanjoy.netlify.app/</loc>
    <lastmod>{bd_time.strftime("%Y-%m-%d")}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>'''

with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap_content)

print(f"Done! {len(data['questions'])} questions generated for {today_str}")
