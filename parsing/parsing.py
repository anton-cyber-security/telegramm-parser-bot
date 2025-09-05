from dotenv import load_dotenv
from telethon.tl.functions.messages import GetHistoryRequest
from datetime import datetime
from telethon.sync import TelegramClient
import os ,time, asyncio
import sqlite3, re
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
SESSION = os.getenv('SESSION')
TIME_FOR_UPDATE = float(os.getenv("TIME_FOR_UPDATE"))
PHONE = os.getenv("PHONE")
CODE = int(os.getenv("CODE"))
ROOT_DIR = os.getenv("ROOT_DIR")
NAME_DB = os.getenv("NAME_DB")
NAME_TABLE_ACTIVE_MESSAGES = os.getenv("NAME_TABLE_ACTIVE_MESSAGES")
NAME_TABLE_PASSIVE_MESSAGES = os.getenv("NAME_TABLE_PASSIVE_MESSAGES")
MIN_ID = [0]


class DataBase():
    def __init__(self):
        self.name_db = NAME_DB
        self.connection = sqlite3.connect(os.path.join("./data_base", self.name_db))
        self.cursor = self.connection.cursor()

        self.create_table_active_messages()
        self.create_table_passive_messages()

    def create_table_active_messages(self):
        self.cursor.execute(f'''CREATE TABLE IF NOT EXISTS {NAME_TABLE_ACTIVE_MESSAGES}(
        message_id INTEGER PRIMARY KEY,
        datetime DATETIME NOT NULL,
        message TEXT NULL,
        media TEXT NULL,
        type_media VARCHAR(256),
        grouped_id BIGINT NULL)
    ''')
        self.connection.commit()

    def create_table_passive_messages(self):
        self.cursor.execute(f'''CREATE TABLE IF NOT EXISTS {NAME_TABLE_PASSIVE_MESSAGES}(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT NULL,
        media TEXT NULL,
        type_media VARCHAR(256),
        grouped_id BIGINT NULL)
    ''')
        self.connection.commit()

    def get_all_id(self):
        self.cursor.execute(f'SELECT message_id FROM {NAME_TABLE_ACTIVE_MESSAGES}')
        all_message_id = self.cursor.fetchall()
        return all_message_id


    def add_message(self, message_id, datetime, message, media, type_media, grouped_id):
        self.cursor.execute(f'''
        INSERT INTO {NAME_TABLE_ACTIVE_MESSAGES} (message_id, datetime, message, media, type_media, grouped_id) 
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (message_id, datetime, message, media, type_media, grouped_id))
        self.connection.commit()


    def get_media_for_delete(self, ids):
        placeholders = ','.join('?' * len(ids))
        query = f"SELECT * FROM {NAME_TABLE_ACTIVE_MESSAGES} WHERE message_id IN ({placeholders})"
        self.cursor.execute(query, ids)
        self.delete_media(self.cursor.fetchall())


    def delete_media(self, all_media):

        for media in all_media:
            media = self.check_tuple_1(media)
            abs_path = os.path.join(ROOT_DIR, media[3])

            try:
                os.remove(abs_path)
            except OSError as e:
                print(f"Ошибка при удалении файла '{abs_path}': {e}")


    def delete_records(self, delete_ids):
        params = [(message_id,) for message_id in delete_ids]
        self.get_media_for_delete(delete_ids)
        self.cursor.executemany(f"DELETE FROM {NAME_TABLE_ACTIVE_MESSAGES} WHERE message_id = ?", params)
        self.connection.commit()

    '''
    делаем элементы списка tuple -> int
    '''
    def check_tuple_1(self, list_ids):
        if list_ids:
            if type(list_ids[0]) == tuple:
                new_list_ids = [id[0] for id in list_ids]
                return new_list_ids
            else:
                return list_ids

    '''
    Возвращаем все id для удаления
    '''
    def get_id_for_delete(self, latest_messages):
        latest_ids = []
        all_message_id_from_db = self.check_tuple_1(self.get_all_id())
        sorted_ids_bd = sorted(all_message_id_from_db)[-len(latest_messages.messages):]
        for message in latest_messages.messages:
            latest_ids.append(message.id)
        sorted_ids_now = sorted(latest_ids)
        delete_ids = list(set(sorted_ids_bd) - set(sorted_ids_now))
        return delete_ids



class MessageEgidaTelecom():
    def __init__(self, message_id, datetime, message, media,  grouped_id):
        self.message_id = message_id
        self.datetime = datetime
        self.message = message
        self.media = media
        self.grouped_id = grouped_id


'''
Ищем какие элементы есть в 1 списке но нет во 2 
'''
async def difference(list_messages, list_2):
    list_2 = await check_tuple(list_2)
    list_1 =[]
    for message in list_messages.messages:
        list_1.append(message.id)
    if list_2:
        ids_list = list(set(list_1) - set(list_2))
    else:
        ids_list = list_1

    return ids_list

'''
Ищем какие элементы есть во 2 списке но нет в 1  
'''
async def difference2(list_messages, list_2):
    list_2 = await check_tuple(list_2)
    list_1 = []
    for message in list_messages.messages:
        list_1.append(message.id)
    ids_list = list(set(list_2) - set(list_1))

    return ids_list

'''
Скачиваем медиа
'''
async def download_media_our(client,message):
    path = await client.download_media(message, "media/")
    type_media = await check_media_type(path)
    return path, type_media




'''
Проверяем тип медиа
'''
async def check_media_type(filename):
    pattern = r'\.(mp4|mov|avi|png|jpg|webp)$'
    match = re.search(pattern, filename, re.IGNORECASE)

    if match:
        extension = match.group(1).lower()
        if extension in ['mp4', 'mov', 'avi']:
            return 'video'
        elif extension in ['png', 'jpg', 'webp']:
            return 'photo'
    return 'unknown'


'''
Делаем все элементы списка INT
'''
async def check_tuple(list_ids):
    if list_ids:
        if type(list_ids[0]) == tuple:
            new_list_ids = [id[0] for id in list_ids]
            return new_list_ids
        else:
            return list_ids



'''
Добавление новых записей
'''
async def add_records(client = None, all_messages = None , append_ids = None):

    min_id = 0

    for message in all_messages.messages:
        id_media = None
        type_media = None
        egida_telecom_message = MessageEgidaTelecom(message.id, message.date, message.message, message.media, message.grouped_id)


        if egida_telecom_message.message or egida_telecom_message.media:
            if append_ids:
                if egida_telecom_message.message_id in append_ids:

                    if egida_telecom_message.media:
                        id_media, type_media = await download_media_our(client, message)

                    db.add_message(egida_telecom_message.message_id, egida_telecom_message.datetime,
                                egida_telecom_message.message,
                               id_media, type_media, egida_telecom_message.grouped_id)

        min_id = egida_telecom_message.message_id

    return min_id


"""
Получение последних сообщений из канала
"""
async def periodic_request(client, min_id):
    latest_messages = await client(GetHistoryRequest(
        peer=CHANNEL_ID,
        limit=10,
        offset_id=0,
        offset_date=datetime.now(),
        min_id=min_id,
        add_offset=0,
        max_id=0,
        hash=0
    ))
    return latest_messages

'''
Постоянный парсинг сообщений
'''
async def infinite_parsing(client,db):
    while True:
        all_message_id_from_db = db.get_all_id()

        await asyncio.sleep(TIME_FOR_UPDATE)
        latest_messages = await periodic_request(client, MIN_ID[0])

        append_ids = await difference(latest_messages, all_message_id_from_db)

        if append_ids:
            MIN_ID[0] = await add_records(client, latest_messages, append_ids)

        delete_ids_list = db.get_id_for_delete(latest_messages)
        if delete_ids_list:
            db.delete_records(delete_ids_list)

        print(f"История обновлена {time.strftime('%H:%M:%S')}")


if __name__ == "__main__":
    os.chdir(ROOT_DIR)
    db = DataBase()
    client = TelegramClient("egidat", API_ID, API_HASH, device_model="iPhone 12 Pro", system_version="4.16.30-CUSTOM")
    client.connect()
    client.sign_in(PHONE)
    #code = input('enter code: ')
    client.sign_in(phone=PHONE, code=CODE)
    client.loop.run_until_complete(infinite_parsing(client,db))

    '''except Exception as e:
        print(f'Sign-in failed: {e}')
    '''


