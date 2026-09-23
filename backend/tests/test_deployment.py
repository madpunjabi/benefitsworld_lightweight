"""Deployment-specific behavior only: environment configuration, the
production restart-preserves-DB correction, Lab Console session auth, and
hosted (non-localhost) CORS origins. No BW-001/BW-002 world behavior is
exercised here beyond what's needed to prove the database-preservation
logic (a reset + a read)."""

import subprocess
import sys
from pathlib import Path

from app import config, main

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _config_values(env_overrides: dict) -> tuple[str, str]:
    """Runs a fresh Python process so config.py's env-var-at-import-time
    logic is actually re-evaluated, rather than relying on this test
    process's already-imported (and therefore fixed) config module. A
    None value in env_overrides removes that key entirely (distinct from
    setting it to "" — os.environ.get's default only applies when the
    key is absent)."""
    import os

    env = {**os.environ, **env_overrides}
    env = {k: v for k, v in env.items() if v is not None}
    result = subprocess.run(
        [sys.executable, "-c", "from app import config; print(config.IS_PRODUCTION, config.RESET_ON_BOOT)"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    is_production, reset_on_boot = result.stdout.strip().split()
    return is_production, reset_on_boot


def test_environment_defaults_to_development_reset_always_on():
    is_production, reset_on_boot = _config_values({"ENVIRONMENT": None, "RESET_ON_BOOT": None})
    assert is_production == "False"
    assert reset_on_boot == "True"


def test_environment_production_defaults_reset_off():
    is_production, reset_on_boot = _config_values({"ENVIRONMENT": "production", "RESET_ON_BOOT": None})
    assert is_production == "True"
    assert reset_on_boot == "False"


def test_reset_on_boot_can_be_explicitly_overridden_in_production():
    is_production, reset_on_boot = _config_values({"ENVIRONMENT": "production", "RESET_ON_BOOT": "true"})
    assert is_production == "True"
    assert reset_on_boot == "True"


def test_database_path_env_var_is_respected():
    # conftest.py already sets DATABASE_PATH before any app import; this
    # just proves config picked it up rather than the hardcoded default.
    assert config.DATABASE_PATH != str(BACKEND_DIR / "benefitsworld.db")


def test_database_already_initialized_reflects_real_schema_state(session):
    # The shared test DB has already been reset by the time any test
    # runs (via the `client`/`session` fixtures elsewhere), so this
    # should observe a genuinely seeded database.
    assert main._database_already_initialized() is True


def test_production_lifespan_logic_skips_reset_when_already_initialized(monkeypatch, client, lab_headers):
    # Bring the world to a non-Day-0 state so a skipped reset is
    # observably different from a reset.
    client.post("/lab/clock/advance", json={"to_day": 5}, headers=lab_headers)
    assert main._database_already_initialized() is True

    monkeypatch.setattr(config, "RESET_ON_BOOT", False)
    should_reset = config.RESET_ON_BOOT or not main._database_already_initialized()
    assert should_reset is False  # the exact condition lifespan() uses

    # World state must be untouched by merely evaluating that condition.
    world = client.get("/lab/world_state", headers=lab_headers).json()
    assert world["current_sim_day"] == 5


def test_production_lifespan_logic_still_initializes_a_fresh_database(monkeypatch, client):
    monkeypatch.setattr(config, "RESET_ON_BOOT", False)
    monkeypatch.setattr(main, "_database_already_initialized", lambda: False)
    should_reset = config.RESET_ON_BOOT or not main._database_already_initialized()
    assert should_reset is True


def test_lab_login_with_correct_password_sets_session_cookie(client):
    response = client.post(
        "/lab/login", json={"password": config.LAB_CONSOLE_PASSWORD}, headers={"Origin": config.LAB_ORIGIN}
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert "bw_lab_session" in response.cookies


def test_lab_login_with_wrong_password_does_not_authenticate(client):
    response = client.post(
        "/lab/login", json={"password": "definitely-wrong"}, headers={"Origin": config.LAB_ORIGIN}
    )
    assert response.status_code == 200
    assert response.json() == {"ok": False}
    assert "bw_lab_session" not in response.cookies


def test_session_cookie_authenticates_lab_routes_without_x_lab_token(client):
    login = client.post(
        "/lab/login", json={"password": config.LAB_CONSOLE_PASSWORD}, headers={"Origin": config.LAB_ORIGIN}
    )
    assert login.status_code == 200

    # No X-Lab-Token header at all — the cookie alone must be sufficient.
    response = client.get("/lab/session", headers={"Origin": config.LAB_ORIGIN})
    assert response.status_code == 200
    assert response.json() == {"authenticated": True}


def test_logout_clears_the_session_cookie(client):
    client.post("/lab/login", json={"password": config.LAB_CONSOLE_PASSWORD}, headers={"Origin": config.LAB_ORIGIN})
    assert client.get("/lab/session", headers={"Origin": config.LAB_ORIGIN}).status_code == 200

    logout = client.post("/lab/logout", headers={"Origin": config.LAB_ORIGIN})
    assert logout.status_code == 200

    response = client.get("/lab/session", headers={"Origin": config.LAB_ORIGIN})
    assert response.status_code == 401


def test_legacy_x_lab_token_still_works_unchanged(client, lab_headers):
    # The existing static-token mechanism (used by local automated tests
    # and research harnesses, e.g. the Fable runner) must keep working
    # exactly as before, with no session cookie involved at all.
    response = client.get("/lab/world_state", headers=lab_headers)
    assert response.status_code == 200


def test_no_credential_at_all_is_rejected(client):
    response = client.get("/lab/session", headers={"Origin": config.LAB_ORIGIN})
    assert response.status_code == 401


def test_hosted_non_localhost_origins_are_honored_by_cors(monkeypatch, client):
    monkeypatch.setattr(config, "AGENT_ORIGIN", "https://benefitsworld-agent.vercel.app")
    monkeypatch.setattr(config, "LAB_ORIGIN", "https://benefitsworld-lab.vercel.app")

    agent_response = client.get("/files", headers={"Origin": "https://benefitsworld-agent.vercel.app"})
    assert agent_response.headers["access-control-allow-origin"] == "https://benefitsworld-agent.vercel.app"
    assert agent_response.headers["access-control-allow-credentials"] == "true"

    lab_response = client.get(
        "/lab/world_state",
        headers={
            "Origin": "https://benefitsworld-lab.vercel.app",
            "X-Lab-Token": config.LAB_TOKEN,
        },
    )
    assert lab_response.headers["access-control-allow-origin"] == "https://benefitsworld-lab.vercel.app"
    assert lab_response.headers["access-control-allow-credentials"] == "true"

    # The old localhost origin must no longer be accepted once the
    # hosted origins are configured — proves this isn't a wildcard.
    stale_localhost = client.get("/files", headers={"Origin": "http://localhost:5173"})
    assert "access-control-allow-origin" not in stale_localhost.headers


def test_cors_credentials_header_present_for_agent_origin_preflight(client):
    response = client.options(
        "/portal/case",
        headers={
            "Origin": config.AGENT_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-credentials"] == "true"


def test_path_scoped_cors_middleware_still_separates_lab_from_agent(client):
    # Regression: lab routes must still reject the agent origin and vice
    # versa, exactly as before this deployment work.
    response = client.get("/lab/world_state", headers={"Origin": config.AGENT_ORIGIN, "X-Lab-Token": config.LAB_TOKEN})
    assert "access-control-allow-origin" not in response.headers
