from app import world_state


def test_d107_not_visible_before_day_18(client, agent_headers, session):
    files = client.get("/files", headers=agent_headers).json()
    assert "D-107" not in {f["id"] for f in files}
    assert client.get("/files/D-107", headers=agent_headers).status_code == 404
    assert "EVT-employment-change" not in world_state.get_applied_event_ids(session)
    assert "updated_income_verification" not in world_state.get_open_requirements(session)


def test_event_does_not_fire_before_day_18(client, lab_headers, session):
    client.post("/lab/clock/advance", json={"to_day": 17}, headers=lab_headers)
    assert "EVT-employment-change" not in world_state.get_applied_event_ids(session)
    assert "updated_income_verification" not in world_state.get_open_requirements(session)


def test_event_fires_deterministically_at_day_18(client, agent_headers, lab_headers, session):
    client.post("/lab/clock/advance", json={"to_day": 18}, headers=lab_headers)
    assert "EVT-employment-change" in world_state.get_applied_event_ids(session)
    assert "updated_income_verification" in world_state.get_open_requirements(session)

    files = client.get("/files", headers=agent_headers).json()
    assert "D-107" in {f["id"] for f in files}

    messages = client.get("/inbox/messages", headers=agent_headers).json()
    assert any(m["subject"] == "Updated Income Verification Needed" for m in messages)


def test_event_fires_exactly_once_across_repeated_advances(client, lab_headers, session):
    client.post("/lab/clock/advance", json={"to_day": 18}, headers=lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 20}, headers=lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 25}, headers=lab_headers)
    assert world_state.get_applied_event_ids(session).count("EVT-employment-change") == 1
    assert world_state.get_open_requirements(session).count("updated_income_verification") == 1
    assert len(
        [m for m in world_state.get_inbox_messages(session) if m.subject == "Updated Income Verification Needed"]
    ) == 1


def test_d101_does_not_satisfy_the_updated_requirement(client, agent_headers, lab_headers, session):
    client.post("/lab/clock/advance", json={"to_day": 18}, headers=lab_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-101", "requirement": "updated_income_verification"}, headers=agent_headers
    )
    # The upload itself persists (D-101 is a real document, no scripted
    # failure here) but it does not satisfy the Day-18 requirement.
    case = client.get("/portal/case", headers=agent_headers).json()
    assert "D-101" in case["received_document_ids"]
    assert "updated_income_verification" in case["open_requirements"]
    assert "EVT-updated-income-verified" not in world_state.get_applied_event_ids(session)


def test_d107_satisfies_the_updated_requirement(client, agent_headers, lab_headers, session):
    client.post("/lab/clock/advance", json={"to_day": 18}, headers=lab_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-107", "requirement": "updated_income_verification"}, headers=agent_headers
    )
    case = client.get("/portal/case", headers=agent_headers).json()
    assert "D-107" in case["received_document_ids"]
    assert "updated_income_verification" not in case["open_requirements"]
    assert "EVT-updated-income-verified" in world_state.get_applied_event_ids(session)


def test_reset_returns_to_original_day0_world(client, agent_headers, lab_headers, session):
    client.post("/lab/clock/advance", json={"to_day": 18}, headers=lab_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-107", "requirement": "updated_income_verification"}, headers=agent_headers
    )
    client.post("/lab/reset", headers=lab_headers)

    assert world_state.get_current_day(session) == 0
    files = client.get("/files", headers=agent_headers).json()
    assert {f["id"] for f in files} == {"D-101", "D-102", "D-103", "D-104", "D-105", "D-106"}
    case = client.get("/portal/case", headers=agent_headers).json()
    assert case["open_requirements"] == ["earned_income_verification"]
    assert case["received_document_ids"] == []


def test_document_view_endpoint_logs_a_structured_view_action(client, agent_headers, lab_headers, session):
    client.post("/lab/clock/advance", json={"to_day": 18}, headers=lab_headers)
    response = client.get("/files/D-107", headers=agent_headers)
    assert response.status_code == 200
    assert response.json()["id"] == "D-107"
    assert any(
        row.action_type == "view_document" for row in world_state.get_action_log(session)
    )


def test_new_paystub_content_makes_recency_inferable_without_hidden_tags(client, agent_headers, lab_headers):
    client.post("/lab/clock/advance", json={"to_day": 18}, headers=lab_headers)
    d101 = client.get("/files/D-101", headers=agent_headers).json()
    d107 = client.get("/files/D-107", headers=agent_headers).json()
    assert d107["date"] > d101["date"]
    assert "Golden State Logistics" in d107["visible_text"]
    assert d107["visible_text"] != d101["visible_text"]
