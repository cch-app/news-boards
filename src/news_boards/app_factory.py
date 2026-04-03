"""Flask application factory."""

from __future__ import annotations

import os
from datetime import UTC, datetime

from flask import Flask

from news_boards.config import (
    ConfigError,
    load_blog_sources,
    load_cache_ttl_seconds,
    load_posts_per_source,
)
from news_boards.extensions import cache
from news_boards.routes import bp


def create_app() -> Flask:
    """Create and configure the Flask app."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        static_url_path="/static",
    )
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-in-production")

    app.config["BLOG_SOURCES_ERROR"] = None
    try:
        app.config["BLOG_SOURCES"] = load_blog_sources()
        app.config["POSTS_PER_SOURCE"] = load_posts_per_source()
        app.config["CACHE_TTL_SECONDS"] = load_cache_ttl_seconds()
    except ConfigError as e:
        app.config["BLOG_SOURCES_ERROR"] = str(e)
        app.config["BLOG_SOURCES"] = []
        app.config["POSTS_PER_SOURCE"] = 6
        app.config["CACHE_TTL_SECONDS"] = 300

    ttl = int(app.config["CACHE_TTL_SECONDS"])
    cache.init_app(
        app,
        config={
            "CACHE_TYPE": "SimpleCache",
            "CACHE_DEFAULT_TIMEOUT": ttl if ttl > 0 else 1,
        },
    )

    @app.context_processor
    def inject_template_globals() -> dict:
        name = os.environ.get("SITE_NAME", "").strip() or "News boards"
        footer_text = os.environ.get("FOOTER_TEXT", "").strip() or "News boards by Alan Chan"
        return {
            "current_year": datetime.now(UTC).year,
            "site_name": name,
            "footer_text": footer_text,
        }

    app.register_blueprint(bp)
    return app
