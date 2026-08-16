from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from cybersec_api.main import app
from cybersec_api.normalizers.text import detect_language, normalize_content, normalized_hash

DUPLICATE_RSS_FEED = b"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>CyberSec Normalization Feed</title>
    <item>
      <title>Critical firewall vulnerability exploited</title>
      <link>https://example.com/intel/normalization-one</link>
      <guid>normalization-one</guid>
      <description><![CDATA[
        <article><h1>Critical firewall vulnerability exploited</h1>
        <p>Attackers are exploiting vulnerable edge devices.</p>
        <script>ignored()</script></article>
      ]]></description>
      <pubDate>Mon, 10 Aug 2026 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Critical firewall vulnerability exploited</title>
      <link>https://example.com/intel/normalization-two</link>
      <guid>normalization-two</guid>
      <description><![CDATA[
        <div>Critical firewall vulnerability exploited</div>
        <p>Attackers are exploiting vulnerable edge devices.</p>
      ]]></description>
      <pubDate>Mon, 10 Aug 2026 11:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


def test_normalize_content_extracts_readable_html() -> None:
    content = normalize_content(
        "<article><h1>Threat</h1><p>Attackers&nbsp;abuse VPN devices.</p>"
        "<script>alert('x')</script></article>"
    )

    assert content == "Threat Attackers abuse VPN devices."


def test_detect_language_and_normalized_hash_are_deterministic() -> None:
    title = "Critical firewall vulnerability exploited"
    content = "Attackers are exploiting vulnerable edge devices."

    assert detect_language(title, content) == "en"
    assert normalized_hash(title, content) == normalized_hash(title.upper(), content)


@pytest.mark.integration
def test_normalization_endpoint_marks_duplicate_items(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_fetch_feed(url: str) -> bytes:
        assert url.startswith("https://example.com/feed/")
        return DUPLICATE_RSS_FEED

    monkeypatch.setattr("cybersec_api.collectors.rss.fetch_feed", fake_fetch_feed)

    client = TestClient(app)
    unique_id = uuid4().hex
    source_response = client.post(
        "/sources",
        json={
            "name": f"Normalization Test {unique_id}",
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

    normalization_response = client.post("/normalization/run")
    assert normalization_response.status_code == 200
    normalization = normalization_response.json()
    assert normalization["status"] == "ok"
    assert normalization["normalized"] >= 1
    assert normalization["duplicates"] >= 1

    items_response = client.get("/items", params={"source_id": source_id})
    assert items_response.status_code == 200
    items = items_response.json()
    statuses = {item["status"] for item in items}
    assert "normalized" in statuses
    assert "duplicate" in statuses
    assert all("<" not in item["normalized_content"] for item in items)
    assert all(item["language"] == "en" for item in items)
    assert all(item["normalized_hash"] for item in items)

    client.delete(f"/sources/{source_id}")
