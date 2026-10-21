import json

import anyio
import httpx
from mcp.client import Client

from mcp_orders.server import mcp

ADDR = {"line1": "1 Main St", "city": "Pune", "postal_code": "411001", "country": "IN"}


def call(tool: str, args: dict) -> dict:
    async def run():
        async with Client(mcp) as client:
            result = await client.call_tool(tool, args)
            return json.loads(result.content[0].text)

    return anyio.run(run)


def test_create_and_list_order(shop_api, token):
    stock = lambda: httpx.get(f"{shop_api}/products/P001").json()["stock"]
    before = stock()
    r = call("create_order", {"token": token, "items": {"P001": 1}, **ADDR})
    assert r["status"] == "ok" and r["order"]["status"] == "placed"
    assert stock() == before - 1
    ids = [o["id"] for o in call("list_orders", {"token": token})["orders"]]
    assert r["order"]["id"] in ids


def test_create_order_errors(token):
    assert call("create_order", {"token": token, "items": {"nope": 1}, **ADDR})["status"] == "error"
    assert (
        call("create_order", {"token": token, "items": {"P001": 10**6}, **ADDR})["status"]
        == "error"
    )
    assert call("create_order", {"token": token, "items": {"P001": 0}, **ADDR})["status"] == "error"


def test_delivery_date_is_string():
    assert isinstance(call("estimate_delivery_date", ADDR)["delivery_date"], str)
