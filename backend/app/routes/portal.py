from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import visible_state
from app.db import get_session
from app.schemas.portal import CaseOut, NoticeOut

router = APIRouter(prefix="/portal", tags=["portal"])


@router.get("/case", response_model=CaseOut)
def get_case(session: Session = Depends(get_session)):
    return visible_state.portal_case_view(session)


@router.get("/notices", response_model=list[NoticeOut])
def get_notices(session: Session = Depends(get_session)):
    return visible_state.portal_notices_view(session)
