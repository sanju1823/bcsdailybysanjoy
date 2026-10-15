import feedparser
import json
import os
import re
import time
from datetime import datetime
import pytz
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY, http_options=types.HttpOptions(api_version='v1'))

RSS_FEEDS = {
    "প্রথম আলো": "https://www.prothomalo.com/feed/",
    "ডেইলি স্টার": "https://www.thedailystar.net/frontpage/rss.xml",
    "যুগান্তর": "https://www.jugantor.com/feed/",
    "বিবিসি বাংলা": "https://feeds.bbci.co.uk/bengali/rss.xml"
}

print("Fetching main headlines...")
news_text = ""
for name, url in RSS_FEEDS.items():
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:4]:  # sudhu top 4 main news
            title = re.sub('<[^<]+?>', '', getattr(entry, 'title', '')).strip()
            summary = re.sub('<[^<]+?>', '', getattr(entry, 'summary', '')[:200]).strip()
            link = getattr(entry, 'link', '')
            m = re.search(r'https?://[^\s"<>]+', link)
            if m: link = m.group(0)
            if title and len(title) > 15:
                news_text += f"- SOURCE: {name} | TITLE: {title} | SUMMARY: {summary} | URL: {link}\n"
                print(f"✓ {name}: {title[:60]}")
    except Exception as e:
        print(f"❌ {name} {e}")

bd_time = datetime.now(pytz.timezone('Asia/Dhaka'))
today_str = bd_time.strftime("%d %B %Y")
today_iso = bd_time.strftime("%Y-%m-%d")

prompt = f"""
You are a senior BCS Preliminary question setter with 10 years experience.
Today: {today_str}

TASK: From the MAIN HEADLINES below, create 20 HIGH-STANDARD BCS questions.

NEWS HEADLINES (only use these, no outside knowledge):
{news_text}

STRICT RULES - MUST FOLLOW:

1. QUALITY FILTER:
   - BAD (ajaira) question examples you MUST NOT create:
     "এই খবরের লেখক কে?" "এই খবরের লিংক কি?" "এই শিরোনামে কয়টি শব্দ আছে?"
   - GOOD (standard) question examples you MUST create:
     "সম্প্রতি IMF বাংলাদেশকে কত বিলিয়ন ডলার ঋণ অনুমোদন করেছে?"
     "সংবিধানের কততম সংশোধনীতে তত্ত্বাবধায়ক সরকার বাতিল হয়?"
     "COP29 সম্মেলন কোথায় অনুষ্ঠিত হচ্ছে?"

2. RELEVANCE:
   - Only create questions from news that is BCS-relevant: বাংলাদেশ বিষয়াবলি, আন্তর্জাতিক, সংবিধান, অর্থনীতি, বিজ্ঞান, পরিবেশ, খেলাধুলা (যদি জাতীয় গুরুত্ব)
   - If a news is about celebrity gossip or trivial local crime, SKIP IT
   - Select 10-12 most important news and make 1-2 questions from each

3. STANDARD:
   - Question must be exactly like BCS Preliminary exam (PSC standard)
   - Options must be plausible and close
   - Explanation must mention the fact from the news + 1 extra BCS info
   - category must be one of: বাংলাদেশ বিষয়াবলি, আন্তর্জাতিক বিষয়াবলি, সংবিধান ও রাজনীতি, অর্থনীতি, বিজ্ঞান ও প্রযুক্তি, পরিবেশ, খেলাধুলা

4. OUTPUT - Strict JSON only:
{{
  "date": "{today_str}",
  "questions": [
    {{
      "id": 1,
      "category": "অর্থনীতি",
      "question": "সম্প্রতি বাংলাদেশ ব্যাংকের তথ্য অনুযায়ী রেমিট্যান্স কত শতাংশ বেড়েছে?",
      "options": ["ক) ১০%", "খ) ১৫%", "গ) ২২%", "ঘ) ৩০%"],
      "answer": "গ) ২২%",
      "explanation": "বাংলাদেশ ব্যাংকের সর্বশেষ প্রতিবেদন অনুযায়ী... BCS এর জন্য রেমিট্যান্স গুরুত্বপূর্ণ",
      "source": "প্রথম আলো",
      "sourceUrl": "https://www.prothomalo.com/..."
    }}
  ],
  "vocabulary": [
    {{"word":"Sanction","bangla":"নিষেধাজ্ঞা","pronunciation":"স্যাংশন","example":"The US imposed sanction."}},
    {{"word":"Inflation","bangla":"মুদ্রাস্ফীতি","pronunciation":"ইনফ্লেশন","example":"Inflation is rising."}}
  ]
}}

- questions 20 ta MUST, vocabulary 10 ta MUST (BCS high-frequency words from news like sanction, diplomacy, agreement etc)
- sourceUrl MUST be exact URL from NEWS list above
- No markdown, only valid JSON
- If you cannot make 20 from given news, use your knowledge of Bangladesh current affairs to fill remaining but still BCS standard
"""

def generate(p):
    models = ["gemini-2.5-flash","gemini-2.0-flash","gemini-1.5-flash"]
    try:
        for m in client.models.list():
            if 'generateContent' in m.supported_actions:
                n = m.name.replace("models/","")
                if n not in models: models.append(n)
    except: pass
    models = list(dict.fromkeys(models))[:6]
    for model in models:
        try:
            print(f"Trying {model}...")
            r = client.models.generate_content(model=model, contents=p)
            txt = r.text
            if txt and len(txt)>500:
                print(f"✅ {model} success")
                return txt
        except Exception as e:
            print(f"⚠️ {model} {str(e)[:150]}")
            if "503" in str(e): time.sleep(4)
    return None

raw = generate(prompt)
if not raw:
    print("❌ failed"); exit(1)

clean = raw.replace("```json","").replace("```","").strip()
m = re.search(r'\{.*\}', clean, re.DOTALL)
if m: clean = m.group(0)

try:
    data = json.loads(clean)
except Exception as e:
    print(f"JSON fail {e}\n{clean[:3000]}")
    exit(1)

# ensure counts
if len(data.get('questions',[])) < 15:
    print(f"Q low {len(data.get('questions',[]))}"); exit(1)

# vocab fix if low
voc = data.get('vocabulary',[])
if len(voc) < 10:
    print(f"Vocab low {len(voc)}, padding...")
    need = 10 - len(voc)
    p2 = f"Give {need} BCS high-frequency English vocabulary JSON array: [ {{\"word\":\"...\",\"bangla\":\"...\",\"pronunciation\":\"...\",\"example\":\"...\"}} ]"
    r2 = generate(p2)
    if r2:
        m2 = re.search(r'\[.*\]', r2.replace("```json","").replace("```",""), re.DOTALL)
        if m2:
            try:
                extra = json.loads(m2.group(0))
                voc.extend(extra)
            except: pass
    data['vocabulary'] = voc[:10]

while len(data['vocabulary']) < 10:
    data['vocabulary'].append(data['vocabulary'][-1] if data['vocabulary'] else {"word":"Diplomacy","bangla":"কূটনীতি","pronunciation":"ডিপ্লোম্যাসি","example":"Diplomacy is important."})

data['questions'] = data['questions'][:20]

with open("data.json","w",encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Saved {len(data['questions'])} Q, {len(data['vocabulary'])} Vocab - HIGH STANDARD")

with open("sitemap.xml","w",encoding="utf-8") as f:
    f.write(f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://sanju1823.github.io/bcsdailybysanjoy/</loc><lastmod>{today_iso}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>
</urlset>''')
