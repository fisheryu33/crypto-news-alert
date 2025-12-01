import os
import threading
from flask import Flask
from news_bot import main

app = Flask(__name__)


@app.route("/")
def index():
    return "Crypto News Bot is running"


def start_bot():
    # 在背景執行 Telegram 新聞機器人
    main()


# daemon=True：主程式結束時一起關閉
threading.Thread(target=start_bot, daemon=True).start()

if __name__ == "__main__":
    # Render 會給一個 PORT 環境變數，沒給就用 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
