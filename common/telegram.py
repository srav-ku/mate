import os
from telegram import Bot

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

def send_message(msg):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
    except Exception as e:
        print(f"Telegram send error: {e}")
