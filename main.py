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
    "ultimate_guard_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

app = Flask(__name__)

# DATA
BANNED_WORDS = []
LOGS = []
JOIN_LOG = []
BANNED_COUNT = 0


# WEB DASHBOARD
@app.route("/")
def home():

    return f"""
    <h2>🛡 Safety Guard Dashboard</h2>
    <p><b>Blocked Keywords:</b> {len(BANNED_WORDS)}</p>
    <p><b>Banned Users:</b> {BANNED_COUNT}</p>
    <p><b>Raid Protection:</b> Active</p>
    <p><b>AI Detection:</b> Active</p>
    """


def run_web():

    port = int(os.environ.get("PORT", 8080))

    app.run(host="0.0.0.0", port=port)


def is_admin(uid):

    return uid == ADMIN_ID


# START
@bot.on_message(filters.command("start"))
async def start(client, message):

    await message.reply_text(
        "🛡 Safety Guard Bot Active\n\n"
        "/add word\n"
        "/remove word\n"
        "/list\n"
        "/logs\n"
        "/stats"
    )


# ADD KEYWORD
@bot.on_message(filters.command("add"))
async def add_word(client, message):

    if not is_admin(message.from_user.id):
        return await message.reply("Admin only")

    word = message.command[1].lower()

    BANNED_WORDS.append(word)

    await message.reply(f"Blocked: {word}")


# REMOVE KEYWORD
@bot.on_message(filters.command("remove"))
async def remove_word(client, message):

    if not is_admin(message.from_user.id):
        return await message.reply("Admin only")

    word = message.command[1].lower()

    if word in BANNED_WORDS:
        BANNED_WORDS.remove(word)

    await message.reply("Removed")


# LIST
@bot.on_message(filters.command("list"))
async def list_words(client, message):

    if not BANNED_WORDS:
        return await message.reply("No blocked words")

    await message.reply("\n".join(BANNED_WORDS))


# STATS
@bot.on_message(filters.command("stats"))
async def stats(client, message):

    text = (
        f"📊 Guard Stats\n\n"
        f"Blocked Words: {len(BANNED_WORDS)}\n"
        f"Banned Users: {BANNED_COUNT}"
    )

    await message.reply(text)


# LOGS
@bot.on_message(filters.command("logs"))
async def logs(client, message):

    if not LOGS:
        return await message.reply("No logs")

    await message.reply("\n".join(LOGS[-10:]))


# DELETE SPAM LINKS
@bot.on_message(filters.group & filters.regex(r"(https?://|t.me/)"))
async def delete_links(client, message):

    try:
        await message.delete()
    except:
        pass


# AI SPAM DETECTION
def ai_spam_detect(name, username):

    score = 0

    suspicious_words = [
        "crypto",
        "earn",
        "profit",
        "airdrop",
        "signal",
        "vip",
        "free",
        "money"
    ]

    for word in suspicious_words:

        if word in name or word in username:

            score += 3

    if any(char.isdigit() for char in username):

        score += 2

    if len(name) < 3:

        score += 2

    if score >= 5:

        return True

    return False


# BOT FARM DETECTION
def bot_farm_detect():

    now = time.time()

    JOIN_LOG.append(now)

    JOIN_LOG[:] = [t for t in JOIN_LOG if now - t < 5]

    if len(JOIN_LOG) > 15:

        return True

    return False


# CHANNEL JOIN REQUEST FILTER
@bot.on_chat_join_request()
async def join_request(client, request):

    user = request.from_user

    name = f"{user.first_name or ''} {(user.last_name or '')}".lower()
    username = (user.username or "").lower()

    if user.is_bot:

        await request.decline()

        return

    if ai_spam_detect(name, username):

        await request.decline()

        return

    for word in BANNED_WORDS:

        if word in name or word in username:

            await request.decline()

            return

    await request.approve()


# JOIN GUARD
@bot.on_chat_member_updated()
async def guard(client, update: ChatMemberUpdated):

    global BANNED_COUNT

    if not update.new_chat_member:
        return

    user = update.new_chat_member.user

    name = f"{user.first_name or ''} {(user.last_name or '')}".lower()
    username = (user.username or "").lower()

    # BOT BAN
    if user.is_bot:

        await client.ban_chat_member(update.chat.id, user.id)

        BANNED_COUNT += 1

        LOGS.append(f"Bot banned {user.first_name}")

        return

    # AI DETECT
    if ai_spam_detect(name, username):

        await client.ban_chat_member(update.chat.id, user.id)

        BANNED_COUNT += 1

        LOGS.append(f"AI banned {user.first_name}")

        return

    # KEYWORD BLOCK
    for word in BANNED_WORDS:

        if word in name or word in username:

            await client.ban_chat_member(update.chat.id, user.id)

            BANNED_COUNT += 1

            LOGS.append(f"{user.first_name} banned ({word})")

            return

    # BOT FARM DETECT
    if bot_farm_detect():

        await client.ban_chat_member(update.chat.id, user.id)

        BANNED_COUNT += 1

        LOGS.append("Bot farm detected")

        return


def main():

    Thread(target=run_web).start()

    print("GUARD BOT LIVE")

    bot.run()


if __name__ == "__main__":

    main()
