import feedparser
import requests
import time
import json
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://coindesk.com/arc/outboundfeeds/rss/",
    "https://cryptoslate.com/feed/",
    "https://theblock.co/rss.xml",
]

SENT_FILE = "sent_news.json"

def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE) as f:
            return json.load(f)
    return []

def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(sent[-500:], f)

def process_with_gemini(title):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={GEMINI_API_KEY}"
        prompt = f"""Ты опытный крипто-трейдер который ведет Telegram канал.
Перепиши эту новость на русском языке в своем стиле: коротко, по делу, с эмоциями настоящего трейдера.
Добавь 1-2 эмодзи. Максимум 3-4 предложения. Без ссылки.

Новость: {title}"""

        response = requests.post(url, json={
            "contents": [{"parts": [{"text": prompt}]}]
        })
        data = response.json()
        print("Gemini response:", data)
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Gemini error: {e}")
        return title

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    })

def check_news():
    sent = load_sent()
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:3]:
                if entry.link not in sent:
                    processed = process_with_gemini(entry.title)
                    msg = f"{processed}\n\n🔗 {entry.link}"
                    send_to_telegram(msg)
                    sent.append(entry.link)
                    time.sleep(3)
        except Exception as e:
            print(f"Помилка: {e}")
    save_sent(sent)

while True:
    check_news()
    time.sleep(1800)
