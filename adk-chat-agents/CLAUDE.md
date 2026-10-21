# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Python 3.12, managed with `uv`.

```sh
uv sync
cp .env.example .env                      # Vertex AI (ADC) config: GOOGLE_CLOUD_PROJECT etc.; optional MODEL override
uv run pytest                             # callback + wiring tests (no LLM/API needed)
uv run ruff check . && uv run ruff format .
```

Ruff: line length 100, rules E, F, I, UP, B.

## Architecture

A conversational shopping assistant on Google ADK. The ADK entry point is `root_agent` in `src/adk_chat_agents/agent.py` (an `LlmAgent`, so `adk run`/`adk web` can load the package).

- **Coordinator + specialists**: `root_agent` handles login itself (account tools) and routes via `sub_agents` to catalog, cart, checkout, and order-summary agents defined in `agents/specialists.py`. Routing rules live in the root agent's instruction string. Specialists are **factory functions** because an ADK agent can have only one parent — call them fresh for each parent.
- **MCP servers** (`mcp_servers.py`): catalog, accounts, cart and orders are sibling projects launched over stdio; they are thin HTTP clients of the sibling `fake-shop-api` (FastAPI + SQLite), which must be running (`uv run fake-shop-api`) or tool calls fail with "Shop API unreachable" (`config.py` has the dirs). `login` returns a bearer token; `track_session` stores `user_id`, `auth_token` and `shipping_address` on login (stripping the token from what the model sees) and clears them on logout. `bind_session_user` overwrites the `token` arg of user-scoped tools with the session's, so the model can't pick one. Tests in `tests/` cover these callbacks.
- **Web login** (`server.py`, AG-UI endpoint for the CopilotKit UI in `web/`): `LOGIN_MODE=form` (set by `server.py`; default `chat` for `adk web`) removes the `login`/`logout` tools. The UI's sign-in form posts to `/auth/login`, which checks the shop API and writes `user_id`/`auth_token`/`shipping_address` into the thread's ADK session; `ShopADKAgent` strips those keys from `STATE_SNAPSHOT` events so the token never reaches the browser. Run: `uv run shop-agent-server` (:8001) and `npm run dev` in `web/` (:3000).
- `MODEL` env var sets the model for all agents (default `gemini-2.5-flash`).
- `.adk/` (session DB) is gitignored runtime state.
