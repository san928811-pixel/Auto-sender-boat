import os
import re
import telebot

# =========================
# BOT CONFIG
# =========================
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Blogger landing page
BLOGGER_BASE_URL = "https://quickfileshare.blogspot.com/2026/09/welcome-zone.html"


# =========================
# LINK CONVERTER
# =========================
def convert_links(text):
    if not text:
        return text

    # http/https links ko detect karega
    url_pattern = r'https?://[^\s]+'

    def replace_url(match):
        original_url = match.group(0).rstrip('.,!?)]}')

        # Sirf Terabox / 1024tera links convert honge
        if "terabox" in original_url.lower() or "1024tera" in original_url.lower():
            return f"{BLOGGER_BASE_URL}?to={original_url}"

        return original_url

    return re.sub(url_pattern, replace_url, text)


# =========================
# TEXT MESSAGE
# =========================
@bot.message_handler(content_types=["text"])
def handle_text(message):
    new_text = convert_links(message.text)

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
    caption = message.caption or ""
    new_caption = convert_links(caption)

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
    caption = message.caption or ""
    new_caption = convert_links(caption)

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
    caption = message.caption or ""
    new_caption = convert_links(caption)

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
