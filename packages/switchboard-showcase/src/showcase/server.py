"""Showcase dev server: render switchboard's own pages live and reload on change.

Phase 0 of the showcase: the live
surface every later phase iterates against. It renders through the public
``render_document`` exactly as the demo CLI does, themes the page through the
``extra_head`` seam, and reloads the browser on any source edit so the theme and
components can be shaped by sight.

Pure stdlib, no third-party dependency: the package ships zero runtime deps and
only dev tooling, and the showcase honors that identity (no watchfiles, uvicorn,
or livereload). Hot reload is one mechanism for both Python and asset edits:

    watch mtimes -> re-exec the process -> the browser's dropped livereload
    stream reconnects to the fresh process, sees a new start token, and reloads.

Re-exec (not reimport) because a long-lived interpreter will not pick up edited
modules; a fresh process imports them cleanly.
"""

import argparse
import os
import sys
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import switchboard_theme
from showcase.build import (
    build_showcase,
    build_theme_builder,
    showcase_scripts,
    showcase_styles,
    theme_builder_scripts,
    theme_builder_styles,
)
from showcase.docs import DOCS_ROOT, build_doc, docs_scripts, docs_styles
from switchboard_ui import Document, render_document

REPO_ROOT = Path(__file__).resolve().parents[4]
WATCH_DIRS = (
    REPO_ROOT / "src" / "switchboard_ui",
    REPO_ROOT / "packages" / "switchboard-theme" / "src" / "switchboard_theme",
    REPO_ROOT / "packages" / "switchboard-showcase" / "src" / "showcase",
)
WATCH_SUFFIXES = (".py", ".css", ".js")

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9015
LIVERELOAD_PATH = "/__livereload"

# One token per process. A browser whose livereload stream reconnects and sees a
# *different* token knows the server re-exec'd, and reloads itself.
START_TOKEN = str(time.time_ns())

# Injected via extra_scripts (extra_head is reserved for the theme, so the two
# seams never collide). The server sends one token per connection. The first
# token a page sees this life is recorded and ignored; a *later* token arrives
# only because EventSource auto-reconnected after the socket dropped on re-exec,
# so a changed value means the server restarted -> reload. Held in a page-local
# var, never sessionStorage: a reload starts a fresh page that re-records the
# live token and settles, so a token from a prior process cannot outlive the page
# and drive an endless reload loop.
_RELOAD_CLIENT = """
(function () {
  var booted = null;
  var es = new EventSource("/__livereload");
  es.onmessage = function (e) {
    if (booted === null) { booted = e.data; return; }
    if (e.data !== booted) { location.reload(); }
  };
})();
"""


def _render(document: Document, styles: str, scripts: tuple[str, ...]) -> str:
    """Render a document themed, with the live-reload client attached.

    ``extra_head`` carries the components' structural CSS then the theme's paint
    (structure before paint, so the cascade resolves correctly); ``extra_scripts``
    carries the island adapters and the live-reload client.
    """
    return render_document(
        document,
        extra_head=styles + switchboard_theme.head("default"),
        extra_scripts=(*scripts, _RELOAD_CLIENT),
    )


def render_page() -> str:
    """Render the showcase gallery page."""
    return _render(build_showcase(), showcase_styles(), showcase_scripts())


def render_builder_page() -> str:
    """Render the theme-builder page (the capstone dogfood)."""
    return _render(
        build_theme_builder(), theme_builder_styles(), theme_builder_scripts()
    )


def render_docs_page(relpath: str) -> str:
    """Render a documentation page (the docs rendered through switchboard itself)."""
    return _render(build_doc(relpath), docs_styles(), docs_scripts())


def _docs_relpath(path: str) -> str | None:
    """Resolve a ``/docs`` URL path to a doc path under ``docs/``, or ``None``.

    ``/docs`` is the index; ``/docs/<category>/<page>`` is a doc. The resolved
    file must stay inside ``DOCS_ROOT`` (no ``..`` escape) and exist, else this
    returns ``None`` and the caller 404s.
    """
    if path in {"/docs", "/docs/"}:
        return "index.md"
    relpath = f"{path.removeprefix('/docs/')}.md"
    target = (DOCS_ROOT / relpath).resolve()
    if not target.is_relative_to(DOCS_ROOT) or not target.is_file():
        return None
    return relpath


class Handler(BaseHTTPRequestHandler):
    """Serve the rendered showcase page and the live-reload event stream."""

    def do_GET(self) -> None:
        """Route the gallery, the builder, the docs, the live-reload stream, else 404."""
        path = urlparse(self.path).path
        if path == LIVERELOAD_PATH:
            self._serve_livereload()
        elif path in {"/", "/index.html"}:
            self._serve_html(render_page())
        elif path == "/builder":
            self._serve_html(render_builder_page())
        elif path == "/docs" or path.startswith("/docs/"):
            relpath = _docs_relpath(path)
            if relpath is None:
                self.send_error(HTTPStatus.NOT_FOUND)
            else:
                self._serve_html(render_docs_page(relpath))
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def _serve_html(self, html: str) -> None:
        body = html.encode()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_livereload(self) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(f"retry: 500\ndata: {START_TOKEN}\n\n".encode())
            self.wfile.flush()
            while True:
                time.sleep(1.0)
                self.wfile.write(b": keep-alive\n\n")
                self.wfile.flush()
        except BrokenPipeError, ConnectionResetError:
            pass  # client navigated away, or the process is re-execing

    def log_message(self, format: str, *args: object) -> None:
        """Log page requests but not the livereload heartbeat (plumbing noise)."""
        if self.path.startswith(LIVERELOAD_PATH):
            return
        super().log_message(format, *args)


def _latest_mtime() -> int:
    """The newest mtime across every watched source file (0 if none exist)."""
    latest = 0
    for directory in WATCH_DIRS:
        for path in directory.rglob("*"):
            if path.suffix in WATCH_SUFFIXES and path.is_file():
                latest = max(latest, path.stat().st_mtime_ns)
    return latest


def _watch_and_reexec(interval: float = 0.5) -> None:
    """Re-exec the process when any watched source file changes.

    Re-exec via ``-m`` so the package context (``showcase``, ``switchboard_ui``)
    resolves exactly as the launcher set it up; ``sys.executable`` keeps the run
    inside the same virtualenv without re-entering ``uv run``.
    """
    baseline = _latest_mtime()
    while True:
        time.sleep(interval)
        if _latest_mtime() > baseline:
            os.execv(
                sys.executable,
                [sys.executable, "-m", "showcase.server", *sys.argv[1:]],
            )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Showcase dev server with hot reload.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--render",
        action="store_true",
        help="print the rendered HTML and exit (no server, no watcher)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the showcase dev server (or render once and exit with ``--render``)."""
    args = parse_args(argv)
    if args.render:
        print(render_page())
        return 0

    threading.Thread(target=_watch_and_reexec, daemon=True).start()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"showcase: serving http://{args.host}:{args.port} (hot reload on)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshowcase: stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
