"""HTTP client for the fake shop API (``SHOP_API_URL``, default http://127.0.0.1:8000)."""

import os

import httpx


class ApiError(ValueError):
    """The API rejected the request; ``str(e)`` is its human-readable ``detail``."""

    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status = status


def _request(method: str, path: str, token: str | None = None, **kwargs) -> httpx.Response:
    base = os.getenv("SHOP_API_URL", "http://127.0.0.1:8000")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = httpx.request(method, base + path, headers=headers, timeout=10, **kwargs)
    except httpx.HTTPError as e:
        raise ApiError(0, f"Shop API unreachable at {base}: {e.__class__.__name__}") from e
    if resp.is_error:
        try:
            detail = resp.json()["detail"]
        except (ValueError, KeyError, TypeError):
            detail = resp.text
        raise ApiError(resp.status_code, str(detail))
    return resp


def _as_map(cart: dict) -> dict[str, int]:
    return {i["product_id"]: i["qty"] for i in cart["items"]}


def add_to_cart(token: str, product_id: str, quantity: int) -> dict[str, int]:
    body = {"product_id": product_id, "quantity": quantity}
    return _as_map(_request("POST", "/me/cart/items", token, json=body).json())


def remove_from_cart(token: str, product_id: str) -> dict[str, int]:
    return _as_map(_request("DELETE", f"/me/cart/items/{product_id}", token).json())


def clear_cart(token: str) -> None:
    _request("DELETE", "/me/cart", token)


def view_cart(token: str) -> dict:
    return _request("GET", "/me/cart", token).json()
