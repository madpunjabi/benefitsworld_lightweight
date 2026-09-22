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
    "authority_level",
    "benchmark",
    "distractor",
    "conflict",
    "expected_answer",
    "correct_document",
]

PUBLIC_ENDPOINTS = [
    "/portal/case",
    "/portal/notices",
    "/portal/interview/slots",
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
        assert set(doc.keys()) == {"id", "filename", "date", "type", "visible_text"}


def test_portal_case_excludes_internal_fields(client, agent_headers):
    response = client.get("/portal/case", headers=agent_headers)
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {
        "case_id",
        "status",
        "open_requirements",
        "reported_employer",
        "interview",
        "recertification",
        "received_document_ids",
    }


POLICY_PUBLIC_FIELDS = {
    "id",
    "title",
    "source",
    "source_url",
    "jurisdiction",
    "effective_date",
    "source_version",
    "topic",
    "text",
}


def test_policy_item_excludes_authority_level(client, agent_headers):
    response = client.get("/policy/search", headers=agent_headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) > 0
    for item in items:
        assert set(item.keys()) == POLICY_PUBLIC_FIELDS


def test_policy_item_detail_excludes_authority_level(client, agent_headers):
    response = client.get("/policy/POL-001", headers=agent_headers)
    assert response.status_code == 200
    assert set(response.json().keys()) == POLICY_PUBLIC_FIELDS


def test_full_event_chain_still_leaks_nothing(client, agent_headers, lab_headers):
    """Run the entire Milestone-3 sequence (income -> interview -> a
    conflicting schedule -> time advance -> housing) and re-scan every
    public endpoint: applied-event internals, conflict labels, and future
    event data must never appear."""
    client.post(
        "/portal/uploads", json={"document_id": "D-101", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    client.post(
        "/portal/uploads", json={"document_id": "D-103", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    client.post("/portal/interview/schedule", json={"slot_id": "SLOT-2"}, headers=agent_headers)  # the conflicting one
    client.post("/lab/clock/advance", json={"to_day": 3}, headers=lab_headers)

    for path in PUBLIC_ENDPOINTS:
        response = client.get(path, headers=agent_headers)
        assert response.status_code == 200
        body_text = json.dumps(response.json()).lower()
        for forbidden in FORBIDDEN_SUBSTRINGS:
            assert forbidden not in body_text, f"{path} leaked '{forbidden}' after full event chain: {body_text}"

    slots = client.get("/portal/interview/slots", headers=agent_headers).json()
    for slot in slots:
        assert set(slot.keys()) == {"id", "day", "start_time", "end_time"}


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
            "/portal/uploads",
            "/portal/interview/slots",
            "/portal/interview/schedule",
            "/inbox/messages",
            "/inbox/messages/{message_id}/read",
            "/files",
            "/calendar/events",
            "/policy/search",
            "/policy/{policy_id}",
            "/agent/status",
        }
