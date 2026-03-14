import os
import asyncio
from pyrogram import Client, filters
from threading import Thread
from flask import Flask

# --- ENV VARIABLES ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app_bot = Client(
    "guard_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

app_web = Flask(__name__)

# Banned words list
BANNED_LIST = ["scam", "crypto", "paisa", "loot", "fake", "hack"]
BANNED_LOGS = []

@app_web.route('/')
def home():
    return "Bot is Online and Guarding!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host="0.0.0.0", port=port)


# START COMMAND
@app_bot.on_message(filters.command("start"))
async def start(client, message):
    text = (
        "🛡️ **Advanced Name Guard Active!**\n\n"
        "Main suspicious naam aur username wale users ko auto ban karta hoon.\n\n"
        "Commands:\n"
        "🔹 /add word\n"
        "🔹 /unblock word\n"
        "🔹 /list\n"
        "🔹 /banned"
    )
    await message.reply_text(text)


# ADD WORD
@app_bot.on_message(filters.command("add"))
async def add_word(client, message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: /add word")

    target = message.text.split(None, 1)[1].lower()

    if target not in BANNED_LIST:
        BANNED_LIST.append(target)
        await message.reply_text(f"✅ '{target}' added to block list")


# LIST WORDS
@app_bot.on_message(filters.command("list"))
async def list_words(client, message):
    words = ", ".join(BANNED_LIST)
    await message.reply_text(f"🚫 Blocked words:\n{words}")


# UNBLOCK WORD
@app_bot.on_message(filters.command("unblock"))
async def unblock_word(client, message):
    if len(message.command) < 2:
        return

    target = message.text.split(None, 1)[1].lower()

    if target in BANNED_LIST:
        BANNED_LIST.remove(target)
        await message.reply_text(f"🗑️ '{target}' removed from block list")


# SHOW BANNED USERS
@app_bot.on_message(filters.command("banned"))
async def banned_users(client, message):
    logs = "\n".join(BANNED_LOGS[-10:]) if BANNED_LOGS else "No banned users yet."
    await message.reply_text(logs)


# AUTO GUARD
@app_bot.on_chat_member_updated()
async def guard(client, update):

    user = None

    if update.new_chat_member:
        user = update.new_chat_member.user

    if user:
        full_name = f"{user.first_name or ''} {user.last_name or ''}".lower()
        username = (user.username or "").lower()

        for word in BANNED_LIST:

            if word in full_name or word in username:

                try:
                    await client.ban_chat_member(update.chat.id, user.id)

                    BANNED_LOGS.append(
                        f"❌ {user.first_name} banned (match: {word})"
                    )

                except:
                    pass

                break


async def main():

    Thread(target=run_flask, daemon=True).start()
    print("🚀 Web server started")

    async with app_bot:
        print("✅ BOT IS LIVE")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
