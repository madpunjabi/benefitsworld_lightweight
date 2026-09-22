import pytest

from tests.test_visible_state_isolation import PUBLIC_ENDPOINTS


@pytest.mark.parametrize("path", PUBLIC_ENDPOINTS)
def test_public_endpoint_returns_200(client, agent_headers, path):
    response = client.get(path, headers=agent_headers)
    assert response.status_code == 200


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
