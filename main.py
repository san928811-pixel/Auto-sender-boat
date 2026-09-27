import os
import telebot

# BotFather se mila hua Token Railway ke environment variable se uthega
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Aapka specific Blogger post link jahan 5-second timer aur ad laga hua hai
BLOGGER_BASE_URL = "https://quickfileshare.blogspot.com/2026/09/welcome-zone.html"

@bot.message_handler(func=lambda message: True)
def handle_bulk_links(message):
    incoming_text = message.text
    lines = incoming_text.split('\n')
    response_lines = []
    
    for line in lines:
        # Check karte hain ki line me terabox ka link hai ya nahi
        if "terabox" in line.lower() or "1024tera" in line.lower():
            clean_link = line.strip()
            # Smart URL format jo ?to= ke sath asli link jod dega
            monetized_link = f"{BLOGGER_BASE_URL}?to={clean_link}"
            response_lines.append(f"📥 Download Link:\n{monetized_link}")
        else:
            # Agar koi aur text ya description hai toh waisa hi rehne dega
            response_lines.append(line)
            
    final_output = "\n".join(response_lines)
    bot.reply_to(message, final_output, disable_web_page_preview=True)

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
