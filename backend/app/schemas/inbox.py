from pydantic import BaseModel


class InboxMessageOut(BaseModel):
    id: int
    subject: str
    body: str
    is_read: bool
