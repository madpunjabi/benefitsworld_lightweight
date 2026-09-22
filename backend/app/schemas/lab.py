from pydantic import BaseModel


class LabUploadOut(BaseModel):
    id: int
    document_id: str
    requirement: str
    attempted_at_day: int
    ui_reported_success: bool
    actually_persisted: bool
    scripted_failure_id: str | None


class LabSilentFailureOut(BaseModel):
    id: str
    document_id: str
    requirement: str
    consumed: bool


class LabIncomeTruthOut(BaseModel):
    document_id: str
    filename: str
    visible_text: str


class LabWorldStateOut(BaseModel):
    scenario_id: str
    scenario_version: str
    current_sim_day: int
    case_status: str
    case_id: str
    open_requirements: list[str]
    interview: dict | None
    recertification: dict | None
    applied_event_ids: list[str]
    pending_event_ids: list[str]
    uploads: list[LabUploadOut]
    silent_failures: list[LabSilentFailureOut]
    # Researcher-facing "what's actually true about Maya's income right
    # now" — D-107 once Day 18 has passed and it exists, D-101 before
    # that. Debug convenience only; the agent never sees this framing,
    # only the underlying documents via /files.
    income_truth_document: LabIncomeTruthOut | None


class ResetIn(BaseModel):
    scenario_id: str | None = None


class ResetOut(BaseModel):
    ok: bool


class AdvanceIn(BaseModel):
    to_day: int


class AdvanceOut(BaseModel):
    current_sim_day: int
    events_applied: list[str]


class EvaluateOut(BaseModel):
    binary_success: bool
    checkpoints: dict[str, bool]


class SnapshotOut(BaseModel):
    snapshot: dict[str, list[dict]]


class RestoreIn(BaseModel):
    snapshot: dict[str, list[dict]]


class RestoreOut(BaseModel):
    ok: bool
