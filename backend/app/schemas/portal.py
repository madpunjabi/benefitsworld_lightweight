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
    day: int
    text: str


class UploadIn(BaseModel):
    document_id: str
    requirement: str


class UploadOut(BaseModel):
    document_id: str
    requirement: str
    received: bool


class InterviewSlotOut(BaseModel):
    id: str
    day: int
    start_time: str
    end_time: str


class ScheduleInterviewIn(BaseModel):
    slot_id: str


class ScheduleInterviewOut(BaseModel):
    status: str
    slot_id: str
    day: int
    start_time: str
    end_time: str


class RecertificationSubmitOut(BaseModel):
    status: str
    submitted_at_day: int | None
    snapshot_applied_event_ids: list[str]
