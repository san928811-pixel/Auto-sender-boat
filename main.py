import os
import re
import sqlite3
import secrets
from urllib.parse import quote
from flask import Flask, redirect, abort
import threading
import telebot

# =========================
# SETTINGS
# =========================

TOKEN = os.getenv("BOT_TOKEN")

# Yahan apne deployed web app ka URL lagana hai
# Example:
# https://your-bot.onrender.com
SHORT_BASE_URL = os.getenv(
    "SHORT_BASE_URL",
    "https://YOUR-APP-DOMAIN.com"
)

BLOGGER_BASE_URL = (
    "https://quickfileshare.blogspot.com/2026/09/welcome-zone.html"
)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DB_FILE = "links.db"


# =========================
# DATABASE
# =========================

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS links (
            code TEXT PRIMARY KEY,
            original_url TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_link(original_url):
    # Chhota random code
    code = secrets.token_urlsafe(5).replace("-", "").replace("_", "")[:7]

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Duplicate code avoid karo
    while True:
        cur.execute(
            "SELECT code FROM links WHERE code = ?",
            (code,)
        )

        if cur.fetchone() is None:
            break

        code = secrets.token_urlsafe(5).replace("-", "").replace("_", "")[:7]

    cur.execute(
        "INSERT INTO links (code, original_url) VALUES (?, ?)",
        (code, original_url)
    )

    conn.commit()
    conn.close()

    return code


def get_original_url(code):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute(
        "SELECT original_url FROM links WHERE code = ?",
        (code,)
    )

    result = cur.fetchone()

    conn.close()

    if result:
        return result[0]

    return None


# =========================
# SHORT LINK REDIRECT
# =========================

@app.route("/r/<code>")
def redirect_short_link(code):

    original_url = get_original_url(code)

    if not original_url:
        abort(404)

    # Tumhara existing Blogger flow
    blogger_url = (
        BLOGGER_BASE_URL
        + "?to="
        + quote(original_url, safe="")
    )

    return redirect(blogger_url, code=302)


# =========================
# CREATE SHORT LINK
# =========================

def make_short_link(original_url):

    code = save_link(original_url)

    return f"{SHORT_BASE_URL}/r/{code}"


# =========================
# TEXT
# =========================

@bot.message_handler(content_types=["text"])
def handle_text(message):

    text = message.text or ""

    pattern = r'https?://[^\s]+'

    def replace(match):

        url = match.group(0).rstrip('.,!?)]}')

        # Original URL save hogi
        # User ko short URL milegi
        return make_short_link(url)

    new_text = re.sub(pattern, replace, text)

    bot.send_message(
        message.chat.id,
        new_text,
        disable_web_page_preview=True
    )


# =========================
# CAPTION
# =========================

def convert_caption(message):

    caption = message.caption or ""

    pattern = r'https?://[^\s]+'

    def replace(match):

        url = match.group(0).rstrip('.,!?)]}')

        return make_short_link(url)

    return re.sub(pattern, replace, caption)


# =========================
# PHOTO
# =========================

@bot.message_handler(content_types=["photo"])
def handle_photo(message):

    new_caption = convert_caption(message)

    bot.send_photo(
        message.chat.id,
        message.photo[-1].file_id,
        caption=new_caption
    )


# =========================
# VIDEO
# =========================

@bot.message_handler(content_types=["video"])
def handle_video(message):

    new_caption = convert_caption(message)

    bot.send_video(
        message.chat.id,
        message.video.file_id,
        caption=new_caption
    )


# =========================
# DOCUMENT
# =========================

@bot.message_handler(content_types=["document"])
def handle_document(message):

    new_caption = convert_caption(message)

    bot.send_document(
        message.chat.id,
        message.document.file_id,
        caption=new_caption
    )


# =========================
# HEALTH CHECK
# =========================

@app.route("/")
def home():
    return "Link Converter Bot is running."


# =========================
# FLASK SERVER
# =========================

def run_web():
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )


# =========================
# MAIN
# =========================

if __name__ == "__main__":

    init_db()

    # Web server alag thread me
    threading.Thread(
        target=run_web,
        daemon=True
    ).start()

    print("🤖 Bot is running...")

    bot.infinity_polling(
        skip_pending=True
    )
