# Volume / delta / order-flow round (2026-10-21): ORB + delta confirmation and delta patterns

Question (Federico): "Fabio Valentini-style opening-range breakout confirmed with volume delta", plus new strategies built on
volume, delta and order flow. The FundedSync `FabioOrb` DLL was NOT inspected (licensed); its 2026 result was PF 1.14.

Data: real NQ 1-minute bars (Databento `nqdb.npz`, 2010-06..2026-10, with volume). True aggressor delta (Databento NQ trades,
per-minute buy / sell volume): `of_minutes_2025.pkl` 2025-05-01..2026-03-31 + `of_minutes.pkl` 2026-04-01..2026-10-08
(`of_minutes_rich.pkl` adds prints >= 50 contracts from 2026-04-01). $ per MNQ, $1.90 RT + 1 tick slippage.

## Pre-registration (written before any result was looked at)

Layer A, true delta, window 2025-05-01..2026-10-08 (373 RTH days): **CHOOSE = 2025-05..2025-12, CHECK = 2026-01..2026-10-08**.
Layer B, bar-delta proxy on 2010-2026: **T1 = 2019-01..2022-12 (choose), T2 = 2023-01..2026-10 (check)**, cost-normalised
(0.345% ATR) A = 2010-14 and B = 2015-18 as regime control (reported, not required).

Acceptance (a cell survives only if ALL hold):
1. standalone n >= 60 in the choose period;
2. PF >= 1.3 choose, PF >= 1.2 check;
3. check PF with +4 ticks per side (extra $3 per trade over the base 1 tick) >= 1.1;
4. the delta cell beats its own no-delta CONTROL (same cell, no delta condition) by >= +0.15 PF in BOTH periods and keeps >= 50% of
   the control's trades in both;
5. plateau: >= half of the numeric one-step neighbours (range length, stop, target, threshold, m, W, z, k) have choose PF >= 1.15;
6. portfolio: added to `nt_compare.research_set("ultra_d4")` with `wrq_port.conflict_filter`: Sharpe up in both periods, max DD and
   worst month not worse by > 5%, daily correlation < 0.3; 21-day block bootstrap of the daily gain vs the control.
Base rates P(check pass | choose pass) vs P(check pass), and the same for "beats control", are reported for every family.

Not re-tested (already rejected on 2026-10-09): session-CVD-with-trade x2 boost (failed OOS), dl5/dl15/dl30 quintile orderings (flip
between samples), top-of-book imbalance skip rules (fail OOS).

Lookahead: every delta quantity at bar t uses bars <= t with the entry at the open of t+1; resting stop orders at the range edge use
bars <= b-1 (b = the bar that touches the edge). Fills through `core.execute` (stop entries at max(open, level) + 1 tick, stops -1 tick,
targets need a 1-tick trade-through, flat 15:55).

## Proxy validation (`python3 delta_orb.py proxy` -> `proxy_validation.json`)

Overlap 2025-05..2026-10, 511,546 minutes (142,995 RTH). Correlation of the bar proxy with the true aggressor delta:

| proxy | 1-min corr (all / RTH) | sign agreement 1-min | 15-min sums corr | 09:30-11:00 session delta ratio per day: corr / sign |
|---|---|---|---|---|
| `cl` = vol x (2 (c - l) / (h - l) - 1) | 0.544 / 0.565 | 69 / 71% | 0.530 / 0.548 | 0.509 / 66% |
| `tr` = sign(c - o) x vol (tick rule) | 0.608 / 0.625 | 76 / 79% | 0.598 / 0.605 | 0.609 / 74% |

Both are above the 0.5 bar fixed beforehand, so layer B counts as evidence, but it explains only ~35% of the variance of the true
delta: a proxy result can be noise where the true delta is not, and vice versa. The tick rule is the better proxy.

## Layer A: true delta (`delta_orb.py` -> `delta_orb.json`, `delta_orb_cells.csv`, `delta_orb_trades.pkl`)

