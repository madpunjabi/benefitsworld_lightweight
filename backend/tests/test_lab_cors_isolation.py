from app import config


def test_preflight_from_lab_origin_is_allowed(client):
    response = client.options(
        "/lab/world_state",
        headers={
            "Origin": config.LAB_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "x-lab-token",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == config.LAB_ORIGIN


def test_preflight_from_agent_origin_is_rejected(client):
    response = client.options(
        "/lab/world_state",
        headers={
            "Origin": config.AGENT_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "x-lab-token",
        },
    )
    assert response.status_code == 403
    assert "access-control-allow-origin" not in response.headers


def test_lab_response_omits_cors_header_for_agent_origin_even_with_valid_token(client, lab_headers):
    headers = dict(lab_headers)
    headers["Origin"] = config.AGENT_ORIGIN
    response = client.get("/lab/world_state", headers=headers)
    # The token still lets the request succeed server-side, but a real
    # browser on :5173 would never see this body: no CORS header means the
    # browser refuses to expose the response to the page's JavaScript.
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_lab_response_includes_cors_header_for_lab_origin(client, lab_headers):
    response = client.get("/lab/world_state", headers=lab_headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == config.LAB_ORIGIN


def test_public_route_preflight_allows_only_agent_origin(client):
    ok = client.options(
        "/portal/case",
        headers={"Origin": config.AGENT_ORIGIN, "Access-Control-Request-Method": "GET"},
    )
    assert ok.status_code == 200
    assert ok.headers["access-control-allow-origin"] == config.AGENT_ORIGIN

    blocked = client.options(
        "/portal/case",
        headers={"Origin": config.LAB_ORIGIN, "Access-Control-Request-Method": "GET"},
    )
    assert blocked.status_code == 403
