from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from cybersec_api.main import app
from cybersec_api.schemas.enrichment import AIEnrichmentPayload


def rss_feed(unique_id: str) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>CyberSec Intelligence Feed</title>
    <item>
      <title>APT28 exploiting perimeter firewall {unique_id}</title>
      <link>https://example.com/intel/{unique_id}/apt28-firewall</link>
      <guid>{unique_id}-apt28-firewall</guid>
      <description>
        APT28 activity includes CVE exploitation, command and control and edge access.
      </description>
      <pubDate>Tue, 11 Aug 2026 10:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
""".encode()


@pytest.mark.integration
def test_intelligence_entity_sync_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    unique_id = uuid4().hex

    async def fake_fetch_feed(url: str) -> bytes:
        assert url.startswith("https://example.com/intelligence-feed/")
        return rss_feed(unique_id)

    async def fake_enrich_with_openrouter(**kwargs):
        assert "apt28" in kwargs["title"].lower()
        return (
            AIEnrichmentPayload(
                summary="APT28 is exploiting CVE-2026-4242 on perimeter firewalls.",
                severity="critical",
                confidence=92,
                tags=["edge-device", "active-exploitation"],
                cves=["CVE-2026-4242"],
                iocs=["198.51.100.7", "malicious.example"],
                mitre_attack=["T1190 - Exploit Public-Facing Application"],
                recommended_actions=["Patch affected firewalls"],
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
            "name": f"Intelligence Test {unique_id}",
            "url": f"https://example.com/intelligence-feed/{unique_id}.xml",
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

    enrichment_response = client.post(f"/enrichment/items/{item['id']}/run")
    assert enrichment_response.status_code == 200
    assert enrichment_response.json()["status"] == "completed"

    sync_response = client.post("/intelligence/sync", params={"limit": 500})
    assert sync_response.status_code == 200
    assert sync_response.json()["entities_created"] >= 7
    assert client.post("/stories/sync", params={"limit": 500}).status_code == 200

    item_entities_response = client.get(f"/intelligence/items/{item['id']}/entities")
    assert item_entities_response.status_code == 200
    item_entities = item_entities_response.json()
    normalized_values = {entity["normalized_value"] for entity in item_entities}
    assert "CVE-2026-4242" in normalized_values
    assert "198.51.100.7" in normalized_values
    assert "T1190" in normalized_values
    assert "APT28" in normalized_values
    assert max(entity["risk_score"] for entity in item_entities) >= 90

    cve_response = client.get(
        "/intelligence/entities",
        params={"entity_type": "cve", "search": "2026-4242"},
    )
    assert cve_response.status_code == 200
    assert cve_response.json()[0]["normalized_value"] == "CVE-2026-4242"

    stats_response = client.get("/intelligence/stats")
    assert stats_response.status_code == 200
    assert stats_response.json()["unique_entities"] >= 1

    entity_context_response = client.get(
        "/intelligence/entities/context",
        params={"entity_type": "cve", "value": "CVE-2026-4242"},
    )
    assert entity_context_response.status_code == 200
    entity_context = entity_context_response.json()
    assert entity_context["entity"]["normalized_value"] == "CVE-2026-4242"
    assert entity_context["items"][0]["id"] == item["id"]
    assert entity_context["stories"]
    assert {reference["label"] for reference in entity_context["external_references"]} == {
        "CVE.org",
        "NVD",
    }

    item_context_response = client.get(f"/items/{item['id']}/context")
    assert item_context_response.status_code == 200
    item_context = item_context_response.json()
    assert item_context["item"]["id"] == item["id"]
    assert item_context["entities"]
    assert item_context["stories"]

    assert client.delete(f"/sources/{source_id}").status_code == 204
    assert client.post("/stories/sync", params={"limit": 500}).status_code == 200
