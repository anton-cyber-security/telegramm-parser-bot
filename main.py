"""
Telegram Channel Parser Backend (aiogram 3.x)
FastAPI + aiogram

Функционал:
1. Парсинг всех сообщений из канала (текст, фото, видео, аудио)
2. Хранение в хронологическом порядке (от старых к новым)
3. Регулярная проверка новых сообщений
4. Удаление удаленных из канала сообщений
5. API для доступа к сообщениям
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, AsyncGenerator, Optional

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ChatType, ParseMode

# --- Конфигурация ---
load_dotenv()

# Настройки из переменных окружения
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL")  # Например: "@my_channel"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Токен от @BotFather

# Константы приложения
MESSAGE_LIMIT = 1000  # Максимальное количество хранимых сообщений
CHECK_INTERVAL = 300  # Интервал проверки новых сообщений (секунды)
LAST_MESSAGES_TO_CHECK = 50  # Сколько последних сообщений проверять на удаление
API_MESSAGES_LIMIT = 100  # Лимит сообщений для API

# --- Инициализация приложения ---
app = FastAPI(title="Telegram Channel Parser API")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальное хранилище сообщений
messages_store: List[Dict] = []

# Инициализация aiogram
bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# --- Модели данных ---
class ChannelMessage(BaseModel):
    """Модель для представления сообщения канала"""
    id: int  # ID сообщения в Telegram
    type: str  # Тип сообщения: text, photo, video, audio
    date_time: datetime  # Дата и время сообщения
    url_media: Optional[str] = None  # URL медиафайла (если есть)
    category: str = "default"  # Категория сообщения
    text: Optional[str] = None  # Текст сообщения или подпись

# --- Основные функции ---
async def parse_message(message: types.Message) -> Dict:
    """
    Парсит сообщение из Telegram в унифицированный формат
    
    Args:
        message: Объект сообщения из aiogram
    
    Returns:
        Словарь с данными сообщения
    """
    msg_data = {
        "id": message.message_id,
        "date_time": message.date,
        "category": "default",
        "text": message.text or message.caption,
    }

    # Определяем тип сообщения и URL медиа
    if message.photo:
        msg_data.update({
            "type": "photo",
            "url_media": await get_media_url(message.photo[-1].file_id)
        })
    elif message.video:
        msg_data.update({
            "type": "video",
            "url_media": await get_media_url(message.video.file_id)
        })
    elif message.audio:
        msg_data.update({
            "type": "audio",
            "url_media": await get_media_url(message.audio.file_id)
        })
    else:
        msg_data["type"] = "text"

    return msg_data

async def get_media_url(file_id: str) -> str:
    """Получает прямой URL для медиафайла"""
    file = await bot.get_file(file_id)
    return f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file.file_path}"

async def load_all_messages():
    """Загружает всю историю сообщений из канала"""
    global messages_store
    
    try:
        # Для aiogram нужно использовать get_chat_history
        async for message in bot.get_chat_history(TELEGRAM_CHANNEL):
            parsed = await parse_message(message)
            messages_store.append(parsed)
            
            if len(messages_store) >= MESSAGE_LIMIT:
                break
        
        # Сортируем от старых к новым
        messages_store.sort(key=lambda x: x["date_time"])
        logging.info(f"Loaded {len(messages_store)} messages from channel")
        
    except Exception as e:
        logging.error(f"Error loading messages: {e}")

async def check_for_updates():
    """Проверяет новые сообщения и удаленные"""
    global messages_store
    
    while True:
        try:
            # 1. Проверяем новые сообщения
            latest_id = messages_store[-1]["id"] if messages_store else 0
            new_messages = []
            
            async for message in bot.get_chat_history(TELEGRAM_CHANNEL, limit=10):
                if message.message_id > latest_id:
                    parsed = await parse_message(message)
                    new_messages.append(parsed)
            
            if new_messages:
                messages_store.extend(new_messages)
                logging.info(f"Added {len(new_messages)} new messages")
            
            # 2. Проверяем удаленные сообщения
            if messages_store:
                recent_ids = [msg["id"] for msg in messages_store[-LAST_MESSAGES_TO_CHECK:]]
                actual_ids = []
                
                async for message in bot.get_chat_history(TELEGRAM_CHANNEL, limit=LAST_MESSAGES_TO_CHECK):
                    actual_ids.append(message.message_id)
                
                deleted_ids = set(recent_ids) - set(actual_ids)
                if deleted_ids:
                    messages_store = [msg for msg in messages_store if msg["id"] not in deleted_ids]
                    logging.info(f"Removed {len(deleted_ids)} deleted messages")
            
        except Exception as e:
            logging.error(f"Update check error: {e}")
        
        await asyncio.sleep(CHECK_INTERVAL)

# --- Обработчик новых сообщений ---
@dp.channel_post()
async def handle_new_message(message: types.Message):
    """Обработчик новых сообщений в канале"""
    global messages_store
    
    try:
        parsed = await parse_message(message)
        messages_store.append(parsed)
        
        # Поддерживаем лимит сообщений
        if len(messages_store) > MESSAGE_LIMIT:
            messages_store = messages_store[-MESSAGE_LIMIT:]
            
    except Exception as e:
        logging.error(f"Error handling new message: {e}")

# --- API Endpoints ---
@app.get("/messages", response_model=List[ChannelMessage])
async def get_messages(limit: int = API_MESSAGES_LIMIT):
    """
    Возвращает последние сообщения из канала
    
    Args:
        limit: Количество возвращаемых сообщений (макс. API_MESSAGES_LIMIT)
    
    Returns:
        Список сообщений в формате JSON
    """
    return messages_store[-limit:]

# --- Запуск приложения ---
@app.on_event("startup")
async def startup():
    """Запуск приложения FastAPI"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Проверяем обязательные переменные
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL:
        raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL must be set in .env")
    
    # Запускаем бота
    asyncio.create_task(dp.start_polling(bot))
    
    # Загружаем историю сообщений
    await load_all_messages()
    
    # Запускаем фоновую задачу проверки обновлений
    asyncio.create_task(check_for_updates())
    
    logging.info("Application started")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
