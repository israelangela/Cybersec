from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from cybersec_api.main import app
from cybersec_api.schemas.enrichment import AIEnrichmentPayload


def rss_feed(unique_id: str) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>CyberSec Ask Feed</title>
    <item>
      <title>APT29 exploiting VPN gateway {unique_id}</title>
      <link>https://example.com/ask/{unique_id}/apt29-vpn</link>
      <guid>{unique_id}-apt29-vpn</guid>
      <description>APT29 is exploiting a VPN gateway vulnerability for initial access.</description>
      <pubDate>Thu, 13 Aug 2026 10:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
""".encode()


@pytest.mark.integration
def test_ask_cybersec_returns_cited_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    unique_id = uuid4().hex

    async def fake_fetch_feed(url: str) -> bytes:
        assert url.startswith("https://example.com/ask-feed/")
        return rss_feed(unique_id)

    async def fake_enrich_with_openrouter(**kwargs):
        assert "apt29" in kwargs["title"].lower()
        return (
            AIEnrichmentPayload(
                summary="APT29 is exploiting CVE-2026-9090 on VPN gateways for access.",
                severity="critical",
                confidence=91,
                tags=["vpn", "initial-access", "active-exploitation"],
                cves=["CVE-2026-9090"],
                iocs=["vpn-malicious.example"],
                mitre_attack=["T1190 - Exploit Public-Facing Application"],
                recommended_actions=["Patch VPN gateways", "Review remote access logs"],
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
            "name": f"Ask Test {unique_id}",
            "url": f"https://example.com/ask-feed/{unique_id}.xml",
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

    ask_response = client.post(
        "/ask",
        json={
            "question": "Que sabemos de APT29 y CVE-2026-9090?",
            "limit": 4,
            "use_ai": False,
        },
    )

    assert ask_response.status_code == 200
    answer = ask_response.json()
    assert answer["mode"] == "local"
    assert answer["citations"]
    assert answer["citations"][0]["item_id"] == item["id"]
    assert "CVE-2026-9090" in answer["citations"][0]["entities"]
    assert "[S1]" in answer["answer"]
    assert answer["follow_up_questions"]

    assert client.delete(f"/sources/{source_id}").status_code == 204
    assert client.post("/stories/sync", params={"limit": 500}).status_code == 200
