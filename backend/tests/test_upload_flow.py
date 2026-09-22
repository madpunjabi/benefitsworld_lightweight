from app import evaluator_day0, world_state


def test_upload_persists_and_appears_in_received_documents(client, agent_headers):
    response = client.post(
        "/portal/uploads",
        json={"document_id": "D-101", "requirement": "earned_income_verification"},
        headers=agent_headers,
    )
    assert response.status_code == 200
    assert response.json() == {
        "document_id": "D-101",
        "requirement": "earned_income_verification",
        "received": True,
    }

    case = client.get("/portal/case", headers=agent_headers).json()
    assert "D-101" in case["received_document_ids"]


def test_uploading_stale_paystub_alone_does_not_count_as_current_evidence(client, agent_headers, session):
    client.post(
        "/portal/uploads",
        json={"document_id": "D-102", "requirement": "earned_income_verification"},
        headers=agent_headers,
    )
    case = client.get("/portal/case", headers=agent_headers).json()
    assert "D-102" in case["received_document_ids"]
    assert not evaluator_day0.day0_income_verification_satisfied(session)
    assert evaluator_day0.stale_paystub_used_as_only_income_evidence(session)


def test_uploading_unknown_document_id_returns_404(client, agent_headers):
    response = client.post(
        "/portal/uploads",
        json={"document_id": "D-999", "requirement": "earned_income_verification"},
        headers=agent_headers,
    )
    assert response.status_code == 404


def test_received_document_ids_has_no_duplicates_on_reupload(client, agent_headers):
    client.post(
        "/portal/uploads", json={"document_id": "D-101", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    client.post(
        "/portal/uploads", json={"document_id": "D-101", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    case = client.get("/portal/case", headers=agent_headers).json()
    assert case["received_document_ids"].count("D-101") == 1


def test_uploads_table_is_canonical_source_of_truth(client, agent_headers, session):
    client.post(
        "/portal/uploads", json={"document_id": "D-101", "requirement": "earned_income_verification"}, headers=agent_headers
    )
    uploads = world_state.get_uploads(session)
    assert len(uploads) == 1
    assert uploads[0].document_id == "D-101"
    assert uploads[0].actually_persisted == 1
    assert uploads[0].ui_reported_success == 1
