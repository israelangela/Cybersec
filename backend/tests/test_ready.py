import pytest
from fastapi.testclient import TestClient

from cybersec_api.main import app


@pytest.mark.integration
def test_ready() -> None:
    client = TestClient(app)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok"}
