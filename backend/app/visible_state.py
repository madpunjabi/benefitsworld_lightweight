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
        "reported_employer": case.reported_employer,
        "interview": json.loads(case.interview_json) if case.interview_json else None,
        "recertification": json.loads(case.recertification_json) if case.recertification_json else None,
        # Canonical source of truth: uploads WHERE actually_persisted = 1.
        # No second, independently-stored "received documents" field exists
        # anywhere in the schema.
        "received_document_ids": world_state.get_received_document_ids(session),
    }


def portal_notices_view(session: Session) -> list[dict]:
    """Notices are derived from the case's own open_requirements — there is
    no separate notices table to keep in sync. A requirement key like
    "earned_income_verification" becomes a plain-language action item."""
    case = world_state.get_case(session)
    requirements = json.loads(case.open_requirements_json)
    return [
        {
            "id": f"notice-{requirement}",
            "text": (
                f"Action required: {requirement.replace('_', ' ').title()}. "
                "Please submit supporting documentation."
            ),
        }
        for requirement in requirements
    ]


def inbox_messages_view(session: Session) -> list[dict]:
    return []


def files_view(session: Session) -> list[dict]:
    docs = []
    for doc in world_state.get_documents(session):
        doc_type = doc.filename.rsplit(".", 1)[-1].upper() if "." in doc.filename else "FILE"
        docs.append(
            {
                "id": doc.id,
                "filename": doc.filename,
                "date": doc.doc_date,
                "type": doc_type,
                "visible_text": doc.visible_text,
            }
        )
    return docs


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
