"""optlab CLI - command surface for the lab.

Subcommands are registered as the lab grows. For now this is a skeleton so the entry point exists
and ``optlab --version`` works.
"""
from __future__ import annotations

import argparse

from options_lab import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="optlab", description="options-edge-lab research CLI")
    parser.add_argument("--version", action="version", version=f"optlab {__version__}")
    parser.add_subparsers(dest="command")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    # Subcommands are wired here as the lab grows.
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
