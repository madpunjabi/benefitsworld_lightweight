from dataclasses import dataclass
from typing import Callable

from sqlalchemy.orm import Session

from app import world_state


@dataclass
class Event:
    id: str
    event_type: str
    description: str
    predicate: Callable[[Session], bool]
    apply: Callable[[Session], None]


class EventEngine:
    """Deterministic, idempotent event application. No workflow framework:
    events are evaluated in list order, applied at most once each (guarded
    by the persisted `events` table, so applied state survives a process
    restart), and re-scanned in a fixed-point loop so a chain of events
    (e.g. income-verified -> ... -> interview-completed -> housing-request)
    resolves fully within a single tick() call, deterministically."""

    def __init__(self, events: list[Event]):
        self.events = events

    def tick(self, session: Session) -> list[Event]:
        applied_this_tick: list[Event] = []
        while True:
            progressed = False
            for event in self.events:
                if world_state.is_event_applied(session, event.id):
                    continue
                if event.predicate(session):
                    day = world_state.get_current_day(session)
                    event.apply(session)
                    world_state.mark_event_applied(session, event.id, event.event_type, event.description, day)
                    world_state.log_action(
                        session,
                        actor="system",
                        sim_day=day,
                        action_type="event_applied",
                        payload={"event_id": event.id},
                        result="ok",
                    )
                    applied_this_tick.append(event)
                    progressed = True
            if not progressed:
                break
        return applied_this_tick


# --- BW-001 event definitions --------------------------------------------

INTERVIEW_SLOTS = [
    {"id": "SLOT-1", "day": 2, "start_time": "09:00", "end_time": "10:00"},
    {"id": "SLOT-2", "day": 3, "start_time": "10:30", "end_time": "11:30"},  # overlaps the Day-3 pediatric appointment
    {"id": "SLOT-3", "day": 3, "start_time": "13:30", "end_time": "14:30"},
]


def _income_verified_predicate(session: Session) -> bool:
    if "earned_income_verification" not in world_state.get_open_requirements(session):
        return False
    received = world_state.get_received_document_ids(session, requirement="earned_income_verification")
    return "D-101" in received and "D-103" in received


def _income_verified_apply(session: Session) -> None:
    world_state.remove_open_requirement(session, "earned_income_verification")
    world_state.add_open_requirement(session, "interview")
    world_state.add_notice(
        session,
        world_state.get_current_day(session),
        "An interview is required for your CalFresh case. Please schedule an appointment through the portal.",
    )
    world_state.add_interview_slots(session, INTERVIEW_SLOTS)


def _interview_completed_predicate(session: Session) -> bool:
    interview = world_state.get_interview(session)
    if interview is None or interview.get("status") != "scheduled":
        return False
    return world_state.get_current_day(session) > interview["day"]


def _interview_completed_apply(session: Session) -> None:
    interview = world_state.get_interview(session)
    interview["status"] = "completed"
    world_state.set_interview(session, interview)
    world_state.remove_open_requirement(session, "interview")


def _housing_request_predicate(session: Session) -> bool:
    interview = world_state.get_interview(session)
    if interview is None or interview.get("status") != "completed":
        return False
    return "housing_cost_verification" not in world_state.get_open_requirements(session)


def _housing_request_apply(session: Session) -> None:
    day = world_state.get_current_day(session)
    world_state.add_open_requirement(session, "housing_cost_verification")
    world_state.add_inbox_message(
        session,
        day,
        sender="Alameda County Human Services Agency",
        subject="Proof of Housing Costs Needed",
        body=(
            "Your CalFresh case requires updated proof of your housing costs. "
            "Please provide a current lease or rental agreement showing your "
            "monthly rent. You can upload this document through the Portal. "
            "If you have questions, contact your caseworker."
        ),
    )
    world_state.add_notice(
        session, day, "Action required: Housing Cost Verification. Please submit current proof of your housing costs."
    )


def _housing_verified_predicate(session: Session) -> bool:
    if "housing_cost_verification" not in world_state.get_open_requirements(session):
        return False
    received = world_state.get_received_document_ids(session, requirement="housing_cost_verification")
    return "D-104" in received


def _housing_verified_apply(session: Session) -> None:
    world_state.remove_open_requirement(session, "housing_cost_verification")


DAY18_EMPLOYMENT_CHANGE_DAY = 18


def _employment_change_predicate(session: Session) -> bool:
    return world_state.get_current_day(session) >= DAY18_EMPLOYMENT_CHANGE_DAY


def _employment_change_apply(session: Session) -> None:
    day = world_state.get_current_day(session)
    world_state.add_open_requirement(session, "updated_income_verification")
    world_state.add_inbox_message(
        session,
        day,
        sender="Alameda County Human Services Agency",
        subject="Updated Income Verification Needed",
        body=(
            "Your CalFresh case requires updated proof of your current income. "
            "Please provide a current pay statement. You can upload this "
            "document through the Portal. If you have questions, contact "
            "your caseworker."
        ),
    )
    world_state.add_notice(
        session, day, "Action required: Updated Income Verification. Please submit current proof of your income."
    )


def _updated_income_verified_predicate(session: Session) -> bool:
    if "updated_income_verification" not in world_state.get_open_requirements(session):
        return False
    received = world_state.get_received_document_ids(session, requirement="updated_income_verification")
    return "D-107" in received


def _updated_income_verified_apply(session: Session) -> None:
    world_state.remove_open_requirement(session, "updated_income_verification")


def default_engine() -> EventEngine:
    return EventEngine(
        events=[
            Event(
                id="EVT-income-verified",
                event_type="requirement_cleared",
                description=(
                    "Current paystub (D-101) and termination letter (D-103) both persisted against "
                    "earned_income_verification -> clear the requirement, open an interview requirement, "
                    "notify the household, and make appointment slots available."
                ),
                predicate=_income_verified_predicate,
                apply=_income_verified_apply,
            ),
            Event(
                id="EVT-interview-completed",
                event_type="status_transition",
                description=(
                    "Simulated day has passed the scheduled interview day -> mark the interview completed "
                    "and clear the interview requirement."
                ),
                predicate=_interview_completed_predicate,
                apply=_interview_completed_apply,
            ),
            Event(
                id="EVT-housing-request",
                event_type="requirement_opened",
                description=(
                    "Interview completed -> open a housing_cost_verification requirement and notify the "
                    "household via inbox and portal notice."
                ),
                predicate=_housing_request_predicate,
                apply=_housing_request_apply,
            ),
            Event(
                id="EVT-housing-verified",
                event_type="requirement_cleared",
                description="Current lease (D-104) persisted against housing_cost_verification -> clear the requirement.",
                predicate=_housing_verified_predicate,
                apply=_housing_verified_apply,
            ),
            Event(
                id="EVT-employment-change",
                event_type="requirement_opened",
                description=(
                    "Simulated day reaches 18 -> Maya's income changes. A new current paystub "
                    "(D-107) becomes visible in Files, and an updated_income_verification "
                    "requirement opens with an inbox message and portal notice. Purely "
                    "time-triggered; does not depend on earlier requirements being resolved."
                ),
                predicate=_employment_change_predicate,
                apply=_employment_change_apply,
            ),
            Event(
                id="EVT-updated-income-verified",
                event_type="requirement_cleared",
                description=(
                    "New paystub (D-107) persisted against updated_income_verification -> clear "
                    "the requirement. D-101, once valid, no longer satisfies it."
                ),
                predicate=_updated_income_verified_predicate,
                apply=_updated_income_verified_apply,
            ),
        ]
    )
