from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import visible_state
from app.db import get_session
from app.schemas.files import DocumentOut

router = APIRouter(prefix="/files", tags=["files"])


@router.get("", response_model=list[DocumentOut])
def get_files(session: Session = Depends(get_session)):
    return visible_state.files_view(session)
