from __future__ import annotations

from fastapi.testclient import TestClient

from truthguard.api import create_app
from truthguard.pipeline import build_default_pipeline


def test_health_and_query_endpoints() -> None:
    client = TestClient(create_app(build_default_pipeline()))
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    response = client.post("/query", json={"question": "What is the hospitalization waiting period?"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "resolved"
    assert payload["conflicts"][0]["type"] == "T1"


def test_query_validation_rejects_short_questions() -> None:
    client = TestClient(create_app(build_default_pipeline()))
    response = client.post("/query", json={"question": "?"})
    assert response.status_code == 422
