from google.adk.agents import LlmAgent

from .agents import specialists
from .config import LOGIN_MODE, MODEL
from .mcp_servers import bind_session_user, track_session

_LOGIN_INSTRUCTION = {
    "chat": (
        "The user must be logged in before anything else: "
        "if session user_id is missing ({user_id?}), ask for email and password and call login. "
        "After a successful login, greet the user by name and ask what they would like to do; "
        "if login fails, say so and ask them to retry. "
        "If the user asks to log out, call logout. "
    ),
    "form": (
        "The user signs in with the sign-in form in the app, never in chat. "
        "If session user_id is missing ({user_id?}), tell them to sign in with the form and "
        "never ask for or accept an email or password in chat; if they type a password, tell "
        "them not to share it here. Once user_id is set, greet them and ask what they would "
        "like to do. Logging out is done with the Sign out button. "
    ),
}

root_agent = LlmAgent(
    name="ecommerce_agent",
    model=MODEL,
    description="Conversational shopping assistant.",
    instruction=(
        "You are a shopping assistant. "
        + _LOGIN_INSTRUCTION[LOGIN_MODE]
        + "Then route: product search / catalog -> catalog_agent; cart -> cart_agent;"
        "shipping and placing an order -> checkout_agent; order history/summary -> order_agent. "
        "Requests to see products, images or the cart go to catalog_agent. "
        "Any `token` argument is filled in automatically: never ask the user for it; pass any "
        "placeholder value. "
        "All prices are in Indian rupees (INR): show them as ₹<amount>. "
        "Keep replies short and always reply with text."
    ),
    tools=specialists.account_tools_list(),
    before_tool_callback=bind_session_user,
    after_tool_callback=track_session,
    sub_agents=[
        specialists.catalog_agent(),
        specialists.cart_agent(),
        specialists.checkout_agent(),
        specialists.order_agent(),
    ],
)
