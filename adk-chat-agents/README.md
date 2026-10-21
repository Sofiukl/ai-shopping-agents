# adk-chat-agents

A conversational shopping assistant built on [Google ADK](https://google.github.io/adk-docs/):
a coordinator agent plus catalog, cart, checkout and order-history specialists. Their tools are
the sibling `mcp-*` servers, which call the `fake-shop-api` backend.

Two ways to talk to it:

| Front end | Login | Command |
|---|---|---|
| ADK dev UI | typed in chat (`LOGIN_MODE=chat`, the default) | `uv run adk web src --port 8080` |
| CopilotKit web app in [`web/`](web/) | separate sign-in form (`LOGIN_MODE=form`), so the password never reaches the LLM | `uv run shop-agent-server` + `npm run dev` in `web/` |

## Setup

```sh
uv sync
cp .env.example .env   # set GOOGLE_CLOUD_PROJECT (Vertex AI, uses Application Default Credentials)
gcloud auth application-default login
```

## Run

The backend must be running first (`cd ../fake-shop-api && uv run fake-shop-api`, port 8000).

```sh
# ADK dev UI (port 8000 is taken by the shop API, so pick another)
uv run adk web src --port 8080

# CopilotKit UI
uv run shop-agent-server          # AG-UI endpoint on :8001
cd web && npm install && npm run dev   # http://localhost:3000
```

Demo logins: see the root [README](../README.md).

## Develop

```sh
uv run pytest                      # no LLM or API needed
uv run ruff check . && uv run ruff format .
```

Architecture notes live in [CLAUDE.md](CLAUDE.md).
