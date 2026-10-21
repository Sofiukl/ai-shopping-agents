# mcp-orders

MCP server (stdio) for orders, a thin client of `fake-shop-api` (`SHOP_API_URL`, default `http://127.0.0.1:8000`).

Tools: `create_order(token, items, line1, city, postal_code, country)`,
`list_orders(token)`, `estimate_delivery_date(line1, city, postal_code, country)`.
Run: `uv run mcp-orders`.

The API owns stock and orders; start it first with `uv run fake-shop-api` in `../fake-shop-api`.

Tools that act on a user take the session `token` from `login` (sent to the API as a bearer
token). Tests need `../fake-shop-api` checked out (dev dependency by relative path).
