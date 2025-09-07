from dotenv import load_dotenv
from telethon.tl.functions.messages import GetHistoryRequest
from datetime import datetime
from telethon.sync import TelegramClient
import os , asyncio
import sqlite3, re
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
TIME_FOR_UPDATE = float(os.getenv("TIME_FOR_UPDATE"))
PHONE = os.getenv("PHONE")
CODE = int(os.getenv("CODE"))
ROOT_DIR = os.getenv("ROOT_DIR")
NAME_DB = os.getenv("NAME_DB")
NAME_TABLE_MESSAGES = os.getenv("NAME_TABLE_MESSAGES")
MIN_ID = [0]


class DataBase():
    def __init__(self):
        self.name_db = NAME_DB
        self.connection = sqlite3.connect(os.path.join("./data_base", self.name_db))
        self.cursor = self.connection.cursor()

        self.create_table_messages()

    def create_table_messages(self):
        try:
            self.cursor.execute(f'''CREATE TABLE IF NOT EXISTS {NAME_TABLE_MESSAGES}(
            message_id INTEGER PRIMARY KEY,
            datetime DATETIME NOT NULL,
            message TEXT NULL,
            media TEXT NULL,
            type_media VARCHAR(256),
            grouped_id BIGINT NULL)
        ''')
            self.connection.commit()
        except Exception as e:
            logger.error(f'create_table_active_messages failed: {e}')

    '''
    Берем все message_id
    '''
    def get_all_id(self):

        try:
            self.cursor.execute(f'SELECT message_id FROM {NAME_TABLE_MESSAGES}')
            all_messages_id = DataBase.check_tuple(self.cursor.fetchall())
            return all_messages_id

        except Exception as e:
            logger.error(f'get_all_id failed: {e}')


    '''
    Добавление сообщения в БД
    '''

    def add_message(self, name_table, egida_telecom_message, media, type_media):
        try:
            self.cursor.execute(f'''
            INSERT INTO {name_table} (message_id, datetime, message, media, type_media, grouped_id) 
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (egida_telecom_message.message_id, egida_telecom_message.datetime, egida_telecom_message.message, media, type_media, egida_telecom_message.grouped_id))
            self.connection.commit()

        except Exception as e:
            logger.error(f'add_message failed: {e}')


    '''
    Беререм медиа из записей 
    '''
    def get_media_for_delete(self, ids, name_table):
        try:
            placeholders = ','.join('?' * len(ids))
            query = f"SELECT media FROM {name_table} WHERE message_id IN ({placeholders})"
            self.cursor.execute(query, ids)
            self.delete_media(self.cursor.fetchall())
        except Exception as e:
            logger.error(f'get_media_for_delete failed: {e}')


    '''
    Удаляем медиа
    '''
    def delete_media(self, all_media):
        try:
            for media in all_media:
                abs_path = os.path.join(ROOT_DIR, media[0])
                os.remove(abs_path)


        except Exception as e:
            logger.warning(f'delete_media failed: {e, all_media}')


    '''
    Удаление записей
    '''
    def delete_records(self, delete_ids, name_table):
        try:
            params = [(message_id,) for message_id in delete_ids]

            self.get_media_for_delete(delete_ids, name_table)
            self.cursor.executemany(f"DELETE FROM {name_table} WHERE message_id = ?", params)
            self.connection.commit()

        except Exception as e:
            logger.error(f'delete_records failed: {e}')


    '''
    делаем элементы списка tuple -> int
    '''
    @staticmethod
    def check_tuple(list_ids):
        if list_ids:
            if type(list_ids[0]) == tuple:
                new_list_ids = [id[0] for id in list_ids]
                return new_list_ids
            else:
                return list_ids
        else:
            return []

    '''
    Возвращаем все id для удаления
    '''
    def get_id_for_delete(self, telegram_list_messages):
        try:

            latest_ids_from_telegram_where_there_is_text = []
            for message in telegram_list_messages.messages:
                if message.message != "" or message.message:
                    latest_ids_from_telegram_where_there_is_text.append(message.id)


            all_messages_id_from_db = self.get_all_id()
            sorted_messages_ids_bd = sorted(all_messages_id_from_db)[-len(latest_ids_from_telegram_where_there_is_text):]

            delete_messages_ids = list(set(sorted_messages_ids_bd) - set(latest_ids_from_telegram_where_there_is_text))

            return delete_messages_ids

        except Exception as e:
            logger.error(f'get_id_for_delete failed: {e}')

    '''
    Ищем какие элементы есть в 1 списке но нет во 2 
    '''
    def list_append_ids(self, telegram_list_messages):
        try:
            list_ids_from_db =  self.get_all_id()
            list_ids_from_telegram = []
            final_append_list = []

            for message in telegram_list_messages.messages:
                list_ids_from_telegram.append(message.id)

            if list_ids_from_db:
                append_ids_list = list(set(list_ids_from_telegram) - set(list_ids_from_db))

                if append_ids_list:
                    for message in telegram_list_messages.messages:
                        if message.id in append_ids_list:
                            if message.message != "" or message.message:
                                final_append_list.append(message.id)

            # если БД пустая
            else:
                for message in telegram_list_messages.messages:
                    if message.message != "" or message.message:
                        final_append_list.append(message.id)

            return final_append_list

        except Exception as e:
            logger.error(f'list_append_ids failed: {e}')



class MessageEgidaTelecom():
    def __init__(self, message_id, datetime, message, media,  grouped_id):
        self.message_id = message_id
        self.datetime = datetime
        self.message = message
        self.media = media
        self.grouped_id = grouped_id

'''
Скачиваем медиа
'''
async def download_media_our(client,message):
    try:
        path = await client.download_media(message, "media/")
        type_media = await check_media_type(path)
        return path, type_media

    except Exception as e:
        logger.error(f'download_media_our Failed: {e}')



'''
Проверяем тип медиа
'''
async def check_media_type(filename):
    try:
        pattern = r'\.(mp4|mov|avi|png|jpg|webp)$'
        match = re.search(pattern, filename, re.IGNORECASE)

        if match:
            extension = match.group(1).lower()
            if extension in ['mp4', 'mov', 'avi']:
                return 'video'
            elif extension in ['png', 'jpg', 'webp']:
                return 'photo'
        return 'unknown'

    except Exception as e:
        logger.error(f'check_media_type Failed: {e}')


'''
Добавление новых записей
'''
async def add_records(client = None, all_messages = None , append_ids = None):

    try:
        min_id = 0

        for message in all_messages.messages:
            path_media = None
            type_media = None
            egida_telecom_message = MessageEgidaTelecom(message.id, message.date, message.message, message.media, message.grouped_id)

            if egida_telecom_message.message_id in append_ids:

                if egida_telecom_message.media:
                    path_media, type_media = await download_media_our(client, message)

                db.add_message(
                    NAME_TABLE_MESSAGES,
                    egida_telecom_message,
                    path_media,
                    type_media,
                )

            min_id = egida_telecom_message.message_id

        return min_id

    except Exception as e:
        logger.error(f'Add records Failed: {e}')


"""
Получение последних сообщений из канала
"""
async def periodic_request(client, min_id):
    try:
        latest_messages = await client(GetHistoryRequest(
            peer=CHANNEL_ID,
            limit=30,
            offset_id=0,
            offset_date=datetime.now(),
            min_id=min_id,
            add_offset=0,
            max_id=0,
            hash=0
        ))
        return latest_messages

    except Exception as e:
        logger.error(f'periodic_request failed: {e}')

'''
Постоянный парсинг сообщений
'''
async def infinite_parsing(client,db):
    try:
        while True:
            latest_messages = await periodic_request(client, MIN_ID[0])
            append_ids = db.list_append_ids(latest_messages)

            if append_ids:
                MIN_ID[0] = await add_records(client, latest_messages, append_ids)

            delete_messages_ids= db.get_id_for_delete(latest_messages)

            if delete_messages_ids:
                db.delete_records(delete_messages_ids, NAME_TABLE_MESSAGES)

            logger.info("История обновленна")
            await asyncio.sleep(TIME_FOR_UPDATE)

    except Exception as e:
        logger.error(f'infinite_parsing failed: {e}')


if __name__ == "__main__":
    try:
        os.chdir(ROOT_DIR)
        os.makedirs("./data_base", exist_ok=True)
        os.makedirs("./media", exist_ok=True)

        db = DataBase()
        client = TelegramClient("egidat", API_ID, API_HASH, device_model="iPhone 12 Pro",
                                system_version="4.16.30-CUSTOM")
        client.connect()
        client.sign_in(PHONE)
        # code = input('enter code: ')
        client.sign_in(phone=PHONE, code=CODE)
        client.loop.run_until_complete(infinite_parsing(client, db))

    except Exception as e:
        logger.error(f'Sign-in failed: {e}')



