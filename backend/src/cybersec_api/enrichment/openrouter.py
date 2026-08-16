from __future__ import annotations

import json
from typing import Any

import httpx
from pydantic import ValidationError

from cybersec_api.core.config import Settings
from cybersec_api.schemas.enrichment import AIEnrichmentPayload

ENRICHMENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "severity": {
            "type": "string",
            "enum": ["informational", "low", "medium", "high", "critical"],
        },
        "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
        "tags": {"type": "array", "items": {"type": "string"}},
        "cves": {"type": "array", "items": {"type": "string"}},
        "iocs": {"type": "array", "items": {"type": "string"}},
        "mitre_attack": {"type": "array", "items": {"type": "string"}},
        "recommended_actions": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "summary",
        "severity",
        "confidence",
        "tags",
        "cves",
        "iocs",
        "mitre_attack",
        "recommended_actions",
    ],
    "additionalProperties": False,
}


class OpenRouterConfigurationError(RuntimeError):
    pass


class OpenRouterResponseError(RuntimeError):
    pass


def item_prompt(*, title: str, content: str, source_name: str | None, url: str) -> str:
    return "\n".join(
        [
            "Analyze this cyber threat intelligence item.",
            "Return only structured JSON matching the requested schema.",
            "Keep the summary factual and avoid adding unsupported claims.",
            "",
            f"Source: {source_name or 'unknown'}",
            f"URL: {url}",
            f"Title: {title}",
            "",
            "Content:",
            content,
        ]
    )


def parse_payload(raw_content: str) -> AIEnrichmentPayload:
    if not isinstance(raw_content, str) or not raw_content.strip():
        raise OpenRouterResponseError("OpenRouter response content was empty")

    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise OpenRouterResponseError("OpenRouter response was not valid JSON") from exc

    try:
        return AIEnrichmentPayload.model_validate(parsed)
    except ValidationError as exc:
        raise OpenRouterResponseError(
            "OpenRouter response did not match enrichment schema"
        ) from exc


async def enrich_with_openrouter(
    *,
    settings: Settings,
    title: str,
    content: str,
    source_name: str | None,
    url: str,
) -> tuple[AIEnrichmentPayload, dict[str, Any]]:
    api_key = settings.openrouter_api_key.get_secret_value() if settings.openrouter_api_key else ""

    if not api_key:
        raise OpenRouterConfigurationError("OPENROUTER_API_KEY is not configured")

    prompt = item_prompt(
        title=title,
        content=content[: settings.openrouter_max_input_chars],
        source_name=source_name,
        url=url,
    )
    request_body: dict[str, Any] = {
        "model": settings.openrouter_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a senior cyber threat intelligence analyst. "
                    "Extract defensive, evidence-bound enrichment only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 900,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "cybersec_ai_enrichment",
                "strict": True,
                "schema": ENRICHMENT_SCHEMA,
            },
        },
        "provider": {"require_parameters": True},
        "plugins": [{"id": "response-healing"}],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.openrouter_app_url,
        "X-OpenRouter-Title": settings.openrouter_app_title,
    }

    async with httpx.AsyncClient(timeout=settings.openrouter_request_timeout_seconds) as client:
        response = await client.post(
            f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",
            json=request_body,
            headers=headers,
        )
        response.raise_for_status()
        raw_response = response.json()

    try:
        raw_content = raw_response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenRouterResponseError(
            "OpenRouter response did not contain message content"
        ) from exc

    return parse_payload(raw_content), raw_response
