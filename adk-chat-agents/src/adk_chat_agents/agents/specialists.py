"""Specialist agents. Factories, because an ADK agent can have only one parent."""

from google.adk.agents import LlmAgent

from ..config import LOGIN_MODE, MODEL
from ..mcp_servers import (
    accounts_toolset,
    bind_session_user,
    cart_toolset,
    catalog_toolset,
    orders_toolset,
)

RUPEES = " All prices are in Indian rupees (INR): always show them as ₹<amount>, never with $."


def catalog_agent(**kw) -> LlmAgent:
    return LlmAgent(
        name="catalog_agent",
        model=MODEL,
        description="Searches products",
        instruction=(
            "Help the user find products. Use search_products, "
            "Products have a category: call list_categories when the user asks what you sell or "
            "to browse, and filter search_products by category when the user names one. "
            "Never invent products, prices or image URLs; use only values returned by the tools "
            "including the product id." + RUPEES + "\n\n"
            "Below the products list, add one line: "
            "_Reply `add <id>` to add the item to your cart._\n\n"
        ),
        tools=[catalog_toolset()],
        **kw,
    )


def cart_agent(**kw) -> LlmAgent:
    return LlmAgent(
        name="cart_agent",
        model=MODEL,
        description="Adds/views the cart",
        instruction=(
            "Help the user add/remove items and view the cart. Use add_to_cart, "
            "remove_from_cart and view_cart (the user is {user_id?}; "
            "the `token` argument is filled in for you: never ask the user for it). "
            "When showing the user cart, then show in a nice way within a table all the items in "
            "the cart with the quantity, price and total price for each item." + RUPEES
        ),
        tools=[cart_toolset(["add_to_cart", "remove_from_cart", "view_cart"])],
        before_tool_callback=bind_session_user,
        **kw,
    )


def checkout_agent(**kw) -> LlmAgent:
    return LlmAgent(
        name="checkout_agent",
        model=MODEL,
        description="Collects the shipping address and places the order.",
        instruction=(
            "The `token` argument of cart and order tools is filled in for you: never ask the user "
            "for it. Review the cart with view_cart. "
            "If a current shipping address is saved (see below), use it as is and do NOT ask the "
            "user for an address; just show it in the order summary so they can confirm. Only if "
            "none is saved, ask the user for line1, city, postal_code and country. "
            "Calculate the delivery date and time based on the shipping address. "
            "use estimate_delivery_date tool to get the delivery date"
            "Show the delivery date, address, total to the user and call create_order ONLY after "
            "explicit confirmation, passing the items from view_cart as {product_id: qty} and the "
            "address fields. After create_order succeeds, call clear_cart. "
            "Current shipping address: {shipping_address?}." + RUPEES
        ),
        tools=[
            cart_toolset(["view_cart", "clear_cart"]),
            orders_toolset(["create_order", "estimate_delivery_date"]),
        ],
        before_tool_callback=bind_session_user,
        **kw,
    )


def order_agent(**kw) -> LlmAgent:
    return LlmAgent(
        name="order_summary_agent",
        model=MODEL,
        description="Displays order summaries and order history.",
        instruction=(
            "Use list_orders to present orders clearly: id, date, items, total, status. "
            "For 'last'/'latest' order, show only the most recent one. "
            "The user is {user_id?}; the `token` argument is filled in for you: never ask the "
            "user for a token, code or any authentication, and pass any placeholder value." + RUPEES
        ),
        tools=[orders_toolset(["list_orders"])],
        before_tool_callback=bind_session_user,
        **kw,
    )


def account_tools_list():
    """Login/profile/logout come from mcp-accounts (see track_session).

    In form mode the UI owns login and logout, so the model gets neither tool.
    """
    if LOGIN_MODE == "form":
        return [accounts_toolset(["get_profile"])]
    return [accounts_toolset(["login", "get_profile", "logout"])]
