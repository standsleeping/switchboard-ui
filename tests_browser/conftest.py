"""Fixtures for the real-browser regression tests.

These tests exist for the contracts a rendered-HTML assertion cannot reach:
scroll restoration timing, scrollbar geometry, sticky behaviour, and the absence
of movement in the first painted frame. Everything provable without executing
layout stays in the fast suite, which is why this directory sits outside
``testpaths`` and runs under its own target.

The server is stdlib ``http.server`` rather than the showcase's, so a case
controls exactly what it serves and how fast. That last part matters more than it
looks: a localhost fixture normally delivers a whole document in one flush, which
makes *any* end-of-body script run before the first paint. A test written against
that server certifies the one configuration that cannot fail. :func:`slow_site`
therefore chunks and delays its response so the parser reaches the nav long
before it reaches the end of the body, which is what a real connection does.
"""

import threading
import time
from collections.abc import Callable, Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

Routes = dict[str, str]


def _handler(routes: Routes, chunk_delay: float, chunk_size: int) -> type:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args: object) -> None:
            """Silence the per-request stderr logging."""

        def do_GET(self) -> None:
            path = self.path.split("?", 1)[0]
            body = routes.get(path)
            if body is None:
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            payload = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            # A fresh document per navigation: a cached one would let the browser
            # reuse state the test is trying to observe being rebuilt.
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if chunk_delay <= 0:
                self.wfile.write(payload)
                return
            for start in range(0, len(payload), chunk_size):
                self.wfile.write(payload[start : start + chunk_size])
                self.wfile.flush()
                time.sleep(chunk_delay)

    return Handler


class Site:
    """A running fixture server; ``url(path)`` addresses it."""

    def __init__(self, routes: Routes, chunk_delay: float, chunk_size: int) -> None:
        self._server = ThreadingHTTPServer(
            ("127.0.0.1", 0), _handler(routes, chunk_delay, chunk_size)
        )
        self.port = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def url(self, path: str = "/") -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)


@pytest.fixture
def site() -> Iterator[Callable[[Routes], Site]]:
    """Serve a route map in one flush (the fast path, for everything but timing)."""
    started: list[Site] = []

    def serve(routes: Routes) -> Site:
        running = Site(routes, chunk_delay=0.0, chunk_size=0)
        started.append(running)
        return running

    yield serve
    for running in started:
        running.close()


@pytest.fixture
def slow_site() -> Iterator[Callable[[Routes], Site]]:
    """Serve a route map in small delayed chunks, the way a real connection does.

    Without this, the parser reaches the end of the body in the same task that
    began the document, so an end-of-body script always precedes the first paint
    and a restoration bug is invisible. Chunking forces the browser to paint what
    it has before the document finishes, which is the condition the inline
    pre-paint script exists for.
    """
    started: list[Site] = []

    def serve(routes: Routes) -> Site:
        running = Site(routes, chunk_delay=0.02, chunk_size=2048)
        started.append(running)
        return running

    yield serve
    for running in started:
        running.close()
