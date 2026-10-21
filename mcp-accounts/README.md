# mcp-accounts

MCP server (stdio) for user accounts, a thin client of `fake-shop-api` (`SHOP_API_URL`, default `http://127.0.0.1:8000`).

Tools: `login(email, password)` (returns the user and a session `token`), `get_profile(token)`, `logout(token)`. Run: `uv run mcp-accounts`.

Tools that act on a user take the session `token` from `login` (sent to the API as a bearer
token). Tests need `../fake-shop-api` checked out (dev dependency by relative path).
