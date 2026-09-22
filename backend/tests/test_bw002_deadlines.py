from app import world_state
from tests.conftest import reset_bw002


def _full_golden_path(client, agent_headers, lab_headers):
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
    client.post(
        "/portal/uploads", json={"document_id": "D-208", "requirement": "housing_correction"}, headers=agent_headers
    )

    client.post("/lab/clock/advance", json={"to_day": 8}, headers=lab_headers)
    client.post(
        "/portal/uploads",
        json={"document_id": "D-209", "requirement": "updated_income_verification"},
        headers=agent_headers,
    )
    client.post("/portal/recertification/submit", headers=agent_headers)


def test_housing_correction_overdue_at_day10_if_unresolved(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
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
    client.post("/lab/clock/advance", json={"to_day": 6}, headers=lab_headers)  # housing rejected
    client.post("/lab/clock/advance", json={"to_day": 10}, headers=lab_headers)  # never corrected

    assert "EVT-BW002-housing-correction-overdue" in world_state.get_applied_event_ids(session)
    case = client.get("/portal/case", headers=agent_headers).json()
    assert case["status"] == "PENDING"  # not immediately closed


def test_updated_income_overdue_at_day11_if_unresolved(client, lab_headers, session):
    reset_bw002(client, lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 8}, headers=lab_headers)  # employment change
    client.post("/lab/clock/advance", json={"to_day": 11}, headers=lab_headers)  # never verified
    assert "EVT-BW002-updated-income-overdue" in world_state.get_applied_event_ids(session)


def test_recertification_overdue_at_day14_if_unresolved(client, lab_headers, session):
    reset_bw002(client, lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 14}, headers=lab_headers)
    case = client.get("/lab/world_state", headers=lab_headers).json()
    assert case["case_status"] == "RECERTIFICATION_OVERDUE"
    assert "EVT-BW002-recertification-deadline-missed" in world_state.get_applied_event_ids(session)


def test_completing_everything_correctly_avoids_recertification_overdue(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    _full_golden_path(client, agent_headers, lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 14}, headers=lab_headers)

    w = client.get("/lab/world_state", headers=lab_headers).json()
    assert w["case_status"] == "PENDING"
    assert "EVT-BW002-recertification-deadline-missed" not in w["applied_event_ids"]
    case = client.get("/portal/case", headers=agent_headers).json()
    assert case["recertification"]["status"] == "SUBMITTED"
    assert case["open_requirements"] == []
