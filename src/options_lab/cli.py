"""optlab CLI - command surface for the lab."""
from __future__ import annotations

import argparse

from options_lab import __version__

DEFAULT_GEX_CSV = r"D:\workspace\spx-0dte-pinfly-lab\data\squeezemetrics_gex.csv"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="optlab", description="options-edge-lab research CLI")
    parser.add_argument("--version", action="version", version=f"optlab {__version__}")
    sub = parser.add_subparsers(dest="command")
    s = sub.add_parser("stage1a", help="run the Stage-1a incremental-signal gate (v1)")
    s.add_argument("--gex-csv", default=DEFAULT_GEX_CSV)
    s.add_argument("--train-end", default="2025-09-01", help="OOS seal start (exclusive)")
    s.add_argument("--n-splits", type=int, default=5)
    s.add_argument("--out", default="reports/stage1a_v1")
    s.add_argument("--dry-run", action="store_true", help="print the grid plan and exit")
    return parser


def _run_stage1a(args) -> int:
    from options_lab.research.stage1a import HORIZONS, TARGETS

    print(f"stage1a grid: targets={list(TARGETS)} x horizons={list(HORIZONS)}  seal>={args.train_end}")
    if args.dry_run:
        return 0
    from options_lab.data.panel import load_daily_panel
    from options_lab.research.stage1a import run_stage1a

    panel = load_daily_panel(args.gex_csv)
    table, verdict = run_stage1a(panel, n_splits=args.n_splits, oos_start=args.train_end)
    print(table.to_string(index=False))
    print(f"\nOVERALL VERDICT: {verdict}")
    _write_report(args.out, table, verdict, panel, args)
    return 0


def _write_report(out, table, verdict, panel, args) -> None:
    import os
    import subprocess

    os.makedirs(out, exist_ok=True)
    table.to_csv(os.path.join(out, "table.csv"), index=False)
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    except Exception:
        commit = "unknown"
    with open(os.path.join(out, "verdict.md"), "w", encoding="utf-8") as f:
        f.write(f"# Stage-1a v1 verdict: {verdict}\n\n")
        f.write(f"- panel rows: {len(panel)}; "
                f"dates {panel['date'].min().date()} -> {panel['date'].max().date()}\n")
        f.write(f"- seal: >= {args.train_end}; n_splits={args.n_splits}; git {commit}\n\n")
        f.write("```\n" + table.to_string(index=False) + "\n```\n")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    if args.command == "stage1a":
        return _run_stage1a(args)
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
