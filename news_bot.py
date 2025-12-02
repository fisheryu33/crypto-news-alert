# news_bot.py

import os
import time
import requests

CRYPTOPANIC_API_URL = "https://cryptopanic.com/api/v1/posts/"

# 從 Render 設定的環境變數讀取
CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 只追蹤這幾個幣種
TRACKED_COINS = ["BTC", "ETH", "XRP", "SOL", "BNB", "ADA"]

# 查詢 CryptoPanic 的參數（只抓重大新聞 important）
BASE_PARAMS = {
    "auth_token": CRYPTOPANIC_API_KEY,
    "filter": "important",                          # 只抓重大新聞
    "kind": "news",                                 # 只要新聞，不要社群貼文
    "currencies": ",".join(TRACKED_COINS),          # 指定幣種
    "public": "true",
}


def send_telegram(message: str) -> None:
    """把訊息送到 Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID 沒設定，無法發送訊息")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        if not resp.ok:
            print(f"❌ 發送 Telegram 失敗: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        print(f"❌ 發送 Telegram 例外錯誤: {e}")


def fetch_news():
    """從 CryptoPanic 抓重大新聞，只回傳結果 list"""
    try:
        resp = requests.get(CRYPTOPANIC_API_URL, params=BASE_PARAMS, timeout=15)
        if resp.status_code != 200:
            print(f"❌ CryptoPanic HTTP 錯誤: {resp.status_code} {resp.text[:200]}")
            # 非 200 通常是被限流或其他問題，這次就當沒抓到
            return []

        data = resp.json()

        # 如果 API 用完之類的，CryptoPanic 會回傳 error
        if isinstance(data, dict) and "error" in data:
            print(f"❌ CryptoPanic 回傳錯誤: {data['error']}")
            # 丟出去讓外層休息一段時間
            raise RuntimeError("CryptoPanic API error")

        results = data.get("results", [])
        return results

    except Exception as e:
        print(f"❌ 呼叫 CryptoPanic 例外錯誤: {e}")
        # 發生錯誤就回空 list，讓外層決定要不要多休息
        return []


def build_message(item: dict) -> str:
    """把一則新聞轉成 Telegram 要發的文字"""
    title = item.get("title", "(無標題)")
    url = item.get("url") or item.get("source", {}).get("url", "")

    # 把關聯幣種變成字串，例如 BTC, ETH
    currencies = item.get("currencies") or []
    coin_codes = [c.get("code") for c in currencies if c.get("code")]
    coin_text = ", ".join(coin_codes) if coin_codes else "多幣種"

    msg = f"🔔 重大新聞 ({coin_text})\n{title}"
    if url:
        msg += f"\n{url}"

    return msg


def main():
    print("✅ CryptoPanic News Bot 正在運行中")
    print("   ➜ 每 10 分鐘檢查一次")
    print("   ➜ 只推播『重大新聞 important』")
    print("   ➜ 只追蹤幣種：", ", ".join(TRACKED_COINS))

    seen_ids = set()

    while True:
        print("\n🔍 正在檢查最新重大新聞 …")
        news_items = fetch_news()

        if not news_items:
            print("ℹ️ 這次沒有抓到新聞（可能是沒有新重大新聞或 API 限制）")

        new_count = 0

        # 由舊到新發，避免一次來很多時順序亂掉
        for item in reversed(news_items):
            nid = item.get("id")
            if not nid:
                continue

            if nid in seen_ids:
                continue

            seen_ids.add(nid)
            new_count += 1

            msg = build_message(item)
            print(f"📨 推播第 {new_count} 則重大新聞")
            send_telegram(msg)
            # 兩則之間稍微停一下，避免打太快（也比較好看）
            time.sleep(1)

        if new_count == 0:
            print("👌 沒有新的重大新聞")

        # 每 10 分鐘檢查一次（600 秒）
        print("⏱ 下一次檢查在 10 分鐘後 …")
        time.sleep(600)


if __name__ == "__main__":
    main()
