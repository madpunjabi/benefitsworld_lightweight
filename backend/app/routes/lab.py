import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import clock, event_engine, reset, world_state
from app.db import get_session
from app.schemas.lab import AdvanceIn, AdvanceOut, LabWorldStateOut, ResetOut
from app.security import require_lab_token

router = APIRouter(prefix="/lab", tags=["lab"], dependencies=[Depends(require_lab_token)])


@router.get("/world_state", response_model=LabWorldStateOut)
def get_world_state(session: Session = Depends(get_session)):
    meta = world_state.get_meta(session)
    case = world_state.get_case(session)
    applied_ids = set(world_state.get_applied_event_ids(session))
    all_ids = [e.id for e in event_engine.default_engine().events]
    return LabWorldStateOut(
        scenario_id=meta.scenario_id,
        scenario_version=meta.scenario_version,
        current_sim_day=meta.current_sim_day,
        case_status=case.status,
        case_id=case.case_id,
        open_requirements=json.loads(case.open_requirements_json),
        interview=world_state.get_interview(session),
        applied_event_ids=[eid for eid in all_ids if eid in applied_ids],
        pending_event_ids=[eid for eid in all_ids if eid not in applied_ids],
        uploads=[
            {
                "id": u.id,
                "document_id": u.document_id,
                "requirement": u.requirement,
                "attempted_at_day": u.attempted_at_day,
                "ui_reported_success": bool(u.ui_reported_success),
                "actually_persisted": bool(u.actually_persisted),
                "scripted_failure_id": u.scripted_failure_id,
            }
            for u in world_state.get_uploads(session)
        ],
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
