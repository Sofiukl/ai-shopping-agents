# mcp-catalog

MCP server (stdio) for the product catalog. Thin client of `fake-shop-api` (`SHOP_API_URL`, default `http://127.0.0.1:8000`).

Tools: `search_products(query, category, max_price)`, `get_product(product_id)`, `list_categories()`.

```sh
uv run mcp-catalog
uv run pytest
```
