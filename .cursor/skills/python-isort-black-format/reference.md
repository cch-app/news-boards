# isort / black reference (uv)

## Compatibility

- In `pyproject.toml`, **`[tool.isort]`** often sets `profile = "black"` so import wrapping matches Black’s line length. Keep both tools on versions your **`uv.lock`** pins.

## Install (dev)

Add as **dev** dependencies with uv (from project root):

```bash
uv add --dev isort black
uv sync
```

## Check-only mode (CI)

Run **without** writing files (e.g. in GitHub Actions after **`uv sync --frozen`**):

```bash
uv run isort --check-only . --diff
uv run black --check . --diff
```

Use the same `pyproject.toml` / config as local formatting.

## pre-commit (optional)

If hooks are installed in the same environment:

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

Example `.pre-commit-config.yaml` fragment:

```yaml
repos:
  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
      - id: isort
  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
      - id: black
```

Pin `rev` to tags your team uses; run `pre-commit autoupdate` deliberately, not blindly.
