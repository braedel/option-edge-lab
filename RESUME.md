# RESUME — read this first

**Workspace:** `D:\workspace\options-edge-lab` (git &rarr; https://github.com/braedel/option-edge-lab).
**Python:** `D:\workspace\options-edge-lab\.venv\Scripts\python.exe` (full scientific stack) — run all analyses with it.

## ACTIVE GOAL (owner /goal, 2026-06-08)
> Create a tradeable strategy (options / futures / securities) with **Sharpe > 2**, profitable **most months**
> (give up no more than ~2/yr), **low drawdown**, runnable on **&le; $15k** capital.

A session Stop-hook enforces this. **Do NOT fabricate a >2** — see the deflated prior. Pursue it hard the
legitimate way; report only audited, verified numbers.

## DEFLATED PRIOR (carry this — it is the whole point)
A *robust* Sharpe > 2 (cost-real, leak-free, tail-included, OOS) is extraordinarily rare for retail. The goal's
**profile** (very high Sharpe + win-almost-every-month + low DD + small capital) is the textbook signature of
**short-volatility / option-premium selling**, whose lovely Sharpe **hides a catastrophic tail** (2018, 2020).
Hard evidence already in hand: the tradeable **PUTW** ETF (systematic put-selling) ran Sharpe **~0.7**, not >2.
No option-price data + **no data spend** &rarr; options strategies cannot be honestly backtested here.
**Verified ceiling is likely ~1–1.5.** A clean "lower than 2, here's why" is a valid result.

## STATUS
- **Study 1 — COMPLETE & pushed.** Diversified trend-following overlay + 60/40. After independent quant+eng
  audits and self re-verification, honest result = a **leak-free diversification overlay, Sharpe ~0.9–1.0**,
  that halves a 60/40's risk at ~equal return with crisis convexity — **NOT a 60/40-beating alpha** (not
  significant at 95%). Early "1.08 / >1 alpha / futures 1.07 / options-hedge lift" claims were artifacts,
  corrected. Deck: `docs/research/results/2026-06-03-trend-overlay-study-deck.html`; one-pager:
  `docs/research/results/2026-06-03-deployable-onepager.md`; registry: `CAMPAIGN.md`.
- **Study 2 — E1–E4 DONE, VERDICT REACHED & RE-VERIFIED (2026-06-08).** Charter+results+verdict:
  `docs/research/STUDY2-high-sharpe-target.md`. Scripts: c16 (ensemble **0.74**), c17 (short-vol: PUTW 0.68/
  −28%, SVXY 0.34/−95%, regime-filtered 0.27), c18 (pairs **−0.47**), c19 (crypto trend 1.41 full/**0.81 OOS**,
  but 42% pos-months). All 4 re-ran 2026-06-08, numbers replicate exactly, look-ahead audits = 0.00.
  **VERDICT: {Sharpe>2 + ≤2 losing-months/yr + low-DD + ≤$15k} is NOT achievable honestly on free data — the
  criteria are mutually contradictory.** Proof: ≤2 losing-months/yr ⇒ ≥83% positive months ⇒ Sharpe≈3.3
  (symmetric) OR negative skew = premium-selling = catastrophic tail. **Verified ceiling ~0.9–1.0** (Study-1
  trend overlay, already audited/deployable). **Awaiting owner decision (see NEXT STEPS).**

## CRITICAL METHOD LESSONS (from Study-1 audit — non-negotiable)
1. **Leak-free, PROVEN.** Every result passes a perturbation/truncation test (corrupt FUTURE data &rarr; PAST
   returns must not move). **No full-sample scaling** — it is look-ahead. Pattern in `campaign/c11_clean_verify.py`.
2. **Cost on ACTUAL levered turnover** (not pre-leverage) — `campaign/c12_audit_verify.py`. Add **short-borrow**
   on short legs (ETF proxy). Stress to 10 bps.
3. **Tail-inclusive DD** (bootstrap; one path understates it). **OOS** split + sub-periods. **Significance:**
   SE(Sharpe) &asymp; &radic;((1+0.5&middot;SR&sup2;)/years) &asymp; 0.3 over ~18 yr &rarr; "beats benchmark" needs a block-bootstrap.
4. **Independent audits, then RE-VERIFY them yourself** — subagents here have **fabricated** numbers (one audit's
   "0.67 @10bps" did NOT replicate; real 0.93). Always re-check in your own code.
5. Lead with the deflated prior; don't oversell.

## INFRA / DATA / HOW-TO
- **Reusable code:** `campaign/c5_tsmom.py` &rarr; `load(ticker)` (Yahoo JSON &rarr; daily adjclose Series),
  `sharpe`, `scale10`. `c11_clean_verify.py` = canonical leak-free trend+60/40 build + `audit()`. `c12` = audit
  re-verification. `c13`/`c14` = tearsheets. `c15` = deck generator.
- **Free data on disk:** `campaign/data/tsmom_*.json` = Yahoo daily for 21 ETFs (SPY QQQ IWM EFA EEM SHY IEF TLT
  TIP LQD HYG DBC USO UNG DBA GLD SLV VNQ UUP FXE FXY) + vix/spy/putw/svxy/gspc. Pull more free tickers:
  `Invoke-WebRequest "https://query1.finance.yahoo.com/v8/finance/chart/<T>?period1=1167609600&period2=1893456000&interval=1d" -Headers @{"User-Agent"="Mozilla/5.0"}` &rarr; save to `campaign/data/tsmom_<T>.json`.
- **No Databento key** (blank in `.env.txt`); **NO data spend**. In-hand SPX 0DTE = 90-sec close snapshot only
  (no morning option prices). Futures ES/NQ/YM 1-min live under `dat-trading-strategy-research` / `moc-signal-analysis`.
- **Git/GitHub:** `origin` = github.com/braedel/option-edge-lab (token-free URL; PAT in encrypted Windows cred +
  gitignored `.env.txt` &rarr; `OPT_EDGE_LAB_API_KEY`). `git -C D:\workspace\options-edge-lab push origin main` works.

## NEXT STEPS (Study 2 — awaiting owner decision, 2026-06-08)
The >2 goal is a verified NULL on free data. Owner to choose direction:
1. **Deliver the ~1.0 deployable** (recommended) — relax "win most months"; package the audited Study-1 trend
   overlay (Sharpe ~1.0, halves 60/40 risk, ≤$15k) as the real tradeable strategy. Only path that yields an
   actual tradeable result with no data spend and no fabrication.
2. **Write up the NULL** — document the verified result (criteria contradictory; ceiling ~1.0) as a Study-2
   result page/deck, mirroring Study-1's honest close.
3. **Spend on option data** — lift the no-spend constraint to test defined-risk option selling (the one path
   that *could* reach >2; but PUTW≈0.7 and a crash hits all positions at once).
4. **Keep hunting free data** — untested avenues (intraday ES/NQ 1-min, crypto funding carry). Low prior +
   multiple-testing risk: every new strategy on the same data raises the odds of a spurious >2.
