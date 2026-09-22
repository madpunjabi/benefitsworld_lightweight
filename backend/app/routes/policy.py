from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import visible_state
from app.db import get_session
from app.schemas.policy import PolicyItemOut

router = APIRouter(prefix="/policy", tags=["policy"])


@router.get("/search", response_model=list[PolicyItemOut])
def search_policy(q: str | None = None, session: Session = Depends(get_session)):
    return visible_state.policy_items_view(session, query=q)
