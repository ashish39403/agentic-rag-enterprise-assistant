import os

# The application builds its graph during import, so CI needs placeholder
# credentials even though this health test never calls an LLM or Qdrant.
os.environ.setdefault("OPENAI_API_KEY", "ci-test-key")
os.environ.setdefault("OPENAI_BASE_URL", "https://example.com/v1")
os.environ.setdefault("QDRANT_CLUSTER_ENDPOINT", "http://localhost:6333")
os.environ.setdefault("QDRANT_API_KEY", "ci-test-key")
os.environ.setdefault("LOGFIRE_IGNORE_NO_CONFIG", "1")

from fastapi.testclient import TestClient

from app.main import app


def test_home_route():
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "Enterprise LangGraph RAG API is live."
