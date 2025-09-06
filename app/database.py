import sqlite3
from typing import List, Tuple, Optional
from dotenv import load_dotenv
import os
import sqlite3
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
SESSION = os.getenv('SESSION')
TIME_FOR_UPDATE = float(os.getenv("TIME_FOR_UPDATE"))
PHONE = os.getenv("PHONE")
CODE = int(os.getenv("CODE"))
ROOT_DIR = os.getenv("ROOT_DIR")
NAME_DB = os.getenv("NAME_DB")
NAME_TABLE_ACTIVE_MESSAGES = os.getenv("NAME_TABLE_ACTIVE_MESSAGES")
NAME_TABLE_PASSIVE_MESSAGES = os.getenv("NAME_TABLE_PASSIVE_MESSAGES")



class DataBase():
    def __init__(self):
        self.name_db = NAME_DB
        self.connection = sqlite3.connect(os.path.join("./data_base", self.name_db))
        self.cursor = self.connection.cursor()


    '''
    Берем все message_id из не группированых сообщений или их одно главное сообщений 
    '''
    def get_all_active_id(self):
        try:
            self.cursor.execute(f'SELECT message_id FROM {NAME_TABLE_ACTIVE_MESSAGES}')
            all_active_message_id = self.cursor.fetchall()
            return all_active_message_id
        except Exception as e:
            logger.error(f'get_all_passive_id failed: {e}')

    '''
    Берем все message_id из группированных сообщений
    '''
    def get_all_passive_id(self):
        try:
            self.cursor.execute(f'SELECT message_id FROM {NAME_TABLE_PASSIVE_MESSAGES}')
            all_passive_message_id = self.cursor.fetchall()
            return all_passive_message_id
        except Exception as e:
            logger.error(f'get_all_passive_id failed: {e}')

    '''
    Берем все message_id
    '''
    def get_all_id(self):
        try:
            all_passive_messages_id = self.check_tuple(self.get_all_passive_id())
            all_active_messages_id = self.check_tuple(self.get_all_active_id())

            all_messages_id=list(set(all_passive_messages_id + all_active_messages_id))
            return all_messages_id

        except Exception as e:
            logger.error(f'get_all_id failed: {e}')


    '''
    делаем элементы списка tuple -> int
    '''
    def check_tuple(self, list_ids):
        if list_ids:
            if type(list_ids[0]) == tuple:
                new_list_ids = [id[0] for id in list_ids]
                return new_list_ids
            else:
                return list_ids
        else:
            return []


