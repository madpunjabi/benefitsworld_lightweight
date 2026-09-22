from pydantic import BaseModel


class PolicyItemOut(BaseModel):
    id: str
    title: str
    topic: str
    text: str
