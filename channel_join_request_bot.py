#!/usr/bin/env python3
# ---------------- Channel Join-Request Bot ----------------
# Sends a forwardable text message with Name + Link below it.

import os
import sqlite3
import logging
from datetime import datetime
from telegram import ChatJoinRequest
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes
from telegram.error import Forbidden, RetryAfter, TelegramError
import asyncio

# ---------------- BOT TOKEN ----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("ERROR: BOT_TOKEN not set! Add it in Heroku Config Vars.")

# ---------------- FORWARDABLE WELCOME MESSAGE ----------------
WELCOME_TEMPLATE = (
    "Hello {first_name} 👋\n"
    "Thanks for requesting to join @{chat_username}.\n\n"
    "Here are some useful resources:\n\n"

    "⭐ Instagram Viral Hub\n"
    "https://t.me/+_z12fStYCckzZWE0\n\n"

    "⭐ Open Video Collection\n"
    "https://t.me/+6LuFjPOyAG84ZGI8\n\n"

    "⭐ Premium Video\n"
    "https://t.me/ruhi_roy_01?text=primium_membership_collection🥵\n"
)

# ---------------- SQLITE ANTI-SPAM DB ----------------
DB_PATH = "joinreq_bot.sqlite"
MIN_SECONDS_BETWEEN = 24 * 3600  # 24 hours

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sent_users (
            user_id INTEGER PRIMARY KEY,
            last_ts INTEGER
        )
    """)
    conn.commit()
    conn.close()

def should_send(user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT last_ts FROM sent_users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    now = int(datetime.utcnow().timestamp())

    if row is None:
        cur.execute("INSERT INTO sent_users VALUES (?, ?)", (user_id, now))
        conn.commit()
        conn.close()
        return True

    last_ts = row[0]
    if now - last_ts >= MIN_SECONDS_BETWEEN:
        cur.execute("UPDATE sent_users SET last_ts=? WHERE user_id=?", (now, user_id))
        conn.commit()
        conn.close()
        return True

    conn.close()
    return False

# ---------------- HANDLER ----------------
async def join_request_handler(update, context: ContextTypes.DEFAULT_TYPE):
    req: ChatJoinRequest = update.chat_join_request
    user = req.from_user
    chat = req.chat

    if not should_send(user.id):
        return

    msg_text = WELCOME_TEMPLATE.format(
        first_name=user.first_name,
        chat_username=chat.username or chat.title
    )

    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=msg_text
        )
        logging.info(f"Sent welcome message to {user.id}")

    except Forbidden:
        logging.warning(f"Cannot send message to {user.id} (Forbidden)")
    except RetryAfter as e:
        logging.warning(f"Rate limited. Sleeping {e.retry_after}s")
        await asyncio.sleep(e.retry_after)
        try:
            await context.bot.send_message(chat_id=user.id, text=msg_text)
        except Exception as e2:
            logging.error(e2)
    except TelegramError as e:
        logging.error(e)

# ---------------- MAIN ----------------
def main():
    logging.basicConfig(level=logging.INFO)
    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(ChatJoinRequestHandler(join_request_handler))

    logging.info("Bot is running...")
    app.run_polling(allowed_updates=["chat_join_request"])

if __name__ == "__main__":
    main()
