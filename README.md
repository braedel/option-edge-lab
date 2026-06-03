# options-edge-lab

A disciplined, underlying- and structure-agnostic research lab for systematic **options** strategies.

Greenfield clean slate — spun out from `spx-0dte-pinfly-lab`, keeping the *process and mechanics* and
dropping the strategy-specific noise. No strategy code lives here yet: candidate edges are selected,
pressure-tested under the integrity rules, and only then built.

## Philosophy
- **Truth over a good-looking backtest.** A clean "no edge" is a valid, valuable result.
- **Mechanics on demand.** Reusable code (CPCV validation, multiple-testing haircut, fill modeling,
  data loaders, ...) is ported from prior labs only when a candidate actually needs it — never bulk-copied.
- **Seal the OOS, correct for multiple testing, demand |t|>3, beat dumb baselines, model real fills.**
  Full standards in `CLAUDE.md`; process in `docs/research/quant_research_process.md`.

## Layout
```
src/options_lab/        # the package (core / data / research / forensic) — empty skeleton, filled as needed
tests/                  # pytest is the single source of truth for "tests pass"
docs/research/          # research process + methodology
data/                   # raw / interim / processed (gitignored; placeholders only)
```

## Getting started
```
python -m venv .venv
.venv\Scripts\activate            # Windows (use source .venv/bin/activate elsewhere)
pip install -e ".[dev]"           # full scientific stack + pytest/ruff
python -m pytest                  # green from day 1
optlab --version
```
The heavy scientific stack is only needed once an idea does real computation; the smoke tests pass with
just `pytest` installed.

## Status
Selecting candidate options edges (deflated-prior-first triage). Target structure / underlying: **TBD**
— see `GOAL.md`.
