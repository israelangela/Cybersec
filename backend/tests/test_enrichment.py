from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from cybersec_api.main import app
from cybersec_api.schemas.enrichment import AIEnrichmentPayload


def rss_feed(unique_id: str) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>CyberSec Enrichment Feed</title>
    <item>
      <title>Critical firewall vulnerability {unique_id}</title>
      <link>https://example.com/intel/{unique_id}/firewall</link>
      <guid>{unique_id}-firewall</guid>
      <description>
        Attackers are exploiting vulnerable edge devices in case {unique_id}.
      </description>
      <pubDate>Mon, 10 Aug 2026 10:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
""".encode()


@pytest.mark.integration
def test_item_enrichment_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    unique_id = uuid4().hex

    async def fake_fetch_feed(url: str) -> bytes:
        assert url.startswith("https://example.com/feed/")
        return rss_feed(unique_id)

    async def fake_enrich_with_openrouter(**kwargs):
        assert "firewall" in kwargs["title"].lower()
        return (
            AIEnrichmentPayload(
                summary="Active exploitation of an edge firewall vulnerability.",
                severity="high",
                confidence=88,
                tags=["edge-device", "active-exploitation"],
                cves=["CVE-2026-12345"],
                iocs=["203.0.113.10"],
                mitre_attack=["T1190"],
                recommended_actions=["Patch affected firewalls", "Review edge access logs"],
            ),
            {"choices": [{"message": {"content": "{}"}}]},
        )

    monkeypatch.setattr("cybersec_api.collectors.rss.fetch_feed", fake_fetch_feed)
    monkeypatch.setattr(
        "cybersec_api.enrichment.service.enrich_with_openrouter",
        fake_enrich_with_openrouter,
    )

    source_response = client.post(
        "/sources",
        json={
            "name": f"Enrichment Test {unique_id}",
            "url": f"https://example.com/feed/{unique_id}.xml",
            "source_type": "rss",
            "weight": "1.00",
            "is_enabled": True,
        },
    )
    assert source_response.status_code == 201
    source_id = source_response.json()["id"]

    collection_response = client.post(f"/collection/sources/{source_id}/run")
    assert collection_response.status_code == 200
    assert collection_response.json()["created"] == 1

    item = client.get("/items", params={"source_id": source_id}).json()[0]
    normalization_response = client.post(f"/normalization/items/{item['id']}/run")
    assert normalization_response.status_code == 200

    enrichment_response = client.post(f"/enrichment/items/{item['id']}/run")
    assert enrichment_response.status_code == 200
    result = enrichment_response.json()
    assert result["status"] == "completed"
    assert result["enrichment"]["severity"] == "high"
    assert result["enrichment"]["cves"] == ["CVE-2026-12345"]

    item_response = client.get(f"/items/{item['id']}")
    assert item_response.status_code == 200
    enriched_item = item_response.json()
    assert enriched_item["ai_severity"] == "high"
    assert "active-exploitation" in enriched_item["ai_tags"]
    assert enriched_item["ai_cves"] == ["CVE-2026-12345"]
    assert enriched_item["ai_mitre_attack"] == ["T1190"]

    stats_response = client.get("/items/stats")
    assert stats_response.status_code == 200
    assert stats_response.json()["enriched"] >= 1

    read_enrichment_response = client.get(f"/enrichment/items/{item['id']}")
    assert read_enrichment_response.status_code == 200
    assert read_enrichment_response.json()["summary"].startswith("Active exploitation")

    client.delete(f"/sources/{source_id}")


@pytest.mark.integration
def test_item_enrichment_retry_updates_existing_error(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    unique_id = uuid4().hex
    attempts = 0

    async def fake_fetch_feed(url: str) -> bytes:
        assert url.startswith("https://example.com/feed/")
        return rss_feed(unique_id)

    async def flaky_enrich_with_openrouter(**kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("temporary provider failure")

        return (
            AIEnrichmentPayload(
                summary="Retried enrichment succeeded.",
                severity="medium",
                confidence=72,
                tags=["retry"],
                cves=[],
                iocs=[],
                mitre_attack=[],
                recommended_actions=["Review the retried enrichment"],
            ),
            {"choices": [{"message": {"content": "{}"}}]},
        )

    monkeypatch.setattr("cybersec_api.collectors.rss.fetch_feed", fake_fetch_feed)
    monkeypatch.setattr(
        "cybersec_api.enrichment.service.enrich_with_openrouter",
        flaky_enrich_with_openrouter,
    )

    source_response = client.post(
        "/sources",
        json={
            "name": f"Enrichment Retry Test {unique_id}",
            "url": f"https://example.com/feed/{unique_id}.xml",
            "source_type": "rss",
            "weight": "1.00",
            "is_enabled": True,
        },
    )
    assert source_response.status_code == 201
    source_id = source_response.json()["id"]

    collection_response = client.post(f"/collection/sources/{source_id}/run")
    assert collection_response.status_code == 200

    item = client.get("/items", params={"source_id": source_id}).json()[0]
    normalization_response = client.post(f"/normalization/items/{item['id']}/run")
    assert normalization_response.status_code == 200

    failed_response = client.post(f"/enrichment/items/{item['id']}/run")
    assert failed_response.status_code == 200
    failed = failed_response.json()
    assert failed["status"] == "error"
    assert failed["enrichment"]["summary"] is None
    assert failed["enrichment"]["tags"] == []

    retried_response = client.post(f"/enrichment/items/{item['id']}/run")
    assert retried_response.status_code == 200
    retried = retried_response.json()
    assert retried["status"] == "completed"
    assert retried["enrichment"]["summary"] == "Retried enrichment succeeded."

    client.delete(f"/sources/{source_id}")
