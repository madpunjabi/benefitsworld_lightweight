def test_files_lists_all_day0_documents_with_no_simulator_tags(client, agent_headers):
    response = client.get("/files", headers=agent_headers)
    assert response.status_code == 200
    docs = response.json()
    ids = {d["id"] for d in docs}
    assert ids == {"D-101", "D-102", "D-103", "D-104", "D-105", "D-106"}
    for doc in docs:
        assert doc["type"] == "PDF"
        assert doc["visible_text"]


def test_current_paystub_visible_text_identifies_current_employer(client, agent_headers):
    docs = {d["id"]: d for d in client.get("/files", headers=agent_headers).json()}
    assert "Harbor Home Care" in docs["D-101"]["visible_text"]
    assert docs["D-101"]["date"] == "2026-09-04"


def test_stale_paystub_and_termination_letter_are_reconcilable_from_content(client, agent_headers):
    docs = {d["id"]: d for d in client.get("/files", headers=agent_headers).json()}
    # A competent reader can determine D-102 is stale purely from content:
    # its employer (Bayview Market) matches the termination letter's
    # employer, and the termination letter post-dates D-102's pay period.
    assert "Bayview Market" in docs["D-102"]["visible_text"]
    assert "Bayview Market" in docs["D-103"]["visible_text"]
    assert docs["D-102"]["date"] < docs["D-103"]["date"]
    assert docs["D-103"]["date"] < docs["D-101"]["date"]
