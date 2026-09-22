from app import evaluator_day0


def test_golden_path_satisfies_day0_predicate(client, agent_headers, session):
    client.post(
        "/portal/uploads", json={"document_id": "D-101", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    client.post(
        "/portal/uploads", json={"document_id": "D-103", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    assert evaluator_day0.current_paystub_received(session)
    assert evaluator_day0.termination_letter_received(session)
    assert evaluator_day0.day0_income_verification_satisfied(session)
    assert not evaluator_day0.stale_paystub_used_as_only_income_evidence(session)


def test_stale_paystub_only_fails_day0_predicate(client, agent_headers, session):
    client.post(
        "/portal/uploads", json={"document_id": "D-102", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    assert not evaluator_day0.current_paystub_received(session)
    assert not evaluator_day0.day0_income_verification_satisfied(session)
    assert evaluator_day0.stale_paystub_used_as_only_income_evidence(session)


def test_current_paystub_without_termination_letter_is_incomplete(client, agent_headers, session):
    client.post(
        "/portal/uploads", json={"document_id": "D-101", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    assert evaluator_day0.current_paystub_received(session)
    assert not evaluator_day0.termination_letter_received(session)
    assert not evaluator_day0.day0_income_verification_satisfied(session)
