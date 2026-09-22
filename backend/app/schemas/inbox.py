from pydantic import BaseModel


class InboxMessageOut(BaseModel):
    id: int
    day: int
    sender: str
    subject: str
    body: str
    is_read: bool
