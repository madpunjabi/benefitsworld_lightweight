from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import visible_state
from app.db import get_session
from app.schemas.calendar import CalendarEventOut

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/events", response_model=list[CalendarEventOut])
def get_events(session: Session = Depends(get_session)):
    return visible_state.calendar_events_view(session)
