# Diversified Trend Overlay + 60/40 — One-Pager (AUDITED: independent quant + engineering review)

**Date:** 2026-06-03 · **Scripts:** `campaign/c7`–`c12` · **Data:** free Yahoo daily, 21 ETFs, 2008-04 → 2026-06.
**Review:** independent engineering audit (code) + quant audit (methodology), each finding **independently
re-verified** in `c12`. Headline corrected DOWN from earlier overstatements.

## What it actually is (corrected)
A **diversifying risk-reduction overlay** — a trend-following sleeve combined 50/50 with a 60/40 core.
It is **NOT a 60/40-beating alpha.** Verified contributions:
- Earns **~the same return as 60/40** (CAGR 8.1% vs 8.8%, i.e. **−0.7%/yr**) …
- … at **much lower risk: vol 7.6% vs 11.4%, maxDD −12.4% vs −31%**, with crisis convexity (+ in 2008/2022).
- The Sharpe edge is **entirely risk reduction**, not added return.

## Verified, audited numbers
| | Sharpe | maxDD | vol | CAGR |
|---|---:|---:|---:|---:|
| 60/40 | 0.80 | −31% | 11.4% | 8.8% |
| **DEPLOY — full 21-ETF, 2bps** | **1.07** | −12.4% | 7.6% | 8.1% |
| DEPLOY — liquid core, proper cost + 1% borrow | **~0.91** | −14% | — | — |

**Honest Sharpe ≈ 0.9–1.0** (the realistically tradeable, properly-costed, borrow-charged, liquid version).
The 1.07 leans ~0.1 on illiquid/carry names (esp. SHY, a near-cash ETF levered by inverse-vol sizing).

## Audit findings (independently re-verified in `c12`)
- **Code: clean.** No look-ahead — proven by truncation/prefix-recompute (exact-zero invariance, stronger
  than the shipped perturbation test); timing, cost, borrow all correct; deterministic; numbers reproduce.
- **Cost realism:** charging cost on *actual levered* daily turnover (not pre-leverage monthly) is minor:
  Sharpe 1.02 @5bps / **0.93 @10bps** (an earlier audit estimate of 0.67@10bps did **not** replicate).
- **Significance:** SE(Sharpe) ≈ 0.30 → DEPLOY 95% CI ≈ **[0.49, 1.65]**; block-bootstrap of
  Sharpe(DEPLOY) − Sharpe(60/40) = **[−0.04, +0.56], P(>0)=0.96** → the improvement over 60/40 is **borderline,
  not significant at 95%.** Sub-period spread (0.79–1.38) is within ~1 SE → consistent with noise, **not**
  independent robustness.
- **Universe dependence:** drop SHY → 0.98; drop illiquid (UNG/USO/DBA/FX/SHY/TIP) → 0.90; liquid-core-11 →
  0.91. ~0.10–0.15 of the headline rides on illiquid/carry names.
- **"Futures vehicle" claim WITHDRAWN:** the "~1.07 futures" was just the borrow-off ETF run **with
  dividends/coupons**; price-return futures (ES/ZN/ZT) *lose* that carry and add roll/tracking — so the ETF
  number is, if anything, **optimistic**, not "conservative." A real futures backtest is **not done**.
- **Multiple-testing:** the spec was improved *after seeing results* (universe 8→21 was the single biggest
  lever, +~0.15 Sharpe; lookback blend; xsec tested-then-dropped; hedge + full-sample-scaling added-then-
  removed). No deflated-Sharpe/Bonferroni haircut was applied; doing so pushes the effective number toward
  the lower ~0.9 end. Mitigant: a parameter grid (lookbacks, vol-window, weight, cap) stays 0.91–1.14, and
  the chosen config is **not** the grid max → not single-knob overfit.
- **Drawdown:** −12.4% realized is one path; bootstrapped tail ≈ −16% (5th pct). (The earlier −10.2% was the
  look-ahead bug.)
- **Options hedge:** EXCLUDED (optimistic premium, unverifiable without option data; it's DD-insurance at a
  Sharpe cost, not a Sharpe add).

## Honest verdict
A **legitimate, leak-free, low-overfit diversification overlay** worth **Sharpe ≈ 0.9–1.0**, whose real and
significant value is **cutting a 60/40's volatility ~⅓ and drawdown ~½ at roughly equal return, with crisis
convexity.** It is **not** a statistically-significant 60/40-beating alpha, and the standalone trend factor
(Sharpe ~0.76) is the documented managed-futures premium. Deployable as a risk-reduction/diversification
sleeve; to claim more would require (a) a real futures backtest with carry/roll and (b) more data than 18
years can give for Sharpe-distinguishing significance.
