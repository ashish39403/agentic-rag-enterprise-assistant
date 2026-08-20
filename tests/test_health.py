from fastapi.testclient import TestClient

from app.main import app


def test_home_route():
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "Enterprise LangGraph RAG API is live."
