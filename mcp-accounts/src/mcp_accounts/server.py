"""MCP server exposing user accounts over stdio."""

from mcp.server import MCPServer

from . import client

mcp = MCPServer("accounts")


@mcp.tool()
def login(email: str, password: str) -> dict:
    """Check an email and password. On success returns the user profile and a session token."""
    result = client.authenticate(email, password)
    if result is None:
        return {"status": "error", "error": "Invalid email or password."}
    return {"status": "ok", **result}


@mcp.tool()
def get_profile(token: str) -> dict:
    """Get the profile of the user that owns the session token."""
    try:
        return {"status": "ok", "user": client.get_user(token)}
    except ValueError as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
def logout(token: str) -> dict:
    """End the session: invalidate the session token."""
    try:
        client.logout(token)
    except ValueError as e:
        return {"status": "error", "error": str(e)}
    return {"status": "ok"}


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
