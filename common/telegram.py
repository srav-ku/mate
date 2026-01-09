import os
import asyncio
from telegram import Bot

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

_bot = Bot(token=TELEGRAM_TOKEN)

async def _send(msg):
    await _bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

def send_message(msg):
    try:
        asyncio.run(_send(msg))
    except RuntimeError:
        # fallback if event loop already running
        loop = asyncio.get_event_loop()
        loop.create_task(_send(msg))
    except Exception as e:
        print(f"Telegram error: {e}")
