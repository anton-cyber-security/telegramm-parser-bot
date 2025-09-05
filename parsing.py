from dotenv import load_dotenv
from telethon.tl.functions.messages import GetHistoryRequest
from datetime import datetime
from telethon.sync import TelegramClient
import os ,time, asyncio
import sqlite3
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
SESSION = os.getenv('SESSION')
TIME_FOR_UPDATE = float(os.getenv("TIME_FOR_UPDATE"))
PHONE = os.getenv("PHONE")
CODE = int(os.getenv("CODE"))
ROOT_DIR = os.getenv("ROOT_DIR")
MIN_ID = [0]


class DataBase():
    def __init__(self, name_db):
        self.name_db = name_db
        self.connection = sqlite3.connect(self.name_db)
        self.cursor = self.connection.cursor()

        self.create_db()

    def create_db(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS Messages(
        message_id INTEGER PRIMARY KEY,
        datetime DATETIME NOT NULL,
        message TEXT NULL,
        media TEXT NULL,
        type_media VARCHAR(256))
    ''')

        self.connection.commit()

    def get_all_id(self):
        self.cursor.execute(f'SELECT message_id FROM Messages')
        all_message_id = self.cursor.fetchall()
        return all_message_id


    def add_message(self, message_id, datetime, message, media, type_media):
        self.cursor.execute('''
        INSERT INTO Messages (message_id, datetime, message, media, type_media) 
        VALUES (?, ?, ?, ?, ?)
        ''', (message_id, datetime, message, media, type_media))
        self.connection.commit()


    def get_media_for_delete(self, ids):
        placeholders = ','.join('?' * len(ids))
        query = f"SELECT * FROM Messages WHERE message_id IN ({placeholders})"
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
        self.cursor.executemany("DELETE FROM Messages WHERE message_id = ?", params)
        self.connection.commit()


    def check_tuple_1(self, list_ids):
        if list_ids:
            if type(list_ids[0]) == tuple:
                new_list_ids = [id[0] for id in list_ids]
                return new_list_ids
            else:
                return list_ids






class MessageEgidaTelecom():
    def __init__(self, message_id, datetime, message, media):
        self.message_id = message_id
        self.datetime = datetime
        self.message = message
        self.media = media


'''
Ищем какие элементы есть в 1 списке но нет во 2 
'''
async def difference(list_messages, list_2):
    list_2 = await check_tuple(list_2)
    list_1 =[]
    for message in list_messages.messages:
        list_1.append(message.id)
    ids_list = list(set(list_1) - set(list_2))

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
    print(type(message.media))
    print(message)
    print(message.media)
    path = await client.download_media(message, "media/")
    return path



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
        egida_telecom_message = MessageEgidaTelecom(message.id, message.date, message.message, message.media)


        if egida_telecom_message.message or egida_telecom_message.media:
            if append_ids:
                if egida_telecom_message.message_id in append_ids:

                    if egida_telecom_message.media:
                        id_media = await download_media_our(client, message)

                    db.add_message(egida_telecom_message.message_id, egida_telecom_message.datetime,
                                egida_telecom_message.message,
                               id_media, type_media)

            else:
                if egida_telecom_message.media:
                    id_media = await download_media_our(client, message)


                db.add_message(egida_telecom_message.message_id, egida_telecom_message.datetime,
                               egida_telecom_message.message,
                               id_media, type_media)

        min_id = egida_telecom_message.message_id

    return min_id



'''
Удаление из БД удаленных последних записей
'''
async def delete_latest_records(db, latest_messages):
    latest_ids = []
    all_message_id_from_db = await check_tuple(db.get_all_id())
    sorted_ids_bd = sorted(all_message_id_from_db)[-len(latest_messages.messages):]
    for message in latest_messages.messages:
        latest_ids.append(message.id)
    sorted_ids_now = sorted(latest_ids)
    delete_ids = list(set(sorted_ids_bd) - set(sorted_ids_now))
    db.delete_records(delete_ids)




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


"""
Первое получение всех сообщений из канала
"""
async def first_launch(client,db):
    all_messages = await client(GetHistoryRequest(
        peer = CHANNEL_ID,
        limit = 300,
        offset_id = 0,
        offset_date = datetime.now(),
        min_id = 0,
        add_offset = 0,
        max_id = 0,
        hash = 0
    ))

    all_message_id_from_db = db.get_all_id()

    # Если БД Пустая
    if not all_message_id_from_db:
        MIN_ID[0] = await add_records(client, all_messages)

    # Если в БД есть записи
    else:
        delete_ids = await difference2(all_messages, all_message_id_from_db)
        if delete_ids:
            db.delete_records(delete_ids)


    '''
    Постоянный парсинг сообщений
    '''
    while True:
        all_message_id_from_db = db.get_all_id()

        await asyncio.sleep(TIME_FOR_UPDATE)
        latest_messages = await periodic_request(client, MIN_ID[0])

        append_ids = await difference(latest_messages, all_message_id_from_db)

        if append_ids:
            MIN_ID[0] = await add_records(client, latest_messages, append_ids)

        await delete_latest_records(db, latest_messages)

        print(f"История обновлена {time.strftime('%H:%M:%S')}")




if __name__ == "__main__":
    db = DataBase("messages.db")
    client = TelegramClient("egidat", API_ID, API_HASH, device_model="iPhone 12 Pro", system_version="4.16.30-CUSTOM")
    client.connect()
    client.sign_in(PHONE)
    #code = input('enter code: ')
    client.sign_in(phone=PHONE, code=CODE)
    client.loop.run_until_complete(first_launch(client,db))

    '''except Exception as e:
        print(f'Sign-in failed: {e}')
    '''


