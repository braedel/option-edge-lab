from __future__ import annotations

from options_lab import cli


def test_stage1a_dry_run(capsys):
    rc = cli.main(["stage1a", "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "stage1a grid" in out
