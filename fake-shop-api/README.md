# fake-shop-api

Fake e-commerce backend (FastAPI + SQLite) that the `mcp-*` servers call over HTTP.
The DB is created and seeded from `src/fake_shop_api/seed/*.json` on first request
(`SHOP_DB` overrides the file path; default `src/fake_shop_api/data/shop.db`, gitignored).
Delete the file to reset.

Run: `uv run fake-shop-api` (http://127.0.0.1:8000, docs at `/docs`). Tests: `uv run pytest`.

Endpoints: `POST /auth/login` (returns a bearer `token` + `user`), `GET /products`, `GET /categories`,
`GET /products/{id}`, `POST /shipping/estimate` (public); with `Authorization: Bearer <token>`:
`GET /me`, `GET|POST /me/cart[/items]`, `DELETE /me/cart[/items/{product_id}]`, `POST /orders`,
`GET /me/orders`. Tokens expire after 24h and live in the `sessions` table.
Errors are HTTP status codes with a `{"detail": "..."}` body.
