from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_task():
    response = client.post(
        "/tasks",
        json={"title": "pytest task"}
    )

    assert response.status_code == 200

    data = response.json()
    assert data["title"] == "pytest task"
    assert data["completed"] is False
    assert "id" in data
    assert "owner_id" in data
