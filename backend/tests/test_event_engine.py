from app import event_engine, world_state


def _upload_income_evidence(client, agent_headers):
    client.post(
        "/portal/uploads", json={"document_id": "D-101", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    client.post(
        "/portal/uploads", json={"document_id": "D-103", "requirement": "earned_income_verification"}, headers=agent_headers
    )


def test_income_verified_event_applies_exactly_once(client, agent_headers, session):
    _upload_income_evidence(client, agent_headers)
    applied_ids = world_state.get_applied_event_ids(session)
    assert applied_ids.count("EVT-income-verified") == 1
    assert "earned_income_verification" not in world_state.get_open_requirements(session)
    assert "interview" in world_state.get_open_requirements(session)
    assert len(world_state.get_interview_slots(session)) == 3
    assert len(world_state.get_notices(session)) == 2  # Day-0 seed notice + interview notice


def test_income_verified_event_does_not_reapply_on_extra_ticks(client, agent_headers, session):
    _upload_income_evidence(client, agent_headers)
    engine = event_engine.default_engine()
    engine.tick(session)
    engine.tick(session)
    engine.tick(session)
    # Idempotence: repeated ticks must not duplicate notices, requirements, or slots.
    assert world_state.get_open_requirements(session).count("interview") == 1
    assert len(world_state.get_interview_slots(session)) == 3
    assert len(world_state.get_notices(session)) == 2
    assert world_state.get_applied_event_ids(session).count("EVT-income-verified") == 1


def test_stale_paystub_alone_does_not_trigger_income_verified(client, agent_headers, session):
    client.post(
        "/portal/uploads", json={"document_id": "D-102", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    assert "EVT-income-verified" not in world_state.get_applied_event_ids(session)
    assert "earned_income_verification" in world_state.get_open_requirements(session)
    assert "interview" not in world_state.get_open_requirements(session)
    assert world_state.get_interview_slots(session) == []


def test_stale_paystub_alongside_current_still_triggers(client, agent_headers, session):
    # Uploading the stale paystub in addition to the correct evidence
    # should not block the event — only D-101 and D-103 are required.
    client.post(
        "/portal/uploads", json={"document_id": "D-102", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    _upload_income_evidence(client, agent_headers)
    assert "EVT-income-verified" in world_state.get_applied_event_ids(session)


def test_full_chain_income_to_housing_via_time_advance(client, agent_headers, lab_headers, session):
    _upload_income_evidence(client, agent_headers)
    assert "EVT-income-verified" in world_state.get_applied_event_ids(session)

    client.post("/portal/interview/schedule", json={"slot_id": "SLOT-1"}, headers=agent_headers)
    assert world_state.get_interview(session)["status"] == "scheduled"
    assert "EVT-interview-completed" not in world_state.get_applied_event_ids(session)

    # SLOT-1 is on day 2; advancing to day 3 should complete it and, within
    # the same tick, chain into EVT-housing-request (fixed-point tick loop).
    client.post("/lab/clock/advance", json={"to_day": 3}, headers=lab_headers)

    applied = world_state.get_applied_event_ids(session)
    assert "EVT-interview-completed" in applied
    assert "EVT-housing-request" in applied
    assert world_state.get_interview(session)["status"] == "completed"
    assert "interview" not in world_state.get_open_requirements(session)
    assert "housing_cost_verification" in world_state.get_open_requirements(session)
    assert len(world_state.get_inbox_messages(session)) == 1


def test_housing_verified_requires_current_lease(client, agent_headers, lab_headers, session):
    _upload_income_evidence(client, agent_headers)
    client.post("/portal/interview/schedule", json={"slot_id": "SLOT-1"}, headers=agent_headers)
    client.post("/lab/clock/advance", json={"to_day": 3}, headers=lab_headers)

    client.post(
        "/portal/uploads", json={"document_id": "D-105", "requirement": "housing_cost_verification"}, headers=agent_headers
    )
    assert "EVT-housing-verified" not in world_state.get_applied_event_ids(session)
    assert "housing_cost_verification" in world_state.get_open_requirements(session)

    # The first D-104 attempt hits the scripted silent failure (Milestone
    # 4) and does not persist; the second does.
    client.post(
        "/portal/uploads", json={"document_id": "D-104", "requirement": "housing_cost_verification"}, headers=agent_headers
    )
    assert "EVT-housing-verified" not in world_state.get_applied_event_ids(session)
    client.post(
        "/portal/uploads", json={"document_id": "D-104", "requirement": "housing_cost_verification"}, headers=agent_headers
    )
    assert "EVT-housing-verified" in world_state.get_applied_event_ids(session)
    assert "housing_cost_verification" not in world_state.get_open_requirements(session)
