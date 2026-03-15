import os
import time
from pyrogram import Client, filters
from pyrogram.types import ChatMemberUpdated
from flask import Flask
from threading import Thread

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 8611520265

bot = Client(
    "guard_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

app = Flask(__name__)

@app.route("/")
def home():
    return "Guard Bot Running"

def run_web():
    port = int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0",port=port)

# DATA
BANNED_WORDS = []
BANNED_LOGS = []
JOIN_LOG = []

# ADMIN CHECK
def is_admin(uid):
    return uid == ADMIN_ID

# START
@bot.on_message(filters.command("start"))
async def start(client,message):

    text = (
        "🛡 **Advanced Guard Bot Active**\n\n"
        "Commands:\n"
        "/add word\n"
        "/remove word\n"
        "/list\n"
        "/logs"
    )

    await message.reply_text(text)

# ADD WORD
@bot.on_message(filters.command("add"))
async def add_word(client,message):

    if not is_admin(message.from_user.id):
        return await message.reply("❌ Admin only")

    if len(message.command) < 2:
        return await message.reply("Usage: /add word")

    word = message.command[1].lower()

    if word not in BANNED_WORDS:
        BANNED_WORDS.append(word)

    await message.reply(f"✅ Added {word}")

# REMOVE WORD
@bot.on_message(filters.command("remove"))
async def remove_word(client,message):

    if not is_admin(message.from_user.id):
        return await message.reply("❌ Admin only")

    if len(message.command) < 2:
        return

    word = message.command[1].lower()

    if word in BANNED_WORDS:
        BANNED_WORDS.remove(word)

    await message.reply("Removed")

# LIST
@bot.on_message(filters.command("list"))
async def list_words(client,message):

    if not BANNED_WORDS:
        return await message.reply("No banned words")

    await message.reply("\n".join(BANNED_WORDS))

# LOGS
@bot.on_message(filters.command("logs"))
async def logs(client,message):

    if not BANNED_LOGS:
        return await message.reply("No logs")

    await message.reply("\n".join(BANNED_LOGS[-10:]))

# SPAM LINK DELETE
@bot.on_message(filters.group & filters.regex(r"(https?://|t.me/)"))
async def delete_links(client,message):

    try:
        await message.delete()
    except:
        pass

# JOIN GUARD
@bot.on_chat_member_updated()
async def guard(client,update:ChatMemberUpdated):

    if not update.new_chat_member:
        return

    user = update.new_chat_member.user

    name = f"{user.first_name or ''} {(user.last_name or '')}".lower()
    username = (user.username or "").lower()

    # BOT GUARD
    if user.is_bot:

        try:
            await client.ban_chat_member(update.chat.id,user.id)
            BANNED_LOGS.append(f"🤖 Bot banned {user.first_name}")
        except:
            pass

        return

    # FAKE ACCOUNT DETECTION
    suspicious = ["free","earn","crypto","hack","spam"]

    for word in suspicious:

        if word in name or word in username:

            try:
                await client.ban_chat_member(update.chat.id,user.id)

                BANNED_LOGS.append(
                    f"🚫 Fake banned {user.first_name}"
                )

            except:
                pass

            return

    # KEYWORD GUARD
    for word in BANNED_WORDS:

        if word in name or word in username:

            try:
                await client.ban_chat_member(update.chat.id,user.id)

                BANNED_LOGS.append(
                    f"🚫 {user.first_name} banned ({word})"
                )

            except:
                pass

            return

    # RAID PROTECTION
    now = time.time()

    JOIN_LOG.append(now)

    JOIN_LOG[:] = [t for t in JOIN_LOG if now - t < 10]

    if len(JOIN_LOG) > 5:

        try:
            await client.ban_chat_member(update.chat.id,user.id)

            BANNED_LOGS.append(
                f"⚠ Raid banned {user.first_name}"
            )

        except:
            pass

def main():

    Thread(target=run_web).start()

    print("BOT IS LIVE")

    bot.run()

if __name__ == "__main__":
    main()
