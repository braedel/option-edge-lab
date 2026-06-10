# FOMC hawkish/dovish — independent BLIND re-classification (leakage audit + forward rubric)

**Date:** 2026-06-09 · **Purpose:** test whether the #1 trade's FOMC ±1 labels were hindsight-fitted (the top
leakage risk flagged by the critical review), and produce the **written rubric** for pre-committing future
labels. An independent classifier labeled all 22 meetings from **point-in-time info only** (statement, SEP/dots,
decision, presser, what was priced going in via fed-funds/SOFR futures + dealer surveys) — **blind to the
existing labels and to how ZB/Treasuries actually moved.**

## Result: 21/22 match → labels are point-in-time-reproducible, NOT hindsight-fitted
- **21 of 22** blind labels equal the hardcoded labels (`c51` `SURP_FOMC`).
- **Lone mismatch: 2024-06-12** — hardcoded +1 (hawkish), blind 0 (neutral). The classifier's single
  flagged-hardest call (dots cut 3→1 hawkish-lean vs. a soft-CPI morning; also a CPI+FOMC double date). It is a
  **+$90 winner**; removing it moves the headline only **Sharpe 1.25→1.23, t 2.07→2.03** (n 35→34).
- Conclusion: the FOMC leg is **not** a hindsight artifact; the edge is robust to the one ambiguous flip.

## The rubric (forward rule — pre-commit each label IN WRITING at ~14:05 ET before observing the reaction)
Classify the meeting **vs. what the market priced going in**:
- **HAWKISH (+1):** more restrictive than priced (higher dots/fewer cuts, hawkish hold, restrictive language,
  decision/guidance tighter than priced, hawkish presser).
- **DOVISH (−1):** more accommodative than priced.
- **NEUTRAL (0) → no trade:** as priced / mixed / unclear (default here when in doubt).

## The 22 classifications (blind; rationale = priced vs delivered)
| Date | Blind | Hard | Conf | Point-in-time rationale |
|------|:---:|:---:|---|---|
| 2023-02-01 | −1 | −1 | med | 25bp priced; Powell "disinflation has started," didn't push back on easing FCI |
| 2023-03-22 | −1 | −1 | med | SVB; hiked 25bp but "some additional firming," dots ~1 more, backstops flagged |
| 2023-05-03 | −1 | −1 | med | 25bp priced; DROPPED "additional firming may be appropriate" → pause tee-up |
| 2023-06-14 | +1 | +1 | high | Skip priced, but dots penciled **two** more 2023 hikes (hawkish skip) |
| 2023-07-26 | 0 | 0 | med | 25bp fully priced; data-dependent; no guidance surprise |
| 2023-09-20 | +1 | +1 | high | Hold priced; 2024 dots cut 4→**2** (higher-for-longer harder than priced) |
| 2023-11-01 | −1 | −1 | med | Hold priced; Powell declined to defend the Sept "one more hike" dot |
| 2023-12-13 | −1 | −1 | high | Dovish pivot: "any" additional firming; dots ADDED a 3rd 2024 cut |
| 2024-01-31 | +1 | +1 | high | March cut materially priced; Powell explicitly shot it down |
| 2024-03-20 | −1 | −1 | high | After hot CPIs, feared hawkish dots; SEP **kept 3 cuts** (dovish-relative) |
| 2024-05-01 | −1 | −1 | med | Surveys leaned hawkish-pivot; Powell said hike "unlikely" + QT taper |
| **2024-06-12** | **0** | **+1** | **low** | **dots 3→1 (hawkish-lean) vs soft-CPI morning; muted presser → mixed. AMBIGUOUS** |
| 2024-07-31 | −1 | −1 | med | Hold priced; Powell opened Sept cut door explicitly |
| 2024-09-18 | 0 | 0 | low | 50bp ~priced (~59%); Powell "not the new pace / not in a rush" offset |
| 2024-11-07 | 0 | 0 | high | 25bp fully priced; bland; markets little-changed |
| 2024-12-18 | +1 | +1 | high | 25bp cut but 2025 dots 4→**2**, inflation up, "cautious" (hawkish cut) |
| 2025-01-29 | +1 | +1 | med | Hold priced; removed "inflation made progress," "no hurry" |
| 2025-03-19 | −1 | −1 | med | Feared hawkish dots cut; median **kept 2 cuts** + slowed QT |
| 2025-05-07 | 0 | 0 | high | ~97% hold priced; "wait and see"; in line |
| 2025-06-18 | 0 | 0 | low | "Dovish hold" headline vs internal hawkish shift; mixed |
| 2025-07-30 | +1 | +1 | high | Hold priced; Powell "much more hawkish," "no decision on Sept" |
| 2025-09-17 | 0 | 0 | low | 25bp fully priced; dovish near-term dots vs hawkish 2026 dot; mixed |

**Genuinely ambiguous (most hindsight-exposed):** 2024-06-12, 2024-09-18, 2025-09-17, 2025-06-18, 2023-02-01.
Of these, only 2024-06-12 differs from the hardcoded set, and it is immaterial to the headline. Method:
labeled from pre-2:30pm-ET information only; no post-meeting bond/ZB price action consulted.
