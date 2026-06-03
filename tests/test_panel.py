from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from options_lab.data.panel import PANEL_COLUMNS, load_daily_panel

SQZ_CSV = Path(r"D:\workspace\spx-0dte-pinfly-lab\data\squeezemetrics_gex.csv")


def _write_csv(tmp_path, rows):
    p = tmp_path / "gex.csv"
    pd.DataFrame(rows).to_csv(p, index=False)
    return p


def test_panel_shape_and_returns(tmp_path):
    rows = [
        {"date": "2020-01-03", "price": 100.0, "dix": 0.40, "gex": 1.0e9},
        {"date": "2020-01-02", "price": 100.0, "dix": 0.41, "gex": 1.1e9},  # out of order
        {"date": "2020-01-06", "price": 110.0, "dix": 0.39, "gex": 0.9e9},
    ]
    panel = load_daily_panel(_write_csv(tmp_path, rows))
    assert list(panel.columns) == PANEL_COLUMNS
    assert str(panel["date"].dtype).startswith("datetime64")
    assert list(panel["date"]) == sorted(panel["date"])
    assert pd.isna(panel["ret"].iloc[0])
    assert panel["ret"].iloc[2] == pytest.approx(0.10)


def test_panel_dedup_keep_last(tmp_path):
    rows = [
        {"date": "2020-01-02", "price": 100.0, "dix": 0.40, "gex": 1.0e9},
        {"date": "2020-01-02", "price": 101.0, "dix": 0.42, "gex": 1.2e9},
    ]
    panel = load_daily_panel(_write_csv(tmp_path, rows))
    assert len(panel) == 1
    assert panel["spx_close"].iloc[0] == 101.0


def test_panel_rejects_non_real(tmp_path):
    rows = [{"date": "2020-01-02", "price": 100.0, "dix": 0.4, "gex": 1e9, "source": "synthetic"}]
    with pytest.raises(ValueError):
        load_daily_panel(_write_csv(tmp_path, rows))


@pytest.mark.skipif(not SQZ_CSV.exists(), reason="real SqueezeMetrics CSV not present")
def test_panel_real_file():
    panel = load_daily_panel(SQZ_CSV)
    assert len(panel) > 3000
    assert panel["date"].min().year < 2012
    assert panel["spx_close"].notna().all()
