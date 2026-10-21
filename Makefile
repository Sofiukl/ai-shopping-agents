PROJECTS := fake-shop-api mcp-catalog mcp-accounts mcp-cart mcp-orders adk-chat-agents

.PHONY: test lint format

test:
	@for p in $(PROJECTS); do echo "== $$p"; (cd $$p && uv run pytest -q) || exit 1; done

lint:
	@for p in $(PROJECTS); do echo "== $$p"; (cd $$p && uv run ruff check . && uv run ruff format --check .) || exit 1; done

format:
	@for p in $(PROJECTS); do (cd $$p && uv run ruff check --fix . && uv run ruff format .); done
