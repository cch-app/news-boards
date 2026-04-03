"""Fetch URLs, discover feeds, parse entries, and apply top-N."""

from __future__ import annotations

import calendar
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin

import feedparser
import httpx

from news_boards.config import BlogSource
from news_boards.url_safety import UnsafeUrlError, assert_fetchable_http_url

# Browser-like User-Agent (many feeds block generic clients)
DEFAULT_UA = (
    "Mozilla/5.0 (compatible; NewsBoards/0.1; +https://github.com/) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

FEED_TYPES = frozenset(
    {
        "application/rss+xml",
        "application/atom+xml",
        "application/xml",
        "text/xml",
        "application/rdf+xml",
    }
)


@dataclass(frozen=True, slots=True)
class FeedEntry:
    """Normalized post for display."""

    title: str
    link: str
    published: str | None


@dataclass(frozen=True, slots=True)
class SourceResult:
    """Parsed posts or error for one source."""

    source: BlogSource
    entries: list[FeedEntry]
    error: str | None
    last_build_display: str | None = None


class _FeedLinkParser(HTMLParser):
    """Collect <link rel='alternate' href='...' type='...'> candidates."""

    def __init__(self) -> None:
        super().__init__()
        self._candidates: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "link":
            return
        ad = {k.lower(): (v or "") for k, v in attrs}
        rel = ad.get("rel", "").lower()
        if "alternate" not in rel.split():
            return
        href = ad.get("href", "").strip()
        typ = ad.get("type", "").strip().lower()
        if not href:
            return
        if typ in FEED_TYPES or "xml" in typ or "rss" in typ or "atom" in typ:
            self._candidates.append((href, typ))


def _looks_like_feed_body(content_type: str | None, body: bytes) -> bool:
    ct = (content_type or "").lower()
    if any(x in ct for x in ("rss+xml", "atom+xml", "application/xml", "text/xml")):
        return True
    head = body[:512].lstrip()
    if head.startswith(b"<?xml") or head.startswith(b"<rss") or head.startswith(b"<feed"):
        return True
    return False


def _discover_feed_url_from_html(base_url: str, body: str) -> str | None:
    parser = _FeedLinkParser()
    try:
        parser.feed(body)
        parser.close()
    except Exception:
        return None
    for href, _typ in parser._candidates:
        absolute = urljoin(base_url, href)
        if absolute.startswith(("http://", "https://")):
            return absolute
    return None


def _format_struct_time(st: time.struct_time) -> str:
    """Format feedparser time_struct as YYYY-MM-DD HH:MM:SS +ZZZZ (UTC from struct)."""
    secs = calendar.timegm(st)
    dt = datetime.fromtimestamp(secs, tz=UTC)
    return dt.strftime("%Y-%m-%d %H:%M:%S %z")


def _format_display_datetime(raw: str) -> str:
    """Normalize RFC 2822 / similar strings to YYYY-MM-DD HH:MM:SS +ZZZZ."""
    try:
        dt = parsedate_to_datetime(raw.strip())
    except (TypeError, ValueError):
        return raw
    return dt.strftime("%Y-%m-%d %H:%M:%S %z")


def _format_entry_published(entry: Any) -> str | None:
    """Prefer parsed tuples; otherwise parse published/updated strings."""
    t = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if t:
        return _format_struct_time(t)
    raw = getattr(entry, "published", None) or getattr(entry, "updated", None)
    if raw:
        return _format_display_datetime(str(raw).strip())
    return None


def _feed_last_build_display(parsed: Any) -> str | None:
    """Channel-level last build / updated time for display next to source name."""
    feed = getattr(parsed, "feed", None)
    if not feed:
        return None
    t = (
        getattr(feed, "updated_parsed", None)
        or getattr(feed, "published_parsed", None)
        or getattr(feed, "lastbuilddate_parsed", None)
    )
    if t:
        return _format_struct_time(t)
    raw = None
    if hasattr(feed, "get"):
        raw = feed.get("lastbuilddate") or feed.get("updated") or feed.get("published")
    if not raw:
        raw = getattr(feed, "lastbuilddate", None) or getattr(feed, "updated", None)
    if raw:
        return _format_display_datetime(str(raw).strip())
    return None


def _entry_sort_key(entry: Any) -> tuple:
    """Prefer published_parsed, then updated_parsed."""
    t = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if t:
        return (0, t)
    return (1, (0, 0, 0, 0, 0, 0))


def _normalize_entries(parsed: Any, limit: int) -> list[FeedEntry]:
    items = list(getattr(parsed, "entries", []) or [])
    items.sort(key=_entry_sort_key, reverse=True)
    out: list[FeedEntry] = []
    for e in items[:limit]:
        title = getattr(e, "title", None) or "(no title)"
        title = str(title).strip() or "(no title)"
        link = getattr(e, "link", None) or ""
        link = str(link).strip()
        pub_s = _format_entry_published(e)
        out.append(FeedEntry(title=title, link=link, published=pub_s))
    return out


def _client_factory(timeout: float) -> httpx.Client:
    """Build an httpx client (overridable in tests via monkeypatch)."""
    return httpx.Client(
        timeout=httpx.Timeout(timeout, connect=min(5.0, timeout)),
        headers={"User-Agent": DEFAULT_UA},
        follow_redirects=False,
    )


def _get_with_safe_redirects(
    client: httpx.Client, url: str, max_redirects: int = 5
) -> httpx.Response:
    """GET following redirects manually so each hop is checked against SSRF rules."""
    current = url
    for _ in range(max_redirects + 1):
        assert_fetchable_http_url(current)
        r = client.get(current)
        if r.status_code in (301, 302, 303, 307, 308):
            loc = r.headers.get("location")
            if not loc:
                r.raise_for_status()
            current = urljoin(str(r.url), loc.strip())
            continue
        r.raise_for_status()
        return r
    raise RuntimeError("Too many redirects while fetching feed.")


def _fetch_feed_after_redirects(client: httpx.Client, url: str) -> tuple[str, httpx.Response]:
    """GET url with per-hop URL safety checks."""
    r = _get_with_safe_redirects(client, url)
    assert_fetchable_http_url(str(r.url))
    return str(r.url), r


def fetch_source_entries(
    source: BlogSource,
    posts_per_source: int,
    fetch_timeout_seconds: float = 8.0,
) -> SourceResult:
    """Resolve feed URL or HTML page, parse, return top posts_per_source entries."""
    try:
        assert_fetchable_http_url(source.url)
    except UnsafeUrlError as e:
        return SourceResult(source=source, entries=[], error=str(e))

    with _client_factory(fetch_timeout_seconds) as client:
        try:
            _final, resp = _fetch_feed_after_redirects(client, source.url)
        except UnsafeUrlError as e:
            return SourceResult(source=source, entries=[], error=str(e))
        except httpx.HTTPError as e:
            return SourceResult(
                source=source,
                entries=[],
                error=f"HTTP error while fetching {source.url!r}: {e}",
            )

        ctype = resp.headers.get("content-type", "").split(";")[0].strip()
        body = resp.content

        if _looks_like_feed_body(ctype, body):
            parsed = feedparser.parse(body)
            if getattr(parsed, "bozo", False) and not getattr(parsed, "entries", None):
                err = getattr(parsed, "bozo_exception", None)
                return SourceResult(
                    source=source,
                    entries=[],
                    error=f"Feed parse error: {err!s}",
                )
            entries = _normalize_entries(parsed, posts_per_source)
            return SourceResult(
                source=source,
                entries=entries,
                error=None,
                last_build_display=_feed_last_build_display(parsed),
            )

        # HTML: discover feed link
        try:
            text = resp.text
        except Exception as e:
            return SourceResult(
                source=source,
                entries=[],
                error=f"Could not decode response body: {e}",
            )

        feed_url = _discover_feed_url_from_html(str(resp.url), text)
        if not feed_url:
            return SourceResult(
                source=source,
                entries=[],
                error="No RSS or Atom feed found in the page (no suitable <link rel='alternate'>).",
            )

        try:
            assert_fetchable_http_url(feed_url)
            _final2, r2 = _fetch_feed_after_redirects(client, feed_url)
        except UnsafeUrlError as e:
            return SourceResult(source=source, entries=[], error=str(e))
        except httpx.HTTPError as e:
            return SourceResult(
                source=source,
                entries=[],
                error=f"HTTP error while fetching discovered feed {feed_url!r}: {e}",
            )

        parsed = feedparser.parse(r2.content)
        if getattr(parsed, "bozo", False) and not getattr(parsed, "entries", None):
            err = getattr(parsed, "bozo_exception", None)
            return SourceResult(
                source=source,
                entries=[],
                error=f"Feed parse error: {err!s}",
            )
        entries = _normalize_entries(parsed, posts_per_source)
        return SourceResult(
            source=source,
            entries=entries,
            error=None,
            last_build_display=_feed_last_build_display(parsed),
        )


def fetch_all_sources(
    sources: list[BlogSource],
    posts_per_source: int,
    max_workers: int = 4,
    fetch_timeout_seconds: float = 8.0,
) -> list[SourceResult]:
    """Fetch all sources in parallel (bounded pool)."""
    if not sources:
        return []
    workers = min(max_workers, len(sources))
    results: list[SourceResult | None] = [None] * len(sources)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {
            ex.submit(fetch_source_entries, s, posts_per_source, fetch_timeout_seconds): i
            for i, s in enumerate(sources)
        }
        for fut in as_completed(futs):
            idx = futs[fut]
            try:
                results[idx] = fut.result()
            except Exception as e:
                src = sources[idx]
                results[idx] = SourceResult(
                    source=src,
                    entries=[],
                    error=f"Unexpected error: {e}",
                )
    return [r for r in results if r is not None]
