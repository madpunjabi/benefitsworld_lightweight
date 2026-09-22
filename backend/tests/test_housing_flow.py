from app import evaluator_m3, world_state


def _complete_interview(client, agent_headers, lab_headers, slot_id="SLOT-1"):
    client.post(
        "/portal/uploads", json={"document_id": "D-101", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    client.post(
        "/portal/uploads", json={"document_id": "D-103", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    client.post("/portal/interview/schedule", json={"slot_id": slot_id}, headers=agent_headers)
    client.post("/lab/clock/advance", json={"to_day": 3}, headers=lab_headers)


def test_housing_request_does_not_appear_before_interview_completes(client, agent_headers, session):
    client.post(
        "/portal/uploads", json={"document_id": "D-101", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    client.post(
        "/portal/uploads", json={"document_id": "D-103", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    assert "housing_cost_verification" not in world_state.get_open_requirements(session)
    assert world_state.get_inbox_messages(session) == []
    assert not evaluator_m3.housing_request_appeared(session)


def test_housing_request_appears_exactly_once_after_interview_completes(client, agent_headers, lab_headers, session):
    _complete_interview(client, agent_headers, lab_headers)
    assert world_state.get_open_requirements(session).count("housing_cost_verification") == 1
    assert len(world_state.get_inbox_messages(session)) == 1

    # Extra ticks / a no-op time advance must not duplicate it.
    client.post("/lab/clock/advance", json={"to_day": 4}, headers=lab_headers)
    assert world_state.get_open_requirements(session).count("housing_cost_verification") == 1
    assert len(world_state.get_inbox_messages(session)) == 1
    assert world_state.get_applied_event_ids(session).count("EVT-housing-request") == 1


def test_housing_message_reads_like_correspondence_not_instructions(client, agent_headers, lab_headers, session):
    _complete_interview(client, agent_headers, lab_headers)
    messages = client.get("/inbox/messages", headers=agent_headers).json()
    assert len(messages) == 1
    message = messages[0]
    assert message["sender"] == "Alameda County Human Services Agency"
    assert message["subject"] == "Proof of Housing Costs Needed"
    assert message["is_read"] is False
    forbidden = ["d-104", "d-105", "simulator", "checkpoint", "benchmark"]
    body_lower = message["body"].lower()
    for word in forbidden:
        assert word not in body_lower
    assert evaluator_m3.housing_message_visible(session)


def test_inbox_message_can_be_marked_read(client, agent_headers, lab_headers):
    _complete_interview(client, agent_headers, lab_headers)
    message_id = client.get("/inbox/messages", headers=agent_headers).json()[0]["id"]
    response = client.post(f"/inbox/messages/{message_id}/read", headers=agent_headers)
    assert response.status_code == 200
    assert response.json()["is_read"] is True
    messages = client.get("/inbox/messages", headers=agent_headers).json()
    assert messages[0]["is_read"] is True


def test_current_lease_satisfies_housing_requirement(client, agent_headers, lab_headers, session):
    _complete_interview(client, agent_headers, lab_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-104", "requirement": "housing_cost_verification"}, headers=agent_headers
    )
    assert evaluator_m3.current_lease_uploaded(session)
    assert evaluator_m3.housing_requirement_cleared(session)
    assert "housing_cost_verification" not in world_state.get_open_requirements(session)


def test_expired_lease_does_not_satisfy_housing_requirement(client, agent_headers, lab_headers, session):
    _complete_interview(client, agent_headers, lab_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-105", "requirement": "housing_cost_verification"}, headers=agent_headers
    )
    assert not evaluator_m3.current_lease_uploaded(session)
    assert not evaluator_m3.housing_requirement_cleared(session)
    assert evaluator_m3.stale_lease_used_as_only_evidence(session)
    assert "housing_cost_verification" in world_state.get_open_requirements(session)

    # Received, though — uploads always persist in Milestone 3.
    case = client.get("/portal/case", headers=agent_headers).json()
    assert "D-105" in case["received_document_ids"]
    assert "D-104" not in case["received_document_ids"]
