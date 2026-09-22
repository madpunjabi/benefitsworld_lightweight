from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import visible_state
from app.db import get_session
from app.schemas.inbox import InboxMessageOut

router = APIRouter(prefix="/inbox", tags=["inbox"])


@router.get("/messages", response_model=list[InboxMessageOut])
def get_messages(session: Session = Depends(get_session)):
    return visible_state.inbox_messages_view(session)
