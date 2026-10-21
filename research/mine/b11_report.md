# Batch 11: the classic index-futures literature on intraday NQ (2026-10-21)

Federico asked for NEW strategies never tested here, chosen on 2019-2023 and compared on 2023-2026. This batch adapts the classic daily-bar literature (Williams, Raschke/Connors, Crabel, Connors, Taylor, Steidlmayer) to intraday NQ with every trade flat at 15:55 ET. Real Databento NQ futures `research/data/nqdb.npz` (2010-06..2026-10), $ per MNQ including $1.90 commission and 1 tick per side, cost-normalised view (0.345% of the daily ATR) for 2010-18. Generators `research/mine/families11.py` (15 families, 3,105 cells), miner run `MINE_TAG=b11 MINE_PROCS=2 MINE_T1=20190101 MINE_T2=20230101 python3 run_mine_db.py ...` (27 s; `run_mine_db.py` got `MINE_T1` / `MINE_T2` overrides, defaults unchanged) -> `results_b11.csv`, `trades_b11.pkl` (24 MB); selection `b11_select.py` -> `b11_select.json`, `results_b11_staged.csv`; lookahead check `b11_lookahead.py` -> `b11_lookahead.json`.

## Pre-registered protocol (written in `b11_select.py` before `results_b11.csv` was opened)

- Periods: T1 = 2019-01..2022-12 (choose; real $ and the cost-normalised view T1n), T2 = 2023-01..2026-10 (check), A = 2010-14 and B = 2015-18 cost-normalised (regime check).
- s1 choose: T1 n >= 80, PF >= 1.30, WR >= 50.0 and T1n PF >= 1.15 (the only stage used to choose).
- s2 T2 PF >= 1.20; s3 A PF >= 1.00 and B PF >= 1.00; s4 T2 with +4 ticks per side ($3.00 per trade) PF >= 1.10; s5 plateau: >= 2/3 of the one-step numeric neighbours (>= 2 neighbours) have T1 PF >= 1.15; s6 one representative per signal (exits sk / R / exp / nb / t0 / dtf and the daily trend filter are not a signal): the survivor with the best T1 PF.
- Portfolio (each representative alone): trades on NQMaster days (ATR >= 150, no FOMC) added to the raw 2027 default set (`nt_compare.research_set("ultra_d4")` before its conflict filter, P&L = w x u) and run through `wrq_port.conflict_filter`; T1p = 2020-10-15..2022-12 (base start), T2p = 2023-01..: Sharpe up in BOTH, max DD and worst month not worse by > 5% in either, daily-P&L correlation with the base < 0.3; 21-day block bootstrap (1,000 joint draws of base and combined daily P&L) of the Sharpe gain per period.
- Base rates P(T2 PF >= 1.2) over all cells vs given s1, per family and overall, so selection bias can be judged.

## Families (all new to the archive)

