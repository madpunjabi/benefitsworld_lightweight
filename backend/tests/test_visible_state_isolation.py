import json

FORBIDDEN_SUBSTRINGS = [
    "simulator_tags",
    "actually_persisted",
    "scripted_failure_id",
    "checkpoint",
    "evaluator",
    "silent_failure",
    "event_type",
    "trigger_description",
    "applied_at_day",
    "terminal",
]

PUBLIC_ENDPOINTS = [
    "/portal/case",
    "/portal/notices",
    "/inbox/messages",
    "/files",
    "/calendar/events",
    "/policy/search",
    "/agent/status",
]


def test_public_endpoints_never_leak_lab_only_fields(client, agent_headers):
    for path in PUBLIC_ENDPOINTS:
        response = client.get(path, headers=agent_headers)
        assert response.status_code == 200, f"{path} returned {response.status_code}"
        body_text = json.dumps(response.json()).lower()
        for forbidden in FORBIDDEN_SUBSTRINGS:
            assert forbidden not in body_text, f"{path} leaked '{forbidden}': {body_text}"


def test_files_endpoint_excludes_simulator_tags_specifically(client, agent_headers):
    response = client.get("/files", headers=agent_headers)
    assert response.status_code == 200
    for doc in response.json():
        assert set(doc.keys()) == {"id", "filename", "date", "visible_text"}


def test_portal_case_excludes_internal_fields(client, agent_headers):
    response = client.get("/portal/case", headers=agent_headers)
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {
        "case_id",
        "status",
        "open_requirements",
        "interview",
        "recertification",
        "received_document_ids",
    }


def test_public_router_has_no_lab_paths():
    from app.main import app

    paths = {route.path for route in app.router.routes}
    for path in paths:
        if path in ("/health",):
            continue
        assert not path.startswith("/docs") and not path.startswith("/openapi")
        assert path.startswith("/lab") or path in {
            "/portal/case",
            "/portal/notices",
            "/inbox/messages",
            "/files",
            "/calendar/events",
            "/policy/search",
            "/agent/status",
        }
