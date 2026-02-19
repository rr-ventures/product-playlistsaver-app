import os

from fastapi.testclient import TestClient

os.environ["SKIP_DB_INIT"] = "true"
from app.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
