def test_portal_case_reflects_day0_state(client, agent_headers):
    response = client.get("/portal/case", headers=agent_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["case_id"] == "CF-ALM-10482"
    assert body["status"] == "PENDING"
    assert body["open_requirements"] == ["earned_income_verification"]
    assert body["reported_employer"] == "Bayview Market"
    assert body["received_document_ids"] == []


def test_portal_notices_reflect_open_requirement(client, agent_headers):
    response = client.get("/portal/notices", headers=agent_headers)
    assert response.status_code == 200
    notices = response.json()
    assert len(notices) == 1
    assert "Income Verification" in notices[0]["text"] or "income verification" in notices[0]["text"].lower()
