import requests
import time
import json
import uuid
from datetime import datetime, timezone, timedelta
import threading

TOKEN = "7672898225:AAHymEtVaPhC9SbKKSjCaRlkPx68S4ujLEc"
BOT_USERNAME = "XBegoobot"
URL = f"https://api.telegram.org/bot{TOKEN}/"

whispers = {}

# اختلاف زمانی تهران (IRST) با UTC (+3:30)
IRST_OFFSET = timedelta(hours=3, minutes=30)

def escape_markdown(text):
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + char if char in escape_chars else char for char in text])

def get_irst_time(timestamp):
    """تبدیل زمان UTC به IRST"""
    utc_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    irst_time = utc_time + IRST_OFFSET
    return irst_time.strftime("%H:%M")

def get_updates(offset=None):
    url = URL + "getUpdates"
    params = {"timeout": 15, "offset": offset}  # افزایش timeout به 15 ثانیه
    resp = requests.get(url, params=params)
    return resp.json()

def answer_inline_query(inline_query_id, results):
    url = URL + "answerInlineQuery"
    data = {
        "inline_query_id": inline_query_id,
        "results": json.dumps(results),
        "cache_time": 0,
        "is_personal": True
    }
    resp = requests.post(url, data=data)
    if resp.status_code != 200:
        print(f"Error answering inline query: {resp.text}")

def answer_callback_query(callback_query_id, text, show_alert=False):
    url = URL + "answerCallbackQuery"
    data = {
        "callback_query_id": callback_query_id,
        "text": text,
        "show_alert": show_alert
    }
    requests.post(url, data=data)

def edit_message_text(chat_id=None, message_id=None, inline_message_id=None, text=None, reply_markup=None):
    url = URL + "editMessageText"
    data = {
        "text": text,
        "parse_mode": "MarkdownV2",
        "reply_markup": json.dumps(reply_markup) if reply_markup else None
    }
    if chat_id and message_id:
        data["chat_id"] = chat_id
        data["message_id"] = message_id
    elif inline_message_id:
        data["inline_message_id"] = inline_message_id
    else:
        raise ValueError("Either (chat_id and message_id) or inline_message_id must be provided.")
    response = requests.post(url, data=data)
    if response.status_code != 200:
        print(f"Failed to edit message: {response.text}")
    return response

def format_block_code(whisper_data):
    receiver_display_name = whisper_data['receiver_display_name']
    view_times = whisper_data.get("receiver_views", [])
    view_count = len(view_times)
    view_time_str = get_irst_time(view_times[-1]) if view_times else "هنوز دیده نشده"
    code_content = f"{escape_markdown(receiver_display_name)} {view_count} | {view_time_str}\n"
    code_content += "___________"

    if whisper_data["curious_users"]:
        code_content += "\n" + "\n".join([escape_markdown(user) for user in whisper_data["curious_users"]])
    else:
        code_content += "\nNothing"

    return code_content

