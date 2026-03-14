import os
import asyncio
from pyrogram import Client, filters
from threading import Thread
from flask import Flask

# ENV VARIABLES
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# PYROGRAM CLIENT
app_bot = Client(
    "safety_guard_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

# FLASK APP
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Safety Guard Bot Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host="0.0.0.0", port=port)

# DATA
BANNED_LIST = ["scam", "crypto", "paisa", "loot", "fake", "hack"]
BANNED_LOGS = []
TOTAL_BANS = 0

# ADMIN CHECK
async def is_admin(client, message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    return member.status in ["administrator", "creator"]

# START
@app_bot.on_message(filters.private & filters.command("start"))
async def start(client, message):

    text = (
        "🛡️ **Safety Guard Bot Active**\n\n"
        "Main group ko scam aur spam se protect karta hoon.\n\n"
        "Commands:\n"
        "/add word\n"
        "/unblock word\n"
        "/list\n"
        "/stats\n"
        "/ping"
    )

    await message.reply_text(text)

# PING
@app_bot.on_message(filters.command("ping"))
async def ping(client, message):
    await message.reply_text("✅ Bot Online")

# ADD WORD
@app_bot.on_message(filters.command("add"))
async def add_word(client, message):

    if not await is_admin(client, message):
        return await message.reply_text("❌ Admin only command")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /add word")

    word = message.command[1].lower()

    if word not in BANNED_LIST:
        BANNED_LIST.append(word)

    await message.reply_text(f"✅ '{word}' added")

# LIST
@app_bot.on_message(filters.command("list"))
async def list_words(client, message):

    words = ", ".join(BANNED_LIST)

    await message.reply_text(f"🚫 Blocked words:\n{words}")

# REMOVE WORD
@app_bot.on_message(filters.command("unblock"))
async def remove_word(client, message):

    if not await is_admin(client, message):
        return await message.reply_text("❌ Admin only command")

    if len(message.command) < 2:
        return

    word = message.command[1].lower()

    if word in BANNED_LIST:
        BANNED_LIST.remove(word)

    await message.reply_text(f"🗑️ '{word}' removed")

# STATS
@app_bot.on_message(filters.command("stats"))
async def stats(client, message):

    text = (
        f"📊 **Safety Guard Stats**\n\n"
        f"Total Bans: {TOTAL_BANS}\n"
        f"Blocked Words: {len(BANNED_LIST)}"
    )

    await message.reply_text(text)

# SPAM LINK DELETE
@app_bot.on_message(filters.group & filters.regex(r"(https?://|t.me/)"))
async def delete_links(client, message):

    try:
        await message.delete()
    except:
        pass

# AUTO NAME GUARD
@app_bot.on_chat_member_updated()
async def guard(client, update):

    global TOTAL_BANS

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

                    TOTAL_BANS += 1

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
