from __future__ import annotations

import re
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser


class ReadableHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._ignored_depth += 1
        elif tag in {"br", "p", "div", "li", "tr", "h1", "h2", "h3", "h4"}:
            self._parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._ignored_depth:
            self._ignored_depth -= 1
        elif tag in {"p", "div", "li", "tr", "h1", "h2", "h3", "h4"}:
            self._parts.append(" ")

    def handle_data(self, data: str) -> None:
        if self._ignored_depth == 0:
            self._parts.append(data)

    def text(self) -> str:
        return " ".join(self._parts)


HTML_PATTERN = re.compile(r"<[a-zA-Z][^>]*>")
WHITESPACE_PATTERN = re.compile(r"\s+")
WORD_PATTERN = re.compile(r"[a-zA-ZÀ-ÿ']+")

LANGUAGE_MARKERS: dict[str, set[str]] = {
    "en": {
        "and",
        "are",
        "attack",
        "campaign",
        "critical",
        "devices",
        "exploit",
        "reported",
        "ransomware",
        "the",
        "vulnerability",
    },
    "es": {
        "amenaza",
        "ataque",
        "campaña",
        "crítica",
        "de",
        "dispositivos",
        "el",
        "explotan",
        "la",
        "los",
        "ransomware",
        "vulnerabilidad",
    },
    "fr": {"attaque", "campagne", "critique", "des", "la", "les", "menace", "vulnérabilité"},
    "de": {"angriff", "bedrohung", "der", "die", "kampagne", "kritische", "schwachstelle"},
}


def normalize_whitespace(value: str | None) -> str:
    if not value:
        return ""

    return WHITESPACE_PATTERN.sub(" ", unescape(value)).strip()


def strip_html(value: str) -> str:
    parser = ReadableHTMLParser()
    parser.feed(value)
    parser.close()
    return normalize_whitespace(parser.text())


def normalize_content(value: str | None) -> str:
    normalized = normalize_whitespace(value)

    if not normalized:
        return ""

    if HTML_PATTERN.search(normalized):
        return strip_html(normalized)

    return normalized


def detect_language(*values: str) -> str:
    text = " ".join(value for value in values if value).lower()
    words = WORD_PATTERN.findall(text)

    if not words:
        return "unknown"

    scores = {
        language: sum(1 for word in words if word in markers)
        for language, markers in LANGUAGE_MARKERS.items()
    }

    if any(character in text for character in "áéíóúñ¿¡"):
        scores["es"] += 2
    if any(character in text for character in "àâçèêëîïôùûüÿœ"):
        scores["fr"] += 2
    if any(character in text for character in "äöüß"):
        scores["de"] += 2

    language, score = max(scores.items(), key=lambda item: item[1])
    return language if score > 0 else "unknown"


def normalized_hash(title: str, content: str) -> str:
    canonical = f"{title}\n{content}".casefold()
    return sha256(canonical.encode("utf-8")).hexdigest()
