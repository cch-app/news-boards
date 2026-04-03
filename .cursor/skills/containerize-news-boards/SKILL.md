---
name: containerize-news-boards
description: Builds and runs Docker images for the news-boards Flask app (Gunicorn WSGI) for local development and container hosts such as Fly.io, Railway, Render, or Google Cloud Run. Explains that Vercel uses managed Python serverless (requirements.txt + api/index.py), not a Docker runtime for the app. Use when the user asks for Docker, Docker Compose, containerization, Kubernetes, image builds, or running the app in a container alongside or instead of bare-metal local runs.
---

# Containerize news-boards

## Vercel vs Docker (read first)

| Environment | How this app runs | Use Docker? |
|-------------|-------------------|-------------|
| **Vercel** | Python **serverless** function: [`api/index.py`](../../../api/index.py) + [`vercel.json`](../../../vercel.json) + [`requirements.txt`](../../../requirements.txt) | **No** — Vercel does not execute your Dockerfile as the production runtime for this pattern. Keep deploying via Git + env vars as documented in [README.md](../../../README.md). |
| **Local / Fly / Railway / Cloud Run / etc.** | Long-lived process: **Gunicorn** + Flask `create_app` | **Yes** — use [`Dockerfile`](../../../Dockerfile) and optionally [`docker-compose.yml`](../../../docker-compose.yml). |

If the goal is “same app on laptop and Vercel,” the split is: **Docker locally (or on a container platform)** and **serverless on Vercel**, not one Docker image deployed to both.

## Local Docker workflow

1. **Set config** — `BLOG_SOURCES` is required (JSON array). Same shape as [README.md](README.md). Optionally `POSTS_PER_SOURCE`, `CACHE_TTL_SECONDS`, `SECRET_KEY`.
2. **Build** — `docker compose build` (or `make docker-build`; see [Makefile](../../../Makefile)).
3. **Run** — `docker compose up` with env set, or `make docker-up`.
4. **Smoke test** — `curl -sS http://localhost:8000/` expects HTML.

## Dockerfile expectations

- **Base**: `python:3.13-slim` (match [`pyproject.toml`](../../../pyproject.toml) `requires-python`).
- **Install**: `pip install .` from repo root so `news_boards` is importable (hatchling build).
- **Server**: `gunicorn` with WSGI app **`news_boards:create_app()`** (trailing `()` selects the Flask application factory; do not pass a nonexistent `--factory` CLI flag).
- **Bind**: `0.0.0.0` and a fixed port (e.g. `8000`).
- **Env**: pass `BLOG_SOURCES` at runtime (`docker run -e` / compose `environment` / platform secrets).

Details and example commands: [reference.md](reference.md).

## What to put in `.dockerignore`

Exclude `.venv`, `.git`, `__pycache__`, `.pytest_cache`, `.env` (secrets), and large dev-only trees so images stay small and builds fast. See repo [`.dockerignore`](../../../.dockerignore).

## Agent checklist when adding or changing containers

- [ ] Do not remove or bypass the Vercel entry (`api/index.py`) unless the user explicitly migrates off Vercel.
- [ ] Keep **one** WSGI story: `create_app()` from package `news_boards` (see [`src/news_boards/__init__.py`](../../../src/news_boards/__init__.py)).
- [ ] Never bake `BLOG_SOURCES` secrets into the image; use runtime env or orchestrator secrets.
- [ ] After changing Python deps for the **image**, rebuild the image; for **Vercel**, regenerate `requirements.txt` with `make requirements` (see [Makefile](../../../Makefile)) or `uv export --no-hashes --no-dev`.

## Additional resources

- [reference.md](reference.md) — Gunicorn command, compose patterns, platform notes
