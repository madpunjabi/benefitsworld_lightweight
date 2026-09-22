def test_policy_search_with_no_query_returns_all_items(client, agent_headers):
    response = client.get("/policy/search", headers=agent_headers)
    assert response.status_code == 200
    assert {i["id"] for i in response.json()} == {"POL-001", "POL-002", "POL-003"}


def test_policy_search_finds_income_verification_item(client, agent_headers):
    response = client.get("/policy/search", params={"q": "income verification"}, headers=agent_headers)
    assert response.status_code == 200
    ids = {i["id"] for i in response.json()}
    assert "POL-001" in ids


def test_policy_search_finds_employment_change_item(client, agent_headers):
    response = client.get("/policy/search", params={"q": "change in employment"}, headers=agent_headers)
    assert response.status_code == 200
    ids = {i["id"] for i in response.json()}
    assert "POL-003" in ids


def test_policy_item_detail_returns_full_text(client, agent_headers):
    response = client.get("/policy/POL-001", headers=agent_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Responding to an Income Verification Request"
    assert len(body["text"]) > 0


def test_policy_item_not_found(client, agent_headers):
    response = client.get("/policy/POL-999", headers=agent_headers)
    assert response.status_code == 404
