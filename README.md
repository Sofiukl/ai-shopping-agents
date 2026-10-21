# build-ai-agents

A small, self-contained example of an AI shopping assistant: a fake shop backend, four MCP
servers on top of it, and a Google ADK agent with a chat UI.

```
 Browser ── Next.js + CopilotKit ──AG-UI──▶ ADK agent ──stdio (MCP)──▶ mcp-catalog  ┐
 (web/, :3000)                              (:8001)                    mcp-accounts │ HTTP
                                                                       mcp-cart     ├──▶ fake-shop-api
                                                                       mcp-orders   ┘    (FastAPI + SQLite, :8000)
```

| Project                                                                                                  | What it is                                                                                                         |
| -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| [fake-shop-api](fake-shop-api)                                                                           | FastAPI + SQLite backend: products (₹, with categories), carts, orders, token auth. Seeds itself on first request. |
| [mcp-catalog](mcp-catalog), [mcp-accounts](mcp-accounts), [mcp-cart](mcp-cart), [mcp-orders](mcp-orders) | Thin MCP (stdio) servers, each wrapping part of the API. Also usable from Claude Code/Desktop on their own.        |
| [adk-chat-agents](adk-chat-agents)                                                                       | The ADK coordinator + specialist agents, an AG-UI server, and the CopilotKit web UI in `web/`.                     |

## Prerequisites

[uv](https://docs.astral.sh/uv/), Python 3.12+, Node 20+, and a Google Cloud project with
Vertex AI enabled (the agents default to `gemini-2.5-flash`).

## Quick start

```sh
# 1. backend (port 8000)
cd fake-shop-api && uv run fake-shop-api

# 2. agent: configure once, then run the AG-UI server (port 8001)
cd adk-chat-agents
uv sync && cp .env.example .env     # set GOOGLE_CLOUD_PROJECT
gcloud auth application-default login
uv run shop-agent-server

# 3. web UI (port 3000)
cd adk-chat-agents/web && npm install && npm run dev
```

Open http://localhost:3000 and sign in with a demo user.

The MCP servers are launched by the agent automatically (`uv run --directory ../mcp-…`), so there
is nothing to start for them. To use them from Claude Code instead, see each project's README.

## Tests and linting

```sh
make test     # pytest in every Python project
make lint     # ruff check + format check
make format
```

`mcp-*` tests start `fake-shop-api` from the sibling directory, so keep the projects side by side.

## Resetting data

Delete `fake-shop-api/src/fake_shop_api/data/shop.db`; it is re-seeded from
`fake-shop-api/src/fake_shop_api/seed/*.json` on the next request.
