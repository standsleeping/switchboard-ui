"""Render the React example shell for Vite."""

import argparse
from pathlib import Path

from switchboard_ui import Island, Shell, render_shell

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "index.html"

EXAMPLE_HEAD = '<script type="module" src="/src/main.jsx"></script>'


def build_page() -> str:
    """Render the example shell."""
    shell = Shell(
        title="switchboard-ui React example",
        regions={
            "head-c": (
                Island(
                    name="react-title",
                    initial="switchboard-ui / React",
                ),
            ),
            "body-c": (
                Island(
                    name="react-counter",
                    props={"start": 0},
                    publishes=("react:count",),
                    initial='<div class="sb-demo-pad">Loading counter...</div>',
                ),
            ),
            "body-r": (
                Island(
                    name="react-readout",
                    subscribes=("react:count",),
                    initial='<div class="sb-demo-readout">Loading readout...</div>',
                ),
            ),
            "foot-c": (
                Island(
                    name="react-note",
                    initial="React owns the island; switchboard owns the shell.",
                ),
            ),
        },
    )
    return render_shell(shell, extra_head=EXAMPLE_HEAD)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="where to write the generated index.html",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Render the Vite entry HTML."""
    args = parse_args(argv)
    args.out.write_text(build_page(), encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
