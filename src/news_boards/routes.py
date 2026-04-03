"""HTTP routes."""

from __future__ import annotations

from flask import Blueprint, current_app, render_template

from news_boards.extensions import cache
from news_boards.feeds import SourceResult, fetch_all_sources

bp = Blueprint("main", __name__)

_CACHE_KEY = "feed_results_v1"


@bp.route("/")
def index():
    """Grouped latest posts per configured source."""
    err = current_app.config.get("BLOG_SOURCES_ERROR")
    if err:
        return render_template("error.html", error=err), 503

    sources = current_app.config["BLOG_SOURCES"]
    n = int(current_app.config["POSTS_PER_SOURCE"])
    ttl = int(current_app.config["CACHE_TTL_SECONDS"])

    results: list[SourceResult]
    if ttl > 0:
        cached = cache.get(_CACHE_KEY)
        if cached is not None:
            results = cached
        else:
            results = fetch_all_sources(sources, n)
            cache.set(_CACHE_KEY, results, timeout=ttl)
    else:
        results = fetch_all_sources(sources, n)

    return render_template("index.html", results=results, posts_per_source=n)
