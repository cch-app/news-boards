# Context7 MCP reference

## Server

- **Identifier:** `user-context7` (project MCP).

## Tools

| Tool | Required args | Notes |
|------|----------------|------|
| `resolve-library-id` | `libraryName`, `query` | Run before `query-docs` unless the user already gave an ID like `/org/project` or `/org/project/version`. |
| `query-docs` | `libraryId`, `query` | **Max 3 calls per question** for this tool; combine questions to stay under the cap. |

## Query tips for deprecations

- Ask: “What is the **recommended** API as of current docs?” and “What is **deprecated** and what replaces it?”
- Name the **language/runtime version** (e.g. Python 3.13) so snippets match your environment.

## Choosing `libraryId`

- Prefer **High** source reputation and higher **benchmark score** when multiple IDs match.
- Use a **versioned** ID (`/org/project/version`) when it matches the dependency version in **`pyproject.toml`** / **`uv.lock`**.
