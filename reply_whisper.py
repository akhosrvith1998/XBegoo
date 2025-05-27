import json
import uuid
import requests
from utils import escape_markdown, get_irst_time, get_user_profile_photo, answer_inline_query, answer_callback_query, edit_message_text, format_block_code
from database import history, save_history
from cache import get_cached_inline_query, set_cached_inline_query
from logger import logger

whispers = {}
BOT_USERNAME = "XBCodebot"
TOKEN = "7844345303:AAGyDzl4oJjm646ePdx0YQP32ARuhWL6qHk"
URL = f"https://api.telegram.org/bot{TOKEN}/"

def process_reply_whisper(update):
    if "message" in update and "reply_to_message" in update["message"]:
        message = update["message"]
        text = message.get("text", "")
        if text.startswith(f"@{BOT_USERNAME} "):
            secret_message = text.replace(f"@{BOT_USERNAME} ", "", 1).strip()
            reply_to = message["reply_to_message"]
            receiver = reply_to["from"]
            receiver_id = str(receiver["id"])
            receiver_username = receiver.get("username", "").lstrip('@').lower() if receiver.get("username") else None
            receiver_display_name = f"@{receiver_username}" if receiver_username else str(receiver_id)

            sender = message["from"]
            sender_id = str(sender["id"])
            sender_username = sender.get("username", "").lstrip('@').lower() if sender.get("username") else None
            sender_display_name = f"{sender.get('first_name', '')} {sender.get('last_name', '')}".strip() if sender.get('last_name') else sender.get('first_name', '')

            unique_id = uuid.uuid4().hex

            profile_photo = get_user_profile_photo(receiver_id)
            profile_photo_url = f"https://api.telegram.org/file/bot{TOKEN}/{profile_photo}" if profile_photo else ""

            existing_receiver = next((r for r in history.get(sender_id, []) if r["receiver_id"] == receiver_id), None)
            if not existing_receiver:
                if sender_id not in history:
                    history[sender_id] = []
                receiver_data = {
                    "receiver_id": receiver_id,
                    "display_name": receiver_display_name,
                    "first_name": receiver.get("first_name", ""),
                    "profile_photo_url": profile_photo_url,
                    "curious_users": set()
                }
                history[sender_id].append(receiver_data)
                history[sender_id] = history[sender_id][-10:]
                save_history(sender_id, receiver_data)

            whispers[unique_id] = {
                "sender_id": sender_id,
                "sender_username": sender_username,
                "sender_display_name": sender_display_name,
                "receiver_username": receiver_username,
                "receiver_user_id": receiver_id,
                "receiver_display_name": receiver_display_name,
                "secret_message": secret_message,
                "curious_users": set(),
                "receiver_views": []
            }

            receiver_id_display = escape_markdown(receiver_display_name)
            code_content = format_block_code(whispers[unique_id]).replace("هنوز دیده نشده", "Unopened")
            public_text = f"{receiver_id_display}\n\n```\n{code_content}\n```"

            reply_target = f"@{sender_username}" if sender_username else str(sender_id)
            reply_text = f"{reply_target} "
            keyboard = {
                "inline_keyboard": [[
                    {"text": "👁️ show", "callback_data": f"show|{unique_id}"},
                    {"text": "🗨️ reply", "switch_inline_query_current_chat": reply_text}
                ]]
            }

            # ارسال پیام به چت
            url = URL + "sendMessage"
            data = {
                "chat_id": message["chat"]["id"],
                "text": public_text,
                "parse_mode": "MarkdownV2",
                "reply_markup": json.dumps(keyboard)
            }
            requests.post(url, data=data)

            # پاسخ به کاربر
            url = URL + "sendMessage"
            data = {
                "chat_id": message["chat"]["id"],
                "text": f"نجوا به {receiver_display_name} ارسال شد.",
                "reply_to_message_id": message["message_id"]
            }
            requests.post(url, data=data)