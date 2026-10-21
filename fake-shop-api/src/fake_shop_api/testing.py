"""Run the API on a free local port with a throwaway DB, for other projects' tests."""

import socket
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import uvicorn

from .app import app


@contextmanager
def live_server(db_file: Path) -> Iterator[str]:
    """Yield the base URL of a running API backed by a fresh seeded DB at ``db_file``."""
    import os

    os.environ["SHOP_DB"] = str(db_file)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.01)
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=5)
