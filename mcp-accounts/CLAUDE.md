# CLAUDE.md

Uses `uv` (Python >=3.12). Run: `uv run mcp-accounts`; tests: `uv run pytest`; lint: `uv run ruff check .`.

MCP server (`MCPServer("accounts")`, stdio). `server.py` holds tools (`login`, `get_profile`) that wrap
results in `{"status": "ok"|"error", ...}`; `backend.py` is the fake JSON-backed API (`DATA_DIR`
overrides the dir containing `users.json`); `auth.py` is scrypt verification. The server is stateless:
it validates credentials but the calling agent owns the session (it must store `user.id` itself).
