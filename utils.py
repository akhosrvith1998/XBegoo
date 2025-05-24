import requests
from datetime import datetime, timezone, timedelta
import json

TOKEN = "7672898225:AAHymEtVaPhC9SbKKSjCaRlkPx68S4ujLEc"
URL = f"https://api.telegram.org/bot{TOKEN}/"
IRST_OFFSET = timedelta(hours=3, minutes=30)
PROFILE_PHOTO_CACHE = {}  # کش برای عکس‌های پروفایل

def escape_markdown(text):
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + char if char in escape_chars else char for char in text])

def get_irst_time(timestamp):
    utc_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    irst_time = utc_time + IRST_OFFSET
    return irst_time.strftime("%H:%M")

def get_user_profile_photo(user_id):
    if user_id in PROFILE_PHOTO_CACHE:
        return PROFILE_PHOTO_CACHE[user_id]
    
    url = URL + "getUserProfilePhotos"
    params = {"user_id": user_id, "limit": 1}
    resp = requests.get(url, params=params).json()
    if resp.get("ok") and resp["result"]["total_count"] > 0:
        photo = resp["result"]["photos"][0][0]["file_id"]
        PROFILE_PHOTO_CACHE[user_id] = photo
        return photo
    PROFILE_PHOTO_CACHE[user_id] = None
    return None

def answer_inline_query(inline_query_id, results):
    url = URL + "answerInlineQuery"
    data = {
        "inline_query_id": inline_query_id,
        "results": json.dumps(results),
        "cache_time": 0,
        "is_personal": True
    }
    requests.post(url, data=data)

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
    return requests.post(url, data=data)

def format_block_code(whisper_data):
    receiver_display_name = whisper_data['receiver_display_name']
    view_times = whisper_data.get("receiver_views", [])
    view_count = len(view_times)
    view_time_str = get_irst_time(view_times[-1]) if view_times else "هنوز دیده نشده"
    code_content = f"{escape_markdown(receiver_display_name)} {view_count} | {view_time_str}\n___________"
    code_content += "\n" + ("\n".join([escape_markdown(user) for user in whisper_data["curious_users"]]) if whisper_data["curious_users"] else "Nothing")
    return code_content