from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from cybersec_api.main import app
from cybersec_api.schemas.enrichment import AIEnrichmentPayload


def rss_feed(unique_id: str) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>CyberSec Stories Feed</title>
    <item>
      <title>Gateway botnet exploiting edge devices {unique_id}</title>
      <link>https://example.com/stories/{unique_id}/gateway-botnet</link>
      <guid>{unique_id}-gateway-botnet</guid>
      <description>Operators are abusing edge devices as proxy relay nodes.</description>
      <pubDate>Wed, 12 Aug 2026 10:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
""".encode()


@pytest.mark.integration
def test_story_sync_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    unique_id = uuid4().hex

    async def fake_fetch_feed(url: str) -> bytes:
        assert url.startswith("https://example.com/stories-feed/")
        return rss_feed(unique_id)

    async def fake_enrich_with_openrouter(**kwargs):
        assert "botnet" in kwargs["title"].lower()
        return (
            AIEnrichmentPayload(
                summary="A Linux botnet is exploiting edge devices for SOCKS5 relay access.",
                severity="high",
                confidence=86,
                tags=["botnet", "edge-device", "proxy-relay"],
                cves=["CVE-2026-7777"],
                iocs=["203.0.113.77"],
                mitre_attack=["T1190 - Exploit Public-Facing Application"],
                recommended_actions=["Patch internet-facing gateways"],
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
            "name": f"Stories Test {unique_id}",
            "url": f"https://example.com/stories-feed/{unique_id}.xml",
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

    sync_response = client.post("/stories/sync", params={"limit": 500})
    assert sync_response.status_code == 200
    sync_result = sync_response.json()
    assert sync_result["stories_created"] >= 1
    assert sync_result["story_items_created"] >= 1

    stories_response = client.get("/stories", params={"search": "CVE-2026-7777"})
    assert stories_response.status_code == 200
    stories = stories_response.json()
    assert stories
    assert stories[0]["risk_score"] >= 70
    assert "CVE-2026-7777" in stories[0]["keywords"]

    detail_response = client.get(f"/stories/{stories[0]['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["items"][0]["item_id"] == item["id"]

    stats_response = client.get("/stories/stats")
    assert stats_response.status_code == 200
    assert stats_response.json()["total_stories"] >= 1

    client.delete(f"/sources/{source_id}")
