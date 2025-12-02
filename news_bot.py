import os
import time
import requests
import logging

CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

API_URL = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_API_KEY}&kind=news"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

last_post_id = None

def fetch_news():
    global last_post_id

    try:
        response = requests.get(API_URL, timeout=10)
        data = response.json()

        if "results" not in data:
            logging.error("API response invalid:", data)
            return

        posts = data["results"]

        if not posts:
            return

        latest = posts[0]

        # 如果是第一次運作，把最新一篇的 ID 記起來，不發送，避免洗版
        if last_post_id is None:
            last_post_id = latest["id"]
            logging.info("Initialize latest post ID:", latest["id"])
            return

        # 找到所有比 last_post_id 更新的新聞
        new_posts = []
        for p in posts:
            if p["id"] == last_post_id:
                break
            new_posts.append(p)

        if not new_posts:
            logging.info("No new posts")
            return

        # 逆序，最舊的先送
        for p in reversed(new_posts):
            send_to_telegram(p)

        # 更新 last_post_id
        last_post_id = latest["id"]

    except Exception as e:
        logging.error(f"Error fetching news: {e}")


def send_to_telegram(post):
    title = post.get("title", "No title")
    link = post.get("url", "")

    message = f"🟢 新聞更新：\n\n{title}\n{link}"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}

    try:
        requests.post(url, data=payload, timeout=10)
        logging.info(f"發送成功：{title}")
    except Exception as e:
        logging.error(f"Telegram 錯誤：{e}")


# 主迴圈
logging.info("📡 CryptoPanic News Bot 正在運行中（每 10 分鐘檢查一次）")

while True:
    fetch_news()
    time.sleep(600)   # 10分鐘
