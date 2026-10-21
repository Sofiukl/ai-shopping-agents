"""MCP server exposing per-user shopping carts over stdio."""

from mcp.server import MCPServer

from . import client

mcp = MCPServer("cart")


@mcp.tool()
def add_to_cart(token: str, product_id: str, quantity: int) -> dict:
    """Add a quantity of a product to the logged-in user's cart (checked against stock)."""
    try:
        cart = client.add_to_cart(token, product_id, quantity)
    except ValueError as e:
        return {"status": "error", "error": str(e)}
    return {"status": "ok", "cart": cart}


@mcp.tool()
def remove_from_cart(token: str, product_id: str) -> dict:
    """Remove a product from the logged-in user's cart."""
    try:
        cart = client.remove_from_cart(token, product_id)
    except ValueError as e:
        return {"status": "error", "error": str(e)}
    return {"status": "ok", "cart": cart}


@mcp.tool()
def view_cart(token: str) -> dict:
    """Show the logged-in user's cart with line totals and the cart total."""
    try:
        return {"status": "ok", **client.view_cart(token)}
    except ValueError as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
def clear_cart(token: str) -> dict:
    """Empty the logged-in user's cart. Call after an order is placed."""
    try:
        client.clear_cart(token)
    except ValueError as e:
        return {"status": "error", "error": str(e)}
    return {"status": "ok"}


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
