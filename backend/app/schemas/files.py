from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    filename: str
    date: str
    visible_text: str
