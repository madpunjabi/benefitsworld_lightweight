from app import world_state
from tests.conftest import reset_bw002


def test_interview_overdue_at_day5_if_never_scheduled(client, lab_headers, session):
    reset_bw002(client, lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 5}, headers=lab_headers)
    assert "EVT-BW002-interview-overdue" in world_state.get_applied_event_ids(session)
    assert world_state.get_case(session).status == "PENDING"  # not closed
    messages = world_state.get_inbox_messages(session)
    assert any(m.subject == "Interview Overdue" for m in messages)


def test_interview_overdue_does_not_fire_once_scheduled_on_time(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    client.post("/portal/interview/schedule", json={"slot_id": "BW2-SLOT-1"}, headers=agent_headers)  # day 0
    client.post("/lab/clock/advance", json={"to_day": 5}, headers=lab_headers)
    assert "EVT-BW002-interview-overdue" not in world_state.get_applied_event_ids(session)


def test_interview_checkpoint_true_when_scheduled_and_completed_on_time(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    client.post("/portal/interview/schedule", json={"slot_id": "BW2-SLOT-1"}, headers=agent_headers)  # day 2
    client.post("/lab/clock/advance", json={"to_day": 5}, headers=lab_headers)  # completes (5 > 2)
    result = client.get("/lab/evaluate", headers=lab_headers).json()
    assert result["checkpoints"]["interview_scheduled_and_completed"] is True


def test_interview_checkpoint_false_when_scheduled_late_even_if_later_completed(client, agent_headers, lab_headers, session):
    """The interview is genuinely completed, but only because it was
    scheduled after the Day-5 deadline had already passed — the
    checkpoint must still be False."""
    reset_bw002(client, lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 6}, headers=lab_headers)  # deadline missed, overdue fires
    client.post("/portal/interview/schedule", json={"slot_id": "BW2-SLOT-2"}, headers=agent_headers)  # scheduled at day 6
    assert "EVT-BW002-interview-completed" in world_state.get_applied_event_ids(session)  # genuinely completes
    result = client.get("/lab/evaluate", headers=lab_headers).json()
    assert result["checkpoints"]["interview_scheduled_and_completed"] is False


def test_income_overdue_at_day7_if_unresolved(client, lab_headers, session):
    reset_bw002(client, lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 7}, headers=lab_headers)
    assert "EVT-BW002-income-overdue" in world_state.get_applied_event_ids(session)
    assert world_state.get_case(session).status == "PENDING"  # not closed
    messages = world_state.get_inbox_messages(session)
    assert any(m.subject == "Income Verification Overdue" for m in messages)


def test_income_overdue_does_not_fire_once_resolved_on_time(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-201", "requirement": "income_verification"}, headers=agent_headers
    )
    client.post(
        "/portal/uploads", json={"document_id": "D-203", "requirement": "income_verification"}, headers=agent_headers
    )
    client.post("/lab/clock/advance", json={"to_day": 7}, headers=lab_headers)
    assert "EVT-BW002-income-overdue" not in world_state.get_applied_event_ids(session)


def test_income_checkpoint_true_when_resolved_on_time(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-201", "requirement": "income_verification"}, headers=agent_headers
    )
    client.post(
        "/portal/uploads", json={"document_id": "D-203", "requirement": "income_verification"}, headers=agent_headers
    )
    client.post("/lab/clock/advance", json={"to_day": 7}, headers=lab_headers)
    result = client.get("/lab/evaluate", headers=lab_headers).json()
    assert result["checkpoints"]["initial_income_verification_resolved_correctly"] is True


def test_income_checkpoint_false_when_resolved_late_even_if_eventually_correct(client, agent_headers, lab_headers, session):
    """income_verification genuinely clears, but only after the Day-7
    deadline had already passed — the checkpoint must still be False."""
    reset_bw002(client, lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 7}, headers=lab_headers)  # deadline missed, overdue fires
    client.post(
        "/portal/uploads", json={"document_id": "D-201", "requirement": "income_verification"}, headers=agent_headers
    )
    client.post(
        "/portal/uploads", json={"document_id": "D-203", "requirement": "income_verification"}, headers=agent_headers
    )
    assert "EVT-BW002-income-verified" in world_state.get_applied_event_ids(session)  # genuinely resolves
    result = client.get("/lab/evaluate", headers=lab_headers).json()
    assert result["checkpoints"]["initial_income_verification_resolved_correctly"] is False


def test_other_bw002_mechanics_unaffected_by_the_deadline_patch(client, agent_headers, lab_headers, session):
    """Everything preserved unchanged: Day-6 housing rejection, Day-8
    employment change, Day-10/11/14 downstream deadlines, and a full
    on-time golden path still reaches binary_success."""
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
    client.get("/files/D-201", headers=agent_headers)
    client.post("/lab/clock/advance", json={"to_day": 3}, headers=lab_headers)
    client.post("/portal/recertification/submit", headers=agent_headers)

    client.post("/lab/clock/advance", json={"to_day": 6}, headers=lab_headers)
    client.get("/files/D-208", headers=agent_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-208", "requirement": "housing_correction"}, headers=agent_headers
    )

    client.post("/lab/clock/advance", json={"to_day": 8}, headers=lab_headers)
    client.get("/files/D-209", headers=agent_headers)
    client.post(
        "/portal/uploads",
        json={"document_id": "D-209", "requirement": "updated_income_verification"},
        headers=agent_headers,
    )
    client.post("/portal/recertification/submit", headers=agent_headers)
    client.post("/lab/clock/advance", json={"to_day": 14}, headers=lab_headers)

    applied = world_state.get_applied_event_ids(session)
    assert "EVT-BW002-housing-rejected" in applied
    assert "EVT-BW002-employment-change" in applied
    assert "EVT-BW002-housing-correction-overdue" not in applied
    assert "EVT-BW002-updated-income-overdue" not in applied
    assert "EVT-BW002-recertification-deadline-missed" not in applied
    assert "EVT-BW002-interview-overdue" not in applied
    assert "EVT-BW002-income-overdue" not in applied
    assert world_state.get_case(session).status == "PENDING"

    result = client.get("/lab/evaluate", headers=lab_headers).json()
    assert all(result["checkpoints"].values()), result["checkpoints"]
    assert result["binary_success"] is True
