# Long-lived WSGI for local Docker and container hosts (not used by Vercel serverless).
FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir --upgrade pip

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir .

# Production WSGI server (not required on Vercel).
RUN pip install --no-cache-dir "gunicorn>=22.0,<24"

EXPOSE 8000

# Factory apps: use module:callable() — not a separate --factory CLI flag.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "news_boards:create_app()"]
