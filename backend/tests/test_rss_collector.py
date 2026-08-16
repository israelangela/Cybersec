from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from cybersec_api.collectors.rss import hash_entry, parse_feed_entries
from cybersec_api.main import app

RSS_FEED = b"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>CyberSec Test Feed</title>
    <item>
      <title>Critical firewall vulnerability exploited</title>
      <link>https://example.com/intel/firewall-vulnerability</link>
      <guid>firewall-vulnerability-1</guid>
      <description>Attackers are exploiting vulnerable edge devices.</description>
      <pubDate>Mon, 10 Aug 2026 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Ransomware campaign targets banks</title>
      <link>https://example.com/intel/ransomware-banks</link>
      <guid>ransomware-banks-1</guid>
      <description>Multiple banks report intrusion attempts.</description>
      <pubDate>Mon, 10 Aug 2026 11:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


def test_parse_feed_entries_and_hashing() -> None:
    entries = parse_feed_entries(RSS_FEED)

    assert len(entries) == 2
    assert entries[0].title == "Critical firewall vulnerability exploited"
    assert entries[0].url == "https://example.com/intel/firewall-vulnerability"
    assert entries[0].external_id == "firewall-vulnerability-1"
    assert entries[0].published_at is not None
    assert entries[0].content_hash == hash_entry(
        entries[0].title,
        entries[0].url,
        entries[0].summary,
        entries[0].raw_content,
    )


@pytest.mark.integration
def test_source_collection_endpoint_deduplicates(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_fetch_feed(url: str) -> bytes:
        assert url.startswith("https://example.com/feed/")
        return RSS_FEED

    monkeypatch.setattr("cybersec_api.collectors.rss.fetch_feed", fake_fetch_feed)

    client = TestClient(app)
    unique_id = uuid4().hex
    source_response = client.post(
        "/sources",
        json={
            "name": f"RSS Collection Test {unique_id}",
            "url": f"https://example.com/feed/{unique_id}.xml",
            "source_type": "rss",
            "weight": "1.00",
            "is_enabled": True,
        },
    )
    assert source_response.status_code == 201
    source_id = source_response.json()["id"]

    first_run = client.post(f"/collection/sources/{source_id}/run")
    assert first_run.status_code == 200
    assert first_run.json()["fetched"] == 2
    assert first_run.json()["created"] == 2
    assert first_run.json()["duplicates"] == 0

    second_run = client.post(f"/collection/sources/{source_id}/run")
    assert second_run.status_code == 200
    assert second_run.json()["fetched"] == 2
    assert second_run.json()["created"] == 0
    assert second_run.json()["duplicates"] == 2

    items_response = client.get("/items", params={"source_id": source_id})
    assert items_response.status_code == 200
    items = items_response.json()
    assert len(items) == 2
    assert {item["status"] for item in items} == {"raw"}

    client.delete(f"/sources/{source_id}")


@pytest.mark.integration
def test_collection_run_skips_non_rss_source() -> None:
    client = TestClient(app)
    unique_id = uuid4().hex
    source_response = client.post(
        "/sources",
        json={
            "name": f"Web Source {unique_id}",
            "url": f"https://example.com/web/{unique_id}",
            "source_type": "web",
            "weight": "1.00",
            "is_enabled": True,
        },
    )
    assert source_response.status_code == 201
    source_id = source_response.json()["id"]

    collection_response = client.post(f"/collection/sources/{source_id}/run")
    assert collection_response.status_code == 200
    assert collection_response.json()["status"] == "skipped"

    client.delete(f"/sources/{source_id}")
