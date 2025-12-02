import os
import time
import requests
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Crypto News Bot is running!"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY")

API_URL = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_API_KEY}&filter=important"

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    requests.post(url, json=payload)

def fetch_news():
    try:
        response = requests.get(API_URL)
        data = response.json()

        results = data.get("results", [])

        if results:
            for item in results[:5]:
                message = f"🔥重要新聞🔥\n{item['title']}\n{item['url']}"
                send_message(message)

        print("取得新聞完成")

    except Exception as e:
        print("錯誤:", e)

if __name__ == "__main__":
    print("CryptoPanic News Bot 已啟動（每 10 分鐘檢查一次）")
    while True:
        fetch_news()
        time.sleep(600)
