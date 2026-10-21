import json

import anyio
from mcp.client import Client

from mcp_accounts.server import mcp


def call(tool: str, args: dict) -> dict:
    async def run():
        async with Client(mcp) as client:
            result = await client.call_tool(tool, args)
            return json.loads(result.content[0].text)

    return anyio.run(run)


def test_login_ok_returns_token_and_hides_hash():
    r = call("login", {"email": "Alice@example.com", "password": "alice123"})
    assert r["status"] == "ok" and r["user"]["id"] == "U001" and r["token"]
    assert "password_hash" not in r["user"]


def test_login_bad_password():
    assert call("login", {"email": "alice@example.com", "password": "x"})["status"] == "error"


def test_get_profile(token):
    assert call("get_profile", {"token": token})["user"]["email"] == "alice@example.com"
    assert call("get_profile", {"token": "nope"})["status"] == "error"


def test_logout_invalidates_token(token):
    assert call("logout", {"token": token})["status"] == "ok"
    assert call("get_profile", {"token": token})["status"] == "error"
    assert call("logout", {"token": token})["status"] == "error"
