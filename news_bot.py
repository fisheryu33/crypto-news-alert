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


def send_telegram(msg: str) -> None:
    """發送訊息到 Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram 設定尚未完成，請確認環境變數。")
        return

    try:
        requests.get(
            TELEGRAM_URL,
            params={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
            timeout=10,
        )
    except Exception as e:
        print("Telegram Error:", e)


def fetch_news():
    """從 CryptoPanic 抓取最新消息"""
    if not CRYPTOPANIC_API_KEY:
        print("CRYPTOPANIC_API_KEY 尚未設定，略過抓新聞。")
        return []

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


def run_once():
    """跑一次抓新聞 + 發送"""
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
        print("Send:", msg)
        send_telegram(msg)


def main():
    """主迴圈，每 60 秒檢查一次"""
    print("🚀 Crypto News Bot Started...")
    while True:
        run_once()
        time.sleep(60)


if __name__ == "__main__":
    main()
