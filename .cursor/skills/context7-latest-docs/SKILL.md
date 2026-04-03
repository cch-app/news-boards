---
name: context7-latest-docs
description: Resolves library IDs and queries Context7 MCP for current documentation, migration notes, and recommended APIs before coding. Use when implementing or configuring third-party libraries, frameworks, CLIs, or cloud SDKs; when the user mentions deprecations, latest syntax, or version-specific behavior; or before writing integration code that must match current docs.
---

# Context7: latest docs before implementation

## When to use

- Adding or changing **dependencies** (HTTP clients, web frameworks, DB drivers, cloud SDKs, linters).
- The user asks for **up-to-date** syntax, **migration** from an older API, or **avoiding deprecations**.
- Training data might be stale—**prefer Context7 over guessing** for library-specific APIs.

**Do not** use Context7 for: pure refactoring, greenfield scripts with no external API surface, business-logic debugging, or generic CS concepts (per server guidance).

## Workflow (MCP: `user-context7`)

1. **Resolve library ID** — call **`resolve-library-id`** with:
   - `libraryName`: PyPI/npm/crate name or common product name (e.g. `httpx`, `fastapi`, `pydantic`).
   - `query`: Short intent tied to the task (e.g. “async client timeouts and SSL in Python 3.13”).
2. From results, pick the best **`/org/project`** ID (higher reputation/snippet coverage when unsure). If the project pins a version, prefer **`/org/project/version`** when listed.
3. **Query documentation** — call **`query-docs`** with:
   - `libraryId`: exact ID from step 1 (or user-supplied `/org/project` or `/org/project/version`).
   - `query`: Specific question; include **Python 3.13** (or pinned runtime) and ask explicitly for **non-deprecated** / **current** APIs and **migration** from old patterns when replacing code.

Repeat step 3 only if needed; **do not exceed 3 calls per tool per user question** (server limit)—batch related sub-questions into one `query` when possible.

## Implementation rules

- Prefer examples and signatures returned by Context7 over memory when they conflict.
- After fetching docs, write code using **current** constructors, settings objects, and module paths from the response.
- If docs mention **deprecated** aliases, use the **replacement** in new code and note removals in PR-style summaries when editing existing code.

## Safety

- Never put **secrets, API keys, credentials, proprietary code, or PII** into `libraryName`, `query`, or any Context7 tool argument.

## Additional resources

- Tool limits and selection tips: [reference.md](reference.md)
