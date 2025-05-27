import sqlite3
from utils import get_user_profile_photo

DATABASE = "history.db"

def init_database():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            sender_id TEXT,
            receiver_id TEXT,
            display_name TEXT,
            first_name TEXT,
            profile_photo_url TEXT,
            PRIMARY KEY (sender_id, receiver_id)
        )
    """)
    conn.commit()
    conn.close()

def load_history():
    history = {}
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT sender_id, receiver_id, display_name, first_name, profile_photo_url FROM history")
    rows = cursor.fetchall()
    for row in rows:
        sender_id, receiver_id, display_name, first_name, profile_photo_url = row
        if sender_id not in history:
            history[sender_id] = []
        history[sender_id].append({
            "receiver_id": receiver_id,
            "display_name": display_name,
            "first_name": first_name,
            "profile_photo_url": profile_photo_url,
            "curious_users": set()  # برای سازگاری با کد قبلی
        })
    conn.close()
    return history

def save_history(sender_id, receiver):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO history (sender_id, receiver_id, display_name, first_name, profile_photo_url)
        VALUES (?, ?, ?, ?, ?)
    """, (sender_id, receiver["receiver_id"], receiver["display_name"], receiver["first_name"], receiver["profile_photo_url"]))
    conn.commit()
    conn.close()
    # به‌روزرسانی حافظه
    from database import history
    if sender_id not in history:
        history[sender_id] = []
    existing = next((r for r in history[sender_id] if r["receiver_id"] == receiver["receiver_id"]), None)
    if not existing:
        history[sender_id].append(receiver)
        history[sender_id] = history[sender_id][-10:]  # محدود به 10 گیرنده

# مقداردهی اولیه دیتابیس
init_database()
history = load_history()