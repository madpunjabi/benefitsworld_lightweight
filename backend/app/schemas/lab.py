from pydantic import BaseModel


class LabUploadOut(BaseModel):
    id: int
    document_id: str
    requirement: str
    attempted_at_day: int
    ui_reported_success: bool
    actually_persisted: bool
    scripted_failure_id: str | None


class LabWorldStateOut(BaseModel):
    scenario_id: str
    scenario_version: str
    current_sim_day: int
    case_status: str
    case_id: str
    open_requirements: list[str]
    interview: dict | None
    applied_event_ids: list[str]
    pending_event_ids: list[str]
    uploads: list[LabUploadOut]


class ResetOut(BaseModel):
    ok: bool


class AdvanceIn(BaseModel):
    to_day: int


class AdvanceOut(BaseModel):
    current_sim_day: int
    events_applied: list[str]
