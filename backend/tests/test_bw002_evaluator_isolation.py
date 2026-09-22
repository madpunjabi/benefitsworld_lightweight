import json

from tests.conftest import reset_bw002
from tests.test_visible_state_isolation import FORBIDDEN_SUBSTRINGS

BW002_PUBLIC_ENDPOINTS = [
    "/portal/case",
    "/portal/notices",
    "/portal/interview/slots",
    "/inbox/messages",
    "/files",
    "/calendar/events",
    "/policy/search",
    "/agent/status",
]


def _full_golden_path(client, agent_headers, lab_headers):
    client.get("/files/D-201", headers=agent_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-201", "requirement": "income_verification"}, headers=agent_headers
    )
    client.post(
        "/portal/uploads", json={"document_id": "D-203", "requirement": "income_verification"}, headers=agent_headers
    )
    client.post(
        "/portal/uploads", json={"document_id": "D-204", "requirement": "housing_verification"}, headers=agent_headers
    )
    client.post("/portal/interview/schedule", json={"slot_id": "BW2-SLOT-1"}, headers=agent_headers)
    client.post("/lab/clock/advance", json={"to_day": 3}, headers=lab_headers)
    client.post("/portal/recertification/submit", headers=agent_headers)

    client.post("/lab/clock/advance", json={"to_day": 6}, headers=lab_headers)
    client.get("/files/D-208", headers=agent_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-208", "requirement": "housing_correction"}, headers=agent_headers
    )

    client.post("/lab/clock/advance", json={"to_day": 8}, headers=lab_headers)
    client.get("/files/D-209", headers=agent_headers)
    client.post(
        "/portal/uploads",
        json={"document_id": "D-209", "requirement": "updated_income_verification"},
        headers=agent_headers,
    )
    client.post("/portal/recertification/submit", headers=agent_headers)


def test_evaluator_all_false_at_day0(client, lab_headers, session):
    reset_bw002(client, lab_headers)
    result = client.get("/lab/evaluate", headers=lab_headers).json()
    assert result["binary_success"] is False
    assert all(v is False for v in result["checkpoints"].values())
    assert set(result["checkpoints"].keys()) == {
        "initial_income_verification_resolved_correctly",
        "initial_housing_requirement_resolved",
        "interview_scheduled_and_completed",
        "day6_housing_rejection_visible",
        "d208_inspected",
        "housing_correction_resolved_before_deadline",
        "day8_employment_change_visible",
        "d209_inspected",
        "updated_income_verification_resolved_before_deadline",
        "recertification_reflects_latest_case_facts",
        "recertification_completed_before_day14",
        "final_world_has_no_open_requirements",
    }


def test_evaluator_full_success_on_golden_path(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    _full_golden_path(client, agent_headers, lab_headers)
    result = client.get("/lab/evaluate", headers=lab_headers).json()
    assert all(result["checkpoints"].values()), result["checkpoints"]
    assert result["binary_success"] is True


def test_binary_success_false_if_recertification_overdue_despite_checkpoints(
    client, agent_headers, lab_headers, session
):
    """A recertification submitted late enough to miss Day 14 (submitted
    on Day 14 itself, after the deadline event already fired) must not
    count as success even though every other checkpoint is satisfied —
    proves binary_success also gates on case.status, not just the 12
    named checkpoints."""
    reset_bw002(client, lab_headers)
    _full_golden_path(client, agent_headers, lab_headers)
    # Undo the submission's effect by advancing past day 14 without ever
    # having submitted: reset and replay everything except the final submit.
    reset_bw002(client, lab_headers)
    client.get("/files/D-201", headers=agent_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-201", "requirement": "income_verification"}, headers=agent_headers
    )
    client.post(
        "/portal/uploads", json={"document_id": "D-203", "requirement": "income_verification"}, headers=agent_headers
    )
    client.post(
        "/portal/uploads", json={"document_id": "D-204", "requirement": "housing_verification"}, headers=agent_headers
    )
    client.post("/portal/interview/schedule", json={"slot_id": "BW2-SLOT-1"}, headers=agent_headers)
    client.post("/lab/clock/advance", json={"to_day": 3}, headers=lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 6}, headers=lab_headers)
    client.get("/files/D-208", headers=agent_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-208", "requirement": "housing_correction"}, headers=agent_headers
    )
    client.post("/lab/clock/advance", json={"to_day": 8}, headers=lab_headers)
    client.get("/files/D-209", headers=agent_headers)
    client.post(
        "/portal/uploads",
        json={"document_id": "D-209", "requirement": "updated_income_verification"},
        headers=agent_headers,
    )
    # Requirements are all clear, but recertification was never submitted.
    client.post("/lab/clock/advance", json={"to_day": 14}, headers=lab_headers)
    w = client.get("/lab/world_state", headers=lab_headers).json()
    assert w["case_status"] == "RECERTIFICATION_OVERDUE"
    result = client.get("/lab/evaluate", headers=lab_headers).json()
    assert result["checkpoints"]["final_world_has_no_open_requirements"] is True
    assert result["binary_success"] is False


def test_bw002_public_endpoints_never_leak_lab_only_fields(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    _full_golden_path(client, agent_headers, lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 14}, headers=lab_headers)

    for path in BW002_PUBLIC_ENDPOINTS:
        response = client.get(path, headers=agent_headers)
        assert response.status_code == 200, f"{path} returned {response.status_code}"
        body_text = json.dumps(response.json()).lower()
        for forbidden in FORBIDDEN_SUBSTRINGS:
            assert forbidden not in body_text, f"{path} leaked '{forbidden}': {body_text}"


def test_bw002_portal_case_shape_matches_bw001(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    body = client.get("/portal/case", headers=agent_headers).json()
    assert set(body.keys()) == {
        "case_id",
        "status",
        "open_requirements",
        "reported_employer",
        "interview",
        "recertification",
        "received_document_ids",
    }


def test_bw002_files_endpoint_excludes_simulator_tags(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    for doc in client.get("/files", headers=agent_headers).json():
        assert set(doc.keys()) == {"id", "filename", "date", "type", "visible_text"}
