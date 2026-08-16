from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from cybersec_api.main import app
from cybersec_api.schemas.enrichment import AIEnrichmentPayload


def rss_feed(unique_id: str) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>CyberSec Alerts Feed</title>
    <item>
      <title>Edge firewall exploited in active campaign {unique_id}</title>
      <link>https://example.com/alerts/{unique_id}/edge-firewall</link>
      <guid>{unique_id}-edge-firewall</guid>
      <description>Attackers are exploiting an edge firewall CVE for access.</description>
      <pubDate>Sat, 15 Aug 2026 10:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
""".encode()


@pytest.mark.integration
def test_watchlist_alert_sync_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    unique_id = uuid4().hex
    cve_id = f"CVE-2026-{(int(unique_id[:8], 16) % 9000) + 1000}"

    async def fake_fetch_feed(url: str) -> bytes:
        assert url.startswith("https://example.com/alerts-feed/")
        return rss_feed(unique_id)

    async def fake_enrich_with_openrouter(**kwargs):
        assert "firewall" in kwargs["title"].lower()
        return (
            AIEnrichmentPayload(
                summary=f"Attackers are exploiting {cve_id} on edge firewalls.",
                severity="critical",
                confidence=93,
                tags=["edge-firewall", "active-exploitation"],
                cves=[cve_id],
                iocs=["alert-firewall.example"],
                mitre_attack=["T1190 - Exploit Public-Facing Application"],
                recommended_actions=["Patch affected edge firewalls"],
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
            "name": f"Alerts Test {unique_id}",
            "url": f"https://example.com/alerts-feed/{unique_id}.xml",
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

    watchlist_response = client.post(
        "/watchlists",
        json={
            "name": f"Critical CVE Watch {unique_id}",
            "entity_type": "cve",
            "value_pattern": cve_id,
            "severity": "critical",
            "min_risk_score": 80,
            "is_enabled": True,
        },
    )
    assert watchlist_response.status_code == 201
    watchlist_id = watchlist_response.json()["id"]

    sync_response = client.post("/alerts/sync", params={"limit": 500})
    assert sync_response.status_code == 200
    assert sync_response.json()["alerts_created"] >= 1

    second_sync_response = client.post("/alerts/sync", params={"limit": 500})
    assert second_sync_response.status_code == 200
    assert second_sync_response.json()["alerts_created"] == 0

    alerts_response = client.get("/alerts", params={"watchlist_id": watchlist_id})
    assert alerts_response.status_code == 200
    alerts = alerts_response.json()
    assert len(alerts) == 1
    assert alerts[0]["entity_value"] == cve_id
    assert alerts[0]["item_id"] == item["id"]
    assert alerts[0]["status"] == "open"

    status_response = client.patch(
        f"/alerts/{alerts[0]['id']}/status",
        json={"status": "acknowledged"},
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "acknowledged"
    assert status_response.json()["acknowledged_at"] is not None

    assert client.delete(f"/watchlists/{watchlist_id}").status_code == 204
    assert client.delete(f"/sources/{source_id}").status_code == 204
    assert client.post("/stories/sync", params={"limit": 500}).status_code == 200
