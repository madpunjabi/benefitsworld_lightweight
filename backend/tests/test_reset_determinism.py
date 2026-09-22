from app import reset, world_state


def test_reset_is_deterministic(client, session):
    snapshot_a = world_state.snapshot(session)

    # Mutate state.
    case = world_state.get_case(session)
    case.status = "SOME_OTHER_STATUS"
    session.commit()
    assert world_state.snapshot(session) != snapshot_a

    # Reset and capture again.
    reset.reset(session)
    snapshot_b = world_state.snapshot(session)

    assert snapshot_a == snapshot_b


def test_reset_twice_in_a_row_is_stable(client, session):
    reset.reset(session)
    first = world_state.snapshot(session)
    reset.reset(session)
    second = world_state.snapshot(session)
    assert first == second


def _run_full_m3_sequence(client, agent_headers, lab_headers):
    client.post(
        "/portal/uploads", json={"document_id": "D-101", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    client.post(
        "/portal/uploads", json={"document_id": "D-103", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    client.post("/portal/interview/schedule", json={"slot_id": "SLOT-3"}, headers=agent_headers)
    client.post("/lab/clock/advance", json={"to_day": 4}, headers=lab_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-104", "requirement": "housing_cost_verification"}, headers=agent_headers
    )


def test_reset_determinism_across_the_full_event_sequence(client, agent_headers, lab_headers, session):
    _run_full_m3_sequence(client, agent_headers, lab_headers)
    snapshot_a = world_state.snapshot(session)
    assert snapshot_a["case"]["open_requirements"] == []
    assert snapshot_a["case"]["interview"]["status"] == "completed"

    client.post("/lab/reset", headers=lab_headers)
    _run_full_m3_sequence(client, agent_headers, lab_headers)
    snapshot_b = world_state.snapshot(session)

    assert snapshot_a == snapshot_b
