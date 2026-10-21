"""MCP server exposing the product catalog over stdio."""

from mcp.server import MCPServer

from . import client

mcp = MCPServer("catalog")


@mcp.tool()
def search_products(query: str = "", category: str = "", max_price: float = 0) -> dict:
    """Search products. All filters are optional; max_price 0 means no limit."""
    return {
        "status": "ok",
        "products": client.search_products(query, category, max_price or None),
    }


@mcp.tool()
def list_categories() -> dict:
    """List the product categories, each with its number of products."""
    return {"status": "ok", "categories": client.list_categories()}


@mcp.tool()
def get_product(product_id: str) -> dict:
    """Get one product by id, including stock and price."""
    product = client.get_product(product_id)
    if product is None:
        return {"status": "error", "error": f"Unknown product {product_id}"}
    return {"status": "ok", "product": product}


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
