import feedparser
import requests
import time
import json
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://coindesk.com/arc/outboundfeeds/rss/",
    "https://cryptoslate.com/feed/",
]

KEYWORDS = [
    "price", "market", "rally", "crash", "dump", "pump",
    "bitcoin", "btc", "ethereum", "eth", "sec", "etf",
    "fed", "inflation", "liquidat", "ath",
    "bullish", "bearish", "whale", "volume", "trading"
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

def is_relevant(title):
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in KEYWORDS)

def process_with_groq(title):
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": "Bearer " + GROQ_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{
                    "role": "user",
                    "content": "Ты опытный крипто-трейдер. Переведи и перескажи эту новость на русском языке кратко (2-3 предложения) с эмодзи. Без ссылок. Новость: " + title
                }],
                "max_tokens": 200
            },
            timeout=15
        )
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("Groq error: " + str(e))
        return title

def send_to_telegram(text, link):
    url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"
    try:
        res = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": text + "\n\n#новости\n\nЧитать полностью: " + link
        })
        return res.status_code == 200
    except Exception as e:
        print("Telegram error: " + str(e))
        return False

def check_news():
    sent = load_sent()
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                if entry.link not in sent:
                    if is_relevant(entry.title):
                        processed = process_with_groq(entry.title)
                        if send_to_telegram(processed, entry.link):
                            sent.append(entry.link)
                            time.sleep(5)
                    else:
                        sent.append(entry.link)
        except Exception as e:
            print("Feed error: " + str(e))
    save_sent(sent)

if __name__ == "__main__":
    while True:
        check_news()
        time.sleep(600)
