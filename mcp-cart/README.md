# mcp-cart

MCP server (stdio) for per-user shopping carts, a thin client of `fake-shop-api` (`SHOP_API_URL`, default `http://127.0.0.1:8000`).

Tools: `add_to_cart(token, product_id, quantity)`, `remove_from_cart(token, product_id)`,
`view_cart(token)`, `clear_cart(token)`. Run: `uv run mcp-cart`.

The API must be running (`uv run fake-shop-api` in `../fake-shop-api`).

Tools that act on a user take the session `token` from `login` (sent to the API as a bearer
token). Tests need `../fake-shop-api` checked out (dev dependency by relative path).
