# wflow-cli

A uv workspace with two packages released together under one version:

- `packages/wflow-api` — `wflow_api`, the async Python client for the wflow.com public API (httpx, pydantic).
- `packages/wflow-cli` — `wflow_cli`, the `wflow` command, generated from `wflow_api`'s operations (Typer).

```bash
make install       # uv sync --all-packages
make test          # pytest with coverage, fail under 90 %
make lint          # ruff format --check, ruff check, mypy
make lint_format   # ruff format + ruff check --fix
```

## Rules

- `wflow_api` never reads environment variables, never imports FastMCP, and raises only `WflowError` / `WflowApiError`. Only `wflow_cli` reads the environment.
- Every operation is `async def`, decorated with `@operation`, takes `client: WflowClient` first, and keeps the MCP tool's name, parameters, `Annotated` descriptions, return model and docstring.
- An operation docstring is customer-facing documentation: it is the CLI's `--help` and will be the MCP tool description. No dates, no test history, no wflow error codes, and nothing that names the MCP ("tool", "MCP client", "reconnect").
- Messages of `WflowError` name no MCP concept.
- Files move as raw bytes: uploads take `content: bytes`, downloads return `FileContent`.
- Internal code carries no comments by default; at most one short line where the code cannot be understood without it.

## Working in the AI box

- The MCP server is cloned writable at `~/mcp-public-api-beta`; the two repos often change together.
- Code copied from the MCP records its source in the commit body: `Source: wflowcom/mcp-public-api-beta@<sha>` from `git -C ~/mcp-public-api-beta rev-parse --short HEAD`.
- The spec and plans are in `docs/superpowers/` — a symlink to the host's gitignored `docs/`, mounted read-write. Never commit them. At the end of every phase, update that phase's row and notes in `docs/superpowers/plans/PROGRESS.md` directly.
- Work on a feature branch from `develop`, open the PR into `develop` with `gh pr create --base develop`. The owner merges.
- Never add a `Co-authored-by` line to a commit.
