"""Fake e-commerce REST API. Errors are HTTP status codes with a ``{"detail": "..."}`` body."""

import json
import secrets
import sqlite3
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from . import db
from .auth import verify_password

app = FastAPI(title="Fake Shop API")


def get_conn() -> Iterator[sqlite3.Connection]:
    with db.connect() as conn:
        yield conn


Conn = Annotated[sqlite3.Connection, Depends(get_conn)]

TOKEN_TTL = timedelta(hours=24)


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def current_user(conn: Conn, authorization: Annotated[str | None, Header()] = None) -> sqlite3.Row:
    """Resolve ``Authorization: Bearer <token>`` to the logged-in user, or 401."""
    scheme, _, token = (authorization or "").partition(" ")
    row = None
    if scheme.lower() == "bearer" and token:
        row = conn.execute(
            "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id "
            "WHERE s.token = ? AND s.expires_at > ?",
            (token, _now()),
        ).fetchone()
    if row is None:
        raise HTTPException(401, "Invalid or missing token.")
    return row


User = Annotated[sqlite3.Row, Depends(current_user)]


class Address(BaseModel):
    line1: str
    city: str
    postal_code: str
    country: str


class LoginIn(BaseModel):
    email: str
    password: str


class CartItemIn(BaseModel):
    product_id: str
    quantity: int


class OrderIn(BaseModel):
    items: dict[str, int]
    shipping_address: Address


def _user(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "default_address": json.loads(row["default_address"]),
    }


def _require_product(conn: sqlite3.Connection, product_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if row is None:
        raise HTTPException(404, f"Unknown product {product_id}")
    return row


# --- auth ---------------------------------------------------------------------------------


@app.post("/auth/login")
def login(body: LoginIn, conn: Conn) -> dict:
    row = conn.execute("SELECT * FROM users WHERE email = ?", (body.email,)).fetchone()
    if row is None or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(401, "Invalid email or password.")
    token = secrets.token_urlsafe(32)
    expires = (datetime.now(UTC) + TOKEN_TTL).isoformat(timespec="seconds")
    conn.execute("INSERT INTO sessions VALUES (?,?,?)", (token, row["id"], expires))
    return {"token": token, "user": _user(row)}


@app.post("/auth/logout", status_code=204)
def logout(user: User, conn: Conn, authorization: Annotated[str | None, Header()] = None) -> None:
    """Invalidate the bearer token used for this request."""
    token = (authorization or "").partition(" ")[2]
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


@app.get("/me")
def get_me(user: User) -> dict:
    return _user(user)


# --- products -------------------------------------------------------------------------------


@app.get("/products")
def search_products(
    conn: Conn, query: str = "", category: str = "", max_price: float | None = None
) -> list[dict]:
    sql, args = "SELECT * FROM products WHERE 1=1", []
    if query:
        sql += " AND (name LIKE ? OR description LIKE ?)"
        args += [f"%{query}%"] * 2
    if category:
        sql += " AND category = ? COLLATE NOCASE"
        args.append(category)
    if max_price is not None:
        sql += " AND price <= ?"
        args.append(max_price)
    return [dict(r) for r in conn.execute(sql + " ORDER BY id", args)]


@app.get("/categories")
def list_categories(conn: Conn) -> list[dict]:
    rows = conn.execute(
        "SELECT category AS name, COUNT(*) AS product_count FROM products "
        "GROUP BY category ORDER BY category"
    )
    return [dict(r) for r in rows]


@app.get("/products/{product_id}")
def get_product(product_id: str, conn: Conn) -> dict:
    return dict(_require_product(conn, product_id))


# --- carts ----------------------------------------------------------------------------------


def _cart(conn: sqlite3.Connection, user_id: str) -> dict:
    items = [
        {**dict(r), "line_total": round(r["qty"] * r["unit_price"], 2)}
        for r in conn.execute(
            "SELECT c.product_id, p.name, c.qty, p.price AS unit_price, p.image_url "
            "FROM cart_items c JOIN products p ON p.id = c.product_id "
            "WHERE c.user_id = ? ORDER BY c.rowid",
            (user_id,),
        )
    ]
    return {"items": items, "total": round(sum(i["line_total"] for i in items), 2)}


@app.get("/me/cart")
def view_cart(user: User, conn: Conn) -> dict:
    return _cart(conn, user["id"])


@app.post("/me/cart/items")
def add_to_cart(body: CartItemIn, user: User, conn: Conn) -> dict:
    user_id = user["id"]
    with db.transaction(conn):
        product = _require_product(conn, body.product_id)
        row = conn.execute(
            "SELECT qty FROM cart_items WHERE user_id = ? AND product_id = ?",
            (user_id, body.product_id),
        ).fetchone()
        new_qty = (row["qty"] if row else 0) + body.quantity
        if body.quantity < 1 or new_qty > product["stock"]:
            raise HTTPException(400, f"Invalid quantity (stock: {product['stock']}).")
        conn.execute(
            "INSERT INTO cart_items VALUES (?,?,?) "
            "ON CONFLICT(user_id, product_id) DO UPDATE SET qty = excluded.qty",
            (user_id, body.product_id, new_qty),
        )
    return _cart(conn, user_id)


@app.delete("/me/cart/items/{product_id}")
def remove_from_cart(product_id: str, user: User, conn: Conn) -> dict:
    user_id = user["id"]
    with db.transaction(conn):
        deleted = conn.execute(
            "DELETE FROM cart_items WHERE user_id = ? AND product_id = ?", (user_id, product_id)
        ).rowcount
    if not deleted:
        raise HTTPException(404, f"{product_id} is not in the cart.")
    return _cart(conn, user_id)


@app.delete("/me/cart", status_code=204)
def clear_cart(user: User, conn: Conn) -> None:
    with db.transaction(conn):
        conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user["id"],))


