"""AG-UI HTTP endpoint for the shopping agent (consumed by the CopilotKit frontend).

Sign-in happens here, not in chat: the form posts credentials to ``/auth/login``, this server
checks them against the shop API and stores the resulting token in the ADK session for the
thread. The token and password never reach the browser's chat stream or the LLM.
"""

import os

import httpx
import uvicorn
from ag_ui.core import EventType
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()
os.environ.setdefault("LOGIN_MODE", "form")  # before the agent module reads it

from .agent import root_agent  # noqa: E402
from .mcp_servers import SHIPPING, TOKEN, USER_ID  # noqa: E402

APP_NAME = "ecommerce_agent"
USER = "web-user"

app = FastAPI(title="Shop agent (AG-UI)")

SERVER_ONLY_STATE = {TOKEN, USER_ID, SHIPPING}


class ShopADKAgent(ADKAgent):
    """ADKAgent that keeps credentials in ``SERVER_ONLY_STATE`` out of the client event stream."""

    async def run(self, input):
        async for event in super().run(input):
            if event.type == EventType.STATE_SNAPSHOT and isinstance(event.snapshot, dict):
                event.snapshot = {
                    k: v for k, v in event.snapshot.items() if k not in SERVER_ONLY_STATE
                }
            yield event


# One ADK session per CopilotKit thread: the login token, user id and shipping address live in
# session state (see mcp_servers.py), so the UI must reuse the same thread for a conversation.
agent = ShopADKAgent(
    adk_agent=root_agent,
    app_name=APP_NAME,
    user_id=USER,
    use_thread_id_as_session_id=True,
)


class LoginIn(BaseModel):
    thread_id: str
    email: str
    password: str


class ThreadIn(BaseModel):
    thread_id: str


async def _set_session_state(thread_id: str, updates: dict) -> None:
    # ag-ui-adk has no public API for writing session state; this is its session manager.
    sessions = agent._session_manager
    _, session_id = await sessions.get_or_create_session(thread_id, APP_NAME, USER)
    await sessions.update_session_state(session_id, APP_NAME, USER, updates)


@app.post("/auth/login")
async def login(body: LoginIn) -> dict:
    base = os.getenv("SHOP_API_URL", "http://127.0.0.1:8000")
    try:
        async with httpx.AsyncClient(timeout=10) as http:
            resp = await http.post(
                f"{base}/auth/login", json={"email": body.email, "password": body.password}
            )
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Shop API unreachable at {base}") from e
    if resp.status_code == 401:
        raise HTTPException(401, "Invalid email or password.")
    resp.raise_for_status()
    data = resp.json()
    user = data["user"]
    await _set_session_state(
        body.thread_id,
        {USER_ID: user["id"], TOKEN: data["token"], SHIPPING: user.get("default_address")},
    )
    return {"user": {"name": user["name"], "email": user["email"]}}


@app.post("/auth/logout")
async def logout(body: ThreadIn) -> dict:
    await _set_session_state(body.thread_id, {USER_ID: None, TOKEN: None, SHIPPING: None})
    return {"status": "ok"}


add_adk_fastapi_endpoint(app, agent, path="/")


def main() -> None:
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("AGENT_PORT", "8001")))


if __name__ == "__main__":
    main()
