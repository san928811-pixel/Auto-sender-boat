import os
import asyncio
from pyrogram import Client, filters
from threading import Thread
from flask import Flask

# --- CONFIG ---
API_ID = 34214308
API_HASH = "1dc1da15588ee6df9178e1211a436d4b"
BOT_TOKEN = "8663869825:AAFFE1QWz5HDUZVQC4qeUCtOqxNaGkXtFqg"
app_bot = Client("guard_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
app_web = Flask(__name__)

# Banned Names aur Keywords ki list
BANNED_LIST = ["scam", "crypto", "paisa", "loot", "fake", "hack"]
BANNED_LOGS = []

@app_web.route('/')
def home(): return "Bot is Online and Guarding!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
# 1. START Command - Bot ki details dikhayega
@app_bot.on_message(filters.command("start"))
async def start(client, message):
    text = (
        "🛡️ **Advanced Name & Keyword Guard Active!**\n\n"
        "Main aapke Channel aur Group ka bodyguard hoon. Main in cheezon se block karta hoon:\n"
        "✅ **Full Name:** Agar naam mein galat word hua.\n"
        "✅ **Username:** Agar username suspicious hua.\n"
        "✅ **Keyword:** Jo aap `/add` se list mein daalenge.\n\n"
        "🚀 **Commands (Sabke liye):**\n"
        "🔹 `/add [naam]` - Naya naam/word block karein\n"
        "🔹 `/unblock [naam]` - List se hatayein\n"
        "🔹 `/list` - Banned words dekhein\n"
        "🔹 `/banned` - Blocked users dekhein"
    )
    await message.reply_text(text)

# 2. ADD - Naya word ya naam block list mein daalne ke liye
@app_bot.on_message(filters.command("add"))
async def add_target(client, message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Sahi tarika: `/add Deepak`")
    target = message.text.split(None, 1)[1].lower()
    if target not in BANNED_LIST:
        BANNED_LIST.append(target)
        await message.reply_text(f"✅ **'{target}'** ab block list mein hai.")

# 3. LIST - Blocked list dekhne ke liye
@app_bot.on_message(filters.command("list"))
async def list_targets(client, message):
    targets = ", ".join(BANNED_LIST)
    await message.reply_text(f"🚫 **Blocked Names/Words:**\n`{targets}`")

# 4. UNBLOCK - Kisi word ko list se hatane ke liye
@app_bot.on_message(filters.command("unblock"))
async def unblock_target(client, message):
    if len(message.command) < 2: return
    target = message.text.split(None, 1)[1].lower()
    if target in BANNED_LIST:
        BANNED_LIST.remove(target)
        await message.reply_text(f"🗑️ **'{target}'** ko list se hata diya gaya.")

# 5. BANNED - Blocked users ka record
@app_bot.on_message(filters.command("banned"))
async def show_banned(client, message):
    logs = "\n".join(BANNED_LOGS[-10:]) if BANNED_LOGS else "Abhi tak koi record nahi hai."
    await message.reply_text(f"👤 **Aakhiri 10 Blocked Users:**\n{logs}")

# --- ASLI PEHRA (Group & Channel Scanner) ---
@app_bot.on_chat_member_updated()
async def name_guard(client, update):
    user = None
    if update.new_chat_member:
        user = update.new_chat_member.user
    
    if user:
        full_name = f"{(user.first_name or '')} {(user.last_name or '')}".lower().strip()
        username = (user.username or "").lower()
        
        for target in BANNED_LIST:
            if target in full_name or target in username:
                try:
                    await client.ban_chat_member(update.chat.id, user.id)
                    BANNED_LOGS.append(f"❌ Blocked: {user.first_name} (Match: {target})")
                except:
                    pass
                break

async def main():
    Thread(target=run_flask, daemon=True).start()
    print("🚀 Web Server Started")
    async with app_bot:
        print("✅✅ BOT IS LIVE NOW! ✅✅")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
