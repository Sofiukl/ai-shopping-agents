"""MCP server exposing orders over stdio."""

from mcp.server import MCPServer

from . import client

mcp = MCPServer("orders")


@mcp.tool()
def create_order(
    token: str, items: dict[str, int], line1: str, city: str, postal_code: str, country: str
) -> dict:
    """Place an order for the logged-in user. items maps product_id to quantity. Decrements stock.

    Only call after the user has explicitly confirmed the order.
    """
    address = {"line1": line1, "city": city, "postal_code": postal_code, "country": country}
    try:
        order = client.create_order(token, items, address)
    except ValueError as e:
        return {"status": "error", "error": str(e)}
    return {"status": "ok", "order": order}


@mcp.tool()
def list_orders(token: str) -> dict:
    """List all orders placed by the logged-in user."""
    try:
        return {"status": "ok", "orders": client.list_orders(token)}
    except ValueError as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
def estimate_delivery_date(line1: str, city: str, postal_code: str, country: str) -> dict:
    """Estimate the delivery date (YYYY-MM-DD) for a shipping address."""
    address = {"line1": line1, "city": city, "postal_code": postal_code, "country": country}
    return {"status": "ok", "delivery_date": client.estimate_delivery_date(address)}


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
