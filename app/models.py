from pydantic import BaseModel
from datetime import datetime




class Message(BaseModel):
    message_id: int
    datetime: datetime
    message: str
    media: str
    type_media: str
    grouped_id: int

    class Config:
        from_attributes = True



class MessageGroup(BaseModel):
    group_messages: list[Message]



class MessagesPaginatedResponse(BaseModel):
    all_group_messages: list[MessageGroup]
    total: int
    limit: int
    offset: int
    has_more: bool