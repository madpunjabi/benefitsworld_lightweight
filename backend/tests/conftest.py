import os
import tempfile
from pathlib import Path

os.environ.setdefault("DB_PATH", str(Path(tempfile.gettempdir()) / "benefitsworld_test.db"))

import pytest
from fastapi.testclient import TestClient

from app import config
from app.db import SessionLocal
from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def client_no_raise():
    # Starlette's TestClient re-raises unhandled exceptions by default
    # (useful for debugging most tests), which defeats a test that wants to
    # assert on the *sanitized 500 response* our own handler produces.
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture()
def session():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture()
def lab_headers():
    return {"X-Lab-Token": config.LAB_TOKEN, "Origin": config.LAB_ORIGIN}


@pytest.fixture()
def agent_headers():
    return {"Origin": config.AGENT_ORIGIN}
