from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import inspect

from app import config, models, reset
from app.cors import PathScopedCORSMiddleware
from app.db import SessionLocal, engine
from app.routes import agent, calendar, files, inbox, lab, policy, portal
from app.security import install_sanitized_error_handlers


def _database_already_initialized() -> bool:
    """True iff the schema exists AND has been seeded — checked (not just
    "does the file exist") because a fresh persistent volume can contain
    a zero-byte file before SQLite ever writes to it."""
    inspector = inspect(engine)
    if "world_state_meta" not in inspector.get_table_names():
        return False
    with SessionLocal() as session:
        return session.get(models.WorldStateMeta, 1) is not None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Local dev/tests (RESET_ON_BOOT defaults true): always boot into a
    # deterministic Day-0 state, exactly as originally designed —
    # starting fresh every time the process launches removes an entire
    # class of "stale DB from a prior run" nondeterminism.
    #
    # Production (RESET_ON_BOOT defaults false, via ENVIRONMENT=production):
    # a process restart must NOT silently wipe a live public demo. Only
    # initialize the persistent database if it isn't already initialized;
    # otherwise leave it exactly as it was. Reset itself is unchanged —
    # it remains available at any time via the existing explicit
    # POST /lab/reset action.
    if config.RESET_ON_BOOT or not _database_already_initialized():
        session = SessionLocal()
        try:
            reset.reset(session)
        finally:
            session.close()
    yield


app = FastAPI(title="BenefitsWorld", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)

app.add_middleware(PathScopedCORSMiddleware)
install_sanitized_error_handlers(app)

app.include_router(portal.router)
app.include_router(inbox.router)
app.include_router(files.router)
app.include_router(calendar.router)
app.include_router(policy.router)
app.include_router(agent.router)
app.include_router(lab.router)
app.include_router(lab.auth_router)


@app.get("/health")
def health() -> dict:
    return {"ok": True}
