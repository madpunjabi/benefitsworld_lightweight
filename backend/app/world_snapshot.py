"""Full, generic (table-agnostic) snapshot/restore of the entire world
database. Distinct from world_state.snapshot(), which deliberately covers
only the deterministic subset used for reset-determinism testing and
excludes action_log/uploads. This module dumps and restores every row of
every table, byte-for-byte, so a run can be paused at a specific simulated
day and resumed later from that exact state — including its full history
(uploads, action log, inbox, events-applied) — not just scenario truth.

Used to give a paired continuous-context / fresh-context comparison an
identical starting world for both legs: snapshot once at the interruption
point, then restore() before each leg so neither leg's actions can bleed
into the other's.

No model in this schema declares a ForeignKey, so there is no insert-order
constraint between tables — MODELS may be dumped/restored in any order."""

import json

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app import models
from app.db import Base, engine

MODELS = [
    models.WorldStateMeta,
    models.Household,
    models.Case,
    models.Document,
    models.CalendarEvent,
    models.Upload,
    models.SilentFailure,
    models.PolicyItem,
    models.EventRow,
    models.InterviewSlot,
    models.Notice,
    models.InboxMessage,
    models.ActionLog,
]


def snapshot_all(session: Session) -> dict:
    """Every row of every table, as plain JSON-serializable dicts, keyed
    by table name."""
    data: dict[str, list[dict]] = {}
    for model in MODELS:
        columns = [c.key for c in inspect(model).columns]
        rows = session.query(model).order_by(*[getattr(model, c) for c in columns[:1]]).all()
        data[model.__tablename__] = [{c: getattr(row, c) for c in columns} for row in rows]
    return data


def restore_all(session: Session, data: dict) -> None:
    """Drop and recreate the schema (same mechanism reset.reset() already
    uses live, on every /lab/reset call), then reload every row exactly
    as captured by snapshot_all — restoring full history, not just
    scenario truth."""
    session.close()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    for model in MODELS:
        for row in data.get(model.__tablename__, []):
            session.add(model(**row))
    session.commit()


def snapshot_to_json(session: Session) -> str:
    return json.dumps(snapshot_all(session))


def restore_from_json(session: Session, raw: str) -> None:
    restore_all(session, json.loads(raw))
