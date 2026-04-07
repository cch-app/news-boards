"""HTTP routes."""

from __future__ import annotations

from flask import Blueprint, current_app, render_template, request

from news_boards.extensions import cache
from news_boards.feeds import SourceResult, fetch_all_sources

bp = Blueprint("main", __name__)

_CACHE_KEY = "feed_results_v1"


def _group_results_by_category(
    results: list[SourceResult],
) -> list[tuple[str, list[SourceResult]]]:
    """Preserve first-seen category order and source order within each category."""
    order: list[str] = []
    buckets: dict[str, list[SourceResult]] = {}
    for r in results:
        cat = r.source.category
        if cat not in buckets:
            order.append(cat)
            buckets[cat] = []
        buckets[cat].append(r)
    return [(c, buckets[c]) for c in order]


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

    grouped_results = _group_results_by_category(results)
    categories = [name for name, _blocks in grouped_results]

    requested = request.args.get("category")
    if requested in categories:
        selected_category = requested
    elif "AI" in categories:
        selected_category = "AI"
    elif categories:
        selected_category = categories[0]
    else:
        selected_category = None

    blocks: list[SourceResult] = []
    if selected_category is not None:
        for name, blk in grouped_results:
            if name == selected_category:
                blocks = blk
                break

    return render_template(
        "index.html",
        categories=categories,
        selected_category=selected_category,
        blocks=blocks,
        posts_per_source=n,
    )