def process_update(update):
    if "inline_query" in update:
        inline_query = update["inline_query"]
        query_id = inline_query["id"]
        raw_query = inline_query.get("query", "").strip()
        query_text = raw_query.replace(f"@{BOT_USERNAME}", "", 1).strip()
        
        base_result = {
            "type": "article",
            "id": "base",
            "title": "💡 راهنمای نجوا",
            "input_message_content": {
                "message_text": f"✅ فرمت صحیح: @{BOT_USERNAME} @یوزرنیم یا آیدی_عددی پیام\nمثال: @{BOT_USERNAME} @user1 سلام یا @{BOT_USERNAME} 123456789 سلام"
            },
            "description": "همیشه فعال!"
        }

        if not query_text:
            answer_inline_query(query_id, [base_result])
            return

        try:
            parts = query_text.split(" ", 1)
            if len(parts) < 2:
                raise ValueError("فرمت نامعتبر")

            receiver_id = parts[0]
            secret_message = parts[1].strip()

            receiver_username = None
            receiver_user_id = None

            if receiver_id.startswith('@'):
                receiver_username = receiver_id.lstrip('@').lower()
            elif receiver_id.isdigit():
                receiver_user_id = int(receiver_id)
            else:
                raise ValueError("شناسه گیرنده نامعتبر")

            unique_id = uuid.uuid4().hex

            sender = inline_query["from"]
            sender_id = sender["id"]
            sender_username = sender.get("username", "").lstrip('@').lower() if sender.get("username") else None
            sender_display_name = f"{sender.get('first_name', '')} {sender.get('last_name', '')}".strip() if sender.get('last_name') else sender.get('first_name', '')

            receiver_display_name = f"@{receiver_username}" if receiver_username else str(receiver_user_id) if receiver_user_id else "ناشناس"

            whispers[unique_id] = {
                "sender_id": sender_id,
                "sender_username": sender_username,
                "sender_display_name": sender_display_name,
                "receiver_username": receiver_username,
                "receiver_user_id": receiver_user_id,
                "receiver_display_name": receiver_display_name,
                "secret_message": secret_message,
                "curious_users": set(),
                "receiver_views": []
            }

            receiver_id_display = escape_markdown(receiver_display_name)
            code_content = format_block_code(whispers[unique_id])
            public_text = (
                f"{receiver_id_display}\n\n"
                f"```\n{code_content}\n```"
            )

            reply_target = f"@{sender_username}" if sender_username else str(sender_id)
            reply_text = f"{reply_target} "

            keyboard = {
                "inline_keyboard": [[
                    {"text": "👁️ show", "callback_data": f"show|{unique_id}"},
                    {"text": "🗨️ reply", "switch_inline_query_current_chat": reply_text}
                ]]
            }

            results = [
                {
                    "type": "article",
                    "id": unique_id,
                    "title": f"🔒 نجوا به {receiver_display_name}",
                    "input_message_content": {
                        "message_text": public_text,
                        "parse_mode": "MarkdownV2"
                    },
                    "reply_markup": keyboard,
                    "description": f"پیام: {secret_message[:15]}..."
                },
                base_result
            ]

            answer_inline_query(query_id, results)

        except Exception as e:
            print(f"خطا در inline query: {str(e)}")
            answer_inline_query(query_id, [base_result])

    elif "callback_query" in update:
        callback = update["callback_query"]
        callback_id = callback["id"]
        data = callback["data"]
        message = callback.get("message")
        inline_message_id = callback.get("inline_message_id")

        if data.startswith("show|"):
            _, unique_id = data.split("|", 1)
            whisper_data = whispers.get(unique_id)

            if not whisper_data:
                answer_callback_query(callback_id, "⌛️ منقضی شده!", False)
                return

            user = callback["from"]
            user_id = user["id"]
            username = user.get("username", "").lstrip('@').lower() if user.get("username") else None
            first_name = user.get("first_name", "")
            last_name = user.get("last_name", "")
            user_display_name = f"{first_name} {last_name}".strip() if last_name else first_name

            is_allowed = (
                user_id == whisper_data["sender_id"] or
                (whisper_data["receiver_username"] and username and username.lower() == whisper_data["receiver_username"]) or
                (whisper_data["receiver_user_id"] and user_id == whisper_data["receiver_user_id"])
            )

            if is_allowed and user_id != whisper_data["sender_id"]:
                whisper_data["receiver_views"].append(time.time())
                whisper_data["receiver_display_name"] = f"@{username}" if username else str(user_id)

            if not is_allowed:
                whisper_data["curious_users"].add(user_display_name)

            receiver_id_display = escape_markdown(whisper_data["receiver_display_name"])
            code_content = format_block_code(whisper_data)
            new_text = (
                f"{receiver_id_display}\n\n"
                f"```\n{code_content}\n```"
            )

            reply_target = f"@{whisper_data['sender_username']}" if whisper_data['sender_username'] else str(whisper_data['sender_id'])
            reply_text = f"{reply_target} "
            keyboard = {
                "inline_keyboard": [[
                    {"text": "👁️ show", "callback_data": f"show|{unique_id}"},
                    {"text": "🗨️ reply", "switch_inline_query_current_chat": reply_text}
                ]]
            }

            if message:
                edit_message_text(
                    chat_id=message["chat"]["id"],
                    message_id=message["message_id"],
                    text=new_text,
                    reply_markup=keyboard
                )
            elif inline_message_id:
                edit_message_text(
                    inline_message_id=inline_message_id,
                    text=new_text,
                    reply_markup=keyboard
                )

            response_text = (
                f"🔐 پیام نجوا:\n{whisper_data['secret_message']}" 
                if is_allowed 
                else "⚠️ نجوا مال تو نیست!"
            )

            answer_callback_query(callback_id, response_text, is_allowed)

def main():
    offset = None
    print("ربات در حال اجراست...")
    while True:
        updates = get_updates(offset)
        for update in updates.get("result", []):
            offset = update["update_id"] + 1
            threading.Thread(target=process_update, args=(update,)).start()
        time.sleep(0.05)  # کاهش sleep برای واکنش سریع‌تر

if __name__ == "__main__":
    main()
