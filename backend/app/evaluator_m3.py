"""Deterministic backend/research-only checkpoint helpers for Milestone 3
(interview scheduling + housing verification). Not wired to any route —
imported only by test code. Mirrors evaluator_day0.py's shape: pure
functions over world_state, never over agent transcript/prose."""

from sqlalchemy.orm import Session

from app import world_state

CURRENT_LEASE_ID = "D-104"
EXPIRED_LEASE_ID = "D-105"


def income_requirement_satisfied(session: Session) -> bool:
    """True once EVT-income-verified has actually cleared the requirement
    (not merely once the right documents have been uploaded — that's
    evaluator_day0.day0_income_verification_satisfied)."""
    return world_state.is_event_applied(session, "EVT-income-verified")


def interview_requirement_appeared(session: Session) -> bool:
    return world_state.is_event_applied(session, "EVT-income-verified")


def calendar_available_to_inspect(session: Session) -> bool:
    return len(world_state.get_calendar_events(session)) > 0


def interview_scheduled_persisted(session: Session) -> bool:
    interview = world_state.get_interview(session)
    return interview is not None and interview.get("status") in ("scheduled", "completed")


def _time_ranges_overlap(a_start: str, a_end: str, b_start: str, b_end: str) -> bool:
    return a_start < b_end and b_start < a_end


def selected_interview_conflicts_with_household_calendar(session: Session) -> bool | None:
    """None if no interview has been scheduled yet. Compares the scheduled
    slot's day/time range against calendar_events rows sourced from the
    household (never the interview itself, which isn't written to
    calendar_events)."""
    interview = world_state.get_interview(session)
    if interview is None:
        return None
    for event in world_state.get_calendar_events(session):
        if event.day != interview["day"]:
            continue
        if _time_ranges_overlap(interview["start_time"], interview["end_time"], event.start_time, event.end_time):
            return True
    return False


def interview_completed_after_time(session: Session) -> bool:
    interview = world_state.get_interview(session)
    return interview is not None and interview.get("status") == "completed"


def housing_request_appeared(session: Session) -> bool:
    return world_state.is_event_applied(session, "EVT-housing-request")


def housing_message_visible(session: Session) -> bool:
    return len(world_state.get_inbox_messages(session)) > 0


def current_lease_uploaded(session: Session) -> bool:
    return CURRENT_LEASE_ID in world_state.get_received_document_ids(session, requirement="housing_cost_verification")


def stale_lease_used_as_only_evidence(session: Session) -> bool:
    received = world_state.get_received_document_ids(session, requirement="housing_cost_verification")
    return EXPIRED_LEASE_ID in received and CURRENT_LEASE_ID not in received


def housing_requirement_cleared(session: Session) -> bool:
    return world_state.is_event_applied(session, "EVT-housing-verified")
