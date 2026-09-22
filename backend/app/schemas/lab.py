from pydantic import BaseModel


class LabWorldStateOut(BaseModel):
    scenario_id: str
    scenario_version: str
    current_sim_day: int
    case_status: str
    case_id: str
    open_requirements: list[str]


class ResetOut(BaseModel):
    ok: bool


class AdvanceIn(BaseModel):
    to_day: int


class AdvanceOut(BaseModel):
    current_sim_day: int
    events_applied: list[str]