9,792 cells: A1 = 384 ORB controls (T 5/15/30/60, stop-at-edge or close-beyond entry, stop opposite edge / 0.2 / 0.35 ATR, target
1 / 1.5 / 2 R / range width, trend filter on/off, max 1 / 2 per day) x 25 conditions (control + 24 delta conditions);
A2 = ABS 72, DIV 48, VFLIP 24, CLIMAX 48 (controls inside each).

### Counts and base rates

| family | cells | controls | s1 | s2 | s3 | s4 beats ctrl | s5 plateau | median PF choose / check | control median PF choose / check |
|---|---|---|---|---|---|---|---|---|---|
| ORB (A1) | 9,600 | 384 | 88 | 10 | 10 | 4 | 4 | 0.915 / 0.891 | 0.920 / 0.865 |
| ABS | 72 | 24 | 2 | 0 | 0 | 0 | 0 | 0.975 / 1.034 | 1.103 / 1.105 |
| DIV | 48 | 12 | 0 | 0 | 0 | 0 | 0 | 0.964 / 0.980 | 0.907 / 0.978 |
| VFLIP | 24 | 12 | 0 | 0 | 0 | 0 | 0 | 0.817 / 0.938 | 0.800 / 0.950 |
| CLIMAX | 48 | 24 | 1 | 0 | 0 | 0 | 0 | 0.929 / 0.941 | 0.934 / 0.947 |

