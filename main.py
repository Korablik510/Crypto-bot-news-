Бачу новий код! Але проблема в тому що тут знову gemini-1.5-flash і токени вписані прямо в код ("ТВІЙ_ТЕЛЕГРАМ_БОТ_ТОКЕН") — це небезпечно бо репозиторій публічний!
Давай зробимо правильно — встав цей код але з виправленнями:

import feedparser
import requests
import time
import json
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://coindesk.com/arc/outboundfeeds/rss/",
    "https://cryptoslate.com/feed/",
]

SENT_FILE = "sent_news.json"

def load_sent():
    if os.path.exists(SENT_FILE):
        try:
            with open(SENT_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(sent[-500:], f)

def process_with_gemini(title):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"Ты опытный крипто-трейдер. Переведи и перескажи новость на русском языке кратко (2-3 предложения) с эмодзи: {title}"
    try:
        response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
        data = response.json()
        if "candidates" in data:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        print(f"Gemini error: {data}")
        return title
    except Exception as e:
        print(f"Gemini error: {e}")
        return title

def send_to_telegram(text, link):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        res = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": f"{text}\n\n🔗 <a href='{link}'>Читать полностью</a>",
            "parse_mode": "HTML"
        })
        return res.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def check_news():
    sent = load_sent()
    print(f"Перевірка новин: {time.strftime('%H:%M:%S')}")
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:3]:
                if entry.link not in sent:
                    processed = process_with_gemini(entry.title)
                    if send_to_telegram(processed, entry.link):
                        sent.append(entry.link)
                        time.sleep(5)
        except Exception as e:
            print(f"Feed error: {e}")
    save_sent(sent)

if __name__ == "__main__":
    print("Бот запущений!")
    while True:
        check_news()
        print("Чекаю 10 хвилин...")
        time.sleep(600)
