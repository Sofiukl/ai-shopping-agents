"""Toolset factories for the MCP servers (one toolset per agent; they own a stdio subprocess)."""

import json
from pathlib import Path

from google.adk.tools import BaseTool, ToolContext
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

from .config import MCP_ACCOUNTS_DIR, MCP_CART_DIR, MCP_CATALOG_DIR, MCP_ORDERS_DIR

USER_ID = "user_id"
TOKEN = "auth_token"  # bearer token for the shop API; never shown to the model
SHIPPING = "shipping_address"

NOT_AUTH = {"status": "error", "error": "Not logged in. Ask the user to log in first."}

# MCP tools that act on one user's data and take a ``token`` argument.
USER_SCOPED = {
    "add_to_cart",
    "remove_from_cart",
    "view_cart",
    "clear_cart",
    "create_order",
    "list_orders",
    "get_profile",
    "logout",
}


def _stdio(project_dir: Path, script: str, tool_filter: list[str] | None = None) -> McpToolset:
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="uv", args=["run", "--directory", str(project_dir), script]
            ),
            timeout=30,
        ),
        tool_filter=tool_filter,
    )


def catalog_toolset() -> McpToolset:
    tools = ["search_products", "get_product", "list_categories"]
    return _stdio(MCP_CATALOG_DIR, "mcp-catalog", tools)


def accounts_toolset(tool_filter: list[str] | None = None) -> McpToolset:
    return _stdio(MCP_ACCOUNTS_DIR, "mcp-accounts", tool_filter)


def cart_toolset(tool_filter: list[str] | None = None) -> McpToolset:
    return _stdio(MCP_CART_DIR, "mcp-cart", tool_filter)


def orders_toolset(tool_filter: list[str] | None = None) -> McpToolset:
    return _stdio(MCP_ORDERS_DIR, "mcp-orders", tool_filter)


def bind_session_user(tool: BaseTool, args: dict, tool_context: ToolContext) -> dict | None:
    """before_tool_callback: force ``token`` to the session's so the LLM can't pick one."""
    if tool.name not in USER_SCOPED:
        return None
    token = tool_context.state.get(TOKEN)
    if not token:
        return NOT_AUTH
    args["token"] = token
    return None


def _unwrap(response: dict) -> dict:
    """MCP tool results arrive as {"content": [{"text": "<json>"}]}; return the decoded payload."""
    if isinstance(response.get("structuredContent"), dict):
        return response["structuredContent"]
    for part in response.get("content") or []:
        try:
            payload = json.loads(part.get("text", ""))
        except (TypeError, ValueError):
            continue
        if isinstance(payload, dict):
            return payload
    return response


def track_session(tool: BaseTool, args: dict, tool_context: ToolContext, tool_response: dict):
    """after_tool_callback: the stateless accounts server can't set session state, so do it here."""
    if tool.name not in ("login", "logout") or not isinstance(tool_response, dict):
        return None
    result = _unwrap(tool_response)
    if tool.name == "logout":
        for key in (USER_ID, TOKEN, SHIPPING):  # clear even if the token was already invalid
            tool_context.state[key] = None
        return result
    user = result.get("user")
    token = result.pop("token", None)  # keep the credential out of the model's context
    if result.get("status") == "ok" and user and token:
        tool_context.state[USER_ID] = user["id"]
        tool_context.state[TOKEN] = token
        if user.get("default_address"):
            tool_context.state[SHIPPING] = user["default_address"]
    return result  # hand the model the decoded result, not the MCP envelope
