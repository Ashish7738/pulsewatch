import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402

TEST_CONFIG = {
    "TESTING": True,
    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    "JWT_SECRET_KEY": "test-secret-key-that-is-at-least-32-chars",
}


def test_health_returns_ok():
    client = create_app(TEST_CONFIG).test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_metrics_require_token():
    client = create_app(TEST_CONFIG).test_client()
    assert client.get("/api/metrics/latest").status_code == 401
