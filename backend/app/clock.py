from sqlalchemy.orm import Session

from app import event_engine, world_state


def advance_to(session: Session, to_day: int) -> dict:
    """Harness-only: advance the simulated clock to `to_day` and tick the
    event engine. There is no agent-facing equivalent of this function —
    only the lab router calls it, and only after require_lab_token."""
    if to_day < world_state.get_current_day(session):
        raise ValueError("cannot move simulated time backwards")

    world_state.set_current_sim_day(session, to_day)
    applied = event_engine.default_engine().tick(session)

    world_state.log_action(
        session,
        actor="harness",
        sim_day=to_day,
        action_type="advance_time",
        payload={"to_day": to_day, "events_applied": [e.id for e in applied]},
        result="ok",
    )
    return {"current_sim_day": to_day, "events_applied": [e.id for e in applied]}
