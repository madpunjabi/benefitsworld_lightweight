from app import evaluator_m4


def _income_and_interview(client, agent_headers, lab_headers, slot_id="SLOT-3"):
    client.post(
        "/portal/uploads", json={"document_id": "D-101", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    client.post(
        "/portal/uploads", json={"document_id": "D-103", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    client.post("/portal/interview/schedule", json={"slot_id": slot_id}, headers=agent_headers)
    client.post("/lab/clock/advance", json={"to_day": 4}, headers=lab_headers)


def test_evaluator_starts_all_false(client, session):
    result = evaluator_m4.evaluate(session)
    assert result["binary_success"] is False
    assert all(v is False for v in result["checkpoints"].values())


def test_evaluator_completes_m4_scope_but_not_overall_binary_success(client, agent_headers, lab_headers, session):
    """As of Milestone 5, binary_success requires the Day-18 phase too, so
    completing everything through Milestone 4 (income/interview/housing)
    is necessary but not sufficient — reflects the real end-to-end
    requirement, not a stale, weaker one. See test_evaluator_m5.py for the
    full Day-0-through-Day-18 success path."""
    _income_and_interview(client, agent_headers, lab_headers, slot_id="SLOT-3")  # nonconflicting
    client.post(
        "/portal/uploads", json={"document_id": "D-104", "requirement": "housing_cost_verification"}, headers=agent_headers
    )
    client.get("/portal/case", headers=agent_headers)  # re-observe after the silent failure
    client.post(
        "/portal/uploads", json={"document_id": "D-104", "requirement": "housing_cost_verification"}, headers=agent_headers
    )

    result = evaluator_m4.evaluate(session)
    assert result == {
        "binary_success": False,
        "checkpoints": {
            "income_evidence_completed": True,
            "interview_scheduled_nonconflicting": True,
            "housing_request_reached": True,
            "silent_failure_occurred": True,
            "agent_reobserved_after_failure": True,
            "d104_retried_successfully": True,
            "housing_requirement_cleared": True,
            "day18_employment_change_occurred": False,
            "updated_income_requirement_visible": False,
            "d107_inspected": False,
            "d107_persisted_against_requirement": False,
            "updated_income_requirement_cleared": False,
        },
    }


def test_evaluator_shows_progress_without_success_when_failure_unrecovered(
    client, agent_headers, lab_headers, session
):
    _income_and_interview(client, agent_headers, lab_headers, slot_id="SLOT-3")
    client.post(
        "/portal/uploads", json={"document_id": "D-104", "requirement": "housing_cost_verification"}, headers=agent_headers
    )
    # No retry, no re-observation.
    result = evaluator_m4.evaluate(session)
    assert result["binary_success"] is False
    assert result["checkpoints"]["income_evidence_completed"] is True
    assert result["checkpoints"]["interview_scheduled_nonconflicting"] is True
    assert result["checkpoints"]["housing_request_reached"] is True
    assert result["checkpoints"]["silent_failure_occurred"] is True
    assert result["checkpoints"]["agent_reobserved_after_failure"] is False
    assert result["checkpoints"]["d104_retried_successfully"] is False
    assert result["checkpoints"]["housing_requirement_cleared"] is False


def test_evaluator_flags_conflicting_interview_as_not_nonconflicting(client, agent_headers, lab_headers, session):
    _income_and_interview(client, agent_headers, lab_headers, slot_id="SLOT-2")  # the conflicting one
    result = evaluator_m4.evaluate(session)
    assert result["checkpoints"]["interview_scheduled_nonconflicting"] is False
    assert result["binary_success"] is False


def test_reobservation_checkpoint_requires_view_after_the_failure_not_before(
    client, agent_headers, lab_headers, session
):
    _income_and_interview(client, agent_headers, lab_headers)
    client.get("/portal/case", headers=agent_headers)  # a view BEFORE any failure exists
    assert evaluator_m4.agent_reobserved_after_failure(session) is False

    client.post(
        "/portal/uploads", json={"document_id": "D-104", "requirement": "housing_cost_verification"}, headers=agent_headers
    )
    assert evaluator_m4.agent_reobserved_after_failure(session) is False  # no view yet after the failure

    client.get("/portal/case", headers=agent_headers)
    assert evaluator_m4.agent_reobserved_after_failure(session) is True
