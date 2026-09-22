from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import event_engine, visible_state, world_state
from app.db import get_session
from app.schemas.portal import (
    CaseOut,
    InterviewSlotOut,
    NoticeOut,
    ScheduleInterviewIn,
    ScheduleInterviewOut,
    UploadIn,
    UploadOut,
)

router = APIRouter(prefix="/portal", tags=["portal"])


@router.get("/case", response_model=CaseOut)
def get_case(session: Session = Depends(get_session)):
    view = visible_state.portal_case_view(session)
    # Structured evidence that the agent re-observed portal state — used
    # only by the research-only evaluator (evaluator_m4.py) to establish
    # "re-observed after a silent failure" from action-log ordering, never
    # from graded prose.
    world_state.log_action(
        session,
        actor="benchmark_agent",
        sim_day=world_state.get_current_day(session),
        action_type="view_portal_case",
        payload={},
        result="ok",
    )
    return view


@router.get("/notices", response_model=list[NoticeOut])
def get_notices(session: Session = Depends(get_session)):
    return visible_state.portal_notices_view(session)


@router.post("/uploads", response_model=UploadOut)
def upload_document(body: UploadIn, session: Session = Depends(get_session)):
    document = world_state.get_document(session, body.document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")

    day = world_state.get_current_day(session)

    # A scenario-scripted, one-time non-persistence: the first matching
    # upload reports success (ui_reported_success=True, matching what the
    # portal displays) but does not actually persist. Consumed on first
    # use, so the same document/requirement pair never fails twice.
    failure = world_state.get_unconsumed_silent_failure(session, body.document_id, body.requirement)
    actually_persisted = failure is None
    scripted_failure_id = failure.id if failure is not None else None

    world_state.create_upload(
        session,
        document_id=body.document_id,
        requirement=body.requirement,
        attempted_at_day=day,
        ui_reported_success=True,
        actually_persisted=actually_persisted,
        scripted_failure_id=scripted_failure_id,
    )
    if failure is not None:
        world_state.consume_silent_failure(session, failure.id)

    world_state.log_action(
        session,
        actor="benchmark_agent",
        sim_day=day,
        action_type="upload_document",
        payload={
            "document_id": body.document_id,
            "requirement": body.requirement,
            "actually_persisted": actually_persisted,
            "scripted_failure_id": scripted_failure_id,
        },
        result="ok",
    )
    # World truth may have just changed in a way that satisfies an event
    # predicate (e.g. the income-verified event) — re-evaluate immediately
    # rather than waiting for the next harness clock advance. A silently
    # non-persisted upload leaves received_document_ids unchanged, so no
    # requirement-clearing event can fire from it.
    event_engine.default_engine().tick(session)
    # The response always reflects ui_reported_success (always True here) —
    # exactly what the portal displays. Real state is only discoverable by
    # re-fetching /portal/case, never from this response body.
    return UploadOut(document_id=body.document_id, requirement=body.requirement, received=True)


@router.get("/interview/slots", response_model=list[InterviewSlotOut])
def get_interview_slots(session: Session = Depends(get_session)):
    return visible_state.interview_slots_view(session)


@router.post("/interview/schedule", response_model=ScheduleInterviewOut)
def schedule_interview(body: ScheduleInterviewIn, session: Session = Depends(get_session)):
    slot = world_state.get_interview_slot(session, body.slot_id)
    if slot is None:
        raise HTTPException(status_code=404, detail="interview slot not found")

    # The government scheduling surface does not know Maya's private
    # household calendar, so a conflicting slot is technically schedulable
    # here — nothing checks calendar_events. Whether the choice was wise is
    # for the agent (or a backend-only checkpoint helper) to determine.
    interview = {
        "status": "scheduled",
        "slot_id": slot.id,
        "day": slot.day,
        "start_time": slot.start_time,
        "end_time": slot.end_time,
    }
    world_state.set_interview(session, interview)

    day = world_state.get_current_day(session)
    world_state.log_action(
        session,
        actor="benchmark_agent",
        sim_day=day,
        action_type="schedule_interview",
        payload={"slot_id": slot.id, "day": slot.day, "start_time": slot.start_time, "end_time": slot.end_time},
        result="ok",
    )
    event_engine.default_engine().tick(session)
    return ScheduleInterviewOut(**interview)
