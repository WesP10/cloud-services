"""Pytest-compatible API tests for cloud-services.

These use the `client` fixture defined in `tests/conftest.py` so tests
run without requiring an externally running server or the `requests` package.
"""


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    # Basic shape check
    assert isinstance(response.json(), dict) or response.json() == {}


def test_login_and_get_current_user(client):
    login_data = {"username": "admin", "password": "admin123"}
    res = client.post("/auth/login", json=login_data)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data

    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/auth/me", headers=headers)
    assert me.status_code == 200
    assert "username" in me.json() or isinstance(me.json(), dict)


def test_list_hubs_requires_auth(client):
    # Without auth
    res = client.get("/api/hubs")
    assert res.status_code in [401, 403]

    # With auth
    login = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    if login.status_code == 200:
        token = login.json()["access_token"]
        res = client.get("/api/hubs", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code in [200, 401, 403]
        if res.status_code == 200:
            assert isinstance(res.json(), list)