Base rates (all cells): P(check PF >= 1.2) = 5.3%; P(check PF >= 1.2 | choose PF >= 1.3, n >= 60) = 11.0% (91 choose passers -> 10).
"Beats control by 0.15 and keeps 50%": P(beats in check) = 7.4%; P(beats in check | beats in choose) = 21.6% (629 -> 136).
Median (delta - control) PF: choose -0.004, check +0.035; correlation of the choose gain with the check gain across cells: **-0.09**
(a cell's delta gain in 2025 says nothing about its gain in 2026).

### A1 by condition (384 ORB cells each; kept = share of the control's trades in choose; dPF = median delta - control PF)

| condition | kept | dPF choose | dPF check | beats both | beats choose | beats check |
|---|---|---|---|---|---|---|
| dl1 >= 0 / .03 / .06 / .10 (breakout-minute or prior-minute delta) | .87 / .82 / .71 / .47 | -.01 / -.04 / -.09 / -.08 | +.01 / +.02 / -.03 / -.04 | 0 / 0 / 0 / 8 | 4 / 14 / 41 / 41 | 0 / 12 / 20 / 38 |
| dl5 >= 0 / .03 / .06 / .10 | .91 / .74 / .41 / .15 | +.01 / -.03 / -.01 / +.17 | +.03 / +.06 / -.01 / +.02 | 0 / 3 / 9 / 0 | 2 / 22 / 42 / 0 | 18 / 64 / 25 / 0 |
| dl15 >= 0 / .03 / .06 / .10 | .88 / .48 / .17 / .03 | +.02 / +.05 / -.19 / -.72 | +.01 / +.04 / +.17 / +.28 | 0 / 24 / 0 / 0 | 18 / 54 / 0 / 0 | 19 / 44 / 0 / 0 |
| cum (session delta since 09:30) >= 0 / .01 / .02 / .04 | .75 / .54 / .27 / .08 | +.05 / +.06 / +.13 / -.01 | +.04 / +.17 / +.28 / +.46 | 8 / 26 / 12 / 0 | 74 / 36 / 14 / 0 | 15 / 93 / 24 / 0 |
| q5 >= quantile .5 / .75 / .9 of the prior 12 windows | .78 / .68 / .49 | -.02 / -.12 / -.09 | +.04 / +.04 / +.07 | 1 / 3 / 0 | 9 / 23 / 0 | 39 / 24 / 15 |
| q15 >= .5 / .75 / .9 | .82 / .68 / .50 | +.04 / +.08 / +.10 | -.03 / +.01 / +.08 | 14 / 14 / 10 | 24 / 116 / 80 | 72 / 60 / 68 |
| big15 >= 0 / .10 (prints >= 50, 2026-04+ only) | no choose period | - | -.08 / +.03 | 0 | 0 | 21 / 0 |

Reading: the delta-of-the-breakout-minute idea (dl1, dl5) does nothing; the only conditions that help on median are the session
delta since the open (cum >= .01/.02: +0.06/+0.13 choose, +0.17/+0.28 check) and the 15-min delta vs its own recent history
(q15 >= .75/.9), but they cut 30-70% of the trades and the medians sit on top of ORB cells that are mostly losing anyway (control
median PF 0.92 / 0.87 in this window; best control = ORB5 range-width target, PF 1.27 choose -> 0.81 check).

### Survivor (4 cells = 1 independent cell)

ORB15, stop order at the edge, stop at the opposite edge, 1R (= range width here), trend filter, max 1/day (md 2 identical),
condition **q15 >= 0.75** (raw delta of the 15 minutes before the break, with the break, >= the 75th percentile of |the previous
12 15-min windows|): choose n 69 WR 58.0% PF 1.339; check n 75 WR 54.7% PF 1.269, +4 ticks 1.241; control PF 0.977 / 1.006 (n 124 / 121);
plateau 0.8. Block bootstrap of the daily gain vs control: +$11.2/day, P(> 0) 0.97, CI90 [1.1, 18.1].

Neighbourhood (check PF, same condition): T5 0.90, T30 0.80, T60 0.80, stop 0.2 ATR 0.88, stop 0.35 0.99, close-entry 0.92, no trend
0.97, R 1.5 0.94, R 2 1.01 -> the check-period success is isolated to the exact (T15, opposite-edge stop, trend) cell; at that cell
every delta condition gives check PF 1.23-1.32 vs control 1.01, so the "delta with the break" effect is consistent across conditions
but lives on one ORB cell out of 384.

Portfolio (ultra_d4, 2025-05..2026-10): corr 0.08, Sharpe 3.81 -> 4.05 (choose +0.27, check +0.21), net +$5.8k, but **max DD 3,586 -> 4,311
(+20%) and worst month -661 -> -799 (+21%) -> FAILS the 5% limit. Not accepted.**

Cross-check with the proxy on 16 years (same cell in the layer-B grid, tick rule): control T1 0.94 / T2 1.08, q15 >= .75 0.85 / 1.15,
cost-normalised 2010-14 0.88, 2015-18 0.93 -> the cell has no history before 2025. Rejected.

### A2 (true delta)

ABS: 2 choose passers, both `against` at the session extreme (n 32, choose PF 4-5 -> check 0.80 / 0.97; control 1.46 -> 0.88).
CLIMAX: delta climax z4 fade 2R choose 1.30 -> check 0.77 (control 0.97 / 0.96). DIV: best choose 1.13 -> 1.02. VFLIP: best 1.06 -> 1.00
(VFLIP `thr` sits in the `thr` column of `delta_orb_cells.csv`, not in `params`). Nothing passes s2.

## Layer B: proxy on 2010-2026 (`families12.py`, `run_mine_db.py` with FAMILIES12, `b12_select.py` -> `b12_select.json`)

`MINE_TAG=b12 MINE_PROCS=2 MINE_T1=20190101 MINE_T2=20230101 MINE_KEEP_N=60 python3 run_mine_db.py PX_ORB PX_ABS PX_DIV PX_VFLIP PX_CLIMAX`
(70 s, 0 errors) -> `results_b12.csv` (2,208 configs), `trades_b12.pkl` (18.6 MB, configs with T1 n >= 60 and PF >= 1.25).
Grid: PX_ORB 1,824 (T 15/30/60 x stop/close x stop opp/0.35 x 1/2R x trend x proxy cl/tr x 19 conditions incl. control), PX_ABS 144,
PX_DIV 96, PX_VFLIP 48, PX_CLIMAX 96.

| family | configs | median PF T1 / T2 / A / B | s1 | s2 | s3 | s4 beats ctrl | s5 | P(T2 >= 1.2) | P(T2 >= 1.2 \| T1 pass) | P(beat T2) | P(beat T2 \| beat T1) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PX_ORB | 1,824 | 1.073 / 1.115 / 0.959 / 0.929 | 57 | 25 | 25 | 4 | 4 | 18.4% | 43.9% | 6.1% | 50% (10 of 20) |
| PX_ABS | 144 | 0.891 / 0.915 / 0.930 / 0.917 | 2 | 0 | 0 | 0 | 0 | 3.5% | 0% | 7.3% | 0% |
| PX_DIV | 96 | 0.921 / 0.942 / 0.948 / 0.948 | 0 | 0 | 0 | 0 | 0 | 0% | - | 0% | - |
| PX_VFLIP | 48 | 0.906 / 0.899 / 0.891 / 0.886 | 0 | 0 | 0 | 0 | 0 | 0% | - | 8.3% | - |
| PX_CLIMAX | 96 | 0.931 / 0.941 / 0.933 / 0.946 | 0 | 0 | 0 | 0 | 0 | 0% | - | 4.2% | - |

ORB by condition (96 cells each): the delta gain is small everywhere (median dPF T1 -0.03..+0.04, T2 -0.00..+0.11); the only conditions
with any "beats both" are cum >= .01/.02/.04 (3/2/2), q5 >= .5/.75 (2/1). By proxy: tick rule beats both 10 cells, close-location 0.
The 57 T1 passers are all ORB60-with-trend cells (the house ORB60 signal), which is why P(T2 | T1) is 44%: the breakout itself is
the known edge, not the delta.

### Survivors (4 cells, all ORB60 stop-at-edge with trend, tick-rule proxy)

| cell | condition | T1 n / WR / PF | T2 n / WR / PF / +4t | A / B norm PF | control T1 / T2 | plateau | boot gain vs ctrl $/day T1 / T2 (P>0) |
|---|---|---|---|---|---|---|---|
| stop opp, 2R | q5 >= .5 | 266 / 55.3 / 1.327 | 249 / 53.8 / 1.477 / 1.432 | 0.74 / 1.15 | 1.139 / 1.198 | 1.0 | +0.9 (.61) / +2.8 (.61) |
| stop .35, 1R | cum >= .01 | 402 / 59.0 / 1.415 | 385 / 57.7 / 1.265 / 1.218 | 0.95 / 1.06 | 1.244 / 1.105 | 0.75 | +2.8 (.87) / +6.6 (.93) |
| stop .35, 2R | cum >= .01 | 402 / 54.7 / 1.441 | 385 / 53.8 / 1.378 / 1.331 | 0.95 / 1.04 | 1.277 / 1.143 | 1.0 | +2.2 (.84) / +10.4 (.99) |
| stop .35, 2R | q5 >= .5 | 273 / 53.5 / 1.434 | 254 / 52.4 / 1.447 / 1.399 | 0.85 / 1.03 | 1.277 / 1.143 | 1.0 | -4.3 (.23) / +5.7 (.80) |

Portfolio (ultra_d4 2020-10..2026-10, choose < 2023 / check >= 2023): **all four FAIL**: correlation with Ultra 0.34-0.48 (Ultra already
trades ORB60 / ORB90 / ORFAIL / VOLB on the same mornings), Sharpe down in both periods (choose 4.14 -> 3.91..4.05, check 3.58 ->
3.46..3.50), worst month -2,182 -> -2,394..-2,671. The standalone gain is real-looking only for `cum >= 0.01` on ORB60 (0.35 ATR stop,
2R: +$6/day, P 0.99 over 2019-26) but it is a filter on an all-days ORB60 that the house does not trade (NQMaster's ORB60 runs on
pullback days with a 0.6R target and the prior-close filter, PF 1.9-2.4), and before 2015 the cell is below 1.0.

Cross-check with the TRUE delta (2025-05..2026-10, same cells in layer A): control ORB60-trend PF 0.75-0.93 (dead in that window),
cum >= .01: choose 0.69-0.96 (n 34) -> check 1.23-1.58 (n 31); q5 >= .5: 0.72-0.81 -> 0.94-1.17. Fails the choose period with the real
delta; only 31-34 trades per period.

## Delta as a filter on the HOUSE ORB60 / ORB90 trades (`python3 delta_orb.py house` -> `delta_house.json`)

The question Federico actually cares about: does a delta confirmation improve NQMaster's own ORB modules? Same conditions, features
from bars <= fill bar - 1, 7 conditions x ORB60 / ORB90 / both.

- True delta 2025-05..2026-10: only 28-33 house ORB trades per module per period. 1 of 42 cells "beats both" (ORB90 dl15 >= .03, n 15 / 15)
  = the chance level; cum >= .01 keeps 36-45% of the trades with PF 2.1 -> 20 (n 21 / 28) but the dropped trades are also profitable
  (PF 0.95 / 1.51). Too few trades for any conclusion.
- Tick-rule proxy 2020-10..2026-10 (216 / 346 trades): cum >= 0 / .01 keeps 84-88% of the trades, PF 2.16 -> 2.34 (T1) and 1.92 -> 2.01..2.05
  (T2); the 12-16% dropped trades still have PF 1.1-1.5 (net positive). dPF +0.19 / +0.10..+0.13 -> fails the +0.15 bar in T2, and
  dropping profitable trades lowers the $ of the module. q5 / q15 conditions drop the BETTER half (dropped PF 2.5-3.2).

No house rule is accepted.

## Verdict

1. **ORB confirmed with volume delta: no robust edge.** With the true aggressor delta (17 months, 9,600 ORB cells) one cell survives the
   standalone protocol but fails the portfolio DD limit and has no history on 16 years of proxy data; with the proxy on 16 years four
   ORB60-trend cells survive standalone but all lower Ultra's Sharpe (they duplicate the house ORB60) and fail with the true delta.
   The base-rate picture is the usual one: P(check pass | choose pass) 11% vs 5% (true delta), the choose-vs-check gain correlation
   is -0.09, and across conditions only "session delta since 09:30 with the break" has a consistent positive median (+0.06..+0.28 PF)
   at the cost of 50-70% of the trades.
2. **Absorption, delta divergence, delta flip at VWAP, delta climax: nothing** (medians PF 0.8-1.0 with true and proxy delta, 0 cells
   pass the check period).
3. **As a filter on the house ORB60 / ORB90**: the session delta drops 12-16% of trades that are themselves profitable; not worth the
   loss of $ and not implementable in Strategy Analyzer anyway.
4. The FundedSync `FabioOrb` 2026 PF 1.14 is consistent with what an all-days ORB + delta filter does here (PF ~1.1-1.4 on an ORB60-trend
   base, far below the house pullback-day ORB60 at 1.9-2.4).

**Nothing to add to NQMaster.** For the record, if Federico wants to try the one candidate live anyway (group 09 already accumulates
aggressor delta since 18:00 via OnMarketData; it would need a 09:30-anchored accumulator): "ORB60 breakout only if (buy - sell) /
(buy + sell) since 09:30 >= +0.01 in the breakout direction" raised a standalone ORB60-trend 2R from PF 1.28 / 1.14 to 1.44 / 1.38
(2019-22 / 2023-26, proxy) but LOWERED Ultra's Sharpe by 0.09-0.23 in both periods -> not recommended, and it cannot be backtested in
Strategy Analyzer without Tick Replay.

Do not re-run: breakout-minute delta, big-print imbalance (no choose period), delta quantile vs recent windows, ABS / DIV / VFLIP /
CLIMAX families, proxy delta on the house ORB. A new idea would need new data (e.g. order-book depth / iceberg detection at the range
edge, which the per-minute aggressor data cannot see).

## Files

`research/mine/delta_orb.py` (layer A + shared code: Flow features, ORB kernel, A2 generators, `port_test`, `block_boot`,
`proxy_validation`, `house_orb`), `delta_orb.json`, `delta_orb_cells.csv` (all 9,792 cells), `delta_orb_trades.pkl` (survivor trades),
`proxy_validation.json`, `delta_house.json`, `families12.py` (+ `FAMILIES12` registered in `run_mine_db.py`), `results_b12.csv`,
`trades_b12.pkl`, `b12_select.py`, `b12_select.json`. No NQMaster / GoldMaster change, no commit, no Databento spend.
