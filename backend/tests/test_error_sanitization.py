import json

FORBIDDEN_MARKERS = [
    "Traceback",
    "traceback",
    "sqlalchemy",
    "File \"",
    "line ",
    "sqlite3",
    "app.models",
    "app/",
    ".py",
]


def _assert_sanitized(body_text: str):
    for marker in FORBIDDEN_MARKERS:
        assert marker not in body_text, f"leaked internal detail: {marker!r} in {body_text}"


def test_validation_error_is_sanitized(client, agent_headers):
    # Missing required "to_day" field triggers FastAPI/Pydantic's
    # RequestValidationError, which by default includes a stack-trace-ish
    # payload of internal locations; our handler must replace it.
    from app import config

    response = client.post(
        "/lab/clock/advance",
        json={},
        headers={"X-Lab-Token": config.LAB_TOKEN, "Origin": config.LAB_ORIGIN},
    )
    assert response.status_code == 422
    body = response.json()
    assert body == {"error": "invalid_request"}
    _assert_sanitized(json.dumps(body))


def test_unhandled_exception_is_sanitized(client_no_raise, lab_headers):
    client_no_raise.post("/lab/clock/advance", json={"to_day": 18}, headers=lab_headers)
    # Moving time backwards raises a ValueError inside clock.advance_to
    # that no route code catches — this exercises the generic 500 handler.
    response = client_no_raise.post("/lab/clock/advance", json={"to_day": 5}, headers=lab_headers)
    assert response.status_code == 500
    body = response.json()
    assert body == {"error": "internal_error"}
    _assert_sanitized(json.dumps(body))


def test_404_is_sanitized(client, agent_headers):
    response = client.get("/does-not-exist", headers=agent_headers)
    assert response.status_code == 404
    body = response.json()
    assert list(body.keys()) == ["error"]
    _assert_sanitized(json.dumps(body))
