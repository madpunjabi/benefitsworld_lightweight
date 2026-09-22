from pydantic import BaseModel


class CaseOut(BaseModel):
    case_id: str
    status: str
    open_requirements: list[str]
    interview: dict | None
    recertification: dict | None
    received_document_ids: list[str]


class NoticeOut(BaseModel):
    id: str
    text: str
