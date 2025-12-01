import os
import time
import threading
import requests
from flask import Flask

# ========= 環境變數 =========
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
CRYPTOPANIC_API_KEY = os.environ.get("CRYPTOPANIC_API_KEY", "")

CRYPTOPANIC_API_URL = "https://cryptopanic.com/api/v1/posts/"

# 記錄已經發過的新聞，避免一直重複
seen_ids = set()

# ========= Telegram =========
def send_telegram(text: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram 環境變數沒設定好，無法發訊息", flush=True)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": False,
    }
    try:
        resp = requests.post(url, data=data, timeout=10)
        resp.raise_for_status()
        print("✅ 已發送訊息到 Telegram", flush=True)
    except Exception as e:
        print(f"❌ 發送 Telegram 失敗: {e}", flush=True)


# ========= CryptoPanic =========
def fetch_news():
    if not CRYPTOPANIC_API_KEY:
        print("CRYPTOPANIC_API_KEY 沒設定，略過抓新聞", flush=True)
        return []

    params = {
        "auth_token": CRYPTOPANIC_API_KEY,
        "kind": "news",          # 只要新聞
        "filter": "rising",      # 上漲相關 / 熱門新聞
        "public": "true",
        "currencies": "BTC,ETH,SOL,ADA,XRP",
    }

    try:
        resp = requests.get(CRYPTOPANIC_API_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        print(f"📩 取得 {len(results)} 筆新聞", flush=True)
        return results
    except Exception as e:
        print(f"❌ 取得 CryptoPanic 新聞失敗: {e}", flush=True)
        return []


def format_message(item: dict) -> str:
    title = item.get("title", "(無標題)")
    url = item.get("url") or item.get("source", {}).get("url", "")

    vote = (item.get("vote") or {}).get("value")
    if vote == "positive":
        tag = "🟢 多頭"
    elif vote == "negative":
        tag = "🔴 空頭"
    else:
        tag = "⚪️ 中性"

    return f"{tag}\n{title}\n{url}"


# ========= 背景新聞機器人主迴圈 =========
def news_worker_loop():
    print("🚀 Crypto News Bot 背景執行緒啟動！", flush=True)
    send_telegram("🟢 Crypto News Bot 已啟動，開始監控 CryptoPanic 新聞。")

    while True:
        try:
            news_list = fetch_news()
            for item in news_list:
                nid = item.get("id")
                if nid is None or nid in seen_ids:
                    continue

                seen_ids.add(nid)
                msg = format_message(item)
                send_telegram(msg)

        except Exception as e:
            print(f"⚠️ 背景迴圈發生錯誤：{e}", flush=True)

        # 每 60 秒掃一次
        time.sleep(60)


# ========= Flask Web Service =========
app = Flask(__name__)


@app.route("/")
def index():
    return "Crypto News Alert bot is running.", 200


def start_background_worker():
    t = threading.Thread(target=news_worker_loop, daemon=True)
    t.start()
    print("🧵 背景新聞執行緒已啟動", flush=True)


if __name__ == "__main__":
    # 啟動背景執行緒 ＋ Web Server（給 Render 用）
    start_background_worker()
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 啟動 Flask Web 伺服器，port={port}", flush=True)
    app.run(host="0.0.0.0", port=port)