| family | source | setup (intraday adaptation) | cells |
|---|---|---|---|
| LW_OOPS | Williams | RTH open gaps >= g ATR below yesterday's low -> buy stop at that low (mirror); exits sk / R / hold, expiry 11:00-15:00, trend filter | 243 |
| LW_SMASH | Williams | smash day (yesterday closed below the day-before's low) or hidden smash (close < open, bottom 25% of the range) -> buy stop at yesterday's high (+off ATR); mirror | 324 |
| LW_INOUT | Williams | inside day -> OCO breakout of its high / low; outside day -> break of its extreme with / against the close direction | 162 |
| RC_TSOUP | Raschke-Connors | Turtle Soup Plus One (yesterday new N-day low and close <= the previous N-day low; today buy stop back at yesterday's low after an x ATR violation) and intraday Turtle Soup (break of the N-day low by x ATR, stop back at the level) | 288 |
| RC_8020 | Raschke-Connors | yesterday opened in the top pct and closed in the bottom pct of a >= 0.75 ATR range; today, after x ATR below yesterday's low, buy stop at that low; mirror | 216 |
| RC_PINBALL | Raschke | 3-period RSI of the 1-day ROC < thr (> 100 - thr) -> buy (sell) stop at the opening-range (30 / 60 min) extreme | 144 |
| RC_HOLYGRAIL | Raschke-Connors | 15 / 60-min bars: ADX(14) > 25 / 30 and rising, +DI > -DI, first bar touching EMA(10 / 20) -> stop above its high (2 / 4 bars), stop below its low or 0.3 ATR | 192 |
| RC_ANTI | Raschke | 15 / 30-min bars: slow %K(7 / 14, 3) hooks back with a rising / falling %D(10) -> stop beyond the hook bar | 96 |
| CRABEL_NR | Crabel | NR4 / ID-NR4 / narrowest 2-day range of 20 yesterday -> OCO breakout of the 15 / 30-min opening range | 216 |
| CRABEL_STRETCH | Crabel | 10-day mean of min(open - low, high - open) -> OCO stops at open +- 1.0 / 1.5 x stretch, any day / NR4 / ID-NR4 | 216 |
| CN_DOUBLE7 | Connors | yesterday's close = lowest close of 5 / 7 / 10 days (above SMA200 with filt) -> long at the open / on a 0.1 ATR dip, 0.5-1.0 ATR stop, R / hold; mirror | 144 |
| CN_PCTB | Connors | Bollinger(20, 2) %b of yesterday's close < 0 / 0.2 -> long; > 1 / 0.8 -> short; same entries | 96 |
| CN_R3 | Connors | RSI(2) fell 3 days from < 60 to < 10 / 20 -> long (mirror); same entries | 96 |
| TAYLOR | Taylor | 3-day cycle from the lowest low / highest high of the last 3 days -> Buy day: long on a decline x ATR below yesterday's low (limit) or on its failure (stop back); Short-sale day: mirror; target yesterday's extreme / R / hold | 288 |
| STEID_OPEN | Steidlmayer | first 30 / 60 min classified as open-drive / open-test-drive / open-rejection-reverse (trade the implied direction, market or stop entry, structural or 0.3 ATR stop) / open-auction (fade the range with limits) | 384 |

Execution: all fills through `core.execute` (market at the next bar open + 1 tick, stops at max(level, open) + 1 tick, limits need a 1-tick trade-through, stops -1 tick, flat at 15:55). Two-sided (OCO) setups are resolved in the generator: the side whose level is touched first is the only event emitted (a bar touching both sides cancels the day), so no order-priority bias. Structural stops are floored at 0.10 ATR and skipped above 1.0 ATR.

## Lookahead checks

`b11_lookahead.py`: for 588 sampled events (3-5 cells per family, up to 12 events each) every bar after the signal bar was perturbed (prices +137 points, ranges widened, volume x3; for OCO setups the touch bar is kept, the bars between the order placement and the signal bar are collapsed to their close and everything after the touch bar is shifted) and the generator re-run: the event must keep its direction, type, price, stop, target and expiry. **0 violations.** Daily features come from the compact table of RTH days shifted by one row (yesterday = the previous RTH day); opening ranges end before the placement bar; tf-bar indicators (ADX, EMA, stochastics) use the bar's own close.

## Results per family

| family | cells | median PF T1 / T2 / A / B | median WR T1 / T2 | s1 | s2 (T2) | s3 (A, B) | s4 (+4t) | s5 (plateau) | signals | P(T2 pass) all | P(T2 pass given s1) | P(T2 and A/B given s1) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LW_OOPS | 243 | 0.89 / 1.36 / 1.13 / 1.35 | 43.2 / 50.0 | 0 | 0 | 0 | 0 | 0 | 0 | 74% | - | - |
| LW_SMASH | 324 | 1.52 / 1.18 / 1.11 / 1.18 | 54.3 / 51.3 | 51 | 23 | 22 | 22 | 22 | 3 | 44% | 45% | 43% |
| LW_INOUT | 162 | 0.62 / 1.08 / 0.85 / 0.81 | 55.9 / 50.0 | 0 | 0 | 0 | 0 | 0 | 0 | 14% | - | - |
| RC_TSOUP | 288 | 0.89 / 0.93 / 0.89 / 1.03 | 41.7 / 40.5 | 8 | 0 | 0 | 0 | 0 | 0 | 1% | 0% | 0% |
| RC_8020 | 216 | 0.98 / 0.78 / 0.96 / 1.32 | 39.9 / 43.6 | 3 | 0 | 0 | 0 | 0 | 0 | 6% | 0% | 0% |
| RC_PINBALL | 144 | 1.16 / 0.98 / 0.92 / 0.86 | 46.4 / 45.5 | 4 | 1 | 0 | 0 | 0 | 0 | 22% | 25% | 0% |
| RC_HOLYGRAIL | 192 | 0.83 / 1.13 / 1.24 / 1.24 | 40.0 / 46.2 | 0 | 0 | 0 | 0 | 0 | 0 | 27% | - | - |
| RC_ANTI | 96 | 0.89 / 0.92 / 1.02 / 0.95 | 45.0 / 44.3 | 0 | 0 | 0 | 0 | 0 | 0 | 0% | - | - |
| CRABEL_NR | 216 | 1.29 / 0.93 / 0.93 / 0.91 | 50.9 / 45.5 | 7 | 1 | 1 | 1 | 1 | 1 | 4% | 14% | 14% |
| CRABEL_STRETCH | 216 | 1.06 / 1.05 / 1.04 / 1.05 | 50.0 / 50.0 | 0 | 0 | 0 | 0 | 0 | 0 | 20% | - | - |
| CN_DOUBLE7 | 144 | 1.08 / 0.91 / 0.90 / 1.03 | 49.0 / 46.3 | 2 | 0 | 0 | 0 | 0 | 0 | 11% | 0% | 0% |
| CN_PCTB | 96 | 1.02 / 0.88 / 1.11 / 0.98 | 51.7 / 44.1 | 6 | 0 | 0 | 0 | 0 | 0 | 0% | 0% | 0% |
| CN_R3 | 96 | 0.95 / 0.90 / 0.79 / 0.85 | 46.2 / 43.6 | 11 | 0 | 0 | 0 | 0 | 0 | 3% | 0% | 0% |
| TAYLOR | 288 | 0.92 / 0.96 / 0.87 / 1.26 | 44.4 / 42.3 | 1 | 0 | 0 | 0 | 0 | 0 | 9% | 0% | 0% |
| STEID_OPEN | 384 | 1.26 / 1.18 / 1.06 / 1.07 | 53.7 / 53.3 | 118 | 101 | 70 | 70 | 70 | 12 | 41% | 86% | 59% |
| ALL | 3105 | 1.05 / 1.01 / 0.99 / 1.08 | 48.1 / 46.9 | 211 | 126 | 93 | 93 | 93 | 16 | 22% | 60% | 44% |

- 211 of 3,105 cells pass s1; 93 survive s2-s5 (LW_SMASH 22, STEID_OPEN 70, CRABEL_NR 1); 16 representatives (one per signal). P(T2 PF >= 1.2 | s1) = 60% vs 22% unconditional, driven by two families whose whole grid is positive (STEID_OPEN 86%, LW_SMASH 45%); every other family is at or below its unconditional rate (Connors / Raschke-Connors / Taylor / Crabel stretch: 0 survivors, medians PF 0.9-1.1).
- Williams 'Oops!' (gap fade back to yesterday's extreme): T2 cells pass 74% of the time (median PF 1.36) but T1 median 0.89 (2019-22 gaps ran) -> not selectable; gap fade / fill is already on the rejected list and this is the same signal.
- LW_SMASH with the daily trend filter looks spectacular (median T1 PF 2.4-2.6, T2 1.6-3.1) but has 25-49 trades in T1 (about 8 per year) and 15-35 in T2: below the n >= 80 floor, not evidence. Without the filter it passes with ~100 trades per period and PF 1.2-1.7.
- STEID_OPEN open-drive WITH the trend filter is the one robust new cell block: median PF 1.78 / 1.88 / 1.26 / 1.15 (T1 / T2 / A / B), WR ~60%, ~25 trades per year; open-test-drive and open-auction have no edge; rejection-reverse is weak (PF 1.2-1.3, 2010-18 ~1.0).

## Portfolio test of the 16 representatives (each alone, added to the 2027 default set)

Base (ultra_d4, conflict-filtered): T1p Sharpe 4.138, PF 1.568, max DD $2,254, worst month $-1,176; T2p Sharpe 3.575, PF 1.44, max DD $4,667, worst month $-2,182.

| representative | T1 n / WR / PF | T2 n / WR / PF | +4t | A / B | corr | dSharpe T1p / T2p | boot median [p5, p95], P>0 T1p | T2p | dDD% T1p / T2p | dWM% T1p / T2p | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CRABEL_NR#38 {'cond': 'NR4', 'orl': 1000, 'sk': 0.0, 'R': 1.0, 'exp': 1400, 'tf': 0} | 260 / 56.9 / 1.31 | 249 / 55.8 / 1.23 | 1.19 | 1.14 / 1.05 | 0.129 | -0.050 / -0.151 | -0.067 [-0.37, +0.21], 0.36 | -0.175 [-0.39, +0.05], 0.11 | +32.3 / +1.9 | -27.9 / -16.3 | no |
| LW_SMASH#45 {'mode': 'smash', 'off': 0.0, 'exp': 1300, 'sk': 0.5, 'R': 1.0, 'tf': 0} | 108 / 60.2 / 1.70 | 104 / 55.8 / 1.20 | 1.18 | 1.25 / 1.03 | 0.115 | +0.116 / -0.093 | +0.114 [-0.06, +0.37], 0.87 | -0.101 [-0.29, +0.07], 0.18 | -13.8 / +1.3 | +29.8 / +9.1 | no |
| LW_SMASH#192 {'mode': 'hidden', 'off': 0.0, 'exp': 1300, 'sk': 0.0, 'R': 2.0, 'tf': 0} | 87 / 60.9 / 2.15 | 70 / 48.6 / 1.38 | 1.34 | 1.07 / 1.21 | 0.062 | +0.052 / +0.035 | +0.050 [-0.03, +0.15], 0.83 | +0.021 [-0.13, +0.16], 0.59 | +1.6 / -9.3 | -4.4 / +12.9 | no |
| LW_SMASH#282 {'mode': 'hidden', 'off': 0.05, 'exp': 1300, 'sk': 0.25, 'R': 2.0, 'tf': 0} | 95 / 55.8 / 1.64 | 71 / 40.8 / 1.27 | 1.23 | 1.55 / 1.25 | 0.094 | +0.003 / -0.023 | -0.006 [-0.11, +0.10], 0.47 | -0.053 [-0.18, +0.08], 0.25 | +7.5 / -3.4 | +4.5 / +5.5 | no |
| STEID_OPEN#5 {'typ': 'drive', 'W': 30, 'x': 0.15, 'ent': 'mkt', 'sk': 0.0, 'R': 0.0, 'tf': 1} | 124 / 55.6 / 1.79 | 106 / 59.4 / 2.10 | 2.04 | 1.41 / 1.14 | 0.358 | -0.110 / +0.019 | -0.103 [-0.24, +0.05], 0.13 | +0.026 [-0.11, +0.15], 0.63 | +9.7 / -1.8 | +12.5 / +2.6 | no |
| STEID_OPEN#15 {'typ': 'drive', 'W': 30, 'x': 0.15, 'ent': 'stop', 'sk': 0.0, 'R': 2.0, 'tf': 1} | 111 / 55.9 / 1.94 | 99 / 59.6 / 1.85 | 1.79 | 1.04 / 1.19 | 0.357 | -0.086 / -0.040 | -0.089 [-0.24, +0.06], 0.17 | -0.035 [-0.16, +0.09], 0.34 | +10.3 / -5.1 | +17.2 / +4.5 | no |
| STEID_OPEN#33 {'typ': 'drive', 'W': 30, 'x': 0.3, 'ent': 'mkt', 'sk': 0.3, 'R': 2.0, 'tf': 1} | 105 / 53.3 / 1.78 | 95 / 57.9 / 1.91 | 1.85 | 1.40 / 1.25 | 0.3 | -0.052 / +0.033 | -0.042 [-0.17, +0.09], 0.28 | +0.043 [-0.06, +0.15], 0.75 | +18.4 / -1.6 | +11.1 / +0.0 | no |
| STEID_OPEN#37 {'typ': 'drive', 'W': 30, 'x': 0.3, 'ent': 'stop', 'sk': 0.0, 'R': 1.0, 'tf': 1} | 93 / 62.4 / 1.99 | 86 / 66.3 / 1.93 | 1.88 | 1.06 / 1.01 | 0.307 | -0.047 / +0.001 | -0.050 [-0.22, +0.12], 0.30 | -0.000 [-0.11, +0.11], 0.50 | +6.7 / -9.0 | +10.2 / +0.0 | no |
| STEID_OPEN#57 {'typ': 'drive', 'W': 60, 'x': 0.15, 'ent': 'mkt', 'sk': 0.3, 'R': 2.0, 'tf': 1} | 120 / 57.5 / 2.03 | 115 / 50.4 / 1.56 | 1.51 | 1.39 / 1.07 | 0.344 | +0.027 / -0.042 | +0.030 [-0.07, +0.13], 0.68 | -0.051 [-0.17, +0.06], 0.23 | +10.5 / +2.0 | +23.9 / -4.6 | no |
| STEID_OPEN#69 {'typ': 'drive', 'W': 60, 'x': 0.15, 'ent': 'stop', 'sk': 0.3, 'R': 2.0, 'tf': 1} | 102 / 60.8 / 1.82 | 93 / 57.0 / 1.86 | 1.79 | 1.26 / 1.23 | 0.266 | +0.026 / +0.026 | +0.016 [-0.08, +0.11], 0.62 | +0.013 [-0.07, +0.10], 0.59 | +7.8 / +0.4 | +22.5 / -11.5 | no |
| STEID_OPEN#81 {'typ': 'drive', 'W': 60, 'x': 0.3, 'ent': 'mkt', 'sk': 0.3, 'R': 2.0, 'tf': 1} | 114 / 58.8 / 2.15 | 109 / 50.5 / 1.60 | 1.55 | 1.38 / 1.07 | 0.343 | +0.027 / -0.036 | +0.030 [-0.07, +0.13], 0.68 | -0.045 [-0.15, +0.07], 0.26 | +10.5 / +2.0 | +23.9 / -4.6 | no |
| STEID_OPEN#93 {'typ': 'drive', 'W': 60, 'x': 0.3, 'ent': 'stop', 'sk': 0.3, 'R': 2.0, 'tf': 1} | 96 / 62.5 / 1.97 | 87 / 57.5 / 1.96 | 1.89 | 1.26 / 1.24 | 0.265 | +0.027 / +0.034 | +0.018 [-0.08, +0.11], 0.63 | +0.022 [-0.06, +0.11], 0.67 | +7.8 / +0.4 | +22.5 / -11.5 | no |
| STEID_OPEN#251 {'typ': 'rejrev', 'W': 60, 'x': 0.15, 'ent': 'mkt', 'sk': 0.3, 'R': 0.0, 'tf': 1} | 369 / 50.4 / 1.48 | 323 / 47.1 / 1.24 | 1.20 | 1.05 / 1.02 | 0.423 | -0.183 / -0.209 | -0.172 [-0.38, +0.04], 0.10 | -0.213 [-0.39, -0.01], 0.04 | +38.2 / +4.4 | +23.5 / -13.1 | no |
| STEID_OPEN#261 {'typ': 'rejrev', 'W': 60, 'x': 0.15, 'ent': 'stop', 'sk': 0.3, 'R': 2.0, 'tf': 1} | 284 / 54.6 / 1.59 | 259 / 52.1 / 1.29 | 1.25 | 1.22 / 1.21 | 0.36 | -0.079 / -0.058 | -0.094 [-0.27, +0.10], 0.19 | -0.081 [-0.25, +0.10], 0.23 | +42.2 / -0.7 | +25.6 / -14.5 | no |
| STEID_OPEN#275 {'typ': 'rejrev', 'W': 60, 'x': 0.3, 'ent': 'mkt', 'sk': 0.3, 'R': 0.0, 'tf': 1} | 333 / 51.4 / 1.55 | 290 / 46.6 / 1.29 | 1.25 | 1.04 / 1.03 | 0.414 | -0.133 / -0.185 | -0.124 [-0.33, +0.10], 0.19 | -0.186 [-0.37, +0.01], 0.06 | +32.3 / +4.4 | +23.5 / -15.8 | no |
| STEID_OPEN#285 {'typ': 'rejrev', 'W': 60, 'x': 0.3, 'ent': 'stop', 'sk': 0.3, 'R': 2.0, 'tf': 1} | 260 / 55.8 / 1.65 | 233 / 50.6 / 1.32 | 1.28 | 1.25 / 1.24 | 0.35 | -0.041 / -0.058 | -0.057 [-0.23, +0.14], 0.32 | -0.080 [-0.26, +0.10], 0.24 | +35.5 / -0.7 | +25.6 / -19.0 | no |

**0 of 16 pass the portfolio test.** Reasons:
- STEID_OPEN open-drive (12 representatives): correlation 0.27-0.36 with the base (it is the 10:00 / 10:30 RTH move with the daily trend, which MOM1030 / ORB60 / VOLB already trade); Sharpe gain -0.11..+0.03 in T1p and -0.04..+0.03 in T2p, bootstrap P(gain > 0) 0.13-0.75, and the worst month worsens 10-24% in T1p. The best cells (W 60, stop entry, 0.3 ATR stop, 2R: #69 / #93) add +0.03 Sharpe in both periods with P(> 0) 0.6 but fail the max-DD (+8%) and worst-month (+22%) limits.
- LW_SMASH hidden #192 (2R, structural stop): +0.05 / +0.04 Sharpe, corr 0.06, max DD -9% in T2p, but the T2p worst month worsens 13% (one month). Nearest miss of the batch; ~1 trade per week, $1.2k per year per contract in T2.
- LW_SMASH smash #45 and CRABEL_NR #38: Sharpe down in T2p; CRABEL_NR raises the T1p max DD by 32%.
- Rejection-reverse cells: corr 0.35-0.42, Sharpe down in both periods.
- All 16 together (information only, heavy overlap): corr 0.468, Sharpe -0.67 / -0.99, max DD +303% / +181%.

Standalone yearly PF of the two nearest misses (real $ per contract): STEID_OPEN#93 2019-26: 1.57 / 1.36 / 1.88 / 2.54 / 1.20 / 4.88 / 1.89 / 1.29 (net $8.7k over 8 years, ~24 trades per year); 2010-18 norm 1.28 / 1.22 / 1.09 / 1.15 / 1.70 / 0.93 / 0.86 / 0.92 / 2.26. LW_SMASH#192: 1.30 / 5.00 / 2.06 / 1.84 / 0.93 / 1.08 / 2.75 / 1.15 (net $6.3k); 2010-18 norm 5.08 / 2.08 / 0.15 / 1.37 / 0.56 / 0.74 / 1.06 / 1.66 / 1.36.

## Verdict

- Nothing is added to NQMaster. The classic literature on daily bars, executed intraday on NQ, has no edge in 12 of 15 families (Connors mean reversion, Turtle Soup, 80-20s, pinball, Holy Grail, Anti, Crabel stretch, inside / outside days, Taylor cycle: medians PF 0.6-1.1 with 0 survivors), and the three that do survive standalone (Steidlmayer open-drive, Williams smash day, Crabel NR4 opening-range breakout) are versions of the opening momentum / range-expansion effect the 2027 default already holds (corr 0.1-0.36) and do not raise its Sharpe out of sample.
- The open-drive-with-trend block is a genuine, 16-year effect (PF > 1 in all four periods, 59 of 70 survivors) worth remembering if a module ever has to be replaced: STEID_OPEN#93 (W 60, x 0.3 ATR, stop entry at the range high, 0.3 ATR stop, 2R, trend filter) is the representative. As an addition it is redundant.
- The trend-filtered smash day (PF 2-4, WR 70-80%) is 8 trades per year: watch list, not evidence.
- Selection-bias context: P(T2 pass | T1 pass) 60% here vs 21% in the 54k-cell archive, because two whole families are positive; the base rate inside the 12 other families is 0-25%.

Do not re-mine: Connors daily mean reversion (Double 7s, %b, R3), Turtle Soup, 80-20s, momentum pinball, Holy Grail, Anti, Crabel stretch / NR with ORB, inside / outside days, Taylor cycle, Steidlmayer open types, Williams Oops / smash (as an addition).

Files: `research/mine/families11.py`, `b11_select.py`, `b11_lookahead.py`, `b11_lookahead.json`, `results_b11.csv`, `results_b11_staged.csv`, `trades_b11.pkl`, `b11_select.json`, `b11_report.md`; `run_mine_db.py` (FAMILIES11 + `MINE_T1` / `MINE_T2`).
