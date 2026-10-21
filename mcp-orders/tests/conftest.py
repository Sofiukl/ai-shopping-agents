import httpx
import pytest
from fake_shop_api.testing import live_server


@pytest.fixture(autouse=True)
def shop_api(tmp_path, monkeypatch):
    """Run the real fake-shop-api on a throwaway DB; the MCP client talks to it over HTTP."""
    with live_server(tmp_path / "shop.db") as url:
        monkeypatch.setenv("SHOP_API_URL", url)
        yield url


@pytest.fixture
def token(shop_api):
    r = httpx.post(
        f"{shop_api}/auth/login", json={"email": "alice@example.com", "password": "alice123"}
    )
    return r.json()["token"]
