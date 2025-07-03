import threading
import time
import datetime
import requests
from flask import Flask
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "I'm alive!"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    # Flask 서버 별도 스레드로 실행
    t = threading.Thread(target=run)
    t.start()

    # 자기 자신 주기적 핑 함수
    def ping():
        url = os.environ.get("PING_URL")  # 환경변수로 URL 받기
        if not url:
            print("PING_URL 환경변수가 설정되지 않았습니다.")
            return

        while True:
            try:
                requests.get(url)
                print("Ping sent to", url)
            except Exception as e:
                print("Ping failed:", e)
            time.sleep(300)  # 5분마다 ping

    ping_thread = threading.Thread(target=ping)
    ping_thread.start()




