from flask import Flask, request, Response
import requests
import os
from main import process_update
from reply_whisper import process_reply_whisper
from logger import logger

app = Flask(__name__)
TOKEN = "7844345303:AAGyDzl4oJjm646ePdx0YQP32ARuhWL6qHk"
URL = f"https://api.telegram.org/bot{TOKEN}/"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = request.get_json()
        logger.info("Received update: %s", update)
        if "inline_query" in update:
            threading.Thread(target=process_update, args=(update,)).start()
        elif "message" in update and "reply_to_message" in update["message"]:
            threading.Thread(target=process_reply_whisper, args=(update,)).start()
        return Response(status=200)
    except Exception as e:
        logger.error("Webhook error: %s", str(e))
        return Response(status=500)

if __name__ == "__main__":
    webhook_url = os.getenv("WEBHOOK_URL", "https://your-render-app.onrender.com/webhook")
    response = requests.get(f"{URL}setWebhook?url={webhook_url}")
    logger.info("Webhook set: %s", response.text)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))