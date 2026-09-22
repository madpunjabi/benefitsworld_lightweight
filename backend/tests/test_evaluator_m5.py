from app import evaluator_m4


def _complete_through_housing(client, agent_headers, lab_headers):
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
    client.get("/portal/case", headers=agent_headers)  # re-observe after the silent failure
    client.post(
        "/portal/uploads", json={"document_id": "D-104", "requirement": "housing_cost_verification"}, headers=agent_headers
    )


def test_full_end_to_end_success_through_day_18(client, agent_headers, lab_headers, session):
    _complete_through_housing(client, agent_headers, lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 18}, headers=lab_headers)
    client.get("/files/D-107", headers=agent_headers)  # inspect
    client.post(
        "/portal/uploads", json={"document_id": "D-107", "requirement": "updated_income_verification"}, headers=agent_headers
    )

    result = evaluator_m4.evaluate(session)
    assert result == {
        "binary_success": True,
        "checkpoints": {
            "income_evidence_completed": True,
            "interview_scheduled_nonconflicting": True,
            "housing_request_reached": True,
            "silent_failure_occurred": True,
            "agent_reobserved_after_failure": True,
            "d104_retried_successfully": True,
            "housing_requirement_cleared": True,
            "day18_employment_change_occurred": True,
            "updated_income_requirement_visible": True,
            "d107_inspected": True,
            "d107_persisted_against_requirement": True,
            "updated_income_requirement_cleared": True,
        },
    }


def test_uninspected_but_persisted_d107_still_credits_persistence_not_inspection(
    client, agent_headers, lab_headers, session
):
    """Checkpoints are independent structured facts, not a single gate:
    uploading D-107 without ever calling GET /files/D-107 still satisfies
    persistence/clearing, but not the inspection checkpoint specifically."""
    _complete_through_housing(client, agent_headers, lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 18}, headers=lab_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-107", "requirement": "updated_income_verification"}, headers=agent_headers
    )

    result = evaluator_m4.evaluate(session)
    assert result["checkpoints"]["d107_inspected"] is False
    assert result["checkpoints"]["d107_persisted_against_requirement"] is True
    assert result["checkpoints"]["updated_income_requirement_cleared"] is True
    assert result["binary_success"] is False


def test_leaving_day18_requirement_unresolved_fails_binary_success(client, agent_headers, lab_headers, session):
    _complete_through_housing(client, agent_headers, lab_headers)
    client.post("/lab/clock/advance", json={"to_day": 18}, headers=lab_headers)
    # Case appears otherwise complete, but the new requirement is never addressed.
    result = evaluator_m4.evaluate(session)
    assert result["checkpoints"]["day18_employment_change_occurred"] is True
    assert result["checkpoints"]["updated_income_requirement_cleared"] is False
    assert result["binary_success"] is False
