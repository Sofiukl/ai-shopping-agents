import sqlite3

import pytest
from fastapi.testclient import TestClient

from fake_shop_api import db
from fake_shop_api.app import app

ADDR = {"line1": "1 Main St", "city": "Pune", "postal_code": "411001", "country": "IN"}


@pytest.fixture
def api(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOP_DB", str(tmp_path / "shop.db"))
    return TestClient(app)


def login(api, email="bob@example.com", password="bob12345") -> dict:
    r = api.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_login(api):
    ok = api.post("/auth/login", json={"email": "Alice@example.com", "password": "alice123"})
    assert ok.status_code == 200 and ok.json()["user"]["id"] == "U001" and ok.json()["token"]
    assert "password_hash" not in ok.json()["user"]
    bad = api.post("/auth/login", json={"email": "alice@example.com", "password": "nope"})
    assert bad.status_code == 401
    me = api.get("/me", headers=login(api, "alice@example.com", "alice123"))
    assert me.json()["default_address"]["city"] == "Kolkata"


def test_auth_required(api):
    for method, path in [
        ("GET", "/me"),
        ("GET", "/me/cart"),
        ("POST", "/me/cart/items"),
        ("DELETE", "/me/cart"),
        ("GET", "/me/orders"),
        ("POST", "/orders"),
        ("POST", "/auth/logout"),
    ]:
        assert api.request(method, path).status_code == 401, path
    assert api.get("/me", headers={"Authorization": "Bearer nope"}).status_code == 401
    assert api.get("/me", headers={"Authorization": "Basic abc"}).status_code == 401
    assert api.get("/products").status_code == 200  # catalog is public


def test_logout_invalidates_token(api):
    h = login(api)
    other = login(api)  # a second session for the same user stays valid
    assert api.post("/auth/logout", headers=h).status_code == 204
    assert api.get("/me", headers=h).status_code == 401
    assert api.post("/auth/logout", headers=h).status_code == 401
    assert api.get("/me", headers=other).status_code == 200


def test_expired_token(api, tmp_path):
    h = login(api)
    with sqlite3.connect(db.db_path()) as conn:
        conn.execute("UPDATE sessions SET expires_at = '2000-01-01T00:00:00+00:00'")
    assert api.get("/me", headers=h).status_code == 401


def test_products(api):
    assert len(api.get("/products").json()) == 18
    assert [p["id"] for p in api.get("/products", params={"query": "mouse"}).json()] == ["P001"]
    cheap = api.get("/products", params={"category": "home", "max_price": 700}).json()
    assert [p["id"] for p in cheap] == ["P006"]
    assert api.get("/products/P001").json()["price"] == 799
    assert api.get("/products/nope").status_code == 404


def test_categories(api):
    cats = {c["name"]: c["product_count"] for c in api.get("/categories").json()}
    assert cats == {"apparel": 4, "electronics": 10, "home": 4}


def test_cart_is_per_user(api):
    bob, alice = login(api), login(api, "alice@example.com", "alice123")
    add = api.post("/me/cart/items", json={"product_id": "P001", "quantity": 2}, headers=bob)
    assert add.json()["items"][0]["qty"] == 2 and add.json()["total"] == 1598
    assert api.get("/me/cart", headers=alice).json()["items"] == []
    for body in (
        {"product_id": "nope", "quantity": 1},
        {"product_id": "P001", "quantity": 0},
        {"product_id": "P001", "quantity": 10**6},
    ):
        assert api.post("/me/cart/items", json=body, headers=bob).status_code in (400, 404)
    assert api.delete("/me/cart/items/P001", headers=bob).json()["items"] == []
    assert api.delete("/me/cart/items/P001", headers=bob).status_code == 404
    api.post("/me/cart/items", json={"product_id": "P001", "quantity": 1}, headers=bob)
    assert api.delete("/me/cart", headers=bob).status_code == 204
    assert api.get("/me/cart", headers=bob).json()["items"] == []


def test_order_flow(api):
    bob = login(api)
    stock = api.get("/products/P001").json()["stock"]
    r = api.post("/orders", json={"items": {"P001": 2}, "shipping_address": ADDR}, headers=bob)
    assert r.status_code == 201
    order = r.json()
    assert order["user_id"] == "U002" and order["total"] == 1598 and order["status"] == "placed"
    assert order["items"][0]["name"] == "Wireless Mouse"
    assert api.get("/products/P001").json()["stock"] == stock - 2
    assert [o["id"] for o in api.get("/me/orders", headers=bob).json()] == [order["id"]]
    alice = login(api, "alice@example.com", "alice123")
    assert order["id"] not in [o["id"] for o in api.get("/me/orders", headers=alice).json()]


def test_order_errors_are_atomic(api):
    bob = login(api)
    stock = api.get("/products/P001").json()["stock"]
    body = {"items": {"P001": 1, "P002": 10**6}, "shipping_address": ADDR}
    assert api.post("/orders", json=body, headers=bob).status_code == 409
    assert api.post("/orders", json={**body, "items": {"nope": 1}}, headers=bob).status_code == 404
    assert api.post("/orders", json={**body, "items": {}}, headers=bob).status_code == 400
    assert api.get("/products/P001").json()["stock"] == stock  # nothing decremented
    assert api.get("/me/orders", headers=bob).json() == []


def test_estimate(api):
    assert len(api.post("/shipping/estimate", json=ADDR).json()["delivery_date"]) == 10


def test_concurrent_requests_on_real_server(tmp_path):
    """Real server + threads: the thread-affinity bug only shows up outside TestClient."""
    from concurrent.futures import ThreadPoolExecutor

    import httpx

    from fake_shop_api.testing import live_server

    with live_server(tmp_path / "shop.db") as url:
        login = httpx.post(
            f"{url}/auth/login", json={"email": "bob@example.com", "password": "bob12345"}
        )
        h = {"Authorization": f"Bearer {login.json()['token']}"}
        order = {"items": {"P005": 1}, "shipping_address": ADDR}

        def hit(i):
            if i % 2:
                return httpx.post(f"{url}/orders", json=order, headers=h).status_code
            return httpx.delete(f"{url}/me/cart", headers=h).status_code

        with ThreadPoolExecutor(8) as pool:
            codes = list(pool.map(hit, range(40)))
        assert set(codes) == {201, 204}
        assert httpx.get(f"{url}/products/P005").json()["stock"] == 100 - 20
