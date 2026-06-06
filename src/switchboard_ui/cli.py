"""Command-line frontend: render the demo page to stdout.

This is the application layer. It is the only place that configures logging,
and it does so at runtime inside :func:`main` -- never at import time. Piping
the output to a file (``switchboard-ui > demo.html``) is the static-site path;
the renderer itself is backend-free.
"""

import argparse
import logging
import sys

from switchboard_ui.demo import build_demo, demo_scripts
from switchboard_ui.render import render_shell

logger = logging.getLogger(__name__)

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def configure_logging(level: int = logging.WARNING) -> None:
    """Configure the root logger for the application.

    Belongs to the application layer. ``force=True`` replaces any existing
    handlers so repeated invocations stay idempotent.

    Args:
        level: The logging level to set on the root logger.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s",
        stream=sys.stderr,
        force=True,
    )


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: Argument list (defaults to ``sys.argv[1:]``).

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog="switchboard-ui",
        description="Render the switchboard-ui demo page to stdout.",
    )
    parser.add_argument(
        "--runtime",
        choices=["inline", "linked"],
        default="inline",
        help="Embed the CSS/JS (inline) or reference them (linked).",
    )
    parser.add_argument(
        "--log-level",
        choices=LOG_LEVELS,
        default="WARNING",
        help="Logging level (default: WARNING).",
    )
    return parser.parse_args(args)


def main(args: list[str] | None = None) -> int:
    """Run the command-line frontend.

    Args:
        args: Argument list (defaults to ``sys.argv[1:]``).

    Returns:
        The process exit code.
    """
    parsed = parse_args(args)
    configure_logging(level=getattr(logging, parsed.log_level))
    logger.debug("Parsed arguments: %s", parsed)
    html = render_shell(
        build_demo(),
        runtime=parsed.runtime,
        extra_scripts=demo_scripts(),
    )
    print(html)
    return 0


if __name__ == "__main__":
    sys.exit(main())
