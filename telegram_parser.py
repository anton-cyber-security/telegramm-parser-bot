from telethon import TelegramClient
import os
from dotenv import load_dotenv
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
client = TelegramClient("client", API_ID, API_HASH)

async def main():
    print("good")
    await bot.send_message(CHANNEL_ID, 'Hello, group!')


async def main2():
    print("good2")
    channels = []
    async for dialog in client.iter_dialogs():  # Here the problem
        channels.append((dialog.id, dialog.name))
    print(channels)


with bot:
    bot.loop.run_until_complete(main())

with client:
    client.loop.run_until_complete(main())