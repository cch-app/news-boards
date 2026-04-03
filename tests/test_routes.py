"""Flask route tests."""

from __future__ import annotations

import json

import pytest

from news_boards.feeds import SourceResult


def test_index_503_when_blog_sources_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BLOG_SOURCES", raising=False)
    from news_boards.app_factory import create_app

    app = create_app()
    rv = app.test_client().get("/")
    assert rv.status_code == 503
    assert b"Configuration required" in rv.data


def test_index_200_with_mocked_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "BLOG_SOURCES",
        json.dumps([{"name": "My blog", "url": "https://example.com/feed.xml"}]),
    )

    def fake_fetch(sources: list, n: int, **kwargs: object) -> list[SourceResult]:
        return [
            SourceResult(
                source=sources[0],
                entries=[],
                error=None,
            )
        ]

    monkeypatch.setattr("news_boards.routes.fetch_all_sources", fake_fetch)

    from news_boards.app_factory import create_app

    app = create_app()
    rv = app.test_client().get("/")
    assert rv.status_code == 200
    assert b"My blog" in rv.data
