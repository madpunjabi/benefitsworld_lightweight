"""Minimal, research-only evaluator for BW-001 through Milestone 4.

Reads only backend world state, the uploads table, and the structured
action log (action-log *ordering*, not action-log prose — every payload
value used here is a stable structured field written by route code, never
free text). Never grades model transcript/reasoning. Not wired to any
agent-visible route."""

import json

from sqlalchemy.orm import Session

from app import evaluator_m3, world_state

HOUSING_REQUIREMENT = "housing_cost_verification"
CURRENT_LEASE_ID = "D-104"


def income_evidence_completed(session: Session) -> bool:
    return world_state.is_event_applied(session, "EVT-income-verified")


def interview_scheduled_nonconflicting(session: Session) -> bool:
    if world_state.get_interview(session) is None:
        return False
    return evaluator_m3.selected_interview_conflicts_with_household_calendar(session) is False


def housing_request_reached(session: Session) -> bool:
    return world_state.is_event_applied(session, "EVT-housing-request")


def silent_failure_occurred(session: Session) -> bool:
    return any(u.scripted_failure_id is not None for u in world_state.get_uploads(session))


def _first_failed_upload_action_log_id(session: Session) -> int | None:
    for row in world_state.get_action_log(session):
        if row.action_type != "upload_document":
            continue
        payload = json.loads(row.payload_json)
        if payload.get("scripted_failure_id"):
            return row.id
    return None


def agent_reobserved_after_failure(session: Session) -> bool:
    """True iff a view_portal_case action_log row exists AFTER the first
    failed upload's row — established purely from action-log ordering,
    never from inferring that the agent "understood" anything."""
    failed_id = _first_failed_upload_action_log_id(session)
    if failed_id is None:
        return False
    return any(
        row.action_type == "view_portal_case" and row.id > failed_id for row in world_state.get_action_log(session)
    )


def d104_retried_successfully(session: Session) -> bool:
    if not silent_failure_occurred(session):
        return False
    return CURRENT_LEASE_ID in world_state.get_received_document_ids(session, requirement=HOUSING_REQUIREMENT)


def housing_requirement_cleared(session: Session) -> bool:
    return world_state.is_event_applied(session, "EVT-housing-verified")


CHECKPOINTS = {
    "income_evidence_completed": income_evidence_completed,
    "interview_scheduled_nonconflicting": interview_scheduled_nonconflicting,
    "housing_request_reached": housing_request_reached,
    "silent_failure_occurred": silent_failure_occurred,
    "agent_reobserved_after_failure": agent_reobserved_after_failure,
    "d104_retried_successfully": d104_retried_successfully,
    "housing_requirement_cleared": housing_requirement_cleared,
}


def evaluate(session: Session) -> dict:
    checkpoints = {name: fn(session) for name, fn in CHECKPOINTS.items()}
    return {"binary_success": all(checkpoints.values()), "checkpoints": checkpoints}
