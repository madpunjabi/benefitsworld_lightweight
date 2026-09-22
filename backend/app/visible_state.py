"""The only module allowed to translate world_state rows into agent-facing
view models. No public route may query models.py or session.query(...)
directly — every public response is built here, whitelisting fields
explicitly, so a lab-only field (simulator_tags, actually_persisted, etc.)
can never leak onto an agent-visible route by accident."""

import json

from sqlalchemy.orm import Session

from app import recertification, world_state


def portal_case_view(session: Session) -> dict:
    case = world_state.get_case(session)
    return {
        "case_id": case.case_id,
        "status": case.status,
        "open_requirements": json.loads(case.open_requirements_json),
        "reported_employer": case.reported_employer,
        "interview": world_state.get_interview(session),
        "recertification": recertification.get_view(session),
        # Canonical source of truth: uploads WHERE actually_persisted = 1.
        # No second, independently-stored "received documents" field exists
        # anywhere in the schema.
        "received_document_ids": world_state.get_received_document_ids(session),
    }


def portal_notices_view(session: Session) -> list[dict]:
    return [{"id": f"N-{n.id}", "day": n.day, "text": n.text} for n in world_state.get_notices(session)]


def interview_slots_view(session: Session) -> list[dict]:
    """Raw, unlabeled appointment options — no conflict flag, no "recommended"
    marker. The government scheduling surface doesn't know about Maya's
    household calendar; whether a slot conflicts is for the agent (or,
    for research purposes, a backend-only checkpoint helper) to work out."""
    return [
        {"id": s.id, "day": s.day, "start_time": s.start_time, "end_time": s.end_time}
        for s in world_state.get_interview_slots(session)
    ]


def inbox_messages_view(session: Session) -> list[dict]:
    return [
        {
            "id": m.id,
            "day": m.day,
            "sender": m.sender,
            "subject": m.subject,
            "body": m.body,
            "is_read": bool(m.is_read),
        }
        for m in world_state.get_inbox_messages(session)
    ]


def _document_dict(doc) -> dict:
    doc_type = doc.filename.rsplit(".", 1)[-1].upper() if "." in doc.filename else "FILE"
    return {
        "id": doc.id,
        "filename": doc.filename,
        "date": doc.doc_date,
        "type": doc_type,
        "visible_text": doc.visible_text,
    }


def files_view(session: Session) -> list[dict]:
    current_day = world_state.get_current_day(session)
    return [
        _document_dict(doc) for doc in world_state.get_documents(session) if doc.available_from_day <= current_day
    ]


def document_view(session: Session, document_id: str) -> dict | None:
    """Single-document lookup, gated by the same day-based availability as
    files_view — a not-yet-available document's id must 404 just like an
    unknown one, so its existence can't be discovered early by guessing."""
    doc = world_state.get_document(session, document_id)
    if doc is None or doc.available_from_day > world_state.get_current_day(session):
        return None
    return _document_dict(doc)


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


def _policy_item_dict(item) -> dict:
    # authority_level is deliberately excluded here: it's an internal
    # real-vs-synthetic-provenance marker for researchers/maintainers
    # (DATA_POLICY.md), not something a real county policy portal would
    # show a caseworker or applicant, and the literal string
    # "benchmark_synthetic_instruction" would tip off the benchmark agent
    # that it's inside a test environment.
    return {
        "id": item.id,
        "title": item.title,
        "source": item.source,
        "source_url": item.source_url,
        "jurisdiction": item.jurisdiction,
        "effective_date": item.effective_date,
        "source_version": item.source_version,
        "topic": item.topic,
        "text": item.text,
    }


def policy_items_view(session: Session, query: str | None = None) -> list[dict]:
    items = world_state.get_policy_items(session)
    if query:
        q = query.lower()
        items = [
            i
            for i in items
            if q in i.title.lower() or q in i.topic.lower() or q in i.text.lower()
        ]
    return [_policy_item_dict(i) for i in items]


def policy_item_view(session: Session, policy_id: str) -> dict | None:
    item = world_state.get_policy_item(session, policy_id)
    return _policy_item_dict(item) if item else None


def agent_status_view(session: Session) -> dict:
    case = world_state.get_case(session)
    return {
        "case_status": case.status,
        "open_requirements": json.loads(case.open_requirements_json),
    }
