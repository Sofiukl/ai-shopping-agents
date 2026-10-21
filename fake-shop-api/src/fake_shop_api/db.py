"""SQLite storage. The DB file is created and seeded from ``seed/*.json`` on first use."""

import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

SEED_DIR = Path(__file__).parent / "seed"

SCHEMA = """
CREATE TABLE users (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL, default_address TEXT
);
CREATE TABLE products (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL, price REAL NOT NULL,
    stock INTEGER NOT NULL CHECK (stock >= 0), description TEXT NOT NULL, image_url TEXT NOT NULL
);
CREATE TABLE cart_items (
    user_id TEXT NOT NULL REFERENCES users(id), product_id TEXT NOT NULL REFERENCES products(id),
    qty INTEGER NOT NULL CHECK (qty > 0), PRIMARY KEY (user_id, product_id)
);
CREATE TABLE orders (
    id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), total REAL NOT NULL,
    shipping_address TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE sessions (
    token TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), expires_at TEXT NOT NULL
);
CREATE TABLE order_items (
    order_id TEXT NOT NULL REFERENCES orders(id), product_id TEXT NOT NULL, name TEXT NOT NULL,
    qty INTEGER NOT NULL, unit_price REAL NOT NULL
);
"""


def db_path() -> Path:
    return Path(os.getenv("SHOP_DB", Path(__file__).parent / "data" / "shop.db"))


def _seed(conn: sqlite3.Connection) -> None:
    load = lambda name: json.loads((SEED_DIR / f"{name}.json").read_text())
    conn.executescript(SCHEMA)
    for u in load("users"):
        conn.execute(
            "INSERT INTO users VALUES (?,?,?,?,?)",
            (u["id"], u["name"], u["email"], u["password_hash"], json.dumps(u["default_address"])),
        )
    for p in load("products"):
        conn.execute(
            "INSERT INTO products VALUES (?,?,?,?,?,?,?)",
            (p["id"], p["name"], p["category"], p["price"], p["stock"], p["description"],
             p["image_url"]),
        )  # fmt: skip
    for o in load("orders"):
        conn.execute(
            "INSERT INTO orders VALUES (?,?,?,?,?,?)",
            (o["id"], o["user_id"], o["total"], json.dumps(o["shipping_address"]), o["status"],
             o["created_at"]),
        )  # fmt: skip
        for ln in o["items"]:
            conn.execute(
                "INSERT INTO order_items VALUES (?,?,?,?,?)",
                (o["id"], ln["product_id"], ln["name"], ln["qty"], ln["unit_price"]),
            )


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fresh = not path.exists()
    # isolation_level=None: we issue BEGIN/COMMIT ourselves (see ``transaction``).
    # check_same_thread=False: FastAPI may open the connection (dependency) and use it (route) on
    # different worker threads; a connection is still only ever used by one request at a time.
    conn = sqlite3.connect(path, isolation_level=None, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        if fresh:
            _seed(conn)
        yield conn
    finally:
        conn.close()


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[None]:
    """Write transaction; BEGIN IMMEDIATE takes the write lock up front so stock checks are safe."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    conn.execute("COMMIT")
