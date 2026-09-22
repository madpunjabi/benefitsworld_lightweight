from tests.conftest import reset_bw002


def _resolve_day0_trio(client, agent_headers, lab_headers, complete_interview_by_day=3):
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
    client.post("/lab/clock/advance", json={"to_day": complete_interview_by_day}, headers=lab_headers)


def test_recertification_not_ready_at_day0(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    case = client.get("/portal/case", headers=agent_headers).json()
    assert case["recertification"]["status"] == "NOT_READY"


def test_submit_rejected_while_not_ready(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    response = client.post("/portal/recertification/submit", headers=agent_headers)
    assert response.status_code == 400
    case = client.get("/portal/case", headers=agent_headers).json()
    assert case["recertification"]["status"] == "NOT_READY"


def test_recertification_becomes_ready_once_trio_resolved(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    _resolve_day0_trio(client, agent_headers, lab_headers)
    case = client.get("/portal/case", headers=agent_headers).json()
    assert case["recertification"]["status"] == "READY"


def test_submit_succeeds_when_ready_and_records_snapshot(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    _resolve_day0_trio(client, agent_headers, lab_headers)
    response = client.post("/portal/recertification/submit", headers=agent_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "SUBMITTED"
    assert body["submitted_at_day"] == 3
    assert "EVT-BW002-income-verified" in body["snapshot_applied_event_ids"]
    assert "EVT-BW002-housing-verified" in body["snapshot_applied_event_ids"]
    assert "EVT-BW002-interview-completed" in body["snapshot_applied_event_ids"]


def test_recertification_reopens_after_housing_rejection(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    _resolve_day0_trio(client, agent_headers, lab_headers)
    client.post("/portal/recertification/submit", headers=agent_headers)
    client.post("/lab/clock/advance", json={"to_day": 6}, headers=lab_headers)  # housing rejected
    case = client.get("/portal/case", headers=agent_headers).json()
    assert case["recertification"]["status"] == "NEEDS_UPDATE"


def test_recertification_reopens_after_employment_change(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    _resolve_day0_trio(client, agent_headers, lab_headers)
    client.post("/portal/recertification/submit", headers=agent_headers)
    client.post("/lab/clock/advance", json={"to_day": 8}, headers=lab_headers)  # employment change
    case = client.get("/portal/case", headers=agent_headers).json()
    assert case["recertification"]["status"] == "NEEDS_UPDATE"


def test_recertification_not_reopened_if_never_submitted(client, agent_headers, lab_headers, session):
    """The needs_update mechanic only reopens a submission that actually
    existed — it must not spuriously mark an unsubmitted recertification."""
    reset_bw002(client, lab_headers)
    _resolve_day0_trio(client, agent_headers, lab_headers)
    # Never submitted.
    client.post("/lab/clock/advance", json={"to_day": 8}, headers=lab_headers)
    case = client.get("/portal/case", headers=agent_headers).json()
    # updated_income_verification reopened the gate, so it's NOT_READY, not NEEDS_UPDATE.
    assert case["recertification"]["status"] == "NOT_READY"


def test_resubmit_blocked_until_reopened_requirement_cleared(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    _resolve_day0_trio(client, agent_headers, lab_headers)
    client.post("/portal/recertification/submit", headers=agent_headers)
    client.post("/lab/clock/advance", json={"to_day": 6}, headers=lab_headers)
    response = client.post("/portal/recertification/submit", headers=agent_headers)
    assert response.status_code == 400


def test_resubmit_succeeds_once_reopened_requirement_cleared(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    _resolve_day0_trio(client, agent_headers, lab_headers)
    client.post("/portal/recertification/submit", headers=agent_headers)
    client.post("/lab/clock/advance", json={"to_day": 6}, headers=lab_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-208", "requirement": "housing_correction"}, headers=agent_headers
    )
    response = client.post("/portal/recertification/submit", headers=agent_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "SUBMITTED"
    assert body["submitted_at_day"] == 6
