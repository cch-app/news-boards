# News boards

Flask app that aggregates RSS/Atom feeds from URLs configured via environment variables, grouped by source. Intended for [Vercel](https://vercel.com/) (Python serverless).

## Local development

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
export BLOG_SOURCES='[{"name":"Example","url":"https://example.com/feed.xml"}]'
uv run flask --app news_boards:create_app run --debug
```

After `uv sync`, the package is installed in editable mode, so `news_boards` imports without extra `PYTHONPATH`.

Styling uses the [Tailwind Play CDN](https://tailwindcss.com/docs/installation/play-cdn) (browser JIT, no Node build). For a smaller CSS footprint or stricter production defaults, you can replace it later with a built Tailwind CSS pipeline.

## Docker (local or container hosts)

For a **long-lived** server (Gunicorn) in Docker—**not** how Vercel runs this app—use [`Dockerfile`](Dockerfile) and [`docker-compose.yml`](docker-compose.yml):

```bash
export BLOG_SOURCES='[{"name":"Anthropic","url":"https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml"}]'
make docker-build
make docker-up
```

Then open `http://localhost:8000/`. Agent-oriented notes and the Vercel vs Docker distinction live in [`.cursor/skills/containerize-news-boards/SKILL.md`](.cursor/skills/containerize-news-boards/SKILL.md).

## Vercel

1. Connect this repository to Vercel.
2. **Environment variables** (Project → Settings → Environment Variables): set `BLOG_SOURCES` for Production and Preview. Optional: `SITE_NAME`, `FOOTER_TEXT`, `POSTS_PER_SOURCE`, `CACHE_TTL_SECONDS`, `SECRET_KEY`.
3. Vercel installs dependencies from [`requirements.txt`](requirements.txt) (includes editable install `-e .`). Regenerate that file after dependency changes:

   ```bash
   uv export --no-hashes --no-dev -o requirements.txt
   ```

4. The serverless entry is [`api/index.py`](api/index.py); [`vercel.json`](vercel.json) rewrites all routes to it.

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `BLOG_SOURCES` | Yes | JSON array of objects. Each object must have **`name`** (string) and **`url`** (string). **`id`** is optional (defaults to `src-0`, `src-1`, …). URLs may be a direct RSS/Atom feed or a normal site URL; the app looks for `<link rel="alternate" type="application/rss+xml">` (and similar) on HTML pages. |
| `SITE_NAME` | No | Site title (default `News boards`). |
| `FOOTER_TEXT` | No | Footer copyright name in the UI (default `News boards by Alan Chan`) |
| `POSTS_PER_SOURCE` | No | Max posts per source (default `6`, max `100`). |
| `CACHE_TTL_SECONDS` | No | In-memory cache TTL in seconds (default `300`; `0` disables caching and refetches every request). |
| `SECRET_KEY` | No | Flask secret (set in production). |

Example value for `BLOG_SOURCES` (single line in the dashboard, or use multiline JSON if your host allows it):

```json
[
  {"name": "Ada", "url": "https://example.org/", "id": "ada"},
  {"name": "News", "url": "https://example.com/feed.atom"}
]
```

## Tests

```bash
uv run pytest
```
