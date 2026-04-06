import os

from fastapi.testclient import TestClient

os.environ["SKIP_DB_INIT"] = "true"
from app.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("ok", "degraded")
        assert "database" in data
        assert "redis" in data
        assert "encryption_configured" in data


def test_health_reports_encryption_status():
    with TestClient(app) as client:
        response = client.get("/health")
        data = response.json()
        assert isinstance(data["encryption_configured"], bool)
