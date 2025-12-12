#!/usr/bin/env python3
"""
Channel join-request bot (python-telegram-bot v20+)

Behavior:
- Listens for ChatJoinRequest updates (works when bot is admin of a CHANNEL).
- Leaves the request PENDING (does NOT approve/decline).
- Attempts to send a private welcome message to requester with 3 inline links.
- Uses a small sqlite DB to avoid messaging same user more than once per day.

HOW TO USE:
- Replace the three LINK_* values below with your real URLs (or set them later).
- Set BOT_TOKEN either by:
    - Exporting environment variable BOT_TOKEN (recommended, e.g. Heroku Config Vars)
    - OR directly replace the string 'PUT_YOUR_TOKEN_HERE' below (not recommended to commit).
- Add the bot as admin to your CHANNEL (allow it to see join requests).
- Run: python channel_join_request_bot.py
"""

import os
import sqlite3
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatJoinRequest
from telegram.error import Forbidden, RetryAfter, TelegramError
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes

# ---------------- CONFIG ----------------

# BOT TOKEN: recommended to set as environment variable BOT_TOKEN.
# For Heroku: set Config Var BOT_TOKEN = your-token
BOT_TOKEN: str = os.environ.get("BOT_TOKEN") or "8331279978:AAHn_RSnCykYmFrWibkTvvb4tizgKt1Ywjk"
# If you want me to literally fill token here, replace the above string with your token,
# but DO NOT commit the token to a public repo.

# Welcome message (can customize)
WELCOME_TEMPLATE = (
    "Hello {first_name} 👋\n\n"
    "Thanks for requesting to join @{chat_username}.\n\n"
    "Before approval, please check these resources:"
)

# Replace these URLs with your actual links.
# The labels requested:
#  - Open Video Collection
#  - Instagram Viral Hub
#  - Premium Video
LINKS = [
    ("Open Video Collection", "https://example.com/open-video"),     # <-- replace
    ("Instagram Viral Hub", "https://example.com/instagram-hub"),    # <-- replace
    ("Premium Video", "https://example.com/premium-video"),          # <-- replace
]

# Rate-limit: minimum seconds between welcome messages to same user (default 24 hours)
MIN_SECONDS_BETWEEN_MESSAGES = 24 * 3600
DB_PATH = "joinreq_bot.sqlite"

# Logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------- DB helpers ----------------
def init_db(path: str = DB_PATH):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS messaged_users (
            user_id INTEGER PRIMARY KEY,
            last_sent_ts INTEGER
        )
        """
    )
    conn.commit()
    conn.close()


def should_send_to_user(user_id: int, min_seconds: int = MIN_SECONDS_BETWEEN_MESSAGES) -> bool:
    """Return True if we should send a message to this user (based on cooldown)."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT last_sent_ts FROM messaged_users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    now_ts = int(datetime.utcnow().timestamp())
    if row is None:
        cur.execute("INSERT INTO messaged_users(user_id, last_sent_ts) VALUES(?, ?)", (user_id, now_ts))
        conn.commit()
        conn.close()
        return True
    last_ts = row[0]
    if now_ts - last_ts >= min_seconds:
        cur.execute("UPDATE messaged_users SET last_sent_ts = ? WHERE user_id = ?", (now_ts, user_id))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


# ---------------- Handler ----------------
async def handle_join_request(update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles ChatJoinRequest:
    - Keeps request pending (does not approve or decline)
    - Attempts to DM the requester with the welcome message + links
    """
    jreq: Optional[ChatJoinRequest] = update.chat_join_request
    if not jreq:
        return

    user = jreq.from_user
    chat = jreq.chat

    logger.info("Join request from %s (%s) for chat %s (%s)", user.full_name, user.id, chat.title, chat.id)

    # Throttle: avoid messaging same user repeatedly
    if not should_send_to_user(user.id):
        logger.info("Skipping DM to %s — sent recently.", user.id)
        return

    # Build keyboard with provided LINKS
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(text=label, url=url) for (label, url) in LINKS]]
    )

    text = WELCOME_TEMPLATE.format(first_name=user.first_name or user.full_name,
                                   chat_username=getattr(chat, "username", chat.title))

    try:
        await context.bot.send_message(chat_id=user.id, text=text, reply_markup=keyboard)
        logger.info("Sent welcome DM to user %s", user.id)
    except Forbidden as e:
        # User hasn't started the bot OR blocked it
        logger.warning("Forbidden: cannot DM user %s — %s", user.id, e)
    except RetryAfter as e:
        wait = int(e.retry_after) + 1
        logger.warning("Rate-limited by Telegram. Sleeping %s seconds then retrying once.", wait)
        await asyncio.sleep(wait)
        try:
            await context.bot.send_message(chat_id=user.id, text=text, reply_markup=keyboard)
            logger.info("Sent welcome DM after retry to user %s", user.id)
        except Exception as e2:
            logger.error("Failed to send DM after retry: %s", e2)
    except TelegramError as e:
        logger.error("TelegramError when messaging user %s: %s", user.id, e)
    except Exception:
        logger.exception("Unexpected error when messaging user %s", user.id)

    # Intentionally DO NOT approve or decline the join request here.
    # If you want to approve automatically, call:
    #   await context.bot.approve_chat_join_request(chat_id=chat.id, user_id=user.id)
    # or to decline:
    #   await context.bot.decline_chat_join_request(chat_id=chat.id, user_id=user.id)


# ---------------- Main ----------------
def main():
    if BOT_TOKEN == "PUT_YOUR_TOKEN_HERE" or not BOT_TOKEN:
        logger.error("BOT_TOKEN not set! Set environment variable BOT_TOKEN or edit this file.")
        raise SystemExit("BOT_TOKEN not set. Edit file or set env var BOT_TOKEN.")

    init_db(DB_PATH)

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(ChatJoinRequestHandler(handle_join_request))

    logger.info("Bot starting (listening for chat_join_request updates)...")
    # Only request join-request updates
    app.run_polling(allowed_updates=["chat_join_request"])


if __name__ == "__main__":
    main()
