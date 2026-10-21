# Mega-cap earnings and Nasdaq-100 index events on NQ (2026-10-21)

Files: `research/mine/earn_dates_build.py` (date lists), `research/news_dates_earn_<ticker>.csv` (9 tickers), `research/news_dates_ndx_rebal.csv`,
`research/mine/earn_lab.py` (engine, `__main__` guard, 2 processes, ~2 min), `earn_lab.json`, `earn_lab_cells.csv` (10,530 cell x set rows),
`earn_lab_protocol.csv` (protocol columns), `earn_dates_summary.json`. Data: real Databento NQ 1-minute 2010-06..2026-10 (`nqdb.npz`).
No change to NQMaster.cs / GoldMaster.cs. Nothing committed.

## 1. Date lists and validation

Earnings: SEC EDGAR full-text search (`efts.sec.gov/LATEST/search-index`, JSON) for 8-K filings with item 2.02 per CIK, 2009-2026; the 8-K
`period_ending` (press-release day) is used, not the filing date (after-17:30 filings get the next day's filing date). Cleaning: TSLA delivery
reports (item 7.01 2013-22; day 1-3 of Jan/Apr/Jul/Oct 2023+) removed; at most one date per calendar quarter (the last of those within 12 days of
the ticker's usual day-of-quarter, else the nearest: NVDA 2019-01-28 pre-announcement -> 02-14, NVDA 2022-08-08 -> 08-24, NFLX 2019-12-16 recast
dropped); bundled 8-Ks with an earlier `period_ending` (filed 2+ business days later, e.g. TSLA credit agreement 2023-01-20 / release 01-25,
GOOGL 2023-07-25, NFLX 2023-01-19) take the filing date. All nine report after the close, so the NQ reaction is the next session.
Index events: rule-based (Nasdaq methodology): quarterly rebalance / quad witching = close of the third Friday of Mar/Jun/Sep/Dec, annual
reconstitution = the December one, plus the special rebalances of 2011-04-29 and 2023-07-21 (70 dates, 68 in data).

| ticker | dates in data (2010-06..2026-10) | post-close 16:00-16:59 range / ATR vs control (median ratio, 2019+) | next-session gap (09:29 close - prior RTH close) / ATR vs control: median ratio all / pre-2019 / 2019+ | share of next-days above the control median (2019+) | validated |
|---|---|---|---|---|---|
| NVDA | 65 | 2.78 | 1.30 / 0.88 / 1.75 | 0.71 | yes |
| AAPL | 65 | 4.40 | 1.90 / 2.17 / 1.75 | 0.71 | yes |
| MSFT | 65 | 5.26 | 1.91 / 1.56 / 2.02 | 0.77 | yes |
| AMZN | 65 | 6.33 | 1.50 / 1.61 / 1.44 | 0.68 | yes |
| GOOGL | 65 | 5.26 | 1.98 / 2.07 / 1.95 | 0.74 | yes |
| META | 57 | 4.45 | 1.42 / 0.93 / 1.87 | 0.71 | yes |
| TSLA | 64 | 2.78 | 0.98 / 0.95 / 1.25 | 0.55 | NO (flagged: borderline, kept only inside the all-ticker union) |
| AVGO | 64 | 1.53 | 1.18 / 0.77 / 1.42 | 0.65 | yes (weak) |
| NFLX | 65 | 2.11 | 1.36 / 1.42 / 1.36 | 0.61 | yes (weak) |

Validation rule (fixed before looking): 2019+ median gap ratio >= 1.25 and share > 0.60. The post-close range ratios (4-6x for the five
largest, 1.5-2.8x for NVDA/TSLA/NFLX/AVGO) confirm the dates are right; the overnight gap keeps about half of that excess. NVDA, META and AVGO
only move NQ since ~2019 (weights). Index events: rebalance-day RTH range ratio 0.97 (2019+ 1.08), next-day gap 1.08 (2019+ 0.81): no visible
excess volatility. Earnings-cluster weeks (Mon-Fri weeks with >= 4 of the 9 reports): 44 weeks, 219 days; gap ratio 1.39, RTH range 1.11.
Sets: 464 release days, 464 next-days (unions), core-6 294, cluster 219, control 2,877 ordinary days (no earnings/index/CPI/NFP/FOMC).

## 2. Pre-registration (as written in the `earn_lab.py` docstring before running)

Periods: choose on T1 = 2019-01..2022-12 (real $ per MNQ, $1.90 + 1 tick, AND cost-normalised 0.345% ATR), check on T2 = 2023-01..2026-10
(real, plus 4-tick stress), A = 2010-06..2018-12 cost-normalised as the regime control. Control = the same cell on ordinary days.
Cell protocol: T1 n >= 20, T1 PF >= 1.3, T1 normalised PF >= 1.2 -> T2 PF >= 1.2, T2 stress >= 1.1, event-specific (event PF - control PF
>= 0.2 in T1 and T2), plateau (>= half of the one-parameter neighbours T1 PF >= 1.2 and T2 PF >= 1.0); 'robust' adds A PF >= 1.0.
Hypotheses and grids: (a) GAP follow/fade at 09:30 of the move since the 18:00 open (GAP18) or since the prior RTH close (GAPC), x 0.05-0.35
ATR, stop 0.25/0.35/0.5 ATR, R 0.5/1/2, hold 30-240 (576 cells); (a-pre) 15:00 follow/fade of the release-day RTH move (36); (b) ORB60 next
session with/against the gap, any, or the daily-trend filter (48); (c) first-hour reversal at 10:00/10:30 (324); (d) the 2027 default per module
on event days, portfolio with those days x0 / x2; (e) rebalance day 15:30 drift (72) and next-day 09:30 reversal of the last 30 minutes (162);
(f) cluster weeks as a regime. Two single pre-registered tests: the CPI09 cell transplanted to GAPC next-days, fade and follow.
Portfolio: survivors added to `ultra_d4` (2020-10..2026-10) with `conflict_filter`; accepted only if Sharpe rises in T1 (2020-10..2022) and T2
(2023+) and maxDD / worst month do not worsen by > 5%; 21-day block bootstrap.

## 3. Results per hypothesis (median PF of the grid, A / T1 / T2; control T1 / T2; T1 passes; P(T2 ok | T1 ok) vs base rate; survivors)

| hypothesis | set | cells | days T1/T2 | median PF A/T1/T2 | control T1/T2 | T1 pass | P(T2 ok given T1 ok) | base P(T2 ok) | survivors (robust) |
|---|---|---|---|---|---|---|---|---|---|
| (a) GAP | next-day union | 576 | 109/102 | 0.98/0.92/0.99 | 0.94/0.95 | 178 | 0.03 | 0.28 | 0 |
| (a) GAP | validated union | 576 | 101/94 | 0.98/0.91/1.00 | 0.94/0.95 | 151 | 0.03 | 0.33 | 0 |
| (a) GAP | core-6 | 576 | 69/64 | 0.99/0.91/1.02 | 0.94/0.95 | 142 | 0.06 | 0.37 | 0 |
| (a) GAP | per ticker (9) | 576 each | 16/15 | 0.88-1.02 / 0.88-1.11 | | 0 | - | | 0 |
| (a) GAP | rebalance next-day | 576 | 16/16 | 0.99/0.82/0.94 | | 0 | - | 0.24 | 0 |
| (a) GAP | cluster weeks | 576 | 70/70 | 0.96/0.94/1.03 | 0.94/0.95 | 105 | 0.59 | 0.39 | 51 (17) |
| (a-pre) 15:00 release day | release union | 36 | 109/102 | 0.95/0.96/0.93 | 0.95/0.95 | 3 | 0.00 | 0.11 | 0 |
| (b) ORB60 | next-day union | 48 | 109/102 | 0.97/1.35/1.02 | 1.15/1.07 | 28 | 0.36 | 0.23 | 7 (0): all 'trend' filter = the standard ORB |
| (b) ORB60 | validated union | 48 | 101/94 | 0.93/1.20/1.18 | 1.15/1.07 | 18 | 0.44 | 0.48 | 1 (1): with-gap W300 cap 0.25 R2, isolated |
| (c) first-hour reversal | next-day union | 324 | 109/102 | 0.96/0.93/1.02 | 0.95/0.94 | 20 | 0.35 | 0.38 | 0 |
| (c) | release days | 324 | 109/102 | 0.93/0.93/1.02 | | 48 | 0.08 | 0.32 | 0 |
| (c) | rebalance days / cluster | 324 | 16/16, 70/70 | 1.03/0.89/1.00, 0.93/0.92/0.99 | | 0, 26 | -, 0.19 | 0.22, 0.26 | 0 |
| (e) 15:30 drift | rebalance days | 72 | 16/16 | 0.75/1.01/0.73 | 0.87/0.92 | 0 | - | 0.21 | 0 |
| (e) 15:30 drift | release days | 72 | 109/102 | 0.88/0.88/0.93 | 0.87/0.92 | 7 | 0.57 | 0.08 | 1 (0): fade RTH move >= 0.35 ATR, isolated |
| (e) next-day reversal | rebalance next-day | 162 | 16/16 | 0.96/0.72/0.93 | 0.94/0.97 | 0 | - | 0.33 | 0 |
| ALL | | 10,530 rows | | | | 748 | 0.16 | 0.31 | 60 (18) |

Pooled base rate: P(T2 ok | T1 ok) = 0.16 < P(T2 ok) = 0.31: choosing on T1 is ANTI-predictive for these events, because the main effect
flips sign between periods.

The flip (two pre-registered single tests, CPI09 cell x 0.05 / stop 0.35 ATR / 0.5R / hold 60 on the GAPC next-day union, n A/T1/T2 231/103/100):
FADE the overnight earnings gap at 09:30: PF A 1.44, T1 1.47 (WR 71%), T2 0.60 (WR 53%). FOLLOW: A 0.60, T1 0.48, T2 1.53 (WR 69%); core-6
follow T2 PF 2.00. Control (ordinary days) fade 0.93/0.93/1.03, follow 0.90/0.85/0.87. So earnings gaps faded in 2010-22 and continued in
2023-26 (the AI-megacap regime). Neither direction is tradeable with a fixed rule; in the portfolio: fade T1 Sharpe +0.03 / T2 -0.16, follow
T1 -0.16 / T2 +0.03 -> both rejected.

Cluster-week survivors (51 cells, all GAP FOLLOW on the 219 days of the big-tech weeks; 17 'robust'): the strongest cells have n = 21/27
(x >= 0.35 ATR: T1 PF 3.76, T2 2.01, A 1.84; 2019 negative) and the broad cell x 0.05 / stop 0.25 / 0.5R / hold 120 has n 64/60, PF T1 2.08,
T2 1.29, A 0.96, $29 / $17 per month. The same cells on earnings next-days OUTSIDE cluster weeks lose (PF 0.22-0.57 T1, 0.9-1.1 T2) and on the
pre-report days inside the weeks they are mixed (T2 PF 0.94-1.09 for most cells). Portfolio: best cells +0.03-0.04 Sharpe in both periods,
+$0-40 per month, bootstrap P(gain) 0.84/0.90 (n 83 trades), maxDD slightly lower. Formally 'accepted', economically nothing: 17 trading days
per year, $13-50 per month per contract, the broad cell lost in 2019 and the 2R cells lost 2024-25. Watch list, not implemented.

(b) ORB on earnings next-days: the 7 'survivors' are the standard trend-filtered ORB60 (PF T1 1.43-1.56, T2 1.40-2.24, A 0.83-0.94), i.e. the
existing ORB60 module works better on post-earnings days; a second ORB instance is rejected by the portfolio test (DD up, Sharpe T1 down,
conflicts with ORB60). The single with-gap robust cell (W 300, cap 0.25, 2R: T1 2.27, T2 1.25, A 1.02) is 1 of 48, control T1 1.35, portfolio
+0.02/+0.04 Sharpe with maxDD +4.5% and worst month worse (-1,176 -> -1,408): rejected.

## 4. The 2027 default (ultra_d4) on event days (hypotheses d, f)

Whole portfolio, trades on event days vs other days (PF, avg $ per trade per base contract):

| days | T1 2020-10..2022 (days, trades) | PF event / other | avg $ event / other | T2 2023-26 (days, trades) | PF event / other | avg $ event / other |
|---|---|---|---|---|---|---|
| earnings next-day (union) | 81 d, 324 tr | 1.75 / 1.54 | 30.2 / 21.4 | 102 d, 504 tr | 1.45 / 1.44 | 24.5 / 20.7 |
| earnings release day | 81, 292 | 1.41 / 1.59 | 18.5 / 23.0 | 102, 440 | 1.47 / 1.44 | 21.4 / 21.1 |
| core-6 next-day | 189 tr | 1.63 / 1.56 | 28.9 / 22.0 | 302 tr | 1.64 / 1.43 | 34.0 / 20.3 |
| NDX rebalance / quad witching | 12 d, 40 tr | 3.50 / 1.55 | 58.1 / 21.9 | 16 d, 65 tr | 1.80 / 1.44 | 40.5 / 20.9 |
| day after rebalance | 12, 54 | 0.98 / 1.58 | -0.6 / 22.9 | 16, 70 | 2.01 / 1.43 | 34.8 / 20.9 |
| cluster weeks | 55, 205 | 2.49 / 1.51 | 44.5 / 20.7 | 70, 304 | 1.40 / 1.44 | 20.0 / 21.2 |

Per module on earnings next-days (n >= 10 in both periods): ORB60 PF 15.4 / 3.84 (n 16/23, avg $120/$146 vs $60/$48 other), ORB90 3.0 / 2.4,
MOM11 1.35 / 1.32 (vs 1.27 / 1.19), VW13 2.28 / 1.49, VOLB 1.00 / 1.69, MOM1030 1.14 / 1.69, LON 0.80 / 1.40; sign flips T1 vs T2 for MOM13
(3.07 / 0.79), MSEQ (3.40 / 0.84), LATE15 (2.26 / 0.82), ON07 (1.42 / 0.84), REV06 (1.23 / 0.41), ORFAIL (1.73 / 0.75). The full table per module
and set is in `earn_lab.json` -> `module_table`.

Skip (x0) / boost (x2) of whole event days, Sharpe T1 / T2 (base 4.07 / 3.60), bootstrap P(gain) T1 / T2:
next-day x0 3.70 / 3.39 (0.03 / 0.09); next-day x2 3.88 / 3.40 (0.15 / 0.04); release day x0 3.93 / 3.39; x2 3.81 / 3.50; core-6 x2 3.80 / 3.46;
rebalance x0 3.97 / 3.55; rebalance x2 4.02 / 3.57 (0.38 / 0.21); day-after-rebalance x0 4.09 / 3.54; x2 4.01 / 3.60 (0.37 / 0.48);
cluster x0 3.67 / 3.52; cluster x2 4.00 / 3.43; validated next-day x2 3.81 / 3.46. Nothing improves both periods: LEAVE THE DAYS ALONE.
Skipping earnings days costs $280-370 per month per contract (they are above-average days); boosting them raises $ but lowers Sharpe (the
day-level variance doubles).

Post-hoc (NOT pre-registered, picked from the table above): ORB60 x2 on earnings next-days only: T1 Sharpe 4.07 -> 4.14, $/mo 2,332 -> 2,405,
maxDD 2,254 -> 2,071, P(gain) 1.00; T2 3.60 -> 3.63, 2,216 -> 2,291, maxDD 4,667 -> 4,465, P(gain) 0.74. ORB60+ORB90 similar; adding VOLB
reverses it (T1 3.93). 39 trades of evidence after selection from 23 modules: candidate for the January review, not implemented.

## 5. Verdict

- The date lists are correct (post-close range 1.5-6x) and the next-session gap is 1.4-2x normal for eight of the nine names (TSLA borderline).
- No earnings or index-event rule survives the protocol with economic value. 10,530 cell-set rows, 748 T1 passes, 60 formal survivors, 18
  'robust', all in one thin cluster (gap-follow during the 17 big-tech days per year, +0.03 Sharpe, $13-50 per month) or isolated cells.
- The overnight earnings gap reversed in 2019-22 and continued in 2023-26, on every union; a fixed rule in either direction loses in the other
  period, exactly as the memory warns for T1-chosen signals (P(T2 | T1) 0.16 vs base 0.31).
- Release-day pre-close drift, first-hour reversal, rebalance-day closing drift, and next-day reversal after a rebalance: nothing (medians 0.7-1.0,
  rebalance sets have only 16 days per period).
- The 2027 default already earns more than average on earnings next-days and on rebalance days (PF 1.45-1.75 / 1.8-3.5 vs 1.44-1.55), and
  skipping or doubling those days does not raise Sharpe in both periods. No NQMaster change: no CPI09-like module, no skip rule, no boost rule.
- If anything is ever taken from this round it would be `OrbEarningsMultiplier = 2` on the earnings next-day list (post-hoc, 39 trades):
  re-test after the January 2027 review with the new reports added to `news_dates_earn_*.csv` (rerun `earn_dates_build.py`, it caches EDGAR JSON).
- Do not re-run: GAP fade/follow, first-hour reversal, pre-close drift, rebalance drifts, whole-day skip/boost on these events.
