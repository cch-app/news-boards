# News boards — common tasks (requires uv: https://docs.astral.sh/uv/)
UV ?= uv

.DEFAULT_GOAL := help

.PHONY: help sync run test lint format fix requirements verify clean docker-build docker-up

help:
	@echo "News boards — targets"
	@echo ""
	@echo "  make sync         Install/sync locked deps (incl. dev tools)"
	@echo "  make run          Run Flask locally (needs BLOG_SOURCES in env)"
	@echo "  make test         Run pytest"
	@echo "  make lint         Ruff check"
	@echo "  make format       Ruff format"
	@echo "  make fix          Ruff check --fix + format"
	@echo "  make requirements Write requirements.txt for Vercel (no dev deps)"
	@echo "  make verify       lint + test (good before commit or deploy)"
	@echo "  make clean        Remove __pycache__, .pytest_cache, .ruff_cache"
	@echo "  make docker-build Build the Docker image (Gunicorn; not used by Vercel)"
	@echo "  make docker-up    docker compose up (needs BLOG_SOURCES)"
	@echo ""
	@echo "Examples:"
	@echo "  export BLOG_SOURCES='[{\"name\":\"Demo\",\"url\":\"https://example.com/feed.xml\"}]'"
	@echo "  make run"
	@echo ""
	@echo "  make requirements && git add requirements.txt   # after changing pyproject/uv.lock"

sync:
	$(UV) sync

# Dev server: set BLOG_SOURCES first (see README.md).
run:
	$(UV) run flask --app news_boards:create_app run --debug

test:
	$(UV) run pytest

lint:
	$(UV) run ruff check src tests

format:
	$(UV) run ruff format src tests

fix:
	$(UV) run ruff check --fix src tests
	$(UV) run ruff format src tests

# Regenerate what Vercel installs via pip; run after dependency changes.
requirements:
	$(UV) export --no-hashes --no-dev -o requirements.txt

verify: lint test

clean:
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage
	@$(UV) run python -c "import pathlib, shutil; \
[shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__') \
 if '.venv' not in p.parts]"
	@echo "Cleaned caches (venv untouched)."

docker-build:
	docker compose build

docker-up:
	docker compose up --build -d
