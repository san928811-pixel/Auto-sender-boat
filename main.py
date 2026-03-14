import os
import asyncio
from pyrogram import Client, filters
from threading import Thread
from flask import Flask

# --- CONFIG ---
API_ID = 26522774
API_HASH = "85f95874f63ca52f6f40776f8e752948"
BOT_TOKEN = "7677051416:AAFTzO_8N7N0wK_759AOnB-S76pM-X5CAsY"
ADMIN_ID = 7443315904

app_bot = Client("guard_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
app_web = Flask(__name__)

BANNED_KEYWORDS = ["scam", "crypto", "paisa", "loot", "earn"]
BANNED_LOGS = []

@app_web.route('/')
def home(): return "Bot is Online!"

def run_flask():
    # Railway के लिए PORT सेटिंग
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host="0.0.0.0", port=port)

@app_bot.on_message(filters.command("start") & filters.user(ADMIN_ID))
async def start(client, message):
    await message.reply_text("👋 Boss! Bot Railway par active hai.\n\n/add [word]\n/list\n/banned")

@app_bot.on_message(filters.command("add") & filters.user(ADMIN_ID))
async def add_w(client, message):
    if len(message.command) < 2: return
    word = message.text.split(None, 1)[1].lower()
    BANNED_KEYWORDS.append(word)
    await message.reply_text(f"✅ '{word}' added.")

@app_bot.on_message(filters.command("list") & filters.user(ADMIN_ID))
async def list_w(client, message):
    await message.reply_text(f"🚫 Blocked: {', '.join(BANNED_KEYWORDS)}")

@app_bot.on_message(filters.chat_member_updated())
async def auto_guard(client, update):
    if update.new_chat_member:
        user = update.new_chat_member.user
        name = f"{user.first_name} {user.last_name or ''}".lower()
        for word in BANNED_KEYWORDS:
            if word in name or (user.username and word in user.username.lower()):
                try:
                    await client.ban_chat_member(update.chat.id, user.id)
                    BANNED_LOGS.append(f"{user.first_name} ({word})")
                except: pass
                break

async def start_services():
    Thread(target=run_flask, daemon=True).start()
    async with app_bot:
        print("✅✅ BOT IS LIVE NOW! ✅✅")
        await asyncio.Future() 

if __name__ == "__main__":
    try:
        asyncio.run(start_services())
    except (KeyboardInterrupt, SystemExit):
        pass
