from flask import Flask
from threading import Thread
import requests
import time

app = Flask('')

@app.route('/')
def home():
    return "I’m alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def ping():
    while True:
        try:
            requests.get("https://xbegoo.onrender.com")
        except:
            pass
        time.sleep(600)  # هر 10 دقیقه

def keep_alive():
    t1 = Thread(target=run)
    t1.start()
    t2 = Thread(target=ping)
    t2.start()