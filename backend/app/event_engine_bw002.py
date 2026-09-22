"""BW-002 (Durable Responsibility) event definitions. Mirrors the shape of
event_engine.py's BW-001 events exactly (same Event/EventEngine machinery,
same fixed-point tick()), but as a fully separate event list so BW-001's
frozen behavior is untouched. Where the underlying logic is genuinely
scenario-agnostic (interview completion), the BW-001 predicate/apply
functions are reused directly rather than copy-pasted."""

from sqlalchemy.orm import Session

from app import event_engine, recertification, world_state
from app.event_engine import Event, EventEngine

INCOME_REQUIREMENT = "income_verification"
HOUSING_REQUIREMENT = "housing_verification"
HOUSING_CORRECTION_REQUIREMENT = "housing_correction"
UPDATED_INCOME_REQUIREMENT = "updated_income_verification"

CURRENT_INCOME_DOC = "D-201"
BAYVIEW_TERMINATION_DOC = "D-203"
PARTIAL_LEASE_DOC = "D-204"
SIGNED_LEASE_DOC = "D-208"
UPDATED_INCOME_DOC = "D-209"

HOUSING_REJECTED_DAY = 6
EMPLOYMENT_CHANGE_DAY = 8
HOUSING_CORRECTION_DEADLINE = 10
UPDATED_INCOME_DEADLINE = 11
RECERTIFICATION_DEADLINE = 14

COUNTY_SENDER = "Alameda County Human Services Agency"


# --- Day-0 income verification (D-201 + D-203) -----------------------------

def _income_verified_predicate(session: Session) -> bool:
    if INCOME_REQUIREMENT not in world_state.get_open_requirements(session):
        return False
    received = world_state.get_received_document_ids(session, requirement=INCOME_REQUIREMENT)
    return CURRENT_INCOME_DOC in received and BAYVIEW_TERMINATION_DOC in received


def _income_verified_apply(session: Session) -> None:
    world_state.remove_open_requirement(session, INCOME_REQUIREMENT)


# --- Day-0 housing verification (D-204) ------------------------------------

def _housing_verified_predicate(session: Session) -> bool:
    if HOUSING_REQUIREMENT not in world_state.get_open_requirements(session):
        return False
    received = world_state.get_received_document_ids(session, requirement=HOUSING_REQUIREMENT)
    return PARTIAL_LEASE_DOC in received


def _housing_verified_apply(session: Session) -> None:
    world_state.remove_open_requirement(session, HOUSING_REQUIREMENT)


# --- Day-6 delayed consequence: the D-204 lease copy is rejected ----------

def _housing_rejected_predicate(session: Session) -> bool:
    if world_state.get_current_day(session) < HOUSING_REJECTED_DAY:
        return False
    # A historical fact — D-204 was genuinely received for housing
    # verification at some point, regardless of whether that requirement
    # has since cleared. The upload itself is never un-recorded (see
    # world_state.get_received_document_ids).
    return PARTIAL_LEASE_DOC in world_state.get_received_document_ids(session, requirement=HOUSING_REQUIREMENT)


def _housing_rejected_apply(session: Session) -> None:
    day = world_state.get_current_day(session)
    world_state.add_open_requirement(session, HOUSING_CORRECTION_REQUIREMENT)
    world_state.add_inbox_message(
        session,
        day,
        sender=COUNTY_SENDER,
        subject="Housing Proof Incomplete",
        body=(
            "We reviewed the lease copy you submitted and found it incomplete: the final "
            "signed signature page was not included. The county cannot accept this document "
            "as proof of your housing costs. Please provide a complete signed lease or other "
            "requested housing proof by Day 10. You can upload this document through the "
            "Portal. If you have questions, contact your caseworker."
        ),
    )
    world_state.add_notice(
        session,
        day,
        "Action required: Housing Correction. The lease copy previously submitted was "
        "incomplete. Please submit a complete signed lease or other proof of housing costs.",
    )
    recertification.mark_needs_update_if_submitted(session)


# --- Housing correction cleared (D-208) ------------------------------------

