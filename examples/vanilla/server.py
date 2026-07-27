"""Run the vanilla DOM switchboard-ui example."""

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from switchboard_ui import Island, render_document, workbench

ROOT = Path(__file__).resolve().parent
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8001


def build_page() -> str:
    """Render the example page."""
    page = workbench(
        {
            "head-c": (
                Island(
                    name="vanilla-title",
                    initial="switchboard-ui / vanilla DOM",
                ),
            ),
            "body-c": (
                Island(
                    name="vanilla-counter",
                    props={"start": 0},
                    publishes=("vanilla:count",),
                    initial='<div class="sb-demo-pad">Loading counter...</div>',
                ),
            ),
            "body-r": (
                Island(
                    name="vanilla-readout",
                    subscribes=("vanilla:count",),
                    initial='<div class="sb-demo-readout">Loading readout...</div>',
                ),
            ),
            "foot-c": (
                Island(
                    name="vanilla-note",
                    initial="Plain DOM adapters, no framework.",
                ),
            ),
        },
        title="switchboard-ui vanilla example",
    )
    return render_document(
        page,
        extra_scripts=((ROOT / "adapters.js").read_text(encoding="utf-8"),),
    )


class Handler(BaseHTTPRequestHandler):
    """Serve the rendered example page."""

    def do_GET(self) -> None:
        """Serve the page at `/` and `/index.html`."""
        path = urlparse(self.path).path
        if path not in {"/", "/index.html"}:
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        body = build_page().encode()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--render",
        action="store_true",
        help="print the rendered HTML and exit",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the example server."""
    args = parse_args(argv)
    if args.render:
        print(build_page())
        return 0

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Serving http://{args.host}:{args.port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
