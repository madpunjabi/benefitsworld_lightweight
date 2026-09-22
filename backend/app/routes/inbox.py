from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import visible_state, world_state
from app.db import get_session
from app.schemas.inbox import InboxMessageOut

router = APIRouter(prefix="/inbox", tags=["inbox"])


@router.get("/messages", response_model=list[InboxMessageOut])
def get_messages(session: Session = Depends(get_session)):
    return visible_state.inbox_messages_view(session)


@router.post("/messages/{message_id}/read", response_model=InboxMessageOut)
def mark_message_read(message_id: int, session: Session = Depends(get_session)):
    message = world_state.get_inbox_message(session, message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="message not found")
    world_state.mark_inbox_message_read(session, message_id)
    day = world_state.get_current_day(session)
    world_state.log_action(
        session,
        actor="benchmark_agent",
        sim_day=day,
        action_type="read_inbox_message",
        payload={"message_id": message_id},
        result="ok",
    )
    updated = world_state.get_inbox_message(session, message_id)
    return {
        "id": updated.id,
        "day": updated.day,
        "sender": updated.sender,
        "subject": updated.subject,
        "body": updated.body,
        "is_read": bool(updated.is_read),
    }
