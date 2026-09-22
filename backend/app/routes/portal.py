from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import visible_state, world_state
from app.db import get_session
from app.schemas.portal import CaseOut, NoticeOut, UploadIn, UploadOut

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
    # Milestone 2: every upload actually persists. The silent-failure
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
    return UploadOut(document_id=body.document_id, requirement=body.requirement, received=True)
