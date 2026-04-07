"""Tests for environment configuration."""

from __future__ import annotations

import json

import pytest

from news_boards.config import (
    ConfigError,
    load_blog_sources,
    load_cache_ttl_seconds,
    load_posts_per_source,
)


def test_blog_sources_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BLOG_SOURCES", raising=False)
    with pytest.raises(ConfigError, match="BLOG_SOURCES"):
        load_blog_sources()


def test_blog_sources_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BLOG_SOURCES", "not json")
    with pytest.raises(ConfigError, match="valid JSON"):
        load_blog_sources()


def test_blog_sources_not_array(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BLOG_SOURCES", "{}")
    with pytest.raises(ConfigError, match="array"):
        load_blog_sources()


def test_blog_sources_empty_array(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BLOG_SOURCES", "[]")
    with pytest.raises(ConfigError, match="at least one"):
        load_blog_sources()


def test_blog_sources_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "BLOG_SOURCES",
        json.dumps([{"name": " A ", "url": " https://example.com/feed.xml "}]),
    )
    sources = load_blog_sources()
    assert len(sources) == 1
    assert sources[0].name == "A"
    assert sources[0].url == "https://example.com/feed.xml"
    assert sources[0].id == "src-0"
    assert sources[0].category == "General"


def test_blog_sources_category_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "BLOG_SOURCES",
        json.dumps(
            [
                {
                    "name": "A",
                    "url": "https://a.example/feed.xml",
                    "category": " AI ",
                }
            ]
        ),
    )
    sources = load_blog_sources()
    assert sources[0].category == "AI"


def test_blog_sources_category_empty_string_is_general(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "BLOG_SOURCES",
        json.dumps([{"name": "A", "url": "https://a.example/feed.xml", "category": "  "}]),
    )
    sources = load_blog_sources()
    assert sources[0].category == "General"


def test_blog_sources_category_wrong_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "BLOG_SOURCES",
        json.dumps([{"name": "A", "url": "https://a.example/feed.xml", "category": 1}]),
    )
    with pytest.raises(ConfigError, match='"category"'):
        load_blog_sources()


def test_posts_per_source_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("POSTS_PER_SOURCE", raising=False)
    assert load_posts_per_source() == 6


def test_posts_per_source_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTS_PER_SOURCE", "0")
    with pytest.raises(ConfigError):
        load_posts_per_source()


def test_cache_ttl_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CACHE_TTL_SECONDS", raising=False)
    assert load_cache_ttl_seconds() == 300
