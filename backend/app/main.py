from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import reset
from app.cors import PathScopedCORSMiddleware
from app.db import SessionLocal
from app.routes import agent, calendar, files, inbox, lab, policy, portal
from app.security import install_sanitized_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Always boot into a deterministic Day-0 state. This is a benchmark
    # simulator, not a production service: starting fresh every time the
    # process launches removes an entire class of "stale DB from a prior
    # run" nondeterminism, and the harness/Lab Console can reset again
    # explicitly whenever it needs to.
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


@app.get("/health")
def health() -> dict:
    return {"ok": True}
