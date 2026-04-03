---
name: python-isort-black-format
description: Formats Python code with isort then black via uv on relevant paths before commits so imports and style stay consistent. Use when editing Python files, preparing a commit, fixing lint/format CI, or when the user mentions isort, black, import sorting, or pre-commit formatting.
---

# isort + black before commit

## Goal

Every commit that touches Python should leave the tree **isort-clean** and **black-formatted** on the files (or scope) the change affects.

## Local environment

Use **uv** and the project **`.venv`**: run **`uv sync`** first so **isort** and **black** match **`uv.lock`**. Do not rely on a global Python for formatting unless the environment cannot run uv.

## Default commands

From the **project root** (where **`pyproject.toml`** / **`uv.lock`** live):

```bash
uv run isort .
uv run black .
```

If only a few files changed, narrow paths:

```bash
uv run isort path/to/package tests/
uv run black path/to/package tests/
```

Run **isort first**, then **black** (Black can reflow imports isort touched; if your team uses a combined workflow, follow `pyproject.toml` / docs—but default order is isort → black).

## Before committing

1. Run **`uv run isort`** and **`uv run black`** as above (or on staged paths).
2. **Re-run tests** or quick smoke check if formatting touched wide areas (`uv run pytest`, etc.).
3. **`git add`** updated files and commit.

## Configuration

Respect existing project config: **`pyproject.toml`** (`[tool.isort]`, `[tool.black]`), or `setup.cfg` / `.isort.cfg`. Do not override line length or ignore rules ad hoc unless the user asks.

## When the agent edits Python

After substantive edits, **run the formatters** with **`uv run`** (or ask the user to run them if the environment cannot execute tools) before presenting work as “ready to commit.”

## Optional: pre-commit

If the repo uses **pre-commit**, prefer `uv run pre-commit run --all-files` or the hooks that wrap isort/black—see [reference.md](reference.md).

## Additional resources

- Installing formatters and check-only CI: [reference.md](reference.md)
