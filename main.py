import os
import re
from urllib.parse import quote
import telebot

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

BLOGGER_BASE_URL = "https://quickfileshare.blogspot.com/2026/09/welcome-zone.html"


def make_blogger_link(original_url):
    # Original link ko safely Blogger URL ke andar dalega
    encoded_url = quote(original_url, safe="")
    return f"{BLOGGER_BASE_URL}?to={encoded_url}"


def convert_text(text):
    if not text:
        return text

    # Message/caption me visible URLs
    pattern = r'https?://[^\s]+'

    def replace(match):
        url = match.group(0).rstrip('.,!?)]}')
        return make_blogger_link(url)

    return re.sub(pattern, replace, text)


def convert_caption(message):
    caption = message.caption or ""

    # Pehle normal visible URL convert karo
    new_caption = convert_text(caption)

    # Agar hidden clickable URL (text link) hai,
    # uska actual destination bhi Blogger link bana do
    if message.caption_entities:
        for entity in reversed(message.caption_entities):
            if entity.type == "text_link" and entity.url:
                start = entity.offset
                end = entity.offset + entity.length

                # Telegram offsets UTF-16 based ho sakte hain,
                # isliye simple cases me text replacement karenge.
                linked_text = caption[start:end]

                new_link = make_blogger_link(entity.url)

                # Agar linked text visible hai, usko URL se replace nahi karna.
                # Neeche simple fallback hai.
                new_caption = new_caption.replace(
                    linked_text,
                    new_link,
                    1
                )

    return new_caption


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
# MAIN
# =========================

if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.infinity_polling(skip_pending=True)
