from pydantic import BaseModel


class CaseOut(BaseModel):
    case_id: str
    status: str
    open_requirements: list[str]
    reported_employer: str | None
    interview: dict | None
    recertification: dict | None
    received_document_ids: list[str]


class NoticeOut(BaseModel):
    id: str
    text: str


class UploadIn(BaseModel):
    document_id: str
    requirement: str


class UploadOut(BaseModel):
    document_id: str
    requirement: str
    received: bool
