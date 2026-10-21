import os
from pathlib import Path

# Override with MODEL in .env, e.g. MODEL=gemini-2.5-flash-lite
MODEL = os.getenv("MODEL", "gemini-2.5-flash")

# "chat": the agent asks for email/password in chat and calls the login tool (adk web / CLI).
# "form": the web UI signs the user in out of band (server.py), so credentials never reach the LLM.
LOGIN_MODE = os.getenv("LOGIN_MODE", "chat")

# MCP servers are sibling projects, launched over stdio with `uv run --directory`.
_PROJECTS = Path(__file__).resolve().parents[3]
MCP_CATALOG_DIR = Path(os.getenv("MCP_CATALOG_DIR", _PROJECTS / "mcp-catalog"))
MCP_ACCOUNTS_DIR = Path(os.getenv("MCP_ACCOUNTS_DIR", _PROJECTS / "mcp-accounts"))
MCP_ORDERS_DIR = Path(os.getenv("MCP_ORDERS_DIR", _PROJECTS / "mcp-orders"))
MCP_CART_DIR = Path(os.getenv("MCP_CART_DIR", _PROJECTS / "mcp-cart"))
