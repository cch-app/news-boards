"""Shared Flask extensions (avoid circular imports)."""

from flask_caching import Cache

cache = Cache()
