import feedparser
import requests
import time
import json
import os

# --- НАЛАШТУВАННЯ (Впиши свої дані тут) ---
BOT_TOKEN = "ТВІЙ_ТЕЛЕГРАМ_БОТ_ТОКЕН"
CHAT_ID = "ТВІЙ_ID_КАНАЛУ_АБО_ЧАТУ"
GEMINI_API_KEY = "ТВІЙ_GEMINI_API_КЛЮЧ"

# Список джерел новин
RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://coindesk.com/arc/outboundfeeds/rss/",
    "https://cryptoslate.com/feed/",
    "https://theblock.co/rss.xml",
]

SENT_FILE = "sent_news.json"

def load_sent():
    """Завантажує список уже надісланих новин."""
    if os.path.exists(SENT_FILE):
        try:
            with open(SENT_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_sent(sent):
    """Зберігає останні 500 посилань, щоб не дублювати пости."""
    with open(SENT_FILE, "w") as f:
        json.dump(sent[-500:], f)

def process_with_gemini(title):
    """Відправляє заголовок новини в Gemini для перекладу та стилізації."""
    # Використовуємо стабільну модель 1.5 Flash (безкоштовна версія)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = (
        f"Ты опытный крипто-трейдер. Переведи эту новость на русский язык "
        f"и перескажи её в стиле короткого поста для Telegram. Будь дерзким, "
        f"используй 1-2 эмодзи. Максимум 3 предложения. Не пиши ссылки.\n\n"
        f"Новость: {title}"
    )

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        data = response.json()
        
        # Перевірка структури відповіді Google API
        if "candidates" in data and len(data["candidates"]) > 0:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            print(f"⚠️ Помилка Gemini API: {data.get('error', {}).get('message', 'Невідома помилка')}")
            return title # Якщо помилка, повертаємо оригінал
    except Exception as e:
        print(f"⚠️ Помилка з'єднання з Gemini: {e}")
        return title

def send_to_telegram(text, link):
    """Надсилає готовий текст у Telegram канал."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # Формуємо красиве повідомлення з HTML-розміткою
    message_text = f"{text}\n\n🔗 <a href='{link}'>Читать полностью</a>"
    
    payload = {
        "chat_id": CHAT_ID,
        "text": message_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    
    try:
        res = requests.post(url, json=payload)
        return res.status_code == 200
    except Exception as e:
        print(f"⚠️ Помилка Telegram: {e}")
        return False

def check_news():
    """Головна функція перевірки нових постів."""
    sent = load_sent()
    print(f"--- Перевірка новин: {time.strftime('%H:%M:%S')} ---")
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            # Перевіряємо тільки 3 найсвіжіші новини з кожного джерела
            for entry in feed.entries[:3]:
                if entry.link not in sent:
                    print(f"🔄 Обробка: {entry.title}")
                    
                    # Отримуємо обробку від AI
                    processed_text = process_with_gemini(entry.title)
                    
                    # Надсилаємо в ТГ
                    if send_to_telegram(processed_text, entry.link):
                        print(f"✅ Опубліковано: {entry.link}")
                        sent.append(entry.link)
                        time.sleep(5) # Пауза між постами, щоб уникнути спам-фільтру
                    else:
                        print(f"❌ Не вдалося надіслати в Telegram")
        except Exception as e:
            print(f"⚠️ Помилка фіду {feed_url}: {e}")
    
    save_sent(sent)

if __name__ == "__main__":
    print("🚀 Бот запущений!")
    while True:
        check_news()
        print("☕ Чекаю 10 хвилин до наступної перевірки...")
        time.sleep(600) # Перевірка кожні 10 хвилин
