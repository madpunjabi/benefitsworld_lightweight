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


def get_calendar_events(session: Session) -> list[models.CalendarEvent]:
    return session.query(models.CalendarEvent).order_by(models.CalendarEvent.id).all()


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
    }
