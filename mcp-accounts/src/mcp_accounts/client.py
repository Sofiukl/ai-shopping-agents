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


def authenticate(email: str, password: str) -> dict | None:
    """Return ``{"token": ..., "user": {...}}`` or None for bad credentials."""
    try:
        return _request("POST", "/auth/login", json={"email": email, "password": password}).json()
    except ApiError as e:
        if e.status == 401:
            return None
        raise


def get_user(token: str) -> dict:
    return _request("GET", "/me", token=token).json()


def logout(token: str) -> None:
    _request("POST", "/auth/logout", token)
