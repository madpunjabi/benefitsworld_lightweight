from pydantic import BaseModel


class PolicyItemOut(BaseModel):
    id: str
    title: str
    source: str
    source_url: str | None
    jurisdiction: str
    effective_date: str
    topic: str
    text: str
