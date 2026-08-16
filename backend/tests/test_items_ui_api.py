from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from cybersec_api.main import app

def rss_feed(unique_id: str) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>CyberSec UI Feed</title>
    <item>
      <title>Exploit activity {unique_id} targets edge firewalls</title>
      <link>https://example.com/intel/{unique_id}/ui-firewalls</link>
      <guid>{unique_id}-ui-firewalls</guid>
      <description>Attackers are exploiting vulnerable edge devices in case {unique_id}.</description>
      <pubDate>Mon, 10 Aug 2026 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Campaña {unique_id} de ransomware contra bancos</title>
      <link>https://example.com/intel/{unique_id}/ui-ransomware-banks</link>
      <guid>{unique_id}-ui-ransomware-banks</guid>
      <description>Los atacantes lanzan una campaña contra bancos en caso {unique_id}.</description>
      <pubDate>Mon, 10 Aug 2026 11:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
""".encode()


@pytest.mark.integration
def test_item_filters_and_stats_support_intelligence_ui(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    unique_id = uuid4().hex

    async def fake_fetch_feed(url: str) -> bytes:
        assert url.startswith("https://example.com/feed/")
        return rss_feed(unique_id)

    monkeypatch.setattr("cybersec_api.collectors.rss.fetch_feed", fake_fetch_feed)
    source_response = client.post(
        "/sources",
        json={
            "name": f"UI API Test {unique_id}",
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
    assert collection_response.json()["created"] == 2

    source_items_response = client.get("/items", params={"source_id": source_id, "status": "raw"})
    assert source_items_response.status_code == 200

    for item in source_items_response.json():
        normalization_response = client.post(f"/normalization/items/{item['id']}/run")
        assert normalization_response.status_code == 200
        assert normalization_response.json()["status"] == "normalized"

    filtered_response = client.get(
        "/items",
        params={
            "source_id": source_id,
            "status": "normalized",
            "language": "en",
            "search": "firewalls",
            "limit": 10,
        },
    )
    assert filtered_response.status_code == 200
    filtered_items = filtered_response.json()
    assert len(filtered_items) == 1
    assert filtered_items[0]["source_name"].startswith("UI API Test")
    assert filtered_items[0]["language"] == "en"
    assert "firewalls" in filtered_items[0]["normalized_title"].lower()

    stats_response = client.get("/items/stats")
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["total"] >= 2
    assert stats["normalized"] >= 2
    assert any(language["language"] == "en" for language in stats["languages"])
    assert any(source["source_id"] == source_id for source in stats["sources"])

    client.delete(f"/sources/{source_id}")
