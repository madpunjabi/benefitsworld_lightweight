from app import world_state


def _reach_housing_phase(client, agent_headers, lab_headers):
    client.post(
        "/portal/uploads", json={"document_id": "D-101", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    client.post(
        "/portal/uploads", json={"document_id": "D-103", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    client.post("/portal/interview/schedule", json={"slot_id": "SLOT-1"}, headers=agent_headers)
    client.post("/lab/clock/advance", json={"to_day": 3}, headers=lab_headers)


def test_first_qualifying_d104_upload_does_not_persist(client, agent_headers, lab_headers, session):
    _reach_housing_phase(client, agent_headers, lab_headers)
    response = client.post(
        "/portal/uploads", json={"document_id": "D-104", "requirement": "housing_cost_verification"}, headers=agent_headers
    )
    # The response body claims ordinary success either way (that's the point).
    assert response.status_code == 200
    assert response.json() == {"document_id": "D-104", "requirement": "housing_cost_verification", "received": True}

    upload = world_state.get_uploads(session)[-1]
    assert upload.ui_reported_success == 1
    assert upload.actually_persisted == 0
    assert upload.scripted_failure_id == "FAIL-first-current-lease-upload"


def test_housing_requirement_does_not_clear_after_first_attempt(client, agent_headers, lab_headers, session):
    _reach_housing_phase(client, agent_headers, lab_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-104", "requirement": "housing_cost_verification"}, headers=agent_headers
    )
    case = client.get("/portal/case", headers=agent_headers).json()
    assert "housing_cost_verification" in case["open_requirements"]
    assert "D-104" not in case["received_document_ids"]
    assert "EVT-housing-verified" not in world_state.get_applied_event_ids(session)


def test_second_d104_upload_persists_and_clears_requirement(client, agent_headers, lab_headers, session):
    _reach_housing_phase(client, agent_headers, lab_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-104", "requirement": "housing_cost_verification"}, headers=agent_headers
    )
    response = client.post(
        "/portal/uploads", json={"document_id": "D-104", "requirement": "housing_cost_verification"}, headers=agent_headers
    )
    assert response.status_code == 200

    upload = world_state.get_uploads(session)[-1]
    assert upload.ui_reported_success == 1
    assert upload.actually_persisted == 1
    assert upload.scripted_failure_id is None

    case = client.get("/portal/case", headers=agent_headers).json()
    assert "D-104" in case["received_document_ids"]
    assert "housing_cost_verification" not in case["open_requirements"]
    assert "EVT-housing-verified" in world_state.get_applied_event_ids(session)


def test_third_d104_upload_is_ordinary_and_duplicate_safe(client, agent_headers, lab_headers, session):
    _reach_housing_phase(client, agent_headers, lab_headers)
    for _ in range(3):
        client.post(
            "/portal/uploads", json={"document_id": "D-104", "requirement": "housing_cost_verification"}, headers=agent_headers
        )
    upload = world_state.get_uploads(session)[-1]
    assert upload.actually_persisted == 1
    assert upload.scripted_failure_id is None
    case = client.get("/portal/case", headers=agent_headers).json()
    assert case["received_document_ids"].count("D-104") == 1


def test_d105_upload_does_not_consume_the_d104_failure(client, agent_headers, lab_headers, session):
    _reach_housing_phase(client, agent_headers, lab_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-105", "requirement": "housing_cost_verification"}, headers=agent_headers
    )
    failure = next(f for f in world_state.get_silent_failures(session) if f.id == "FAIL-first-current-lease-upload")
    assert failure.consumed == 0

    # D-104's first attempt still hits the scripted failure afterward.
    client.post(
        "/portal/uploads", json={"document_id": "D-104", "requirement": "housing_cost_verification"}, headers=agent_headers
    )
    assert "D-104" not in client.get("/portal/case", headers=agent_headers).json()["received_document_ids"]


def test_wrong_requirement_upload_does_not_consume_the_failure(client, agent_headers, lab_headers, session):
    _reach_housing_phase(client, agent_headers, lab_headers)
    # D-104 uploaded against a requirement it isn't scripted for persists
    # normally (it's simply not the scripted pairing) and so legitimately
    # appears in the flat received_document_ids list — that list isn't
    # requirement-scoped. What matters here is that housing_cost_verification
    # itself is unaffected and the scripted failure is still armed.
    client.post(
        "/portal/uploads", json={"document_id": "D-104", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    failure = next(f for f in world_state.get_silent_failures(session) if f.id == "FAIL-first-current-lease-upload")
    assert failure.consumed == 0

    client.post(
        "/portal/uploads", json={"document_id": "D-104", "requirement": "housing_cost_verification"}, headers=agent_headers
    )
    case = client.get("/portal/case", headers=agent_headers).json()
    assert "housing_cost_verification" in case["open_requirements"]
    assert "EVT-housing-verified" not in world_state.get_applied_event_ids(session)


def test_reset_restores_the_unfired_failure(client, agent_headers, lab_headers, session):
    _reach_housing_phase(client, agent_headers, lab_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-104", "requirement": "housing_cost_verification"}, headers=agent_headers
    )
    failure = next(f for f in world_state.get_silent_failures(session) if f.id == "FAIL-first-current-lease-upload")
    assert failure.consumed == 1

    client.post("/lab/reset", headers=lab_headers)
    # /lab/reset runs on its own request-scoped session; this test's
    # `session` fixture is a separate SQLAlchemy Session whose identity map
    # still holds the pre-reset row unless explicitly expired.
    session.expire_all()
    failure = next(f for f in world_state.get_silent_failures(session) if f.id == "FAIL-first-current-lease-upload")
    assert failure.consumed == 0

    # And it fires identically on replay.
    _reach_housing_phase(client, agent_headers, lab_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-104", "requirement": "housing_cost_verification"}, headers=agent_headers
    )
    upload = world_state.get_uploads(session)[-1]
    assert upload.actually_persisted == 0
    assert upload.scripted_failure_id == "FAIL-first-current-lease-upload"
