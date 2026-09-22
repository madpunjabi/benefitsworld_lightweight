import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import clock, reset, world_state
from app.db import get_session
from app.schemas.lab import AdvanceIn, AdvanceOut, LabWorldStateOut, ResetOut
from app.security import require_lab_token

router = APIRouter(prefix="/lab", tags=["lab"], dependencies=[Depends(require_lab_token)])


@router.get("/world_state", response_model=LabWorldStateOut)
def get_world_state(session: Session = Depends(get_session)):
    meta = world_state.get_meta(session)
    case = world_state.get_case(session)
    return LabWorldStateOut(
        scenario_id=meta.scenario_id,
        scenario_version=meta.scenario_version,
        current_sim_day=meta.current_sim_day,
        case_status=case.status,
        case_id=case.case_id,
        open_requirements=json.loads(case.open_requirements_json),
    )


@router.post("/reset", response_model=ResetOut)
def do_reset(session: Session = Depends(get_session)):
    reset.reset(session)
    world_state.log_action(
        session, actor="harness", sim_day=0, action_type="reset", payload={}, result="ok"
    )
    return ResetOut(ok=True)


@router.post("/clock/advance", response_model=AdvanceOut)
def do_advance(body: AdvanceIn, session: Session = Depends(get_session)):
    result = clock.advance_to(session, body.to_day)
    return AdvanceOut(**result)
