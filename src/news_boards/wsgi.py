"""WSGI application instance for Vercel and other WSGI hosts."""

from news_boards import create_app

app = create_app()
