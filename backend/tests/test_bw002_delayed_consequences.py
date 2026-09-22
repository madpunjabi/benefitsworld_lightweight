from app import world_state
from tests.conftest import reset_bw002


def _resolve_day0_trio(client, agent_headers, lab_headers):
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


def test_housing_rejection_does_not_fire_before_day6(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    _resolve_day0_trio(client, agent_headers, lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 5}, headers=lab_headers)
    assert "EVT-BW002-housing-rejected" not in world_state.get_applied_event_ids(session)
    assert "housing_correction" not in world_state.get_open_requirements(session)


def test_housing_rejection_requires_d204_to_have_been_used(client, agent_headers, lab_headers, session):
    """If D-204 was never uploaded for housing_verification, the Day-6
    rejection has nothing to reject and must not fire."""
    reset_bw002(client, lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 6}, headers=lab_headers)
    assert "EVT-BW002-housing-rejected" not in world_state.get_applied_event_ids(session)


def test_housing_rejection_fires_exactly_once_at_day6(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    _resolve_day0_trio(client, agent_headers, lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 6}, headers=lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 9}, headers=lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 12}, headers=lab_headers)

    assert world_state.get_applied_event_ids(session).count("EVT-BW002-housing-rejected") == 1
    assert world_state.get_open_requirements(session).count("housing_correction") == 1
    messages = [m for m in world_state.get_inbox_messages(session) if m.subject == "Housing Proof Incomplete"]
    assert len(messages) == 1

    # The original upload is never erased from history.
    assert "D-204" in world_state.get_received_document_ids(session, requirement="housing_verification")


def test_d208_resolves_housing_correction(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    _resolve_day0_trio(client, agent_headers, lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 6}, headers=lab_headers)

    files = {f["id"] for f in client.get("/files", headers=agent_headers).json()}
    assert "D-208" in files

    client.post(
        "/portal/uploads", json={"document_id": "D-208", "requirement": "housing_correction"}, headers=agent_headers
    )
    case = client.get("/portal/case", headers=agent_headers).json()
    assert "housing_correction" not in case["open_requirements"]
    assert "EVT-BW002-housing-correction-cleared" in world_state.get_applied_event_ids(session)


def test_employment_change_fires_exactly_once_at_day8_purely_time_triggered(client, lab_headers, session):
    reset_bw002(client, lab_headers)
    # Nothing else resolved — the event is purely time-triggered.
    client.post("/lab/clock/advance", json={"to_day": 7}, headers=lab_headers)
    assert "EVT-BW002-employment-change" not in world_state.get_applied_event_ids(session)

    client.post("/lab/clock/advance", json={"to_day": 8}, headers=lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 9}, headers=lab_headers)
    assert world_state.get_applied_event_ids(session).count("EVT-BW002-employment-change") == 1
    assert world_state.get_open_requirements(session).count("updated_income_verification") == 1


def test_d201_does_not_satisfy_updated_income_verification(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 8}, headers=lab_headers)
    client.post(
        "/portal/uploads",
        json={"document_id": "D-201", "requirement": "updated_income_verification"},
        headers=agent_headers,
    )
    case = client.get("/portal/case", headers=agent_headers).json()
    assert "D-201" in case["received_document_ids"]
    assert "updated_income_verification" in case["open_requirements"]
    assert "EVT-BW002-updated-income-verified" not in world_state.get_applied_event_ids(session)


def test_d209_satisfies_updated_income_verification(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 8}, headers=lab_headers)
    files = {f["id"] for f in client.get("/files", headers=agent_headers).json()}
    assert "D-209" in files
    client.post(
        "/portal/uploads",
        json={"document_id": "D-209", "requirement": "updated_income_verification"},
        headers=agent_headers,
    )
    case = client.get("/portal/case", headers=agent_headers).json()
    assert "updated_income_verification" not in case["open_requirements"]
    assert "EVT-BW002-updated-income-verified" in world_state.get_applied_event_ids(session)
