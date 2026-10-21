"""Tests for the AG-UI server's sign-in endpoints and credential filtering."""

import httpx
import pytest
from ag_ui.core import EventType, StateSnapshotEvent
from fastapi.testclient import TestClient

from adk_chat_agents import server
from adk_chat_agents.mcp_servers import SHIPPING, TOKEN, USER_ID

USER = {"id": "U001", "name": "Alice", "email": "a@example.com", "default_address": {"city": "K"}}


@pytest.fixture
def client():
    return TestClient(server.app)


@pytest.fixture
def session_updates(monkeypatch):
    """Capture what the login/logout endpoints write to the ADK session."""
    calls = []

    async def fake_set(thread_id, updates):
        calls.append((thread_id, updates))

    monkeypatch.setattr(server, "_set_session_state", fake_set)
    return calls


def shop_api_replies(monkeypatch, response: httpx.Response):
    async def post(self, url, **kwargs):
        return response

    monkeypatch.setattr(httpx.AsyncClient, "post", post)


def test_login_stores_token_server_side_and_hides_it(client, session_updates, monkeypatch):
    reply = httpx.Response(
        200, json={"token": "tok", "user": USER}, request=httpx.Request("POST", "x")
    )
    shop_api_replies(monkeypatch, reply)
    r = client.post("/auth/login", json={"thread_id": "t1", "email": "a", "password": "p"})
    assert r.status_code == 200
    assert r.json() == {"user": {"name": "Alice", "email": "a@example.com"}}  # no token
    assert session_updates == [
        ("t1", {USER_ID: "U001", TOKEN: "tok", SHIPPING: {"city": "K"}}),
    ]


def test_login_rejects_bad_credentials(client, session_updates, monkeypatch):
    reply = httpx.Response(401, json={"detail": "nope"}, request=httpx.Request("POST", "x"))
    shop_api_replies(monkeypatch, reply)
    r = client.post("/auth/login", json={"thread_id": "t1", "email": "a", "password": "bad"})
    assert r.status_code == 401 and session_updates == []


def test_logout_clears_session(client, session_updates):
    assert client.post("/auth/logout", json={"thread_id": "t1"}).status_code == 200
    assert session_updates == [("t1", {USER_ID: None, TOKEN: None, SHIPPING: None})]


@pytest.mark.anyio
async def test_state_snapshot_drops_credentials(monkeypatch):
    snapshot = {USER_ID: "U001", TOKEN: "secret", SHIPPING: {}, "_ag_ui_thread_id": "t1"}

    async def fake_run(self, input):
        yield StateSnapshotEvent(type=EventType.STATE_SNAPSHOT, snapshot=snapshot)

    monkeypatch.setattr(server.ADKAgent, "run", fake_run)
    events = [e async for e in server.agent.run(None)]
    assert events[0].snapshot == {"_ag_ui_thread_id": "t1"}
