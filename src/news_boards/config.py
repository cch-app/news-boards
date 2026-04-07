"""Load and validate environment-driven configuration."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any


class ConfigError(Exception):
    """Invalid or missing configuration."""


@dataclass(frozen=True, slots=True)
class BlogSource:
    """A configured blog feed or homepage URL."""

    id: str
    name: str
    url: str
    category: str = "General"


def _parse_sources(raw: str) -> list[BlogSource]:
    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ConfigError(
            "BLOG_SOURCES must be valid JSON array of objects with "
            '"name" and "url" keys (optional "id", "category"). Parse error: '
            f"{e.msg} at position {e.pos}."
        ) from e
    if not isinstance(data, list):
        raise ConfigError("BLOG_SOURCES must be a JSON array.")
    out: list[BlogSource] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ConfigError(f"BLOG_SOURCES[{i}] must be an object, not {type(item).__name__}.")
        name = item.get("name")
        url = item.get("url")
        if not isinstance(name, str) or not name.strip():
            raise ConfigError(f'BLOG_SOURCES[{i}] needs a non-empty string "name".')
        if not isinstance(url, str) or not url.strip():
            raise ConfigError(f'BLOG_SOURCES[{i}] needs a non-empty string "url".')
        sid = item.get("id")
        if sid is not None and not isinstance(sid, str):
            raise ConfigError(f'BLOG_SOURCES[{i}] "id" must be a string if present.')
        raw_cat = item.get("category")
        if raw_cat is not None and not isinstance(raw_cat, str):
            raise ConfigError(f'BLOG_SOURCES[{i}] "category" must be a string if present.')
        category = "General"
        if isinstance(raw_cat, str) and raw_cat.strip():
            category = raw_cat.strip()
        out.append(
            BlogSource(
                id=(sid.strip() if isinstance(sid, str) and sid.strip() else f"src-{i}"),
                name=name.strip(),
                url=url.strip(),
                category=category,
            )
        )
    if not out:
        raise ConfigError("BLOG_SOURCES must contain at least one source.")
    return out


def load_blog_sources() -> list[BlogSource]:
    """Parse BLOG_SOURCES from the environment."""
    raw = os.environ.get("BLOG_SOURCES")
    if raw is None or not str(raw).strip():
        raise ConfigError(
            "Set the BLOG_SOURCES environment variable to a JSON array, for example: "
            '[{"name": "Example", "url": "https://example.com/feed.xml", '
            '"category": "General"}] (category is optional; defaults to General).'
        )
    return _parse_sources(raw.strip())


def load_posts_per_source() -> int:
    """Max posts per source from POSTS_PER_SOURCE (default 6)."""
    raw = os.environ.get("POSTS_PER_SOURCE", "6").strip()
    try:
        n = int(raw)
    except ValueError as e:
        raise ConfigError("POSTS_PER_SOURCE must be a positive integer.") from e
    if n < 1 or n > 100:
        raise ConfigError("POSTS_PER_SOURCE must be between 1 and 100.")
    return n


def load_cache_ttl_seconds() -> int:
    """Cache TTL from CACHE_TTL_SECONDS (default 300)."""
    raw = os.environ.get("CACHE_TTL_SECONDS", "300").strip()
    try:
        ttl = int(raw)
    except ValueError as e:
        raise ConfigError("CACHE_TTL_SECONDS must be a non-negative integer.") from e
    if ttl < 0 or ttl > 86400:
        raise ConfigError("CACHE_TTL_SECONDS must be between 0 and 86400.")
    return ttl
