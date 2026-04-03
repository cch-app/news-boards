"""Tests for URL safety (SSRF mitigation)."""

from __future__ import annotations

import pytest

from news_boards.url_safety import UnsafeUrlError, assert_fetchable_http_url


def test_rejects_non_http_scheme() -> None:
    with pytest.raises(UnsafeUrlError, match="http"):
        assert_fetchable_http_url("ftp://example.com/")


def test_rejects_loopback_literal() -> None:
    with pytest.raises(UnsafeUrlError, match="public fetch"):
        assert_fetchable_http_url("http://127.0.0.1/feed.xml")