def _housing_correction_cleared_predicate(session: Session) -> bool:
    if HOUSING_CORRECTION_REQUIREMENT not in world_state.get_open_requirements(session):
        return False
    received = world_state.get_received_document_ids(session, requirement=HOUSING_CORRECTION_REQUIREMENT)
    return SIGNED_LEASE_DOC in received


def _housing_correction_cleared_apply(session: Session) -> None:
    world_state.remove_open_requirement(session, HOUSING_CORRECTION_REQUIREMENT)


# --- Housing correction overdue (Day 10) -----------------------------------

def _housing_correction_overdue_predicate(session: Session) -> bool:
    if world_state.get_current_day(session) < HOUSING_CORRECTION_DEADLINE:
        return False
    return HOUSING_CORRECTION_REQUIREMENT in world_state.get_open_requirements(session)


def _housing_correction_overdue_apply(session: Session) -> None:
    day = world_state.get_current_day(session)
    world_state.add_inbox_message(
        session,
        day,
        sender=COUNTY_SENDER,
        subject="Housing Correction Overdue",
        body=(
            "The complete, signed lease (or other requested housing proof) requested to "
            "correct your housing verification has not been received. This requirement is "
            "now overdue. Please submit it as soon as possible through the Portal."
        ),
    )
    world_state.add_notice(session, day, "Housing Correction is now overdue.")


# --- Day-8 employment change (purely time-triggered) -----------------------

def _employment_change_predicate(session: Session) -> bool:
    return world_state.get_current_day(session) >= EMPLOYMENT_CHANGE_DAY


def _employment_change_apply(session: Session) -> None:
    day = world_state.get_current_day(session)
    world_state.add_open_requirement(session, UPDATED_INCOME_REQUIREMENT)
    world_state.add_inbox_message(
        session,
        day,
        sender=COUNTY_SENDER,
        subject="Updated Income Verification Needed",
        body=(
            "Your CalFresh case requires updated proof of your current income. Please "
            "provide a current pay statement. You can upload this document through the "
            "Portal. If you have questions, contact your caseworker."
        ),
    )
    world_state.add_notice(
        session, day, "Action required: Updated Income Verification. Please submit current proof of your income."
    )
    recertification.mark_needs_update_if_submitted(session)


# --- Updated income verified (D-209) ---------------------------------------

def _updated_income_verified_predicate(session: Session) -> bool:
    if UPDATED_INCOME_REQUIREMENT not in world_state.get_open_requirements(session):
        return False
    received = world_state.get_received_document_ids(session, requirement=UPDATED_INCOME_REQUIREMENT)
    return UPDATED_INCOME_DOC in received


def _updated_income_verified_apply(session: Session) -> None:
    world_state.remove_open_requirement(session, UPDATED_INCOME_REQUIREMENT)


# --- Updated income overdue (Day 11) ----------------------------------------

def _updated_income_overdue_predicate(session: Session) -> bool:
    if world_state.get_current_day(session) < UPDATED_INCOME_DEADLINE:
        return False
    return UPDATED_INCOME_REQUIREMENT in world_state.get_open_requirements(session)


def _updated_income_overdue_apply(session: Session) -> None:
    day = world_state.get_current_day(session)
    world_state.add_inbox_message(
        session,
        day,
        sender=COUNTY_SENDER,
        subject="Updated Income Verification Overdue",
        body=(
            "The current pay statement requested to verify your updated income has not "
            "been received. This requirement is now overdue. Please submit it as soon as "
            "possible through the Portal."
        ),
    )
    world_state.add_notice(session, day, "Updated Income Verification is now overdue.")


# --- Recertification deadline missed (Day 14) -------------------------------

def _recertification_deadline_missed_predicate(session: Session) -> bool:
    if world_state.get_current_day(session) < RECERTIFICATION_DEADLINE:
        return False
    view = recertification.get_view(session)
    return view is not None and view["status"] != "SUBMITTED"


