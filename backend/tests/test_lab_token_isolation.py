from app import config
from app.main import app


def _lab_get_paths() -> list[str]:
    paths = []
    for route in app.router.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", set()) or set()
        if path.startswith("/lab") and "GET" in methods:
            paths.append(path)
    return paths


def test_every_lab_route_is_enumerated_and_nonempty():
    # Guards against silently forgetting to add new lab routes to this
    # test as the lab router grows in later milestones.
    assert set(_lab_get_paths()) == {"/lab/world_state", "/lab/evaluate"}


def test_lab_route_rejects_missing_token(client):
    response = client.get("/lab/world_state", headers={"Origin": config.LAB_ORIGIN})
    assert response.status_code == 401


def test_lab_route_rejects_wrong_token(client):
    response = client.get(
        "/lab/world_state",
        headers={"X-Lab-Token": "wrong-token", "Origin": config.LAB_ORIGIN},
    )
    assert response.status_code == 401


def test_lab_route_accepts_correct_token(client, lab_headers):
    response = client.get("/lab/world_state", headers=lab_headers)
    assert response.status_code == 200
    assert response.json()["scenario_id"] == "BW-001"


def test_lab_reset_and_advance_also_require_token(client):
    reset_response = client.post("/lab/reset", headers={"Origin": config.LAB_ORIGIN})
    assert reset_response.status_code == 401

    advance_response = client.post(
        "/lab/clock/advance", json={"to_day": 18}, headers={"Origin": config.LAB_ORIGIN}
    )
    assert advance_response.status_code == 401


def test_lab_evaluate_requires_token(client, lab_headers):
    response = client.get("/lab/evaluate", headers={"Origin": config.LAB_ORIGIN})
    assert response.status_code == 401

    response = client.get("/lab/evaluate", headers=lab_headers)
    assert response.status_code == 200
    assert "binary_success" in response.json()
    assert "checkpoints" in response.json()


def test_lab_reset_and_advance_work_with_token(client, lab_headers):
    reset_response = client.post("/lab/reset", headers=lab_headers)
    assert reset_response.status_code == 200
    assert reset_response.json() == {"ok": True}

    advance_response = client.post("/lab/clock/advance", json={"to_day": 18}, headers=lab_headers)
    assert advance_response.status_code == 200
    assert advance_response.json()["current_sim_day"] == 18
