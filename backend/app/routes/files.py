from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import visible_state, world_state
from app.db import get_session
from app.schemas.files import DocumentOut

router = APIRouter(prefix="/files", tags=["files"])


@router.get("", response_model=list[DocumentOut])
def get_files(session: Session = Depends(get_session)):
    return visible_state.files_view(session)


@router.get("/{document_id}", response_model=DocumentOut)
def get_file(document_id: str, session: Session = Depends(get_session)):
    doc = visible_state.document_view(session, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")
    # Structured evidence that a specific document was opened — used only
    # by the research-only evaluator (e.g. "D-107 was inspected"), never
    # from inferring that the agent "understood" anything from prose.
    world_state.log_action(
        session,
        actor="benchmark_agent",
        sim_day=world_state.get_current_day(session),
        action_type="view_document",
        payload={"document_id": document_id},
        result="ok",
    )
    return doc
