import json

import anyio
from mcp.client import Client

from mcp_catalog.server import mcp


def call(tool: str, args: dict) -> dict:
    async def run():
        async with Client(mcp) as client:
            result = await client.call_tool(tool, args)
            return json.loads(result.content[0].text)

    return anyio.run(run)


def test_search_by_category():
    products = call("search_products", {"category": "electronics"})["products"]
    assert products and all(p["category"] == "electronics" for p in products)


def test_list_categories():
    cats = call("list_categories", {})["categories"]
    assert {c["name"] for c in cats} == {"apparel", "electronics", "home"}


def test_get_product():
    assert call("get_product", {"product_id": "P001"})["product"]["name"] == "Wireless Mouse"
    assert call("get_product", {"product_id": "nope"})["status"] == "error"
