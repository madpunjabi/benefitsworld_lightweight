"""Single place that picks which scenario's event engine / evaluator is
active, based on the currently-loaded world's own WorldStateMeta.scenario_id
(set by whichever scenario reset.reset()/scenario_loader last loaded — see
reset.py). Keeps event_engine.py (BW-001, frozen) and event_engine_bw002.py
completely decoupled from each other; every route/clock call site should go
through this module instead of calling either engine module directly."""

from sqlalchemy.orm import Session

from app import evaluator_bw002, evaluator_m4, event_engine, event_engine_bw002, world_state
from app.event_engine import EventEngine


def engine_for(session: Session) -> EventEngine:
    scenario_id = world_state.get_meta(session).scenario_id
    if scenario_id == "BW-002":
        return event_engine_bw002.bw002_engine()
    return event_engine.default_engine()


def evaluate(session: Session) -> dict:
    scenario_id = world_state.get_meta(session).scenario_id
    if scenario_id == "BW-002":
        return evaluator_bw002.evaluate(session)
    return evaluator_m4.evaluate(session)
