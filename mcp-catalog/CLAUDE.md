# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Uses `uv` (Python >=3.12).

- Run the server (stdio): `uv run mcp-catalog`
- Tests: `uv run pytest`; single test: `uv run pytest tests/test_server.py::test_get_product`
- Lint/format: `uv run ruff check .` / `uv run ruff format .` (line length 100)
- Manual end-to-end check over real stdio transport: `uv run python try_client.py`

## Architecture

An MCP server (`mcp` package, `MCPServer("catalog")`) exposing a product catalog over stdio, split into two layers:

- `src/mcp_catalog/server.py` — MCP tool definitions (`search_products`, `get_product`, `list_categories`). Tools wrap backend results in a `{"status": "ok" | "error", ...}` envelope; unknown products return `status: "error"` rather than raising. `max_price=0` means "no limit" at the tool layer and is converted to `None` for the backend.
- `src/mcp_catalog/backend.py` — a fake product API reading `data/products.json` on every call. It is intended to be swapped for a real HTTP client, so keep tool-layer concerns (envelopes, argument sentinels) out of it. Set `DATA_DIR` to point at an alternate directory containing `products.json`.

Tests (`tests/test_server.py`) call tools in-process via `mcp.client.Client(mcp)` against the real `server.mcp` object and parse the JSON text of the result, so they exercise the MCP layer and the bundled data together.
