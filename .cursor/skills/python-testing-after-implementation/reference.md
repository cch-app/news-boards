# Testing reference (pytest + uv)

## Layout (typical)

```
tests/
  conftest.py          # shared fixtures
  unit/
    test_foo.py
  integration/
    test_api.py
```

Use **`test_*.py`** or `*_test.py` per pytest discovery defaults.

## Markers (`pyproject.toml`)

```toml
[tool.pytest.ini_options]
markers = [
    "integration: hits DB, network, or external services",
]
```

Register markers to avoid warnings; filter: `uv run pytest -m "not integration"`.

## Async tests

For **asyncio** code, use **`pytest-asyncio`** with **`@pytest.mark.asyncio`** (or configured asyncio mode) so coroutines are awaited correctly.

## HTTP / ASGI

- **FastAPI / Starlette:** `TestClient` or **`httpx.AsyncClient(app=…, transport=ASGITransport(…))`** for async routes.

## Fixtures

- Prefer **function-scoped** fixtures unless broader scope is required.
- Use **`tmp_path`** / **`tmp_path_factory`** for filesystem integration tests.
