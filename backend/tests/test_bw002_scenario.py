from app import world_state
from tests.conftest import reset_bw002


def test_bw001_default_reset_is_unaffected(client, agent_headers, lab_headers, session):
    """The default reset (no scenario_id, exactly what every BW-001 test
    and the app's own lifespan use) must still load BW-001 — proves the
    BW-002 addition didn't change default behavior."""
    client.post("/lab/reset", headers=lab_headers)
    w = client.get("/lab/world_state", headers=lab_headers).json()
    assert w["scenario_id"] == "BW-001"
    assert w["case_id"] == "CF-ALM-10482"
    case = client.get("/portal/case", headers=agent_headers).json()
    assert case["open_requirements"] == ["earned_income_verification"]
    assert case["recertification"] is None


def test_bw002_reset_loads_bw002(client, lab_headers, session):
    reset_bw002(client, lab_headers)
    w = client.get("/lab/world_state", headers=lab_headers).json()
    assert w["scenario_id"] == "BW-002"
    assert w["scenario_version"] == "0.1"
    assert w["case_id"] == "CF-ALM-20591"
    assert w["case_status"] == "PENDING"
    assert w["current_sim_day"] == 0


def test_bw002_reset_is_deterministic(client, lab_headers, session):
    reset_bw002(client, lab_headers)
    snap1 = world_state.snapshot(session)
    reset_bw002(client, lab_headers)
    snap2 = world_state.snapshot(session)
    assert snap1 == snap2


def test_all_four_day0_responsibilities_visible_simultaneously(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    case = client.get("/portal/case", headers=agent_headers).json()
    assert set(case["open_requirements"]) == {"income_verification", "housing_verification", "interview"}
    assert case["recertification"] is not None
    assert case["recertification"]["status"] == "NOT_READY"
    slots = client.get("/portal/interview/slots", headers=agent_headers).json()
    assert len(slots) >= 1


def test_bw002_day0_documents_all_visible(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    files = {f["id"] for f in client.get("/files", headers=agent_headers).json()}
    assert files == {"D-201", "D-202", "D-203", "D-204", "D-205", "D-206", "D-207"}
    # D-208/D-209 are not yet visible (available_from_day 6/8)
    assert client.get("/files/D-208", headers=agent_headers).status_code == 404
    assert client.get("/files/D-209", headers=agent_headers).status_code == 404


def test_switching_between_scenarios_does_not_bleed_state(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-201", "requirement": "income_verification"}, headers=agent_headers
    )
    # Back to BW-001 — must be a clean, unrelated world, not a merge of the two.
    client.post("/lab/reset", headers=lab_headers)
    case = client.get("/portal/case", headers=agent_headers).json()
    assert case["case_id"] == "CF-ALM-10482"
    assert case["received_document_ids"] == []
    assert case["open_requirements"] == ["earned_income_verification"]
