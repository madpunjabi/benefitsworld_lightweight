import json

from fastapi import APIRouter, Body, Depends, Response
from sqlalchemy.orm import Session

from app import clock, config, recertification, reset, scenario_registry, world_snapshot, world_state
from app.db import get_session
from app.schemas.lab import (
    AdvanceIn,
    AdvanceOut,
    EvaluateOut,
    LabWorldStateOut,
    LoginIn,
    LoginOut,
    ResetIn,
    ResetOut,
    RestoreIn,
    RestoreOut,
    SessionOut,
    SnapshotOut,
)
from app.security import (
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    create_session_token,
    require_lab_token,
)

router = APIRouter(prefix="/lab", tags=["lab"], dependencies=[Depends(require_lab_token)])

# Deliberately a SEPARATE router with no require_lab_token dependency:
# /lab/login is how a browser session is authenticated in the first
# place, so it cannot itself require the credential it's about to grant.
# /lab/logout needs no prior auth either — clearing a cookie that may or
# may not be there is always safe. Both still fall under the /lab path
# prefix, so PathScopedCORSMiddleware still scopes them to LAB_ORIGIN
# only, exactly like every other /lab route.
auth_router = APIRouter(prefix="/lab", tags=["lab-auth"])


@auth_router.post("/login", response_model=LoginOut)
def login(body: LoginIn, response: Response):
    if body.password != config.LAB_CONSOLE_PASSWORD:
        return LoginOut(ok=False)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session_token(),
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        secure=config.IS_PRODUCTION,
        samesite="none" if config.IS_PRODUCTION else "lax",
    )
    return LoginOut(ok=True)


@auth_router.post("/logout", response_model=LoginOut)
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE_NAME)
    return LoginOut(ok=True)


@router.get("/session", response_model=SessionOut)
def get_session_status():
    """Auth-gated by design: reaching this at all (past require_lab_token)
    is the only thing that matters. Used by the Lab Console's frontend to
    probe "am I logged in" without any side effects."""
    return SessionOut(authenticated=True)


@router.get("/world_state", response_model=LabWorldStateOut)
def get_world_state(session: Session = Depends(get_session)):
    meta = world_state.get_meta(session)
    case = world_state.get_case(session)
    applied_ids = set(world_state.get_applied_event_ids(session))
    all_ids = [e.id for e in scenario_registry.engine_for(session).events]
    return LabWorldStateOut(
        scenario_id=meta.scenario_id,
        scenario_version=meta.scenario_version,
        current_sim_day=meta.current_sim_day,
        case_status=case.status,
        case_id=case.case_id,
        open_requirements=json.loads(case.open_requirements_json),
        interview=world_state.get_interview(session),
        recertification=recertification.get_view(session),
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
        silent_failures=[
            {
                "id": f.id,
                "document_id": f.document_id,
                "requirement": f.requirement,
                "consumed": bool(f.consumed),
            }
            for f in world_state.get_silent_failures(session)
        ],
        income_truth_document=_income_truth_document(session),
    )


def _income_truth_document(session: Session) -> dict | None:
    doc_id = "D-107" if world_state.is_event_applied(session, "EVT-employment-change") else "D-101"
    doc = world_state.get_document(session, doc_id)
    if doc is None:
        return None
    return {"document_id": doc.id, "filename": doc.filename, "visible_text": doc.visible_text}


@router.get("/evaluate", response_model=EvaluateOut)
def get_evaluation(session: Session = Depends(get_session)):
    return scenario_registry.evaluate(session)


@router.post("/reset", response_model=ResetOut)
def do_reset(body: ResetIn | None = Body(default=None), session: Session = Depends(get_session)):
    # No body (the original, still-most-common call shape) or an empty
    # body both mean "reset into whatever scenario config.SCENARIO_ID
    # resolves to" — unchanged BW-001 behavior. A body with scenario_id
    # resets into that specific scenario instead.
    scenario_id = body.scenario_id if body is not None else None
    reset.reset(session, scenario_id=scenario_id)
    world_state.log_action(
        session, actor="harness", sim_day=0, action_type="reset", payload={"scenario_id": scenario_id}, result="ok"
    )
    return ResetOut(ok=True)


@router.post("/clock/advance", response_model=AdvanceOut)
def do_advance(body: AdvanceIn, session: Session = Depends(get_session)):
    result = clock.advance_to(session, body.to_day)
    return AdvanceOut(**result)


@router.get("/snapshot", response_model=SnapshotOut)
def get_snapshot(session: Session = Depends(get_session)):
    """Harness-only: a full, byte-for-byte dump of every row of every
    table — not just scenario truth, but the complete run history
    (uploads, action log, inbox, events-applied) up to this point. The
    caller is responsible for persisting the returned snapshot (e.g. to a
    file) if it needs to survive past this process."""
    snap = world_snapshot.snapshot_all(session)
    world_state.log_action(
        session,
        actor="harness",
        sim_day=world_state.get_current_day(session),
        action_type="snapshot",
        payload={},
        result="ok",
    )
    return SnapshotOut(snapshot=snap)


@router.post("/restore", response_model=RestoreOut)
def do_restore(body: RestoreIn, session: Session = Depends(get_session)):
    """Harness-only: replace the entire live world with a previously
    captured snapshot (see GET /lab/snapshot), exactly — schema rebuilt
    from scratch, then every row reloaded. Unlike /lab/reset, this does
    not reseed from a scenario file; it restores whatever state the
    snapshot captured, including any post-Day-0 history."""
    world_snapshot.restore_all(session, body.snapshot)
    world_state.log_action(
        session,
        actor="harness",
        sim_day=world_state.get_current_day(session),
        action_type="restore",
        payload={},
        result="ok",
    )
    return RestoreOut(ok=True)
