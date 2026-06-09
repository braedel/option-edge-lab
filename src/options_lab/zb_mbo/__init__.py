"""ZB MBO selective-taker engine (options-edge-lab study, branch zb-mbo-taker).

Causal L3 replay -> trigger detectors -> latency-adjusted labels -> Stage-1 screen ->
hftbacktest Stage-2. See docs/research/specs/2026-06-08-zb-mbo-taker-design.md and the
v2 plan. Action-code/side conventions in `codes` were attested on real data
(reports/zb_taker/attestation.json) before any dependent code was written.
"""
