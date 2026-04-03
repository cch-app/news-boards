---
name: python-testing-after-implementation
description: Adds or updates pytest unit and integration tests when a feature or fix is implemented so behavior is locked in before work is considered done. Use when finishing a module, endpoint, or bugfix; when the user asks for tests, coverage, or regression checks; or before merge when implementation is complete.
---

# Tests after implementation

## When to apply

Whenever implementation is **functionally complete** (not only “compiles”), add or extend tests **in the same change** unless the user explicitly defers testing. Treat “done” as **code + tests + `uv run pytest` passing**.

## Unit tests

- **Scope:** one module or pure function at a time; **no** real network, filesystem, or DB unless trivial and hermetic.
- **Speed:** keep unit tests fast; use **fakes**, **stubs**, or **`pytest` monkeypatch** at repository/protocol boundaries.
- **Placement:** mirror source layout under `tests/` (e.g. `tests/unit/...`) or colocate `test_*.py` next to packages—follow existing project structure.

## Integration tests

- **Scope:** multiple layers together—real HTTP client against **ASGI test client**, test DB, temp dirs, or dockerized deps as the project already does.
- **Mark** integration tests clearly (`@pytest.mark.integration` or similar) so CI can run `unit` only on tight loops if configured—see [reference.md](reference.md).
- Prefer **explicit setup/teardown** or **fixtures** in `conftest.py`; avoid order-dependent globals.

## What to cover

- **Happy path** plus **one failure path** that matters (validation error, 404, timeout handling) per feature slice—not exhaustive combinatorics unless requested.
- **Regressions:** if fixing a bug, add a test that **fails before** and **passes after** the fix when possible.

## Commands (uv)

```bash
uv sync
uv run pytest
uv run pytest tests/unit -q           # if split by folder/marker
uv run pytest -m "not integration"    # when markers exist
```

## Anti-patterns

- Empty tests or `assert True` placeholders.
- Tests that depend on **wall-clock** time without freezegun or similar when flaky.
- Committing **secrets** or real production URLs in test code.

## Additional resources

- Layout, markers, and `conftest` tips: [reference.md](reference.md)
