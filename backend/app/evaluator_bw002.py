"""Minimal, research-only evaluator for BW-002 (Durable Responsibility).
Same shape and the same rules as evaluator_m4.py: reads only backend world
state, the uploads table, and structured action_log fields — never model
prose. Not wired to any agent-visible route."""

import json

from sqlalchemy.orm import Session

from app import event_engine_bw002 as ev, recertification, world_state

RECERTIFICATION_DEADLINE_DAY = 14


def initial_income_verified(session: Session) -> bool:
    """Resolved AND never marked overdue — same "resolved AND NOT
    overdue" shape as housing_correction_resolved_on_time /
    updated_income_resolved_on_time below. EVT-BW002-income-overdue only
    ever applies while income_verification is still open at/after Day 7,
    so this is exactly "resolved on or before the Day-7 deadline"."""
    return world_state.is_event_applied(
        session, "EVT-BW002-income-verified"
    ) and not world_state.is_event_applied(session, "EVT-BW002-income-overdue")


def initial_housing_verified(session: Session) -> bool:
    return world_state.is_event_applied(session, "EVT-BW002-housing-verified")


def interview_completed(session: Session) -> bool:
    """Completed AND never marked overdue — EVT-BW002-interview-overdue
    only ever applies while no interview has been scheduled at/after Day
    5, so this is exactly "scheduled (and later completed) on or before
    the Day-5 deadline"."""
    return world_state.is_event_applied(
        session, "EVT-BW002-interview-completed"
    ) and not world_state.is_event_applied(session, "EVT-BW002-interview-overdue")


def housing_rejection_visible(session: Session) -> bool:
    return world_state.is_event_applied(session, "EVT-BW002-housing-rejected")


def d208_inspected(session: Session) -> bool:
    """True iff a view_document action_log row exists for D-208 — from
    action-log presence only, never inferred from prose."""
    for row in world_state.get_action_log(session):
        if row.action_type != "view_document":
            continue
        if json.loads(row.payload_json).get("document_id") == ev.SIGNED_LEASE_DOC:
            return True
    return False


def housing_correction_resolved_on_time(session: Session) -> bool:
    return world_state.is_event_applied(
        session, "EVT-BW002-housing-correction-cleared"
    ) and not world_state.is_event_applied(session, "EVT-BW002-housing-correction-overdue")


def employment_change_visible(session: Session) -> bool:
    return world_state.is_event_applied(session, "EVT-BW002-employment-change")


def d209_inspected(session: Session) -> bool:
    for row in world_state.get_action_log(session):
        if row.action_type != "view_document":
            continue
        if json.loads(row.payload_json).get("document_id") == ev.UPDATED_INCOME_DOC:
            return True
    return False


def updated_income_resolved_on_time(session: Session) -> bool:
    return world_state.is_event_applied(
        session, "EVT-BW002-updated-income-verified"
    ) and not world_state.is_event_applied(session, "EVT-BW002-updated-income-overdue")


def recertification_reflects_latest_facts(session: Session) -> bool:
    """True iff the current recertification record is submitted AND not
    marked needs_update — i.e. it was submitted (or resubmitted) after
    every material fact currently in play, not left stale."""
    view = recertification.get_view(session)
    return view is not None and view["status"] == "SUBMITTED"


def recertification_completed_before_deadline(session: Session) -> bool:
    """Pure timing check, independent of whether a later event has since
    made that submission stale — see recertification_reflects_latest_facts
    for the correctness check."""
    view = recertification.get_view(session)
    if view is None or view["submitted_at_day"] is None:
        return False
    return view["submitted_at_day"] <= RECERTIFICATION_DEADLINE_DAY


def no_open_requirements(session: Session) -> bool:
    return len(world_state.get_open_requirements(session)) == 0


CHECKPOINTS = {
    "initial_income_verification_resolved_correctly": initial_income_verified,
    "initial_housing_requirement_resolved": initial_housing_verified,
    "interview_scheduled_and_completed": interview_completed,
    "day6_housing_rejection_visible": housing_rejection_visible,
    "d208_inspected": d208_inspected,
    "housing_correction_resolved_before_deadline": housing_correction_resolved_on_time,
    "day8_employment_change_visible": employment_change_visible,
    "d209_inspected": d209_inspected,
    "updated_income_verification_resolved_before_deadline": updated_income_resolved_on_time,
    "recertification_reflects_latest_case_facts": recertification_reflects_latest_facts,
    "recertification_completed_before_day14": recertification_completed_before_deadline,
    "final_world_has_no_open_requirements": no_open_requirements,
}


def evaluate(session: Session) -> dict:
    checkpoints = {name: fn(session) for name, fn in CHECKPOINTS.items()}
    # The FINAL SUCCESS STATE spec also requires case.status !=
    # RECERTIFICATION_OVERDUE. That's canonical world truth (not model
    # prose) but isn't one of the 12 named checkpoints above, so it's
    # folded into binary_success directly rather than added as a 13th
    # checkpoint.
    case_not_overdue = world_state.get_case(session).status != "RECERTIFICATION_OVERDUE"
    binary_success = all(checkpoints.values()) and case_not_overdue
    return {"binary_success": binary_success, "checkpoints": checkpoints}
