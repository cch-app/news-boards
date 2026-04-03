"""Tests for feed fetching and parsing (mocked HTTP)."""

from __future__ import annotations

import httpx
import pytest

from news_boards import feeds as feeds_mod
from news_boards.config import BlogSource
from news_boards.feeds import fetch_source_entries

SAMPLE_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test</title>
    <lastBuildDate>Wed, 25 Mar 2026 00:00:00 +0000</lastBuildDate>
    <item>
      <title>First post</title>
      <link>https://example.com/p1</link>
      <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Second post</title>
      <link>https://example.com/p2</link>
      <pubDate>Tue, 02 Jan 2024 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

HTML_WITH_FEED = """<!DOCTYPE html>
<html><head>
<link rel="alternate" type="application/rss+xml" title="Feed" href="/feed.xml" />
</head><body></body></html>
"""


def test_fetch_direct_rss(
    monkeypatch: pytest.MonkeyPatch, disable_feed_ssrf_check: None
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).startswith("https://blog.test/")
        return httpx.Response(
            200,
            content=SAMPLE_RSS,
            headers={"content-type": "application/rss+xml; charset=utf-8"},
        )

    monkeypatch.setattr(
        feeds_mod,
        "_client_factory",
        lambda timeout: httpx.Client(
            transport=httpx.MockTransport(handler),
            follow_redirects=False,
        ),
    )
    src = BlogSource(id="t", name="Test", url="https://blog.test/feed.xml")
    result = fetch_source_entries(src, posts_per_source=10)
    assert result.error is None
    assert len(result.entries) == 2
    assert result.entries[0].title == "Second post"
    assert result.entries[0].link == "https://example.com/p2"
    assert result.entries[0].published and "2024-01-02" in result.entries[0].published
    assert result.last_build_display and "2026-03-25" in result.last_build_display


def test_fetch_html_discovers_feed(
    monkeypatch: pytest.MonkeyPatch, disable_feed_ssrf_check: None
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        u = str(request.url)
        if u.rstrip("/").endswith("blog.test") or u.endswith("blog.test/"):
            return httpx.Response(
                200,
                text=HTML_WITH_FEED,
                headers={"content-type": "text/html; charset=utf-8"},
            )
        if "/feed.xml" in u:
            return httpx.Response(
                200,
                content=SAMPLE_RSS,
                headers={"content-type": "application/rss+xml"},
            )
        return httpx.Response(404)

    monkeypatch.setattr(
        feeds_mod,
        "_client_factory",
        lambda timeout: httpx.Client(
            transport=httpx.MockTransport(handler),
            follow_redirects=False,
        ),
    )
    src = BlogSource(id="t", name="Test", url="https://blog.test/")
    result = fetch_source_entries(src, posts_per_source=1)
    assert result.error is None
    assert len(result.entries) == 1
    assert result.entries[0].title == "Second post"


def test_html_no_feed_link(
    monkeypatch: pytest.MonkeyPatch, disable_feed_ssrf_check: None
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text="<html><head></head><body>hi</body></html>",
            headers={"content-type": "text/html"},
        )

    monkeypatch.setattr(
        feeds_mod,
        "_client_factory",
        lambda timeout: httpx.Client(
            transport=httpx.MockTransport(handler),
            follow_redirects=False,
        ),
    )
    src = BlogSource(id="t", name="Test", url="https://blog.test/")
    result = fetch_source_entries(src, posts_per_source=5)
    assert result.error is not None
    assert "No RSS or Atom feed" in result.error
