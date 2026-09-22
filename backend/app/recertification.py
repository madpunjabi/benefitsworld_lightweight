"""Computed recertification status for scenarios that opt in (currently
only BW-002 — see scenario_loader.load_scenario's uses_recertification
seed flag). A case with no recertification record (case.recertification_json
is None, true for BW-001 always) has no recertification concept at all;
callers should check for that first via world_state.get_recertification_raw
being None-equivalent, or simply call get_view() which returns None itself
in that case.

Persisted (raw) fields, stored in Case.recertification_json:
  submitted_at_day: int | None    -- set only by submit()
  needs_update: bool              -- set true by an event when a material
                                      fact changes after a submission
  snapshot_applied_event_ids: list[str] -- which events had applied at the
                                      moment of the most recent submission;
                                      "which case facts/version the
                                      recertification represented"

Everything else (the displayed "status") is computed fresh from canonical
world state on every read, never stored — so it can never drift out of
sync with open_requirements."""

from sqlalchemy.orm import Session

from app import world_state

# Any of these being currently open blocks recertification from being
# submitted, whether that's the original Day-0 trio or a later
# consequence requirement opened after a submission (housing_correction,
# updated_income_verification).
GATING_REQUIREMENTS = {
    "income_verification",
    "housing_verification",
    "interview",
    "housing_correction",
    "updated_income_verification",
}


def _gating_open(session: Session) -> bool:
    open_requirements = set(world_state.get_open_requirements(session))
    return bool(open_requirements & GATING_REQUIREMENTS)


def get_view(session: Session) -> dict | None:
    raw = world_state.get_recertification_raw(session)
    if raw is None:
        return None
    if raw.get("needs_update"):
        status = "NEEDS_UPDATE"
    elif raw.get("submitted_at_day") is not None:
        status = "SUBMITTED"
    elif _gating_open(session):
        status = "NOT_READY"
    else:
        status = "READY"
    return {
        "status": status,
        "submitted_at_day": raw.get("submitted_at_day"),
        "snapshot_applied_event_ids": raw.get("snapshot_applied_event_ids", []),
    }


def mark_needs_update_if_submitted(session: Session) -> None:
    """Called by an event whose effect invalidates a prior recertification
    submission (a material fact changed). A no-op if recertification isn't
    in play for this scenario, or was never submitted, or is already
    marked."""
    raw = world_state.get_recertification_raw(session)
    if raw is None or raw.get("submitted_at_day") is None or raw.get("needs_update"):
        return
    raw["needs_update"] = True
    world_state.set_recertification_raw(session, raw)


class SubmitError(ValueError):
    pass


def submit(session: Session) -> dict:
    """Household/agent action: submit recertification now, if allowed.
    Raises SubmitError (never silently no-ops) when recertification isn't
    part of this scenario, or isn't currently submittable."""
    view = get_view(session)
    if view is None:
        raise SubmitError("recertification is not part of this scenario")
    if view["status"] not in ("READY", "NEEDS_UPDATE"):
        raise SubmitError(f"recertification cannot be submitted from status {view['status']}")
    if _gating_open(session):
        raise SubmitError("cannot submit recertification while requirements remain open")

    day = world_state.get_current_day(session)
    world_state.set_recertification_raw(
        session,
        {
            "submitted_at_day": day,
            "needs_update": False,
            "snapshot_applied_event_ids": world_state.get_applied_event_ids(session),
        },
    )
    world_state.log_action(
        session,
        actor="benchmark_agent",
        sim_day=day,
        action_type="submit_recertification",
        payload={},
        result="ok",
    )
    return get_view(session)
