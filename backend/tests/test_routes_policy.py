def test_policy_search_with_no_query_returns_all_items(client, agent_headers):
    response = client.get("/policy/search", headers=agent_headers)
    assert response.status_code == 200
    assert {i["id"] for i in response.json()} == {"POL-001", "POL-002", "POL-003", "POL-004", "POL-005"}


def test_policy_search_finds_income_change_reporting_item(client, agent_headers):
    response = client.get("/policy/search", params={"q": "change in earned income"}, headers=agent_headers)
    assert response.status_code == 200
    ids = {i["id"] for i in response.json()}
    assert "POL-002" in ids


def test_policy_search_finds_proof_of_earned_income_item(client, agent_headers):
    response = client.get("/policy/search", params={"q": "proof of earned income"}, headers=agent_headers)
    assert response.status_code == 200
    ids = {i["id"] for i in response.json()}
    assert "POL-003" in ids


def test_policy_item_detail_returns_full_text(client, agent_headers):
    response = client.get("/policy/POL-001", headers=agent_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == (
        "SAR 7 Eligibility Status Report Instructions (SAR 7A, 12/23) — "
        "Reviewing and Updating Pre-Populated Information"
    )
    assert body["source"] == "California Department of Social Services"
    assert body["jurisdiction"] == "California"
    # Milestone 2.1 -> 2.1 correction (Milestone 3, section 1): "12/23" is
    # the form's own revision label, not an established effective date.
    assert body["effective_date"] is None
    assert body["source_version"] == "12/23"
    assert body["source_url"] == (
        "https://www.cdss.ca.gov/Portals/9/Additional-Resources/Forms-and-Brochures/"
        "2020/Q-T/SAR7A.pdf?ver=2024-02-02-110154-403"
    )
    assert len(body["text"]) > 0


def test_policy_search_finds_housing_costs_item(client, agent_headers):
    response = client.get("/policy/search", params={"q": "housing costs"}, headers=agent_headers)
    assert response.status_code == 200
    ids = {i["id"] for i in response.json()}
    assert "POL-004" in ids


def test_policy_item_interview_guidance_is_real_and_sourced(client, agent_headers):
    response = client.get("/policy/POL-005", headers=agent_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "CF 37 (11/16): Recertification for CalFresh Benefits — What Happens at the Interview"
    assert body["source"] == "California Department of Social Services"
    assert body["source_url"] == "https://www.cdss.ca.gov/cdssweb/entres/forms/english/cf37.pdf"
    assert body["effective_date"] is None
    assert body["source_version"] == "11/16"
    assert "interview appointment letter" in body["text"]


def test_policy_item_proof_text_matches_source_verbatim(client, agent_headers):
    response = client.get("/policy/POL-003", headers=agent_headers)
    assert response.status_code == 200
    text = response.json()["text"]
    assert "check stubs" in text
    assert "letter from the employer or a signed written statement" in text


def test_policy_item_not_found(client, agent_headers):
    response = client.get("/policy/POL-999", headers=agent_headers)
    assert response.status_code == 404