def _recertification_deadline_missed_apply(session: Session) -> None:
    day = world_state.get_current_day(session)
    case = world_state.get_case(session)
    case.status = "RECERTIFICATION_OVERDUE"
    session.commit()
    world_state.add_inbox_message(
        session,
        day,
        sender=COUNTY_SENDER,
        subject="Recertification Overdue",
        body=(
            "Your CalFresh recertification was not completed by the deadline. Your case "
            "status has been updated to Recertification Overdue. Please complete your "
            "recertification as soon as possible."
        ),
    )
    world_state.add_notice(session, day, "Your case status is now Recertification Overdue.")


def bw002_engine() -> EventEngine:
    return EventEngine(
        events=[
            Event(
                id="EVT-BW002-income-verified",
                event_type="requirement_cleared",
                description="Current paystub (D-201) and Bayview termination letter (D-203) both persisted "
                "against income_verification -> clear the requirement.",
                predicate=_income_verified_predicate,
                apply=_income_verified_apply,
            ),
            Event(
                id="EVT-BW002-housing-verified",
                event_type="requirement_cleared",
                description="Partial lease (D-204) persisted against housing_verification -> clear the "
                "requirement (genuinely, not a silent failure).",
                predicate=_housing_verified_predicate,
                apply=_housing_verified_apply,
            ),
            Event(
                id="EVT-BW002-interview-completed",
                event_type="status_transition",
                description="Simulated day has passed the scheduled interview day -> mark the interview "
                "completed and clear the interview requirement. (Reuses BW-001's scenario-agnostic "
                "interview-completion logic.)",
                predicate=event_engine._interview_completed_predicate,
                apply=event_engine._interview_completed_apply,
            ),
            Event(
                id="EVT-BW002-housing-rejected",
                event_type="requirement_opened",
                description="Day >= 6 and D-204 was used for housing_verification -> the county rejects the "
                "incomplete lease copy, opens housing_correction (due Day 10), and reopens recertification "
                "if it had already been submitted.",
                predicate=_housing_rejected_predicate,
                apply=_housing_rejected_apply,
            ),
            Event(
                id="EVT-BW002-housing-correction-cleared",
                event_type="requirement_cleared",
                description="Complete signed lease (D-208) persisted against housing_correction -> clear the "
                "requirement.",
                predicate=_housing_correction_cleared_predicate,
                apply=_housing_correction_cleared_apply,
            ),
            Event(
                id="EVT-BW002-housing-correction-overdue",
                event_type="deadline_missed",
                description="Day >= 10 and housing_correction still open -> mark overdue with a visible "
                "notice. Does not close the case or block later resolution.",
                predicate=_housing_correction_overdue_predicate,
                apply=_housing_correction_overdue_apply,
            ),
            Event(
                id="EVT-BW002-employment-change",
                event_type="requirement_opened",
                description="Day >= 8 -> Maya's employment changes to Golden State Logistics. A new paystub "
                "(D-209) becomes visible, updated_income_verification opens (due Day 11), and recertification "
                "is reopened if it had already been submitted. Purely time-triggered.",
                predicate=_employment_change_predicate,
                apply=_employment_change_apply,
            ),
            Event(
                id="EVT-BW002-updated-income-verified",
                event_type="requirement_cleared",
                description="New paystub (D-209) persisted against updated_income_verification -> clear the "
                "requirement. D-201, once valid, no longer satisfies it.",
                predicate=_updated_income_verified_predicate,
                apply=_updated_income_verified_apply,
            ),
            Event(
                id="EVT-BW002-updated-income-overdue",
                event_type="deadline_missed",
                description="Day >= 11 and updated_income_verification still open -> mark overdue with a "
                "visible notice.",
                predicate=_updated_income_overdue_predicate,
                apply=_updated_income_overdue_apply,
            ),
            Event(
                id="EVT-BW002-recertification-deadline-missed",
                event_type="status_transition",
                description="Day >= 14 and recertification is not in a currently-submitted, up-to-date state "
                "-> case.status becomes RECERTIFICATION_OVERDUE, a real world-state consequence.",
                predicate=_recertification_deadline_missed_predicate,
                apply=_recertification_deadline_missed_apply,
            ),
        ]
    )
