import os
import time
import requests

# 從環境變數讀取金鑰
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CRYPTOPANIC_API_KEY = os.environ.get("CRYPTOPANIC_API_KEY")

TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
CRYPTOPANIC_URL = "https://cryptopanic.com/api/v1/posts/"

seen_news = set()

def send_telegram(msg):
    try:
        requests.get(
            TELEGRAM_URL,
            params={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
            timeout=10
        )
    except Exception as e:
        print("Telegram Error:", e)

def fetch_news():
    params = {
        "auth_token": CRYPTOPANIC_API_KEY,
        "public": "true",
        "filter": "important",
        "currencies": "BTC,ETH",
    }
    try:
        resp = requests.get(CRYPTOPANIC_URL, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json().get("results", [])
    except Exception as e:
        print("CryptoPanic Error:", e)
        return []

def main():
    print("🚀 Crypto News Bot Started...")
    while True:
        for item in fetch_news():
            nid = item.get("id")
            if nid in seen_news:
                continue
            seen_news.add(nid)

            title = item.get("title", "")
            url = item.get("url", "")
            sentiment = item.get("vote", {}).get("value")

            if sentiment == "bullish":
                tag = "📈 利多"
            elif sentiment == "bearish":
                tag = "📉 利空"
            else:
                tag = "📰 消息"

            msg = f"{tag}\n{title}\n{url}"
            send_telegram(msg)

        time.sleep(60)

if __name__ == "__main__":
    main()
