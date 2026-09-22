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
    return visible_state.portal_case_view(session)


@router.get("/notices", response_model=list[NoticeOut])
def get_notices(session: Session = Depends(get_session)):
    return visible_state.portal_notices_view(session)


@router.post("/uploads", response_model=UploadOut)
def upload_document(body: UploadIn, session: Session = Depends(get_session)):
    document = world_state.get_document(session, body.document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")

    day = world_state.get_current_day(session)
    # Milestone 2/3: every upload actually persists. The silent-failure
    # mechanic (ui_reported_success=True, actually_persisted=False on the
    # first qualifying attempt) is introduced in Milestone 4.
    world_state.create_upload(
        session,
        document_id=body.document_id,
        requirement=body.requirement,
        attempted_at_day=day,
        ui_reported_success=True,
        actually_persisted=True,
    )
    world_state.log_action(
        session,
        actor="benchmark_agent",
        sim_day=day,
        action_type="upload_document",
        payload={"document_id": body.document_id, "requirement": body.requirement},
        result="ok",
    )
    # World truth may have just changed in a way that satisfies an event
    # predicate (e.g. the income-verified event) — re-evaluate immediately
    # rather than waiting for the next harness clock advance.
    event_engine.default_engine().tick(session)
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
