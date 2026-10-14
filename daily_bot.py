import feedparser
import json
import os
import google.generativeai as genai
from datetime import datetime
import pytz

# 1. Gemini API Key - GitHub Secret theke asbe
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# 2. Potrika RSS theke news newa
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
    except:
        continue

# 3. AI diye 20 MCQ + 10 Vocab banano
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
      "source": "Prothom Alo / Daily Star"
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

print("Generating with Gemini...")
response = model.generate_content(prompt)
clean_json = response.text.replace("```json", "").replace("```", "").strip()

# 4. data.json save kora
data = json.loads(clean_json)

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# 5. sitemap.xml er lastmod update
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
