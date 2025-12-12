# ----- Channel Join-Request Handler Bot -----

import os
import logging
from datetime import datetime
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import Forbidden, RetryAfter, TelegramError

BOT_TOKEN = os.environ.get("8331279978:AAHn_RSnCykYmFrWibkTvvb4tizgKt1Ywjk")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WELCOME_TEXT = (
    "Hello {name} 👋\n"
    "Thanks for requesting to join our channel!\n\n"
    "Please check these important links before approval:\n"
)

LINKS = [
    ("Rules", "https://example.com/rules"),
    ("Help", "https://example.com/help"),
    ("Info", "https://example.com/info")
]

async def handle_join_request(update, context: ContextTypes.DEFAULT_TYPE):
    req = update.chat_join_request
    user = req.from_user
    chat = req.chat

    logger.info(f"Join Request from {user.id} for {chat.id}")

    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton(text, url=url) for text, url in LINKS]]
    )

    msg = WELCOME_TEXT.format(name=user.first_name)

    try:
        await context.bot.send_message(chat_id=user.id, text=msg, reply_markup=kb)
        logger.info(f"Welcome message sent to {user.id}")

    except Forbidden:
        logger.warning(f"Cannot send message to {user.id} (Forbidden)")
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after)
    except TelegramError as e:
        logger.error(f"Error: {e}")

def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN not set!")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(ChatJoinRequestHandler(handle_join_request))

    logger.info("Bot is running...")
    app.run_polling(allowed_updates=["chat_join_request"])

if __name__ == "__main__":
    main()
