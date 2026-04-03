# Reference: Docker and Gunicorn

## Gunicorn application factory

The app exposes a **factory** `create_app`, plus a module-level `app` in [`news_boards.wsgi`](../../../src/news_boards/wsgi.py) for Vercel (`api/index.py` imports it).

Use (factory: the `()` on `create_app` tells Gunicorn to call the factory):

```bash
gunicorn --bind 0.0.0.0:8000 --workers 2 "news_boards:create_app()"
```

Adjust `--workers` for CPU; start with `2` for small instances.

## Environment variables

Same as production docs:

| Variable | Notes |
|----------|--------|
| `BLOG_SOURCES` | Required JSON array |
| `POSTS_PER_SOURCE` | Optional |
| `CACHE_TTL_SECONDS` | Optional; `0` = no cache |
| `SECRET_KEY` | Set in real deployments |

## docker compose pattern

- Map host port to container `8000`.
- Pass `BLOG_SOURCES` via `environment:` or `env_file: .env` (ensure `.env` is gitignored).
- Do not commit `.env` with real URLs if they are sensitive.

## Container platforms (not Vercel)

Typical flow:

1. Build image from this repo’s `Dockerfile`.
2. Push to a registry the platform supports.
3. Set the same env vars as in the table above.
4. Expose the HTTP port Gunicorn listens on.

Platforms differ in port expectations (some inject `PORT`); the agent may need a small entrypoint script that maps `PORT` → Gunicorn `--bind` if the user targets Heroku-style runtimes.

## Troubleshooting

- **Import errors** — Ensure `pip install .` runs from repo root and `src/news_boards` is packaged (see `pyproject.toml` hatch config).
- **503 on every request** — `BLOG_SOURCES` missing or invalid inside the container (`docker compose exec` / logs).
- **Vercel confusion** — Redeploying only `Dockerfile` does not change Vercel’s Python serverless deployment; use `vercel.json` + `requirements.txt` + dashboard env vars.
