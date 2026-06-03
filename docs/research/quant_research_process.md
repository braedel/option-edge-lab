# Quant Research Process — options-edge-lab

**Status:** standing methodology (ported & generalized from the PinFly lab's process).
**Companion:** the hard rules live in `CLAUDE.md`; this doc is the "how".

Develop every candidate with a proper quant process: seal out-of-sample data, and let the data reveal
which factors and which *ranges* carry alpha (with honest p-values), rather than hard-coding a verbal
checklist and backtesting it until it "confirms."

## Why this matters
Three failure modes burn options research: **synthetic / mismarked data**, **optimistic fills**, and
**confirmation bias / overfitting** (backtesting your own rules tends to confirm them; hand-tuning
thresholds fits the past). The fixes: (a) seal an OOS set you never look at during discovery, (b) test
each factor's *marginal, pre-specified* relationship to outcomes statistically, and (c) price execution
honestly. Pre-registered hypotheses (from real trading experience or a stated mechanism) beat blind
data-mining and reduce the multiple-testing burden — but you still correct for the trials you run.

## 1. Data splits (decide and SEAL before looking)
Chronological, no shuffling (time-series; the future must never inform the past):
- **TRAIN / discovery** — earliest slice. All factor exploration, IC, bucket analysis, threshold/weight
  fitting happen here.
- **VALIDATION** — middle slice. Check that TRAIN findings hold; pick the final combined rule. Limited
  looks.
- **OOS / TEST (sealed)** — most-recent slice. **Touched exactly once**, at the very end, for the
  headline number. Peek once and it is no longer out-of-sample.

Split by *date*. Purge/embargo any feature whose label horizon overlaps the next fold (multi-day option
holds need a real purge; same-day-settled structures need little).

## 1a. Stratified exploration sample (cheap first pass)
Before a full data pull, pull a **stratified sample** (e.g. ~1 trading day/week spread across the whole
TRAIN+VALIDATION span). Validate the pipeline at scale, read factor distributions, get a rough first IC
— cheaply, spanning regimes rather than one block. Rules: stay strictly inside TRAIN+VALIDATION; never
sample the sealed OOS; rare setups are undercounted by a sample, so real single-factor stats use the
FULL training set.

## 2. Target & single-factor analysis
Prefer a **clean label** as the primary discovery target, not raw PnL — it separates two questions raw
PnL conflates:
- **Stage 1 — signal:** do the factors predict the label (the favorable event the structure monetizes:
  a pin, a direction, a vol expansion/contraction, a tail)? Measure AUC, precision/recall, and **lift
  over base rate**. Low-variance labels show signal with less data.
- **Stage 2 — economics:** on predicted-favorable days only, does the actual structure make money at
  real fills + fees? If Stage 1 fails, no execution tweak helps; if it works, Stage 2 is structure
  optimization. The base rate = opportunity frequency; perfect selection = the alpha ceiling.

Evaluate each factor alone, on TRAIN only, against the label and net PnL:
1. **Quantile / bucket analysis** — 5 buckets by factor value; report mean PnL, win-rate, median label
   error, and N per bucket, each with a t-stat / CI. Shows *which factor ranges* associate with good
   outcomes, no threshold assumed.
2. **Information Coefficient (IC)** — Spearman rank corr between factor and outcome, its t-stat, and
   IR = mean(IC)/std(IC) across sub-periods (|IR| >~ 0.05 is worth attention).
3. **Monotonicity check** — prefer factors whose bucket returns trend monotonically (robust) over ones
   that spike in a single bucket (likely noise).

## 3. Multiple-testing correction (mandatory)
Many factor x range x structure x horizon tests -> a raw p < 0.05 means nothing. Apply and report:
- **Harvey-Liu haircut** on any Sharpe / t-stat (principled function of in-sample SR and trial count).
- **Benjamini-Hochberg FDR** across the factor battery, and/or a hard bar of **|t| > 3** for any single
  claimed effect.
- **Deflated Sharpe Ratio / PBO** (Bailey-Lopez de Prado) on the final rule, given the configurations
  tried. Log the trial count honestly — it is an input to the math.

## 4. Combine factors only after single-factor evidence
Build the composite from factors that survived sections 2-3, weights/thresholds fit on TRAIN, confirmed
on VALIDATION, then **locked**. Keep it simple and explainable (monotone scores, few parameters) —
complexity is overfit surface.

## 5. Honest reporting (every result)
- **Frequency**: how often the setup fires (rare-setup strategies live or die on this).
- Expectancy/trade ± standard error, **t-stat**, win rate, worst day/week, max drawdown.
- **Deflated** Sharpe + PBO for the final rule.
- **Sensitivity** to fill_fraction (0.0 / real / 1.0) and to fees — reject anything that only works at
  optimistic fills.
- The **OOS number is THE number.** In-sample/validation results are discovery, labeled as such.

## 6. Guardrails (hard rules — see CLAUDE.md)
- Never tune on OOS. One look, at the end.
- Real fills, real fees/commissions per leg, official settlement/marks.
- Log every trial/config tried (feeds the multiple-testing math).
- Prefer fewer, monotone, pre-registered factors over flexible fits.
- If the edge isn't there after honest correction, say so — a clean "no edge" is a valid result.

## 7. Standing refinements
- **Walk-forward / CPCV, not a single split.** Purged & embargoed walk-forward (or CPCV) on the non-OOS
  data for a *distribution* of out-of-sample performance, feeding the deflated Sharpe / PBO. The
  most-recent block stays the single sealed final test.
- **Trial registry -> honest multiple-testing.** Log every configuration (factor x range x structure x
  window); Bonferroni/BH and DSR/PBO use that honest count.
- **Statistical power / minimum detectable effect.** Options samples are often small; state the MDE at
  the available n and flag underpowered results — a non-significant result on a tiny sample is
  *inconclusive*, not *negative*.
- **Fill calibration is a caveated cross-check, not a default.** The owner's stated real fill is
  primary; any forensic estimate is a weak cross-check. Always report the full fill-sensitivity sweep.
- **Provenance on every result.** Stamp the dataset version (hash + row counts) and git commit; pin to a
  snapshot when live data may change.

## Sources
- Harvey & Liu, *Backtesting* / *...and the Cross-Section of Expected Returns* (multiple testing, haircut
  Sharpe, |t|>3 bar).
- Bailey & Lopez de Prado, *The Deflated Sharpe Ratio* and *Probability of Backtest Overfitting*.
- Lopez de Prado, *Advances in Financial ML* (purged / combinatorial CV).
- Alphalens / Information Coefficient & quantile factor analysis (single-factor evaluation).
