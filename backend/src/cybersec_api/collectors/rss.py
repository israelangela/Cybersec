from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from time import struct_time
from typing import Any, Protocol
from urllib.parse import urlparse

import feedparser
import httpx
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from cybersec_api.core.config import get_settings
from cybersec_api.crud.items import item_exists
from cybersec_api.models.item import Item
from cybersec_api.models.source import Source


class FeedFetcher(Protocol):
    async def __call__(self, url: str) -> bytes:
        pass


@dataclass(slots=True)
class ParsedFeedEntry:
    title: str
    url: str
    external_id: str | None
    summary: str | None
    raw_content: str | None
    published_at: datetime | None
    content_hash: str


@dataclass(slots=True)
class CollectionStats:
    source_id: str
    source_name: str
    status: str = "ok"
    fetched: int = 0
    created: int = 0
    duplicates: int = 0
    skipped: int = 0
    error: str | None = None


def validate_fetch_url(url: str) -> None:
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http and https source URLs are supported")


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = " ".join(value.split())
    return normalized or None


def hash_entry(*parts: str | None) -> str:
    normalized = "\n".join(part or "" for part in parts)
    return sha256(normalized.encode("utf-8")).hexdigest()


def parsed_datetime(value: struct_time | None) -> datetime | None:
    if value is None:
        return None

    return datetime(*value[:6], tzinfo=UTC)


def entry_value(entry: Any, key: str) -> Any:
    if isinstance(entry, dict):
        return entry.get(key)

    return getattr(entry, key, None)


def parse_feed_entries(content: bytes) -> list[ParsedFeedEntry]:
    parsed = feedparser.parse(content)
    entries: list[ParsedFeedEntry] = []

    for entry in parsed.entries:
        title = normalize_text(entry_value(entry, "title")) or "Untitled intelligence item"
        url = normalize_text(entry_value(entry, "link"))

        if not url:
            entries.append(
                ParsedFeedEntry(
                    title=title,
                    url="",
                    external_id=None,
                    summary=None,
                    raw_content=None,
                    published_at=None,
                    content_hash="",
                )
            )
            continue

        external_id = normalize_text(entry_value(entry, "id") or entry_value(entry, "guid"))
        summary = normalize_text(entry_value(entry, "summary"))
        raw_content = summary
        content = entry_value(entry, "content")

        if isinstance(content, list) and content:
            first_content = content[0]
            raw_content = normalize_text(entry_value(first_content, "value")) or summary

        published_at = parsed_datetime(
            entry_value(entry, "published_parsed") or entry_value(entry, "updated_parsed")
        )

        entries.append(
            ParsedFeedEntry(
                title=title,
                url=url,
                external_id=external_id,
                summary=summary,
                raw_content=raw_content,
                published_at=published_at,
                content_hash=hash_entry(title, url, summary, raw_content),
            )
        )

    return entries


async def fetch_feed(url: str) -> bytes:
    settings = get_settings()
    validate_fetch_url(url)

    async with httpx.AsyncClient(
        follow_redirects=True,
        max_redirects=5,
        timeout=settings.collector_request_timeout_seconds,
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        content = response.content

    if len(content) > settings.collector_max_response_bytes:
        raise ValueError("Feed response exceeds configured maximum size")

    return content


async def collect_source(
    session: AsyncSession,
    source: Source,
    *,
    fetcher: FeedFetcher | None = None,
) -> CollectionStats:
    source_uuid = source.id
    source_id = str(source_uuid)
    source_name = source.name
    source_error_count = source.error_count or 0
    stats = CollectionStats(source_id=source_id, source_name=source_name)
    feed_fetcher = fetcher or fetch_feed

    if not source.is_enabled:
        stats.status = "skipped"
        stats.skipped = 1
        stats.error = "Source is disabled"
        return stats

    if source.source_type != "rss":
        stats.status = "skipped"
        stats.skipped = 1
        stats.error = "Only RSS sources are supported in Phase 2"
        return stats

    try:
        content = await feed_fetcher(source.url)
        entries = parse_feed_entries(content)
        stats.fetched = len(entries)

        for entry in entries:
            if not entry.url:
                stats.skipped += 1
                continue

            exists = await item_exists(
                session,
                source_id=source.id,
                url=entry.url,
                content_hash=entry.content_hash,
                external_id=entry.external_id,
            )

            if exists:
                stats.duplicates += 1
                continue

            session.add(
                Item(
                    source_id=source.id,
                    title=entry.title,
                    url=entry.url,
                    external_id=entry.external_id,
                    content_hash=entry.content_hash,
                    summary=entry.summary,
                    raw_content=entry.raw_content,
                    status="raw",
                    published_at=entry.published_at,
                )
            )
            stats.created += 1

        source.last_fetched_at = datetime.now(UTC)
        source.last_error = None
        source.error_count = 0
        await session.commit()
        return stats
    except Exception as exc:
        await session.rollback()
        await session.execute(
            update(Source)
            .where(Source.id == source_uuid)
            .values(last_error=str(exc), error_count=source_error_count + 1)
        )
        await session.commit()
        return CollectionStats(
            source_id=source_id,
            source_name=source_name,
            status="error",
            error=str(exc),
        )
