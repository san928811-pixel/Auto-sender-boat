import os
import asyncio
from pyrogram import Client, filters
from flask import Flask
from threading import Thread

# ENV VARIABLES
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# PYROGRAM BOT
bot = Client(
    "test_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

# FLASK SERVER
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Running"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# START COMMAND
@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("✅ Bot is working!")

# PING COMMAND
@bot.on_message(filters.command("ping"))
async def ping(client, message):
    await message.reply_text("🏓 Pong!")

async def main():
    Thread(target=run).start()

    async with bot:
        print("BOT IS LIVE")
        await asyncio.Future()

asyncio.run(main())
