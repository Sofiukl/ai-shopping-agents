# CLAUDE.md

Uses `uv` (Python >=3.12). Run: `uv run mcp-orders`; tests: `uv run pytest`; lint: `uv run ruff check .`.

MCP server (`MCPServer("orders")`, stdio). `server.py` holds tools (`create_order`, `list_orders`,
`estimate_delivery_date`) wrapping results in `{"status": "ok"|"error", ...}`; `backend.py` is the
fake JSON-backed API. Stateless: callers pass `user_id`, items and address explicitly (cart/session
live in the calling agent). `create_order` holds an RLock and writes stock (catalog's `products.json`,
`PRODUCTS_FILE`) and `orders.json` (`DATA_DIR`) together. Tests copy both files to a tmp dir via env vars;
keep that for any test that places orders.
