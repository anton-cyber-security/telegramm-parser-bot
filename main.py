from fastapi import FastAPI, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, AsyncGenerator
import httpx
from telegram import Update, Message
from telegram.ext import Application, MessageHandler, filters, CallbackContext
import asyncio
import logging
from datetime import datetime
import json
import os
from enum import Enum
from dotenv import load_dotenv
load_dotenv()

# Настройки
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL")
TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MESSAGE_LIMIT = 100

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
	"category": "Тест"
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

async def init_telegram_bot():
    application = Application.builder().token(TELEGRAM_API_TOKEN).build()
    application.add_handler(MessageHandler(filters.ALL, handle_message))
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(init_telegram_bot())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
