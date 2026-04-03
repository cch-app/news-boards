"""Pytest fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture
def disable_feed_ssrf_check(monkeypatch: pytest.MonkeyPatch) -> None:
    """Skip DNS/SSRF checks so feed tests use MockTransport without real network."""
    monkeypatch.setattr("news_boards.feeds.assert_fetchable_http_url", lambda _url: None)
