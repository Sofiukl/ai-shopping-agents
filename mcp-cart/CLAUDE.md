# CLAUDE.md

Uses `uv` (Python >=3.12). Run: `uv run mcp-cart`; tests: `uv run pytest`; lint: `uv run ruff check .`.

MCP server (`MCPServer("cart")`, stdio). `server.py` holds tools wrapping results in
`{"status": "ok"|"error", ...}`; `backend.py` is the fake JSON store (`carts.json`: `{user_id: {product_id: qty}}`),
validating against the catalog's `products.json` (`PRODUCTS_FILE`). Stateless per call: callers pass `user_id`.
Tests use temp copies via env vars.
