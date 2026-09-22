import json

from sqlalchemy.orm import Session

from app import models


def get_meta(session: Session) -> models.WorldStateMeta:
    return session.get(models.WorldStateMeta, 1)


def get_household(session: Session) -> models.Household:
    return session.get(models.Household, 1)


def get_case(session: Session) -> models.Case:
    return session.get(models.Case, 1)


def get_documents(session: Session) -> list[models.Document]:
    return session.query(models.Document).order_by(models.Document.id).all()


def get_document(session: Session, document_id: str) -> models.Document | None:
    return session.get(models.Document, document_id)


def get_policy_items(session: Session) -> list[models.PolicyItem]:
    return session.query(models.PolicyItem).order_by(models.PolicyItem.id).all()


def get_policy_item(session: Session, policy_id: str) -> models.PolicyItem | None:
    return session.get(models.PolicyItem, policy_id)


def get_calendar_events(session: Session) -> list[models.CalendarEvent]:
    return session.query(models.CalendarEvent).order_by(models.CalendarEvent.id).all()


def create_upload(
    session: Session,
    document_id: str,
    requirement: str,
    attempted_at_day: int,
    ui_reported_success: bool,
    actually_persisted: bool,
    scripted_failure_id: str | None = None,
) -> models.Upload:
    upload = models.Upload(
        document_id=document_id,
        requirement=requirement,
        attempted_at_day=attempted_at_day,
        ui_reported_success=1 if ui_reported_success else 0,
        actually_persisted=1 if actually_persisted else 0,
        scripted_failure_id=scripted_failure_id,
    )
    session.add(upload)
    session.commit()
    return upload


def get_uploads(session: Session) -> list[models.Upload]:
    return session.query(models.Upload).order_by(models.Upload.id).all()


def get_received_document_ids(session: Session, requirement: str | None = None) -> list[str]:
    """The single source of truth for 'what has been received': every
    document_id with at least one persisted (actually_persisted=1) upload,
    optionally scoped to one requirement. No other table duplicates this."""
    query = session.query(models.Upload.document_id).filter(models.Upload.actually_persisted == 1)
    if requirement is not None:
        query = query.filter(models.Upload.requirement == requirement)
    seen: list[str] = []
    for (document_id,) in query.order_by(models.Upload.id).all():
        if document_id not in seen:
            seen.append(document_id)
    return seen


def get_current_day(session: Session) -> int:
    return get_meta(session).current_sim_day


def set_current_sim_day(session: Session, day: int) -> None:
    meta = get_meta(session)
    meta.current_sim_day = day
    session.commit()


def log_action(session: Session, actor: str, sim_day: int, action_type: str, payload: dict, result: str) -> None:
    session.add(
        models.ActionLog(
            actor=actor,
            sim_day=sim_day,
            action_type=action_type,
            payload_json=json.dumps(payload),
            result=result,
        )
    )
    session.commit()


def get_action_log(session: Session) -> list[models.ActionLog]:
    return session.query(models.ActionLog).order_by(models.ActionLog.id).all()


# --- Scripted silent failures --------------------------------------------

def get_silent_failures(session: Session) -> list[models.SilentFailure]:
    return session.query(models.SilentFailure).order_by(models.SilentFailure.id).all()


def get_unconsumed_silent_failure(
    session: Session, document_id: str, requirement: str
) -> models.SilentFailure | None:
    return (
        session.query(models.SilentFailure)
        .filter(
            models.SilentFailure.document_id == document_id,
            models.SilentFailure.requirement == requirement,
            models.SilentFailure.consumed == 0,
        )
        .first()
    )


def consume_silent_failure(session: Session, failure_id: str) -> None:
    row = session.get(models.SilentFailure, failure_id)
    if row is not None:
        row.consumed = 1
        session.commit()


# --- Requirements -----------------------------------------------------

def get_open_requirements(session: Session) -> list[str]:
    return json.loads(get_case(session).open_requirements_json)


def add_open_requirement(session: Session, requirement: str) -> None:
    case = get_case(session)
    requirements = json.loads(case.open_requirements_json)
    if requirement not in requirements:
        requirements.append(requirement)
        case.open_requirements_json = json.dumps(requirements)
        session.commit()


def remove_open_requirement(session: Session, requirement: str) -> None:
    case = get_case(session)
    requirements = json.loads(case.open_requirements_json)
    if requirement in requirements:
        requirements.remove(requirement)
        case.open_requirements_json = json.dumps(requirements)
        session.commit()


# --- Interview ----------------------------------------------------------

def get_interview(session: Session) -> dict | None:
    case = get_case(session)
    return json.loads(case.interview_json) if case.interview_json else None


def set_interview(session: Session, data: dict | None) -> None:
    case = get_case(session)
    case.interview_json = json.dumps(data) if data is not None else None
    session.commit()


def add_interview_slots(session: Session, slots: list[dict]) -> None:
    for slot in slots:
        session.add(
            models.InterviewSlot(
                id=slot["id"], day=slot["day"], start_time=slot["start_time"], end_time=slot["end_time"]
            )
        )
    session.commit()


