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


def snapshot(session: Session) -> dict:
    """A deterministic, JSON-serializable view of world truth, used to
    assert reset/clock determinism. Deliberately excludes action_log: the
    log is a record of what happened during a run, not scenario truth, and
    two resets are expected to produce an identical *scenario* state even
    if a different number of harness actions preceded each reset."""
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
                "topic": p.topic,
                "authority_level": p.authority_level,
                "text": p.text,
            }
            for p in get_policy_items(session)
        ],
        # uploads deliberately excluded, for the same reason action_log is:
        # they record what happened during a run, not scenario truth. A
        # fresh reset always yields zero uploads regardless of prior state.
    }
