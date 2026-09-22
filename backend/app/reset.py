from sqlalchemy.orm import Session

from app import scenario_loader
from app.db import Base, engine


def reset(session: Session, scenario_id: str | None = None) -> None:
    """Deterministic reset: drop every table and recreate the schema from
    scratch (so autoincrement sequences restart at 1), then reload the
    scenario seed. Two consecutive resets of the same scenario version
    always produce byte-identical world state.

    `scenario_id`, when given, resets into that specific scenario (see
    config.SCENARIO_SEED_PATHS); omitting it preserves the original
    behavior of always resetting into whatever config.SCENARIO_ID resolved
    to at process start (BW-001, by default)."""
    session.close()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    scenario_loader.load_scenario(session, scenario_id=scenario_id)
