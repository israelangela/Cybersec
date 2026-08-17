from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from cybersec_api.main import app


@pytest.mark.integration
def test_source_crud_flow() -> None:
    client = TestClient(app)
    unique_id = uuid4().hex
    payload = {
        "name": f"CISA Advisories {unique_id}",
        "url": f"https://www.cisa.gov/news-events/cybersecurity-advisories/{unique_id}",
        "source_type": "rss",
        "description": "Authoritative advisories source",
        "weight": "2.50",
        "is_enabled": True,
    }

    create_response = client.post("/sources", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == payload["name"]
    assert created["url"] == payload["url"]
    assert created["is_enabled"] is True

    source_id = created["id"]

    list_response = client.get("/sources")
    assert list_response.status_code == 200
    assert any(source["id"] == source_id for source in list_response.json())

    read_response = client.get(f"/sources/{source_id}")
    assert read_response.status_code == 200
    assert read_response.json()["id"] == source_id

    update_response = client.patch(
        f"/sources/{source_id}",
        json={"is_enabled": False, "weight": "3.00"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["is_enabled"] is False
    assert updated["weight"] == "3.00"

    enabled_response = client.get("/sources", params={"is_enabled": True})
    assert enabled_response.status_code == 200
    assert all(source["is_enabled"] is True for source in enabled_response.json())

    delete_response = client.delete(f"/sources/{source_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/sources/{source_id}")
    assert missing_response.status_code == 404


@pytest.mark.integration
def test_duplicate_source_url_returns_conflict() -> None:
    client = TestClient(app)
    unique_id = uuid4().hex
    payload = {
        "name": f"Duplicate Test {unique_id}",
        "url": f"https://example.com/source/{unique_id}",
        "source_type": "web",
        "weight": "1.00",
        "is_enabled": True,
    }

    first_response = client.post("/sources", json=payload)
    assert first_response.status_code == 201

    second_response = client.post("/sources", json=payload)
    assert second_response.status_code == 409

    source_id = first_response.json()["id"]
    client.delete(f"/sources/{source_id}")


@pytest.mark.integration
def test_recommended_sources_are_added_idempotently() -> None:
    client = TestClient(app)
    existing_ids = {source["id"] for source in client.get("/sources").json()}

    try:
        first_response = client.post("/sources/recommended")
        assert first_response.status_code == 200
        first = first_response.json()
        assert first["total"] == 20
        assert first["created"] + first["skipped"] == 20
        assert len(first["sources"]) == 20

        second_response = client.post("/sources/recommended")
        assert second_response.status_code == 200
        second = second_response.json()
        assert second["created"] == 0
        assert second["skipped"] == 20
        assert len(second["sources"]) == 20
    finally:
        for source in first_response.json().get("sources", []):
            if source["id"] not in existing_ids:
                client.delete(f"/sources/{source['id']}")
