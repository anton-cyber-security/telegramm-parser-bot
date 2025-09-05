import os
import time
from dotenv import load_dotenv
from telegram import Bot

# Загрузка переменных окружения
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

messages_dict = {}
last_update_id = 0


def check_new_messages_simple(interval_seconds=10):
    """Простая функция проверки новых сообщений"""
    global last_update_id

    bot = Bot(token=BOT_TOKEN)

    print(f"Проверка каждые {interval_seconds} секунд...")
    print("Ctrl+C для остановки")

    try:
        while True:
            try:
                # Получаем обновления
                updates = bot.get_updates(offset=last_update_id + 1, timeout=30)

                for update in updates:
                    if update.update_id > last_update_id:
                        last_update_id = update.update_id

                    if update.message and update.message.chat.id == CHANNEL_ID:
                        message = update.message
                        messages_dict[message.message_id] = {
                            'message_id': message.message_id,
                            'date': message.date.isoformat(),
                            'text': message.text or message.caption or '',
                            'has_media': any([message.photo, message.video, message.audio, message.document])
                        }

                        print(f"Новое сообщение #{message.message_id}")

                time.sleep(interval_seconds)

            except Exception as e:
                print(f"Ошибка: {e}")
                time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print(f"\nСобрано сообщений: {len(messages_dict)}")
        return messages_dict


# Запуск
if __name__ == "__main__":
    result = check_new_messages_simple(15)
    print("Работа завершена")