from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import visible_state
from app.db import get_session
from app.schemas.agent import AgentStatusOut

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/status", response_model=AgentStatusOut)
def get_status(session: Session = Depends(get_session)):
    return visible_state.agent_status_view(session)
