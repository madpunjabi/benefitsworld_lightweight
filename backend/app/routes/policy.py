from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import visible_state
from app.db import get_session
from app.schemas.policy import PolicyItemOut

router = APIRouter(prefix="/policy", tags=["policy"])


@router.get("/search", response_model=list[PolicyItemOut])
def search_policy(q: str | None = None, session: Session = Depends(get_session)):
    return visible_state.policy_items_view(session, query=q)


@router.get("/{policy_id}", response_model=PolicyItemOut)
def get_policy_item(policy_id: str, session: Session = Depends(get_session)):
    item = visible_state.policy_item_view(session, policy_id)
    if item is None:
        raise HTTPException(status_code=404, detail="policy item not found")
    return item