def get_interview_slots(session: Session) -> list[models.InterviewSlot]:
    return session.query(models.InterviewSlot).order_by(models.InterviewSlot.id).all()


def get_interview_slot(session: Session, slot_id: str) -> models.InterviewSlot | None:
    return session.get(models.InterviewSlot, slot_id)


# --- Notices --------------------------------------------------------------

def add_notice(session: Session, day: int, text: str) -> None:
    session.add(models.Notice(day=day, text=text))
    session.commit()


def get_notices(session: Session) -> list[models.Notice]:
    return session.query(models.Notice).order_by(models.Notice.id).all()


# --- Inbox ------------------------------------------------------------

def add_inbox_message(session: Session, day: int, sender: str, subject: str, body: str) -> None:
    session.add(models.InboxMessage(day=day, sender=sender, subject=subject, body=body, is_read=0))
    session.commit()


def get_inbox_messages(session: Session) -> list[models.InboxMessage]:
    return session.query(models.InboxMessage).order_by(models.InboxMessage.id).all()


def get_inbox_message(session: Session, message_id: int) -> models.InboxMessage | None:
    return session.get(models.InboxMessage, message_id)


def mark_inbox_message_read(session: Session, message_id: int) -> None:
    message = get_inbox_message(session, message_id)
    if message is not None:
        message.is_read = 1
        session.commit()


# --- Events -------------------------------------------------------------

def is_event_applied(session: Session, event_id: str) -> bool:
    row = session.get(models.EventRow, event_id)
    return row is not None and row.applied == 1


def mark_event_applied(session: Session, event_id: str, event_type: str, description: str, day: int) -> None:
    row = session.get(models.EventRow, event_id)
    if row is None:
        row = models.EventRow(
            id=event_id, event_type=event_type, trigger_description=description, applied=1, applied_at_day=day
        )
        session.add(row)
    else:
        row.applied = 1
        row.applied_at_day = day
    session.commit()


def get_applied_event_ids(session: Session) -> list[str]:
    rows = session.query(models.EventRow).filter(models.EventRow.applied == 1).order_by(models.EventRow.id).all()
    return [r.id for r in rows]


def snapshot(session: Session) -> dict:
    """A deterministic, JSON-serializable view of world truth, used to
    assert reset/clock determinism. Deliberately excludes action_log and
    uploads: those are a record of what actions were *taken* during a run,
    not scenario truth — running the identical sequence of actions twice
    is expected to (and is separately verified to) produce identical
    uploads, but the snapshot itself only needs to cover state the event
    engine and scenario loader are responsible for keeping deterministic."""
    meta = get_meta(session)
    household = get_household(session)
    case = get_case(session)
    return {
        "meta": {
            "scenario_id": meta.scenario_id,
            "scenario_version": meta.scenario_version,
            "current_sim_day": meta.current_sim_day,
        },
        "household": {
            "id": household.id,
            "primary_applicant": household.primary_applicant,
            "members": json.loads(household.members_json),
            "preferences": json.loads(household.preferences_json),
        },
        "case": {
            "id": case.id,
            "case_id": case.case_id,
            "status": case.status,
            "reported_employer": case.reported_employer,
            "open_requirements": json.loads(case.open_requirements_json),
            "interview": json.loads(case.interview_json) if case.interview_json else None,
            "recertification": json.loads(case.recertification_json) if case.recertification_json else None,
        },
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "doc_date": d.doc_date,
                "visible_text": d.visible_text,
                "simulator_tags": json.loads(d.simulator_tags_json),
                "available_from_day": d.available_from_day,
            }
            for d in get_documents(session)
        ],
        "calendar_events": [
            {
                "id": e.id,
                "day": e.day,
                "start_time": e.start_time,
                "end_time": e.end_time,
                "label": e.label,
                "source": e.source,
            }
            for e in get_calendar_events(session)
        ],
        "policy_items": [
            {
                "id": p.id,
                "title": p.title,
                "source": p.source,
                "source_url": p.source_url,
                "jurisdiction": p.jurisdiction,
                "effective_date": p.effective_date,
                "source_version": p.source_version,
                "topic": p.topic,
                "authority_level": p.authority_level,
                "text": p.text,
            }
            for p in get_policy_items(session)
        ],
        "notices": [{"id": n.id, "day": n.day, "text": n.text} for n in get_notices(session)],
        "interview_slots": [
            {"id": s.id, "day": s.day, "start_time": s.start_time, "end_time": s.end_time}
            for s in get_interview_slots(session)
        ],
        "inbox_messages": [
            {
                "id": m.id,
                "day": m.day,
                "sender": m.sender,
                "subject": m.subject,
                "body": m.body,
                "is_read": m.is_read,
            }
            for m in get_inbox_messages(session)
        ],
        "events_applied": {
            r.id: r.applied_at_day
            for r in session.query(models.EventRow).order_by(models.EventRow.id).all()
        },
        "silent_failures": [
            {"id": f.id, "document_id": f.document_id, "requirement": f.requirement, "consumed": f.consumed}
            for f in get_silent_failures(session)
        ],
    }
