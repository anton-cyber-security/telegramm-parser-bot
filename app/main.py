import os
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from database import DataBase
from models import Message, MessageGroup, MessagesPaginatedResponse
import logging
import uvicorn

ROOT_DIR = os.getenv("ROOT_DIR")
NAME_DB = os.getenv("NAME_DB")
NAME_TABLE_ACTIVE_MESSAGES = os.getenv("NAME_TABLE_ACTIVE_MESSAGES")
NAME_TABLE_PASSIVE_MESSAGES = os.getenv("NAME_TABLE_PASSIVE_MESSAGES")
DOMAIN = os.getenv("DOMAIN")
PROTOCOL = os.getenv("PROTOCOL")

db = DataBase(ROOT_DIR, NAME_DB, NAME_TABLE_ACTIVE_MESSAGES, NAME_TABLE_PASSIVE_MESSAGES)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("web_app_telegram")


app = FastAPI(
    title="WEB_SERVER_FOR_TO_SEND_NEWS_FROM_TELEGRAM",
    description="WEB_SERVER_FOR_TO_SEND_NEWS_FROM_TELEGRAM",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def new_correct_message(message):

    message_text = ""
    media = ""
    type_media = ""
    grouped_id = -1

    if message[2]:
         message_text = message[2]

    if message[3]:
        media =f"{PROTOCOL}://{DOMAIN}/static/{message[3][6:]}"

    if message[4]:
        type_media = message[4]

    if message[5]:
        grouped_id = message[5]


    return message_text, media, type_media, grouped_id




@app.get("/")
async def root():
    return {"message": "WEB SERVER FOR TO SEND NEWS FROM TELEGRAM"}



@app.get("/messages", response_model=MessagesPaginatedResponse)
async def get_items(
        limit: int = Query(5, description="Количество записей на странице", ge=1, le=100),
        offset: int = Query(0, description="Смещение (пропустить N записей)", ge=0)
    ):
    try:
        # Получаем данные из базы
        active_messages = db.get_active_messages(limit, offset)
        total_count = db.get_total_count()

        active_messages = DataBase.from_tuple_to_list(active_messages)

        MessagesPaginatedResponseList = []

        for active_message in active_messages:

            message_text, media, type_media, grouped_id = await new_correct_message(active_message)

            grouped_messages = []

            if active_message[5]:
                try:

                    passive_messages = db.get_passive_messages(active_message[5])
                    passive_messages = DataBase.from_tuple_to_list(passive_messages)



                    grouped_messages.append(
                        Message(
                            message_id=active_message[0],
                            datetime=active_message[1],
                            message=message_text,
                            media=media,
                            type_media=type_media,
                            grouped_id=grouped_id
                        )
                    )


                    for message in passive_messages:

                        message_text, media, type_media, grouped_id = await new_correct_message(message)
                        grouped_messages.append(
                            Message(
                                message_id=message[0],
                                datetime=message[1],
                                message=message_text,
                                media=media,
                                type_media=type_media,
                                grouped_id=grouped_id
                            )
                        )


                except Exception as e:
                    logger.error(f'GROUPED MESSAGES failed: {e, active_message[5], type(active_message[5])}')

            else:
                try:
                    grouped_messages = [
                        Message(
                            message_id=active_message[0],
                            datetime=active_message[1],
                            message=message_text,
                            media=media,
                            type_media=type_media,
                            grouped_id=grouped_id
                        )
                    ]
                except Exception as e:
                    logger.error(f'NO GROUPED MESSAGES failed: {e}')

            MessageGroupRecord = MessageGroup(
                group_messages=grouped_messages
            )
            MessagesPaginatedResponseList.append(MessageGroupRecord)


        # Проверяем, есть ли еще записи
        has_more = (offset + limit) < total_count

        return MessagesPaginatedResponse(
            all_group_messages=MessagesPaginatedResponseList,
            total=total_count,
            limit=limit,
            offset=offset,
            has_more=has_more
        )

    except Exception as e:
        logger.error(f'GET MESSAGES  failed: {e}')



if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8090)