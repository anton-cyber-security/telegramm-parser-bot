from fastapi import FastAPI, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, AsyncGenerator
import httpx
from telegram import Update, Message
from telegram.ext import Application, MessageHandler, filters, CallbackContext
import asyncio
import logging
from datetime import datetime, timedelta
import json
import os
from enum import Enum
from dotenv import load_dotenv
load_dotenv()

# Настройки
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL")
TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MESSAGE_LIMIT = 100
CLEANUP_INTERVAL = 3600  # Проверка каждые 3600 секунд (1 час)
LAST_MESSAGES_TO_CHECK = 20  # Количество последних сообщений для проверки

app = FastAPI(title="Telegram Channel Messages API")

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Хранилище сообщений
messages_store = []

class MessageType(str, Enum):
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"

class TelegramMessage(BaseModel):
    id: int
    date: datetime
    type: MessageType
    text: Optional[str] = None
    media_url: Optional[str] = None
    caption: Optional[str] = None

@app.get("/messages", response_model=List[TelegramMessage])
async def get_messages(limit: int = 10):
    return messages_store[:limit]

async def sse_generator() -> AsyncGenerator[str, None]:
    last_id = None
    while True:
        if messages_store:
            current_id = messages_store[0]['id']
            if current_id != last_id:
                last_id = current_id
                yield f"data: {json.dumps(messages_store[0], default=str)}\n\n"
        await asyncio.sleep(0.5)

@app.get("/sse")
async def message_stream():
    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*"
    }
    return Response(
        content=sse_generator(),
        media_type="text/event-stream",
        headers=headers
    )

async def get_media_url(message: Message, bot, file_id: str) -> str:
    file = await bot.get_file(file_id)
    return f"{file.file_path}"

async def handle_message(update: Update, context: CallbackContext):
    message = update.channel_post
    if not message:
        return

    msg_data = {
        "id": message.message_id,
        "date": message.date,
        "category": "Тест",
        "type": MessageType.TEXT,
        "text": message.text,
        "media_url": None,
        "caption": message.caption
    }

    if message.photo:
        msg_data.update({
            "type": MessageType.PHOTO,
            "media_url": await get_media_url(message, context.bot, message.photo[-1].file_id)
        })
    elif message.video:
        msg_data.update({
            "type": MessageType.VIDEO,
            "media_url": await get_media_url(message, context.bot, message.video.file_id)
        })
    elif message.audio:
        msg_data.update({
            "type": MessageType.AUDIO,
            "media_url": await get_media_url(message, context.bot, message.audio.file_id)
        })
    elif message.document:
        msg_data.update({
            "type": MessageType.DOCUMENT,
            "media_url": await get_media_url(message, context.bot, message.document.file_id)
        })

    messages_store.insert(0, msg_data)
    if len(messages_store) > MESSAGE_LIMIT:
        messages_store.pop()

async def load_history_messages(bot):
    """Загружает историю сообщений из канала (от старых к новым)"""
    try:
        async for message in bot.get_chat_history(TELEGRAM_CHANNEL, limit=MESSAGE_LIMIT):
            msg_data = {
                "id": message.message_id,
                "date": message.date,
                "category": "Тест",
                "type": MessageType.TEXT,
                "text": message.text,
                "media_url": None,
                "caption": message.caption
            }

            if message.photo:
                msg_data.update({
                    "type": MessageType.PHOTO,
                    "media_url": await get_media_url(message, bot, message.photo[-1].file_id)
                })
            elif message.video:
                msg_data.update({
                    "type": MessageType.VIDEO,
                    "media_url": await get_media_url(message, bot, message.video.file_id)
                })
            elif message.audio:
                msg_data.update({
                    "type": MessageType.AUDIO,
                    "media_url": await get_media_url(message, bot, message.audio.file_id)
                })
            elif message.document:
                msg_data.update({
                    "type": MessageType.DOCUMENT,
                    "media_url": await get_media_url(message, bot, message.document.file_id)
                })

            # Добавляем в начало списка (чтобы в итоге получить порядок от старых к новым)
            messages_store.insert(0, msg_data)
            
            # Ограничиваем размер хранилища
            if len(messages_store) > MESSAGE_LIMIT:
                messages_store.pop()
                
    except Exception as e:
        logging.error(f"Error loading history messages: {e}")

async def check_deleted_messages(bot):
    """Периодически проверяет последние сообщения на наличие и удаляет отсутствующие"""
    while True:
        try:
            if not messages_store:
                await asyncio.sleep(CLEANUP_INTERVAL)
                continue
                
            # Получаем ID последних сообщений из хранилища
            stored_ids = [msg['id'] for msg in messages_store[:LAST_MESSAGES_TO_CHECK]]
            
            # Получаем фактические сообщения из канала
            actual_ids = []
            async for message in bot.get_chat_history(TELEGRAM_CHANNEL, limit=LAST_MESSAGES_TO_CHECK):
                actual_ids.append(message.message_id)
            
            # Находим сообщения, которые есть в хранилище, но отсутствуют в канале
            deleted_ids = set(stored_ids) - set(actual_ids)
            
            if deleted_ids:
                # Удаляем отсутствующие сообщения из хранилища
                global messages_store
                messages_store = [msg for msg in messages_store if msg['id'] not in deleted_ids]
                logging.info(f"Removed {len(deleted_ids)} deleted messages from store")
            
        except Exception as e:
            logging.error(f"Error checking deleted messages: {e}")
        
        await asyncio.sleep(CLEANUP_INTERVAL)

async def init_telegram_bot():
    application = Application.builder().token(TELEGRAM_API_TOKEN).build()
    application.add_handler(MessageHandler(filters.ALL, handle_message))
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Загружаем историю сообщений
    await load_history_messages(application.bot)
    
    # Запускаем фоновую задачу проверки удаленных сообщений
    asyncio.create_task(check_deleted_messages(application.bot))

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(init_telegram_bot())

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8000)
