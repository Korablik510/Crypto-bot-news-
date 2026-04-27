import feedparser
import requests
import time
import json
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

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
                    msg = f"📊 <b>{entry.title}</b>\n\n🔗 {entry.link}"
                    send_to_telegram(msg)
                    sent.append(entry.link)
                    time.sleep(2)
        except Exception as e:
            print(f"Помилка: {e}")
    save_sent(sent)

while True:
    check_news()
    time.sleep(1800)
