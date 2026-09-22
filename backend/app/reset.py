from sqlalchemy.orm import Session

from app import scenario_loader
from app.db import Base, engine


def reset(session: Session) -> None:
    """Deterministic reset: drop every table and recreate the schema from
    scratch (so autoincrement sequences restart at 1), then reload the
    scenario seed. Two consecutive resets of the same scenario version
    always produce byte-identical world state."""
    session.close()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    scenario_loader.load_scenario(session)
