"""HTTP client for the fake shop API (``SHOP_API_URL``, default http://127.0.0.1:8000)."""

import os

import httpx


class ApiError(ValueError):
    """The API rejected the request; ``str(e)`` is its human-readable ``detail``."""

    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status = status


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    base = os.getenv("SHOP_API_URL", "http://127.0.0.1:8000")
    try:
        resp = httpx.request(method, base + path, timeout=10, **kwargs)
    except httpx.HTTPError as e:
        raise ApiError(0, f"Shop API unreachable at {base}: {e.__class__.__name__}") from e
    if resp.is_error:
        try:
            detail = resp.json()["detail"]
        except (ValueError, KeyError, TypeError):
            detail = resp.text
        raise ApiError(resp.status_code, str(detail))
    return resp


def search_products(
    query: str = "", category: str = "", max_price: float | None = None
) -> list[dict]:
    params = {"query": query, "category": category, "max_price": max_price}
    return _request("GET", "/products", params={k: v for k, v in params.items() if v}).json()


def list_categories() -> list[dict]:
    return _request("GET", "/categories").json()


def get_product(product_id: str) -> dict | None:
    try:
        return _request("GET", f"/products/{product_id}").json()
    except ApiError as e:
        if e.status == 404:
            return None
        raise
