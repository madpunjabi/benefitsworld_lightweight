"""The only module allowed to translate world_state rows into agent-facing
view models. No public route may query models.py or session.query(...)
directly — every public response is built here, whitelisting fields
explicitly, so a lab-only field (simulator_tags, actually_persisted, etc.)
can never leak onto an agent-visible route by accident."""

import json

from sqlalchemy.orm import Session

from app import world_state


def portal_case_view(session: Session) -> dict:
    case = world_state.get_case(session)
    return {
        "case_id": case.case_id,
        "status": case.status,
        "open_requirements": json.loads(case.open_requirements_json),
        "interview": json.loads(case.interview_json) if case.interview_json else None,
        "recertification": json.loads(case.recertification_json) if case.recertification_json else None,
        # Milestone 2+ derives this from `uploads WHERE actually_persisted = 1`;
        # the uploads table doesn't exist yet in milestone 1, so this is
        # always empty for now rather than backed by any placeholder field.
        "received_document_ids": [],
    }


def portal_notices_view(session: Session) -> list[dict]:
    return []


def inbox_messages_view(session: Session) -> list[dict]:
    return []


def files_view(session: Session) -> list[dict]:
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "date": doc.doc_date,
            "visible_text": doc.visible_text,
        }
        for doc in world_state.get_documents(session)
    ]


def calendar_events_view(session: Session) -> list[dict]:
    return [
        {
            "day": e.day,
            "start_time": e.start_time,
            "end_time": e.end_time,
            "label": e.label,
        }
        for e in world_state.get_calendar_events(session)
    ]


def policy_items_view(session: Session, query: str | None = None) -> list[dict]:
    return []


def agent_status_view(session: Session) -> dict:
    case = world_state.get_case(session)
    return {
        "case_status": case.status,
        "open_requirements": json.loads(case.open_requirements_json),
    }
