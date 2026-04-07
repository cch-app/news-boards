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
    assert b"General" in rv.data
    assert b'id="loading-skeleton-template"' in rv.data


def test_index_defaults_to_ai_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "BLOG_SOURCES",
        json.dumps(
            [
                {"name": "AI feed", "url": "https://ai.example/feed.xml", "category": "AI"},
                {
                    "name": "Frontend feed",
                    "url": "https://fe.example/feed.xml",
                    "category": "Frontend",
                },
            ]
        ),
    )

    def fake_fetch(sources: list, n: int, **kwargs: object) -> list[SourceResult]:
        return [
            SourceResult(source=sources[0], entries=[], error=None),
            SourceResult(source=sources[1], entries=[], error=None),
        ]

    monkeypatch.setattr("news_boards.routes.fetch_all_sources", fake_fetch)

    from news_boards.app_factory import create_app

    app = create_app()
    rv = app.test_client().get("/")
    assert rv.status_code == 200
    data = rv.data.decode()
    assert "AI" in data
    assert "Frontend" in data
    assert "AI feed" in data
    assert "Frontend feed" not in data


def test_index_category_query_param_selects_category(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "BLOG_SOURCES",
        json.dumps(
            [
                {"name": "AI feed", "url": "https://ai.example/feed.xml", "category": "AI"},
                {
                    "name": "Frontend feed",
                    "url": "https://fe.example/feed.xml",
                    "category": "Frontend",
                },
            ]
        ),
    )

    def fake_fetch(sources: list, n: int, **kwargs: object) -> list[SourceResult]:
        return [
            SourceResult(source=sources[0], entries=[], error=None),
            SourceResult(source=sources[1], entries=[], error=None),
        ]

    monkeypatch.setattr("news_boards.routes.fetch_all_sources", fake_fetch)

    from news_boards.app_factory import create_app

    app = create_app()
    rv = app.test_client().get("/?category=Frontend")
    assert rv.status_code == 200
    data = rv.data.decode()
    assert "AI" in data
    assert "Frontend" in data
    assert "Frontend feed" in data
    assert "AI feed" not in data


def test_index_category_query_param_falls_back_to_ai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "BLOG_SOURCES",
        json.dumps(
            [
                {"name": "AI feed", "url": "https://ai.example/feed.xml", "category": "AI"},
                {
                    "name": "Frontend feed",
                    "url": "https://fe.example/feed.xml",
                    "category": "Frontend",
                },
            ]
        ),
    )

    def fake_fetch(sources: list, n: int, **kwargs: object) -> list[SourceResult]:
        return [
            SourceResult(source=sources[0], entries=[], error=None),
            SourceResult(source=sources[1], entries=[], error=None),
        ]

    monkeypatch.setattr("news_boards.routes.fetch_all_sources", fake_fetch)

    from news_boards.app_factory import create_app

    app = create_app()
    rv = app.test_client().get("/?category=DoesNotExist")
    assert rv.status_code == 200
    data = rv.data.decode()
    assert "AI feed" in data
    assert "Frontend feed" not in data


def test_index_category_menu_links_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "BLOG_SOURCES",
        json.dumps(
            [
                {"name": "AI feed", "url": "https://ai.example/feed.xml", "category": "AI"},
                {
                    "name": "Frontend feed",
                    "url": "https://fe.example/feed.xml",
                    "category": "Frontend",
                },
            ]
        ),
    )

    def fake_fetch(sources: list, n: int, **kwargs: object) -> list[SourceResult]:
        return [
            SourceResult(source=sources[0], entries=[], error=None),
            SourceResult(source=sources[1], entries=[], error=None),
        ]

    monkeypatch.setattr("news_boards.routes.fetch_all_sources", fake_fetch)

    from news_boards.app_factory import create_app

    app = create_app()
    rv = app.test_client().get("/")
    assert rv.status_code == 200
    data = rv.data.decode()
    assert "/?category=AI" in data
    assert "/?category=Frontend" in data
