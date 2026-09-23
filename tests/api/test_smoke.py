import pytest

pytestmark = pytest.mark.api


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_home_page(client):
    assert client.get("/").status_code == 200


def test_swagger(client):
    assert client.get("/docs").status_code == 200


def test_create_and_read(client):
    created = client.post("/api/tasks", json={"title": "Smoke task"})
    assert created.status_code == 201
    task = created.json()
    response = client.get(f"/api/tasks/{task['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "Smoke task"


def test_reset_unavailable_in_normal_mode(client):
    assert client.post("/api/test/reset", json={}).status_code == 404
    assert "/api/test/reset" not in client.get("/openapi.json").json()["paths"]
