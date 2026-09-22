from app import evaluator_m3, world_state


def _unlock_interview(client, agent_headers):
    client.post(
        "/portal/uploads", json={"document_id": "D-101", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    client.post(
        "/portal/uploads", json={"document_id": "D-103", "requirement": "earned_income_verification"}, headers=agent_headers
    )


def test_interview_slots_include_one_conflicting_and_two_nonconflicting(client, agent_headers):
    _unlock_interview(client, agent_headers)
    slots = client.get("/portal/interview/slots", headers=agent_headers).json()
    by_id = {s["id"]: s for s in slots}
    assert by_id["SLOT-1"] == {"id": "SLOT-1", "day": 2, "start_time": "09:00", "end_time": "10:00"}
    assert by_id["SLOT-2"] == {"id": "SLOT-2", "day": 3, "start_time": "10:30", "end_time": "11:30"}
    assert by_id["SLOT-3"] == {"id": "SLOT-3", "day": 3, "start_time": "13:30", "end_time": "14:30"}
    # No conflict/label/"expected" hint anywhere in the response.
    for slot in slots:
        assert set(slot.keys()) == {"id", "day", "start_time", "end_time"}


def test_scheduling_a_conflicting_slot_is_technically_allowed(client, agent_headers, session):
    _unlock_interview(client, agent_headers)
    response = client.post("/portal/interview/schedule", json={"slot_id": "SLOT-2"}, headers=agent_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "scheduled"
    # The scheduling surface does not reject or flag this — the checkpoint
    # helper (research-only) is what can tell it conflicts.
    assert evaluator_m3.selected_interview_conflicts_with_household_calendar(session) is True


def test_scheduling_a_nonconflicting_slot(client, agent_headers, session):
    _unlock_interview(client, agent_headers)
    client.post("/portal/interview/schedule", json={"slot_id": "SLOT-3"}, headers=agent_headers)
    assert evaluator_m3.selected_interview_conflicts_with_household_calendar(session) is False


def test_scheduling_unknown_slot_404s(client, agent_headers):
    _unlock_interview(client, agent_headers)
    response = client.post("/portal/interview/schedule", json={"slot_id": "SLOT-999"}, headers=agent_headers)
    assert response.status_code == 404


def test_scheduling_persists_and_is_visible_on_revisit(client, agent_headers):
    _unlock_interview(client, agent_headers)
    client.post("/portal/interview/schedule", json={"slot_id": "SLOT-1"}, headers=agent_headers)
    case = client.get("/portal/case", headers=agent_headers).json()
    assert case["interview"] == {
        "status": "scheduled",
        "slot_id": "SLOT-1",
        "day": 2,
        "start_time": "09:00",
        "end_time": "10:00",
    }


def test_scheduling_does_not_immediately_complete_interview(client, agent_headers, session):
    _unlock_interview(client, agent_headers)
    client.post("/portal/interview/schedule", json={"slot_id": "SLOT-1"}, headers=agent_headers)
    assert world_state.get_interview(session)["status"] == "scheduled"
    assert not evaluator_m3.interview_completed_after_time(session)


def test_advancing_past_scheduled_day_completes_interview(client, agent_headers, lab_headers, session):
    _unlock_interview(client, agent_headers)
    client.post("/portal/interview/schedule", json={"slot_id": "SLOT-1"}, headers=agent_headers)  # day 2

    client.post("/lab/clock/advance", json={"to_day": 2}, headers=lab_headers)
    assert world_state.get_interview(session)["status"] == "scheduled"  # not yet past day 2

    client.post("/lab/clock/advance", json={"to_day": 3}, headers=lab_headers)
    assert world_state.get_interview(session)["status"] == "completed"
    assert evaluator_m3.interview_completed_after_time(session)


def test_checkpoint_helpers_track_lifecycle(client, agent_headers, lab_headers, session):
    assert not evaluator_m3.interview_requirement_appeared(session)
    assert evaluator_m3.calendar_available_to_inspect(session)
    assert not evaluator_m3.interview_scheduled_persisted(session)

    _unlock_interview(client, agent_headers)
    assert evaluator_m3.interview_requirement_appeared(session)
    assert evaluator_m3.income_requirement_satisfied(session)

    client.post("/portal/interview/schedule", json={"slot_id": "SLOT-3"}, headers=agent_headers)
    assert evaluator_m3.interview_scheduled_persisted(session)
