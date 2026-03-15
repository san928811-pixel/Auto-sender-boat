import os
import random
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
    "ultimate_guard_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

app = Flask(__name__)

@app.route("/")
def home():
    return "Ultimate Guard Bot Running"

def run_web():
    port = int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0",port=port)

BANNED_WORDS = []
LOGS = []
CAPTCHA = {}
JOIN_LOG = []

def is_admin(uid):
    return uid == ADMIN_ID


# START
@bot.on_message(filters.command("start"))
async def start(client,message):

    await message.reply_text(
        "🛡 Ultimate Guard Bot Active\n\n"
        "/add word\n"
        "/remove word\n"
        "/list\n"
        "/logs\n"
        "/stats"
    )


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

    await message.reply(f"🚫 Blocked keyword: {word}")


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


# LIST WORDS
@bot.on_message(filters.command("list"))
async def list_words(client,message):

    if not BANNED_WORDS:
        return await message.reply("No blocked words")

    await message.reply("\n".join(BANNED_WORDS))


# STATS
@bot.on_message(filters.command("stats"))
async def stats(client,message):

    text = (
        f"📊 Guard Bot Stats\n\n"
        f"Blocked Words: {len(BANNED_WORDS)}\n"
        f"Banned Users: {len(LOGS)}"
    )

    await message.reply(text)


# LOGS
@bot.on_message(filters.command("logs"))
async def logs(client,message):

    if not LOGS:
        return await message.reply("No logs")

    await message.reply("\n".join(LOGS[-10:]))


# DELETE SPAM LINKS
@bot.on_message(filters.group & filters.regex(r"(https?://|t.me/)"))
async def delete_links(client,message):

    try:
        await message.delete()
    except:
        pass


# CHANNEL JOIN REQUEST FILTER
@bot.on_chat_join_request()
async def join_request(client, request):

    user = request.from_user

    name = f"{user.first_name or ''} {(user.last_name or '')}".lower()
    username = (user.username or "").lower()

    if user.is_bot:
        await request.decline()
        return

    for word in BANNED_WORDS:
        if word in name or word in username:
            await request.decline()
            LOGS.append(f"Join request rejected {user.first_name}")
            return

    await request.approve()


# GROUP JOIN GUARD
@bot.on_chat_member_updated()
async def guard(client,update:ChatMemberUpdated):

    if not update.new_chat_member:
        return

    user = update.new_chat_member.user

    name = f"{user.first_name or ''} {(user.last_name or '')}".lower()
    username = (user.username or "").lower()

    # BOT BAN
    if user.is_bot:
        await client.ban_chat_member(update.chat.id,user.id)
        LOGS.append(f"Bot banned {user.first_name}")
        return

    # KEYWORD BLOCK
    for word in BANNED_WORDS:
        if word in name or word in username:
            await client.ban_chat_member(update.chat.id,user.id)
            LOGS.append(f"{user.first_name} banned ({word})")
            return

    # RAID DETECTION
    now = time.time()

    JOIN_LOG.append(now)

    JOIN_LOG[:] = [t for t in JOIN_LOG if now - t < 10]

    if len(JOIN_LOG) > 60:
        await client.send_message(update.chat.id,"🚨 Raid detected")
        await client.ban_chat_member(update.chat.id,user.id)
        return

    # CAPTCHA
    a = random.randint(1,9)
    b = random.randint(1,9)

    CAPTCHA[user.id] = a + b

    await client.send_message(
        update.chat.id,
        f"{user.mention} solve captcha: {a}+{b}=?"
    )


# CAPTCHA VERIFY
@bot.on_message(filters.group)
async def verify(client,message):

    if message.from_user.id in CAPTCHA:

        if message.text == str(CAPTCHA[message.from_user.id]):

            del CAPTCHA[message.from_user.id]

            await message.reply("✅ Verified")

        else:

            await message.reply("❌ Wrong captcha")


def main():

    Thread(target=run_web).start()

    print("ULTIMATE GUARD BOT LIVE")

    bot.run()


if __name__ == "__main__":
    main()
