import json

import anyio
from mcp.client import Client

from mcp_cart.server import mcp


def call(tool: str, args: dict) -> dict:
    async def run():
        async with Client(mcp) as client:
            result = await client.call_tool(tool, args)
            return json.loads(result.content[0].text)

    return anyio.run(run)


def test_add_view_remove_clear(token):
    assert call("add_to_cart", {"token": token, "product_id": "P001", "quantity": 2})["cart"] == {
        "P001": 2
    }
    cart = call("view_cart", {"token": token})
    assert cart["total"] == 1598 and cart["items"][0]["qty"] == 2
    assert call("view_cart", {"token": "nope"})["status"] == "error"  # carts need a valid token
    assert call("remove_from_cart", {"token": token, "product_id": "P001"})["cart"] == {}
    call("add_to_cart", {"token": token, "product_id": "P001", "quantity": 1})
    call("clear_cart", {"token": token})
    assert call("view_cart", {"token": token})["items"] == []


def test_errors(token):
    bad = {"token": token, "product_id": "nope", "quantity": 1}
    assert call("add_to_cart", bad)["status"] == "error"
    assert call("add_to_cart", {**bad, "product_id": "P001", "quantity": 0})["status"] == "error"
    assert (
        call("add_to_cart", {**bad, "product_id": "P001", "quantity": 10**6})["status"] == "error"
    )
    assert call("remove_from_cart", {"token": token, "product_id": "P001"})["status"] == "error"
