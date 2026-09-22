from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    filename: str
    date: str
    type: str
    visible_text: str
