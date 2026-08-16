from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from cybersec_api.main import app
from cybersec_api.schemas.enrichment import AIEnrichmentPayload


def rss_feed(unique_id: str) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>CyberSec Enterprise Feed</title>
    <item>
      <title>Identity provider attack campaign {unique_id}</title>
      <link>https://example.com/enterprise/{unique_id}/idp-campaign</link>
      <guid>{unique_id}-idp-campaign</guid>
      <description>Attackers are targeting identity provider admin portals.</description>
      <pubDate>Sun, 16 Aug 2026 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
""".encode()


@pytest.mark.integration
def test_enterprise_governance_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    unique_id = uuid4().hex

    async def fake_fetch_feed(url: str) -> bytes:
        assert url.startswith("https://example.com/enterprise-feed/")
        return rss_feed(unique_id)

    async def fake_enrich_with_openrouter(**kwargs):
        assert "identity" in kwargs["title"].lower()
        return (
            AIEnrichmentPayload(
                summary="Identity provider admin portals are being targeted.",
                severity="high",
                confidence=91,
                tags=["identity", "admin-portal"],
                cves=[],
                iocs=["idp-enterprise.example"],
                mitre_attack=["T1190 - Exploit Public-Facing Application"],
                recommended_actions=["Review identity provider admin exposure"],
            ),
            {
                "choices": [{"message": {"content": "{}"}}],
                "usage": {"prompt_tokens": 120, "completion_tokens": 80},
            },
        )

    monkeypatch.setattr("cybersec_api.collectors.rss.fetch_feed", fake_fetch_feed)
    monkeypatch.setattr(
        "cybersec_api.enrichment.service.enrich_with_openrouter",
        fake_enrich_with_openrouter,
    )

    user_response = client.post(
        "/enterprise/users",
        json={
            "email": f"analyst-{unique_id}@example.com",
            "full_name": "Phase 12 Analyst",
            "is_active": True,
            "is_superuser": False,
        },
    )
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]

    department_response = client.post(
        "/enterprise/departments",
        json={
            "name": f"SOC {unique_id}",
            "description": "Security operations center",
            "owner_email": f"owner-{unique_id}@example.com",
            "risk_appetite": "low",
            "is_active": True,
        },
    )
    assert department_response.status_code == 201
    department_id = department_response.json()["id"]

    membership_response = client.post(
        f"/enterprise/departments/{department_id}/memberships",
        json={"user_id": user_id, "role": "analyst", "permissions": [], "is_active": True},
    )
    assert membership_response.status_code == 201
    membership = membership_response.json()
    assert membership["role"] == "analyst"
    assert "alerts:triage" in membership["permissions"]

    roles_response = client.get("/enterprise/roles")
    assert roles_response.status_code == 200
    assert any(role["role"] == "owner" for role in roles_response.json())

    audit_response = client.post(
        "/enterprise/audit-events",
        json={
            "actor_type": "system",
            "action": "enterprise.test",
            "resource_type": "phase12",
            "resource_id": unique_id,
            "outcome": "success",
            "metadata": {"unique_id": unique_id},
        },
    )
    assert audit_response.status_code == 201
    assert audit_response.json()["metadata"]["unique_id"] == unique_id

    source_response = client.post(
        "/sources",
        json={
            "name": f"Enterprise Test {unique_id}",
            "url": f"https://example.com/enterprise-feed/{unique_id}.xml",
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

    usage_sync_response = client.post("/enterprise/model-usage/sync", params={"limit": 500})
    assert usage_sync_response.status_code == 200
    assert usage_sync_response.json()["usage_created"] >= 1

    usage_response = client.get("/enterprise/model-usage", params={"operation": "enrichment"})
    assert usage_response.status_code == 200
    assert any(row["resource_id"] == item["id"] for row in usage_response.json())

    overview_response = client.get("/enterprise/overview")
    assert overview_response.status_code == 200
    overview = overview_response.json()
    assert overview["departments"] >= 1
    assert overview["memberships"] >= 1
    assert overview["audit_events"] >= 1
    assert overview["model_usage_records"] >= 1

    assert client.delete(f"/enterprise/memberships/{membership['id']}").status_code == 204
    assert client.delete(f"/enterprise/departments/{department_id}").status_code == 204
    assert client.delete(f"/enterprise/users/{user_id}").status_code == 204
    assert client.delete(f"/sources/{source_id}").status_code == 204
