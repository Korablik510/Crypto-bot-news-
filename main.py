import feedparser
import requests
import time
import json
import os

# Переконайся, що ці змінні оточення встановлені
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
    try:
        # Використовуємо стабільну версію 1.5 flash
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        headers = {'Content-Type': 'application/json'}
        prompt = f"Ты опытный крипто-трейдер. Переведи и перескажи новость на русском языке кратко (2-3 предложения) с эмодзи: {title}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        # Перевірка наявності відповіді в структурі JSON
        if "candidates" in data and len(data["candidates"]) > 0:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            print(f"Gemini API error: {data}")
            return f"Новость: {title}" # Повертаємо оригінал, якщо API не відповіло
            
    except Exception as e:
        print(f"Gemini connection error: {e}")
        return title

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        res = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        })
        return res.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def check_news():
    sent = load_sent()
    print("Checking for news...")
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:3]: # Беремо тільки 3 останні новини з кожного фіду
                if entry.link not in sent:
                    print(f"Processing: {entry.title}")
                    
                    processed = process_with_gemini(entry.title)
                    msg = f"<b>{processed}</b>\n\n🔗 <a href='{entry.link}'>Источник</a>"
                    
                    if send_to_telegram(msg):
                        sent.append(entry.link)
                        time.sleep(2) # Пауза, щоб не спамити Telegram API
        except Exception as e:
            print(f"Feed error ({feed_url}): {e}")
            
    save_sent(sent)

if __name__ == "__main__":
    while True:
        check_news()
        print("Sleeping for 10 minutes...")
        time.sleep(600) # Перевіряти кожні 10 хвилин, щоб не вичерпати ліміти