# --- orders ---------------------------------------------------------------------------------


def _orders(conn: sqlite3.Connection, user_id: str) -> list[dict]:
    orders = []
    for o in conn.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at", (user_id,)):
        items = conn.execute(
            "SELECT product_id, name, qty, unit_price FROM order_items WHERE order_id = ?",
            (o["id"],),
        )
        orders.append(
            {
                "id": o["id"],
                "user_id": o["user_id"],
                "items": [dict(i) for i in items],
                "total": o["total"],
                "shipping_address": json.loads(o["shipping_address"]),
                "status": o["status"],
                "created_at": o["created_at"],
            }
        )
    return orders


@app.get("/me/orders")
def list_orders(user: User, conn: Conn) -> list[dict]:
    return _orders(conn, user["id"])


@app.post("/orders", status_code=201)
def create_order(body: OrderIn, user: User, conn: Conn) -> dict:
    """Validate stock, decrement it and persist the order in one transaction."""
    if not body.items:
        raise HTTPException(400, "Order has no items.")
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    with db.transaction(conn):
        lines = []
        for pid, qty in body.items.items():
            product = _require_product(conn, pid)
            if qty < 1:
                raise HTTPException(400, f"Invalid quantity for {product['name']}")
            if product["stock"] < qty:
                raise HTTPException(409, f"Only {product['stock']} left of {product['name']}")
            lines.append((pid, product["name"], qty, product["price"]))
        for pid, _, qty, _ in lines:
            conn.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (qty, pid))
        conn.execute(
            "INSERT INTO orders VALUES (?,?,?,?,?,?)",
            (
                order_id,
                user["id"],
                round(sum(q * p for _, _, q, p in lines), 2),
                body.shipping_address.model_dump_json(),
                "placed",
                _now(),
            ),
        )
        conn.executemany(
            "INSERT INTO order_items VALUES (?,?,?,?,?)", [(order_id, *ln) for ln in lines]
        )
    return next(o for o in _orders(conn, user["id"]) if o["id"] == order_id)


@app.post("/shipping/estimate")
def estimate_delivery(address: Address) -> dict:
    return {"delivery_date": (datetime.now(UTC) + timedelta(days=2)).date().isoformat()}


def main() -> None:
    uvicorn.run(app, host="127.0.0.1", port=8000)
