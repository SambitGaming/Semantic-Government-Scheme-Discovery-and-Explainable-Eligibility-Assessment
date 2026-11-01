from fastapi.testclient import TestClient

from src.app.api import app


client = TestClient(app)


def test_home():

    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "running"


def test_health():

    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"


def test_schemes():

    response = client.get("/schemes")

    assert response.status_code == 200

    data = response.json()

    assert "schemes" in data