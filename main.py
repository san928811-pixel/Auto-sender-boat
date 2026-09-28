import os
import re
import sqlite3
import secrets
import threading

import telebot
from flask import Flask, redirect
from urllib.parse import quote

# =========================
# SETTINGS
# =========================

TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Tumhara Railway domain
SHORT_BASE_URL = "https://worker-production-ce31.up.railway.app"

# Tumhari existing Blogger website
BLOGGER_BASE_URL = (
    "https://quickfileshare.blogspot.com/2026/09/welcome-zone.html"
)

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


def create_short_code():
    return secrets.token_urlsafe(6).replace("-", "").replace("_", "")[:8]


def save_link(original_url):
    while True:
        code = create_short_code()

        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()

        cur.execute(
            "SELECT code FROM links WHERE code = ?",
            (code,)
        )

        exists = cur.fetchone()

        if not exists:
            cur.execute(
                """
                INSERT INTO links (code, original_url)
                VALUES (?, ?)
                """,
                (code, original_url)
            )

            conn.commit()
            conn.close()

            return code

        conn.close()


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
# CREATE SHORT LINK
# =========================

def make_short_link(original_url):
    code = save_link(original_url)

    return f"{SHORT_BASE_URL}/terashare/{code}"


# =========================
# SHORT LINK REDIRECT
# =========================

@app.route("/terashare/<code>")
def open_short_link(code):

    original_url = get_original_url(code)

    if not original_url:
        return "Link not found", 404

    # Original system exactly yahin se continue hoga
    blogger_link = (
        BLOGGER_BASE_URL
        + "?to="
        + quote(original_url, safe="")
    )

    return redirect(blogger_link, code=302)


# =========================
# HOME / CHECK
# =========================

@app.route("/")
def home():
    return "Link Converter Bot is running."


# =========================
# CONVERT TEXT
# =========================

def convert_text(text):

    if not text:
        return text

    # Message me normal URLs find karega
    pattern = r'https?://[^\s]+'

    def replace(match):

        url = match.group(0).rstrip('.,!?)]}')

        # Original URL database me save hogi
        # User ko sirf short URL milegi
        return make_short_link(url)

    return re.sub(pattern, replace, text)


# =========================
# CONVERT CAPTION
# =========================

def convert_caption(message):

    caption = message.caption or ""

    return convert_text(caption)


# =========================
# TEXT
# =========================

@bot.message_handler(content_types=["text"])
def handle_text(message):

    new_text = convert_text(message.text)

    bot.send_message(
        message.chat.id,
        new_text,
        disable_web_page_preview=True
    )


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
# RUN WEB SERVER
# =========================

def run_web():

    port = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=port
    )


# =========================
# MAIN
# =========================

if __name__ == "__main__":

    init_db()

    # Flask web server
    threading.Thread(
        target=run_web,
        daemon=True
    ).start()

    print("🤖 Bot is running...")

    bot.infinity_polling(
        skip_pending=True
    )
