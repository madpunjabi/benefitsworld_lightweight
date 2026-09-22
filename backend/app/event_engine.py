from dataclasses import dataclass
from typing import Callable

from sqlalchemy.orm import Session


@dataclass
class Event:
    id: str
    description: str
    predicate: Callable[[Session], bool]
    apply: Callable[[Session], None]


class EventEngine:
    """Deterministic, idempotent event application. No workflow framework:
    events are evaluated in list order, applied at most once each, and the
    list actually applied this tick is returned for logging.

    Milestone 1 defines no events yet (BW-001's income/interview/housing/
    income-change/recertification events are added in milestones 3-5) — the
    engine exists now so clock.advance() has a stable integration point."""

    def __init__(self, events: list[Event]):
        self.events = events

    def tick(self, session: Session) -> list[Event]:
        applied = []
        for event in self.events:
            if event.predicate(session):
                event.apply(session)
                applied.append(event)
        return applied


def default_engine() -> EventEngine:
    return EventEngine(events=[])
