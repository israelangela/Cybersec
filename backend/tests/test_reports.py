from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from cybersec_api.main import app
from cybersec_api.schemas.enrichment import AIEnrichmentPayload


def rss_feed(unique_id: str) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>CyberSec Reports Feed</title>
    <item>
      <title>Critical VPN exploitation campaign {unique_id}</title>
      <link>https://example.com/reports/{unique_id}/vpn-campaign</link>
      <guid>{unique_id}-vpn-campaign</guid>
      <description>Threat actors are exploiting VPN gateways for initial access.</description>
      <pubDate>Fri, 14 Aug 2026 10:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
""".encode()


@pytest.mark.integration
def test_report_generation_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    unique_id = uuid4().hex

    async def fake_fetch_feed(url: str) -> bytes:
        assert url.startswith("https://example.com/reports-feed/")
        return rss_feed(unique_id)

    async def fake_enrich_with_openrouter(**kwargs):
        assert "vpn" in kwargs["title"].lower()
        return (
            AIEnrichmentPayload(
                summary="A critical VPN exploitation campaign is targeting edge access.",
                severity="critical",
                confidence=94,
                tags=["vpn", "edge-access", "active-exploitation"],
                cves=["CVE-2026-6161"],
                iocs=["vpn-report.example"],
                mitre_attack=["T1190 - Exploit Public-Facing Application"],
                recommended_actions=["Patch VPN gateways", "Rotate exposed credentials"],
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
            "name": f"Reports Test {unique_id}",
            "url": f"https://example.com/reports-feed/{unique_id}.xml",
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

    stories = client.get("/stories", params={"search": "CVE-2026-6161"}).json()
    assert stories

    generate_response = client.post(
        "/reports/generate",
        json={
            "title": f"VPN Campaign Report {unique_id}",
            "report_type": "executive",
            "story_ids": [stories[0]["id"]],
            "limit": 1,
        },
    )
    assert generate_response.status_code == 200
    generated = generate_response.json()
    report = generated["report"]
    assert generated["status"] == "created"
    assert report["story_count"] == 1
    assert report["item_count"] >= 1
    assert report["risk_score"] >= 80
    assert "CVE-2026-6161" in report["body_markdown"]
    assert report["items"][0]["citation_id"] == "R1"

    report_id = report["id"]
    list_response = client.get("/reports")
    assert list_response.status_code == 200
    assert any(row["id"] == report_id for row in list_response.json())

    markdown_response = client.get(f"/reports/{report_id}/markdown")
    assert markdown_response.status_code == 200
    assert "# VPN Campaign Report" in markdown_response.text
    assert "[R1]" in markdown_response.text

    assert client.delete(f"/reports/{report_id}").status_code == 204
    assert client.delete(f"/sources/{source_id}").status_code == 204
    assert client.post("/stories/sync", params={"limit": 500}).status_code == 200
