from typing import List, Tuple
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


class DataBase():
    def __init__(self, root_dir, name_bd, name_table_active_messages, name_table_passive_messages ):
        self.name_db = name_bd
        self.name_table_active_messages = name_table_active_messages
        self.name_table_passive_messages = name_table_passive_messages
        self.connection = sqlite3.connect(os.path.join(f"{root_dir}/data_base", self.name_db))
        self.cursor = self.connection.cursor()



    def get_active_messages(self, limit: int = 5, offset: int = 0) -> List[Tuple]:
        self.cursor.execute(f'''
            SELECT *
            FROM {self.name_table_active_messages}
            ORDER BY datetime DESC 
            LIMIT ? OFFSET ?
        ''', (limit, offset))

        active_messages = self.cursor.fetchall()
        return active_messages

    def get_passive_messages(self, grouped_id):
        grouped_id_tuple = (grouped_id,)
        self.cursor.execute(f'''
                SELECT *
                FROM {self.name_table_passive_messages}
                WHERE grouped_id = ?
        ''', (grouped_id_tuple))
        passive_messages = self.cursor.fetchall()
        return passive_messages

    '''
    делаем элементы списка tuple -> list
    '''

    @staticmethod
    def from_tuple_to_list(list_messages):
        if list_messages:
            if type(list_messages[0]) == tuple:
                new_list_messages = [list(message) for message in list_messages]
                return new_list_messages
            else:
                return list_messages
        else:
            return []

    """
    Получить количество всех записей
    """
    def get_total_count(self) -> int:
        self.cursor.execute(f"SELECT COUNT(*) FROM {self.name_table_active_messages}")
        total = self.cursor.fetchone()[0]
        return total


