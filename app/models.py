from pydantic import BaseModel
from datetime import datetime




class Message(BaseModel):
    message_id: int
    datetime: datetime
    message: str
    media: str
    type_media: str
    grouped_id: int
    link_to_message_in_telegram: str

    class Config:
        from_attributes = True



class MessagesPaginatedResponse(BaseModel):
    all_group_messages: list[Message]
    total: int
    limit: int
    offset: int
    has_more: bool
    telegram_channel: str