"""Smoke tests: the package imports and the CLI entry point is wired.

These are intentionally trivial - the lab is greenfield. Real characterization and research tests
arrive with the first ported mechanic / first strategy.
"""
from __future__ import annotations

import options_lab
from options_lab import cli


def test_package_version():
    assert options_lab.__version__ == "0.1.0"


def test_cli_parser_builds():
    parser = cli.build_parser()
    assert parser.prog == "optlab"


def test_cli_no_command_prints_help_and_exits_zero():
    assert cli.main([]) == 0
