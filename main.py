import os
import re
from urllib.parse import quote
import telebot

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

BLOGGER_BASE_URL = "https://quickfileshare.blogspot.com/2026/09/welcome-zone.html"


def make_blogger_link(original_url):
    encoded_url = quote(original_url, safe="")
    return f"{BLOGGER_BASE_URL}?to={encoded_url}"


def convert_text(text):
    if not text:
        return text

    pattern = r'https?://[^\s]+'

    def replace(match):
        url = match.group(0).rstrip('.,!?)]}')
        blogger_link = make_blogger_link(url)

        # URL ki jagah chhota clickable text
        return f'<a href="{blogger_link}">TeraShare File</a>'

    return re.sub(pattern, replace, text)


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
        parse_mode="HTML",
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
        caption=new_caption,
        parse_mode="HTML"
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
        caption=new_caption,
        parse_mode="HTML"
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
        caption=new_caption,
        parse_mode="HTML"
    )


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.infinity_polling(skip_pending=True)
