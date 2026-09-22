from app import world_state
from tests.conftest import reset_bw002


def test_d202_alone_does_not_satisfy_income_verification(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-202", "requirement": "income_verification"}, headers=agent_headers
    )
    case = client.get("/portal/case", headers=agent_headers).json()
    assert "D-202" in case["received_document_ids"]
    assert "income_verification" in case["open_requirements"]
    assert "EVT-BW002-income-verified" not in world_state.get_applied_event_ids(session)


def test_d201_alone_does_not_satisfy_income_verification(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-201", "requirement": "income_verification"}, headers=agent_headers
    )
    case = client.get("/portal/case", headers=agent_headers).json()
    assert "income_verification" in case["open_requirements"]


def test_d201_plus_d203_satisfies_income_verification(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-201", "requirement": "income_verification"}, headers=agent_headers
    )
    client.post(
        "/portal/uploads", json={"document_id": "D-203", "requirement": "income_verification"}, headers=agent_headers
    )
    case = client.get("/portal/case", headers=agent_headers).json()
    assert "income_verification" not in case["open_requirements"]
    assert "EVT-BW002-income-verified" in world_state.get_applied_event_ids(session)


def test_d204_genuinely_satisfies_day0_housing_verification_no_silent_failure(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    response = client.post(
        "/portal/uploads", json={"document_id": "D-204", "requirement": "housing_verification"}, headers=agent_headers
    )
    assert response.json()["received"] is True
    upload_row = world_state.get_uploads(session)[-1]
    assert upload_row.actually_persisted == 1
    assert upload_row.scripted_failure_id is None

    case = client.get("/portal/case", headers=agent_headers).json()
    assert "D-204" in case["received_document_ids"]
    assert "housing_verification" not in case["open_requirements"]
    assert "EVT-BW002-housing-verified" in world_state.get_applied_event_ids(session)


def test_interview_scheduling_and_completion(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    slots = client.get("/portal/interview/slots", headers=agent_headers).json()
    slot_id = slots[0]["id"]
    day = slots[0]["day"]
    client.post("/portal/interview/schedule", json={"slot_id": slot_id}, headers=agent_headers)
    case = client.get("/portal/case", headers=agent_headers).json()
    assert case["interview"]["status"] == "scheduled"

    client.post("/lab/clock/advance", json={"to_day": day + 1}, headers=lab_headers)
    case = client.get("/portal/case", headers=agent_headers).json()
    assert case["interview"]["status"] == "completed"
    assert "interview" not in case["open_requirements"]
