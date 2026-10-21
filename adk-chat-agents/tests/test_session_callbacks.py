import json
from types import SimpleNamespace

import pytest

from adk_chat_agents.agent import root_agent
from adk_chat_agents.mcp_servers import (
    NOT_AUTH,
    SHIPPING,
    TOKEN,
    USER_ID,
    USER_SCOPED,
    bind_session_user,
    track_session,
)

USER = {"id": "U001", "name": "Alice", "default_address": {"line1": "12 Park St", "city": "K"}}


def ctx(**state):
    return SimpleNamespace(state=dict(state))


def tool(name):
    return SimpleNamespace(name=name)


def mcp_result(payload: dict) -> dict:
    """The envelope ADK hands back for an MCP tool call (text content only)."""
    return {"content": [{"type": "text", "text": json.dumps(payload)}], "isError": False}


@pytest.mark.parametrize("name", sorted(USER_SCOPED))
def test_user_scoped_tools_require_login(name):
    args = {}
    assert bind_session_user(tool(name), args, ctx()) == NOT_AUTH
    assert "token" not in args


def test_bind_overrides_model_supplied_token():
    args = {"token": "model-guess", "product_id": "P001"}
    assert bind_session_user(tool("add_to_cart"), args, ctx(**{TOKEN: "real"})) is None
    assert args == {"token": "real", "product_id": "P001"}


def test_unscoped_tools_are_untouched():
    args = {"query": "mouse"}
    assert bind_session_user(tool("search_products"), args, ctx()) is None
    assert args == {"query": "mouse"}


def test_login_stores_session_and_hides_token():
    c = ctx()
    out = track_session(
        tool("login"), {}, c, mcp_result({"status": "ok", "user": USER, "token": "tok123"})
    )
    assert c.state == {USER_ID: "U001", TOKEN: "tok123", SHIPPING: USER["default_address"]}
    assert out["status"] == "ok" and out["user"]["name"] == "Alice"
    assert "tok123" not in json.dumps(out)


def test_failed_login_stores_nothing():
    c = ctx()
    out = track_session(tool("login"), {}, c, mcp_result({"status": "error", "error": "bad"}))
    assert c.state == {} and out["status"] == "error"


def test_logout_clears_session_even_on_error():
    c = ctx(**{USER_ID: "U001", TOKEN: "tok", SHIPPING: {"city": "K"}})
    track_session(tool("logout"), {}, c, mcp_result({"status": "error", "error": "expired"}))
    assert c.state == {USER_ID: None, TOKEN: None, SHIPPING: None}
    assert bind_session_user(tool("view_cart"), {}, c) == NOT_AUTH


def test_other_tools_pass_through():
    assert track_session(tool("view_cart"), {}, ctx(), mcp_result({"status": "ok"})) is None


def test_agent_tree_wiring():
    assert [a.name for a in root_agent.sub_agents] == [
        "catalog_agent",
        "cart_agent",
        "checkout_agent",
        "order_summary_agent",
    ]
