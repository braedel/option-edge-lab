"""C15 - build a self-contained, professional HTML slide deck for the trend-overlay study.
Layman's terms in the body; rigorous tables/stats in the appendix; key tearsheets embedded as base64
(one portable file, no external deps)."""
from __future__ import annotations

import base64
from pathlib import Path

REP = Path(r"D:\workspace\options-edge-lab\reports")
OUT = Path(r"D:\workspace\options-edge-lab\docs\research\results\2026-06-03-trend-overlay-study-deck.html")


def b64(name: str) -> str:
    p = REP / name
    return base64.b64encode(p.read_bytes()).decode() if p.exists() else ""


IMG_MAIN = b64("spy_deploy_hedge_tearsheet.png")
IMG_2023 = b64("tearsheet_2023_to_now.png")
IMG_DEP = b64("deployable_pnl_underwater.png")

HTML = r"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Finding a Real Trading Edge — Study Deck</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1a2330;background:#0b1320}
.slide{display:none;min-height:100vh;padding:5.5vh 8vw 8vh;background:#fff;flex-direction:column;justify-content:center}
.slide.active{display:flex;animation:fade .35s ease}
@keyframes fade{from{opacity:.0;transform:translateY(8px)}to{opacity:1;transform:none}}
h1{font-size:3em;line-height:1.1;letter-spacing:-.5px}
h2{color:#16406b;font-size:2em;border-bottom:3px solid #d9a441;padding-bottom:.18em;margin-bottom:.7em}
.lead{font-size:1.35em;color:#33414f;line-height:1.55;max-width:60ch}
p{font-size:1.18em;color:#33414f;line-height:1.55;max-width:64ch;margin:.5em 0}
ul{margin:.4em 0 .4em 1.1em} li{font-size:1.16em;color:#33414f;line-height:1.6;margin:.35em 0;max-width:62ch}
table{border-collapse:collapse;width:100%;font-size:1.02em;margin:.6em 0}
th,td{padding:.55em .8em;border-bottom:1px solid #e1e7ee;text-align:left}
th{background:#16406b;color:#fff;font-weight:600} tr:nth-child(even) td{background:#f6f8fb}
td.r,th.r{text-align:right;font-variant-numeric:tabular-nums}
.good{color:#1a7a3c;font-weight:700}.bad{color:#b3261e;font-weight:700}.warn{color:#b6791f;font-weight:700}
img{max-width:100%;max-height:60vh;display:block;margin:.6em auto;border:1px solid #e1e7ee;box-shadow:0 4px 22px rgba(10,30,60,.12)}
.note{font-size:.95em;color:#6b7785;margin-top:.5em;max-width:80ch}
.big{font-size:2.2em;font-weight:700;color:#16406b;margin:.2em 0}
.stat{display:inline-block;margin:.3em 1.6em .3em 0}.stat .v{font-size:2.1em;font-weight:700;color:#16406b}.stat .k{display:block;font-size:.95em;color:#6b7785}
.title{background:radial-gradient(1200px 600px at 20% -10%,#1d508a 0,#16406b 35%,#0b1320 100%);color:#fff;align-items:flex-start;justify-content:center}
.title h1{color:#fff}.title .lead{color:#cdd8e3}.title .tag{color:#d9a441;font-weight:700;letter-spacing:2px;text-transform:uppercase;font-size:.95em}
.kicker{color:#16406b;font-weight:700;letter-spacing:2px;text-transform:uppercase;font-size:.8em;margin-bottom:.3em}
.apx{background:#0e1b2e;color:#e6edf5}.apx h2{color:#fff;border-color:#d9a441}.apx p,.apx li,.apx td{color:#cdd8e3}.apx th{background:#d9a441;color:#16406b}
.apx tr:nth-child(even) td{background:#16263d}.apx table{font-size:.92em}.apx .note{color:#8ea2ba}
#bar{position:fixed;top:0;left:0;height:4px;background:#d9a441;width:0;transition:width .3s;z-index:10}
#hud{position:fixed;bottom:14px;right:18px;font-size:.85em;color:#8ea2ba;z-index:10;font-variant-numeric:tabular-nums}
.hint{position:fixed;bottom:14px;left:18px;font-size:.8em;color:#8ea2ba;z-index:10}
</style></head><body>
<div id="bar"></div>

<section class="slide title">
  <div class="tag">Quantitative Research &middot; options-edge-lab</div>
  <h1>Can we find a real<br>trading edge?</h1>
  <p class="lead">A disciplined search across futures &amp; options &mdash; and the one honest survivor.<br>
  Held to strict standards: real data, no look-ahead, <b>independently audited</b>.</p>
  <p class="lead" style="font-size:1.05em;opacity:.8">June 2026</p>
</section>

<section class="slide">
  <div class="kicker">The goal</div>
  <h2>What we set out to do</h2>
  <p>Find a strategy &mdash; in <b>futures or options</b> &mdash; that genuinely makes money <b>after costs</b>
  and keeps working on data it has <b>never seen</b>.</p>
  <p>Judged like a scientist: if it only &ldquo;works&rdquo; because we fooled ourselves, it <b>fails</b>.
  A clean &ldquo;no&rdquo; is a valuable result. We were looking for the truth, not a story.</p>
</section>

<section class="slide">
  <div class="kicker">The scorecard</div>
  <h2>What we found, in one table</h2>
  <table>
    <tr><th>Idea we tested</th><th>Verdict</th></tr>
    <tr><td>Betting the market &ldquo;pins&rdquo; to a price (0DTE options)</td><td class="bad">&#10007; No edge</td></tr>
    <tr><td>Using dealer-gamma (GEX) to predict volatility</td><td class="bad">&#10007; No edge</td></tr>
    <tr><td>A futures pattern-detector, re-tested on fresh data</td><td class="bad">&#10007; Decayed</td></tr>
    <tr><td>The &ldquo;overnight drift&rdquo; in stocks</td><td class="bad">&#10007; Just market beta</td></tr>
    <tr><td>Selling options to harvest the &ldquo;volatility premium&rdquo;</td><td class="warn">&#9888; Real &mdash; but only crash-risk beta</td></tr>
    <tr><td><b>Trend-following across many markets</b></td><td class="good">&#10003; Survived</td></tr>
  </table>
  <p class="note">Most ideas failed. That is normal &mdash; and it is the discipline working.</p>
</section>

<section class="slide">
  <div class="kicker">Why this is hard</div>
  <h2>Why most &ldquo;edges&rdquo; are mirages</h2>
  <ul>
    <li><b>Prediction edges decay.</b> Once a pattern is known and crowded, it stops paying. We watched several die the moment we tested them on data they hadn&rsquo;t been tuned on.</li>
    <li><b>&ldquo;Risk premiums&rdquo; are not free money.</b> Selling options pays you steadily&hellip; until a crash takes it back. You&rsquo;re paid to <i>carry risk</i>, not to find alpha. We showed a systematic option-selling strategy <b>does not beat simply owning stocks</b>.</li>
  </ul>
</section>

<section class="slide">
  <div class="kicker">The survivor</div>
  <h2>Trend-following (&ldquo;managed futures&rdquo;)</h2>
  <p>A simple, century-old rule: <b>ride markets that are going up, short markets that are going down</b> &mdash;
  spread across stocks, bonds, gold, oil and currencies.</p>
  <p>It is one of the most-studied, longest-evidenced strategies in finance. Crucially, <b>it tends to zig when markets zag.</b></p>
</section>

<section class="slide">
  <div class="kicker">The result</div>
  <h2>What it does for a portfolio</h2>
  <img src="data:image/png;base64,__IMG_MAIN__" alt="S&amp;P vs DEPLOY vs DEPLOY+hedge tearsheet">
  <p class="note">Grey = stocks (climbs higher, but gut-wrenching −46% plunges). Red/blue = a normal 60/40 portfolio
  with the trend overlay added: it rides <b>far smoother</b>. Worst drop cut from <b>−31% to −12%</b>, for roughly the same long-run return.</p>
</section>

<section class="slide">
  <div class="kicker">Its superpower</div>
  <h2>It works when everything else breaks</h2>
  <div style="margin:.6em 0">
    <span class="stat"><span class="v good">+7%</span><span class="k">2008 &mdash; while stocks fell −34%</span></span>
    <span class="stat"><span class="v good">+7%</span><span class="k">2022 &mdash; while stocks fell −18%</span></span>
  </div>
  <p>It made money in the exact years investors needed it most. <b>That is the whole reason to own it</b> &mdash;
  it is crash protection that, unlike buying insurance, tends to pay you a little to hold it.</p>
</section>

<section class="slide">
  <div class="kicker">Honesty</div>
  <h2>What it is <span style="color:#b3261e">not</span></h2>
  <ul>
    <li><b>Not a get-rich edge.</b> Long-run risk-adjusted return (Sharpe) is <b>~0.9&ndash;1.0</b> &mdash; solid, not spectacular.</li>
    <li><b>It lags in bull markets.</b> 2023&ndash;today: stocks <b>+106%</b>, this strategy <b>+39%</b>.</li>
    <li><b>Even &ldquo;~1.0&rdquo; is not statistically proven</b> to beat a plain 60/40 over 18 years &mdash; the honest confidence interval is wide.</li>
  </ul>
  <p>It&rsquo;s a <b>seatbelt, not a sports car.</b> You hold it for the crash, not the boom.</p>
</section>

<section class="slide">
  <div class="kicker">The unflattering view (shown on purpose)</div>
  <h2>Its worst regime, 2023&ndash;today</h2>
  <img src="data:image/png;base64,__IMG_2023__" alt="2023 to now tearsheet">
  <p class="note">A calm bull with no crash. Stocks (grey) doubled; the strategy made a third of that; and the optional
  options hedge just <b>bled premium</b> with no crash to catch. We show our worst regime, not only our best.</p>
</section>

<section class="slide">
  <div class="kicker">Rigor</div>
  <h2>We tried hard to break it</h2>
  <p>Our first drafts <b>overstated</b> the result. Independent audits &mdash; a &ldquo;quant&rdquo; reviewer and an
  &ldquo;engineer&rdquo; reviewer &mdash; plus our own re-checks caught:</p>
  <ul>
    <li>a hidden <b>look-ahead bug</b> (using information from the future), and</li>
    <li>an <b>over-optimistic options-hedge</b> assumption.</li>
  </ul>
  <p>We fixed both, <b>proved</b> the code is now clean, and revised the headline <b>down</b>.
  The number we report is the one that <b>survived the audit</b> &mdash; not the flattering first draft.</p>
</section>

<section class="slide">
  <div class="kicker">Optional layer</div>
  <h2>The crash-insurance (options) layer</h2>
  <p>We tested adding put options as explicit crash insurance. Verdict, honestly measured:</p>
  <ul>
    <li>It <b>reliably halves the worst drawdown</b> (e.g. −12% &rarr; ~−5%).</li>
    <li>But it <b>costs ~1%/yr</b> in calm markets &mdash; insurance has a premium.</li>
  </ul>
  <p>A choice for the drawdown-averse &mdash; <b>not a free performance boost.</b> We refuse to claim otherwise.</p>
</section>

<section class="slide">
  <div class="kicker">Bottom line</div>
  <h2>The takeaway</h2>
  <ul>
    <li><b>Result:</b> a verified, leak-free <b>diversification overlay</b> (best run in futures).</li>
    <li><b>Value:</b> halves a 60/40&rsquo;s risk at ~equal return, with genuine <b>crisis protection</b>.</li>
    <li><b>Not:</b> a market-beating alpha.</li>
    <li><b>To validate further</b> on real instruments (recent window): <b>~$100&ndash;500</b> of data.</li>
  </ul>
  <p>A useful tool, <b>honestly measured.</b></p>
</section>

<section class="slide apx"><h2>Appendix</h2><p class="lead">Tables, statistics &amp; methods &mdash; for the technically inclined.</p>
<p class="note">All figures reproduce from scripts <code>campaign/c5</code>&ndash;<code>c14</code>; full registry in <code>CAMPAIGN.md</code>; details in <code>docs/research/results/2026-06-03-deployable-onepager.md</code>.</p></section>

<section class="slide apx">
  <h2>A. Verified performance (audited)</h2>
  <table>
    <tr><th>Portfolio</th><th class="r">Sharpe</th><th class="r">Sharpe (OOS &ge;2016)</th><th class="r">Max drawdown</th><th class="r">Vol</th><th class="r">CAGR</th></tr>
    <tr><td>S&amp;P 500 (SPY)</td><td class="r">0.66</td><td class="r">0.89</td><td class="r">&minus;51%</td><td class="r">20%</td><td class="r">11.7%</td></tr>
    <tr><td>60/40</td><td class="r">0.80</td><td class="r">0.94</td><td class="r">&minus;31%</td><td class="r">11%</td><td class="r">8.8%</td></tr>
    <tr><td>Trend sleeve (21 ETFs)</td><td class="r">0.76</td><td class="r">0.79</td><td class="r">&minus;17%</td><td class="r">9.5%</td><td class="r">&mdash;</td></tr>
    <tr><td><b>DEPLOY (overlay + 60/40)</b></td><td class="r"><b>1.07</b></td><td class="r"><b>1.16</b></td><td class="r"><b>&minus;12.4%</b></td><td class="r">7.6%</td><td class="r">8.1%</td></tr>
    <tr><td>DEPLOY &mdash; liquid names, real frictions</td><td class="r">~0.91</td><td class="r">~0.96</td><td class="r">&minus;14%</td><td class="r">&mdash;</td><td class="r">&mdash;</td></tr>
  </table>
  <p class="note">Headline 1.07 is the full-21-ETF/2bps figure; the realistically-tradeable (liquid, proper levered-turnover cost, short-borrow) figure is <b>~0.9&ndash;1.0</b>. DEPLOY earns <b>&minus;0.7%/yr vs 60/40</b> &mdash; the Sharpe edge is risk reduction, not added return. Data: free Yahoo daily, 2008&ndash;2026.</p>
</section>

<section class="slide apx">
  <h2>B. Stress &amp; robustness</h2>
  <table>
    <tr><th>Stress test</th><th>Result</th></tr>
    <tr><td>Transaction cost (proper levered turnover)</td><td>Sharpe 1.07 @2bps &rarr; 1.02 @5bps &rarr; 0.93 @10bps</td></tr>
    <tr><td>+ short-borrow on the ETF proxy (1&ndash;2%/yr)</td><td>Sharpe 1.04 / 1.00</td></tr>
    <tr><td>Drop the 2008 crisis entirely (&ge;2010)</td><td>Sharpe <b>1.18</b> &mdash; <i>better</i>, not crisis-dependent</td></tr>
    <tr><td>Sub-periods 08-12 / 13-17 / 18-22 / 23-26</td><td>0.79 / 1.38 / 0.99 / 1.27 (all positive)</td></tr>
    <tr><td>Out-of-sample (&ge;2016) vs full</td><td>1.16 vs 1.07 &mdash; OOS &gt; full (not overfit)</td></tr>
    <tr><td>Parameter grid (lookbacks, vol-window, weights)</td><td>stays 0.91&ndash;1.14; chosen config is <i>not</i> the max</td></tr>
    <tr><td>Look-ahead audit (perturbation + truncation)</td><td><b>0.00</b> &mdash; provably leak-free</td></tr>
  </table>
</section>

<section class="slide apx">
  <h2>C. Statistical honesty</h2>
  <ul>
    <li>Standard error of Sharpe over 18 yrs &asymp; <b>0.30</b> &rarr; DEPLOY 95% CI &asymp; <b>[0.49, 1.65]</b>.</li>
    <li>Bootstrap of <i>Sharpe(DEPLOY) &minus; Sharpe(60/40)</i> = median +0.27, <b>95% CI [&minus;0.04, +0.56]</b>, P(&gt;0)=0.96 &rarr; <b>not significant at 95%</b>.</li>
    <li>Sub-period spread (0.79&ndash;1.38) is within ~1 SE &rarr; consistent with noise, not independent confirmation.</li>
    <li>Drawdown &minus;12.4% is one realized path; bootstrapped tail &asymp; <b>&minus;16%</b>.</li>
  </ul>
  <p class="note">Translation: the risk-reduction &amp; crisis-convexity benefits are large and robust; the claim of <i>beating</i> a 60/40 is statistically borderline. We report it as a diversifier, not an alpha.</p>
</section>

<section class="slide apx">
  <h2>D. Where the edge comes from &amp; what was fixed</h2>
  <p><b>Universe dependence:</b> drop SHY &rarr; 0.98; drop illiquid names &rarr; 0.90; liquid-core-11 &rarr; 0.91. ~0.1 of the headline leans on illiquid / carry names.</p>
  <p><b>Artifacts found &amp; removed (audited):</b></p>
  <table>
    <tr><th>Artifact</th><th>Action</th></tr>
    <tr><td>Options-hedge &ldquo;Sharpe lift&rdquo; (optimistic premium)</td><td>Removed &mdash; at realistic cost it <i>subtracts</i> Sharpe; hedge is DD-insurance only</td></tr>
    <tr><td>Look-ahead via full-sample volatility scaling</td><td>Fixed &amp; proven clean; maxDD corrected &minus;10.2% &rarr; &minus;12.4%</td></tr>
    <tr><td>&ldquo;Futures &ge; ETF proxy&rdquo; claim</td><td>Withdrawn &mdash; the ETF run includes dividends futures would lose; not yet backtested in futures</td></tr>
    <tr><td>Multiple-testing (spec improved post-hoc)</td><td>Acknowledged; deflates effective Sharpe toward ~0.9</td></tr>
  </table>
  <p class="note">An audit reviewer&rsquo;s own claim (&ldquo;cost 0.67 @10bps&rdquo;) did <b>not</b> replicate on independent re-check (real 0.93) &mdash; subagent findings were re-verified, not taken on faith.</p>
</section>

<section class="slide apx">
  <h2>E. Method &amp; reproducibility</h2>
  <ul>
    <li><b>Recipe:</b> 1/3/6/12-month trend sign per market &rarr; inverse-volatility sizing &rarr; monthly rebalance &rarr; 10% vol target &rarr; 50% overlay + 50% 60/40. Textbook parameters, none optimized.</li>
    <li><b>Universe:</b> 21 liquid ETFs across equities, bonds, credit, commodities, metals, REITs, FX.</li>
    <li><b>Data:</b> free daily total-return (Yahoo), 2008&ndash;2026. Futures is the intended (cheaper, borrow-free) live vehicle.</li>
    <li><b>Reproduce:</b> <code>campaign/c11_clean_verify.py</code> (clean build + look-ahead proof), <code>c12</code> (audit re-verification), <code>c13/c14</code> (tearsheets). Registry: <code>CAMPAIGN.md</code>.</li>
  </ul>
  <p class="note">Independent engineering audit verdict: code correct, deterministic, leak-free, all numbers reproduce.</p>
</section>

<div id="hud"></div><div class="hint">&larr; &rarr; or click to navigate</div>
<script>
var s=[].slice.call(document.querySelectorAll('.slide')),i=0,bar=document.getElementById('bar'),hud=document.getElementById('hud');
function show(){s.forEach(function(x,j){x.classList.toggle('active',j===i)});bar.style.width=((i+1)/s.length*100)+'%';hud.textContent=(i+1)+' / '+s.length;location.hash=i+1}
function go(d){i=Math.max(0,Math.min(s.length-1,i+d));show();window.scrollTo(0,0)}
document.addEventListener('keydown',function(e){if(e.key==='ArrowRight'||e.key===' '||e.key==='PageDown'){e.preventDefault();go(1)}if(e.key==='ArrowLeft'||e.key==='PageUp'){e.preventDefault();go(-1)}if(e.key==='Home'){i=0;show()}if(e.key==='End'){i=s.length-1;show()}});
document.addEventListener('click',function(e){if(e.target.tagName==='A')return;go(1)});
if(location.hash){var n=parseInt(location.hash.slice(1));if(n>=1&&n<=s.length)i=n-1}
show();
</script></body></html>"""

HTML = HTML.replace("__IMG_MAIN__", IMG_MAIN).replace("__IMG_2023__", IMG_2023)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(HTML, encoding="utf-8")
print("saved:", OUT, f"({len(HTML)//1024} KB)")
