from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from cybersec_api.main import app
from cybersec_api.schemas.enrichment import AIEnrichmentPayload


def rss_feed(unique_id: str) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>CyberSec War Room Feed</title>
    <item>
      <title>Critical APT29 intrusion campaign against identity systems {unique_id}</title>
      <link>https://example.com/war-room/{unique_id}/apt29-identity</link>
      <guid>{unique_id}-apt29-identity</guid>
      <description>
        APT29 is exploiting identity infrastructure and stealing session tokens.
      </description>
      <pubDate>Thu, 13 Aug 2026 10:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
""".encode()


@pytest.mark.integration
def test_war_room_operational_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    unique_id = uuid4().hex

    async def fake_fetch_feed(url: str) -> bytes:
        assert url.startswith("https://example.com/war-room-feed/")
        return rss_feed(unique_id)

    async def fake_enrich_with_openrouter(**kwargs):
        assert "apt29" in kwargs["title"].lower()
        return (
            AIEnrichmentPayload(
                summary="APT29 is targeting identity systems with credential theft tradecraft.",
                severity="critical",
                confidence=94,
                tags=["identity", "credential-theft", "active-intrusion"],
                cves=["CVE-2026-8888"],
                iocs=["203.0.113.88"],
                mitre_attack=["T1550.004 - Web Session Cookie"],
                recommended_actions=["Invalidate exposed sessions", "Review identity logs"],
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
            "name": f"War Room Test {unique_id}",
            "url": f"https://example.com/war-room-feed/{unique_id}.xml",
            "source_type": "rss",
            "weight": "1.00",
            "is_enabled": True,
        },
    )
    assert source_response.status_code == 201
    source_id = source_response.json()["id"]

    assert client.post(f"/collection/sources/{source_id}/run").status_code == 200
    item = client.get("/items", params={"source_id": source_id}).json()[0]
    assert client.post(f"/normalization/items/{item['id']}/run").status_code == 200
    assert client.post(f"/enrichment/items/{item['id']}/run").json()["status"] == "completed"
    assert client.post("/intelligence/sync", params={"limit": 500}).status_code == 200
    assert client.post("/stories/sync", params={"limit": 500}).status_code == 200

    war_room_response = client.get("/war-room", params={"limit": 25})
    assert war_room_response.status_code == 200
    war_room = war_room_response.json()

    assert war_room["summary"]["active_stories"] >= 1
    assert war_room["summary"]["critical_stories"] >= 1
    assert war_room["summary"]["operation_mode"] in {"active", "hot"}
    assert war_room["risk_queue"]
    assert war_room["risk_queue"][0]["urgency"] in {"priority", "immediate"}
    assert any(entity["normalized_value"] == "APT29" for entity in war_room["entity_pulse"])
    assert war_room["timeline"]
    assert any(source["id"] == source_id for source in war_room["source_health"])

    assert client.delete(f"/sources/{source_id}").status_code == 204
    assert client.post("/stories/sync", params={"limit": 500}).status_code == 200
