# Gold re-mining on 16 years of REAL GC futures (gold16, 2026-10-19)

## 0. Protocol (written BEFORE looking at any result)

Data: `research/data/mgcdb.npz` = Databento GLBX GC.v.0 ohlcv-1m 2010-06-07 .. 2026-10-09, forward roll-adjusted,
prices x2.5 (tick 0.25 = 1 MGC tick, $4 per research point), $1.90 commission + 1 tick slippage per side,
flat 16:50 ET (`MINE_FLAT=1010`), one position per config, same executor as every NQ mining run (`core.run_events`).
Every family in `run_mine_db.FAMILIES` (families 1-4, families5-10, and the gold families G_DRIVE / G_ORB / NQ_DRIVE / NQ_ORB)
= 65,544 configs, run twice per config: real $ (T1 = 2020-23, T2 = 2024-26) and cost-normalised (A = 2010-14, B = 2015-19,
P&L in % of the daily ATR with a cost of 0.96 % of the ATR per trade = today's MGC cost / ATR ratio, `MINE_NORM=0.0096`).

Gates, applied in this order (chosen on T1 only; T2 / A / B are out of sample and never used to pick):

1. T1 (real 2020-23): n >= 80, PF >= 1.30, WR >= 50 %.
2. T2 (real 2024-26): PF >= 1.20 (n >= 30).
3. A (2010-14, norm) PF >= 1.00 and B (2015-19, norm) PF >= 1.00 (n >= 30 each).
4. +4 ticks stress on T2 (2 extra ticks per side = $4 per MGC trade, ~1 % of the T2 ATR, the same order as the NQ +$3/MNQ stress): PF >= 1.10.
5. Plateau: the 1-step grid neighbours (same family, exactly one parameter different, T1 n >= 30) have a median T1 PF >= 1.15
   and no more than one third of them below PF 1.00.
6. One representative per signal: a signal = family + the parameters that define the idea (anchor, window, direction/mode,
   level type, pattern); risk/exit parameters (R, x, k, s, cap, hold, stop, body, bk, conf, sweep, exp, w0, w1, ...) are variants.
   The representative is the survivor with the highest T1 PF.
7. Portfolio value (per representative, trades FOMC-skipped like GoldMaster, opposite-position conflict filter like gold_port):
   - gold-only: Robust set (OD1030, ENG0408, SVWAP22, ASIA1R, ENG0206 regenerated on mgcdb) + candidate must raise the gold daily
     Sharpe in T1 AND T2 and not raise the max drawdown by more than 5 % in either period;
   - NQ + gold: NQ base = `nt_compare.research_set("ultra_d4")` (P&L = w x u, 2020-10-15 ..) + gold Robust (+ candidate):
     daily Sharpe up in T1 (2020-10-15..2023) AND T2 (2024..).
8. Report: counts per gate, base rates P(T2 PF >= 1.2 | T1 pass) vs all configs with T1 n >= 80, per family; the current
   GoldMaster modules through the same table; 21-day block bootstrap (1,000 draws) of the Sharpe gain for survivors.

Only a candidate that passes 1-7 is "worth adding"; anything else is reported and not implemented.

## 1. Run

- `run_mine_db.py` got an env `MINE_NORM` (default unchanged 0.00345); run:
  `MINE_DATA=mgcdb.npz MINE_FLAT=1010 MINE_NORM=0.0096 MINE_TAG=gold16_new|gold16_old MINE_PROCS=2 python3 run_mine_db.py <families>`
  (new families first: families5-10 + G_DRIVE/G_ORB/NQ_DRIVE/NQ_ORB = 36,418 cfg, 386 s; then families 1-4 = 29,126 cfg, 678 s; 0 errors).
- Gold families were already inside `run_mine.FAMILIES`, so nothing had to be added. `core.Data` is instrument-aware (mgc: $4/pt, $1.90).
  NQ-flavoured conventions kept on purpose (same as every earlier gold study): daily ATR / trend / PDH-PDL from the 09:30-16:00 ET window,
  session = 18:00 ET Globex day, flat 16:50 (GoldMaster now flattens 16:00; `gold_flat1600.py` showed that re-pricing is neutral).
- Cost ratio on mgcdb, ($1.90 + 2 ticks x $1) / (ATR pts x $4), median per block: A 2.29 %, B 3.36 %, T1 1.90 %, T2 1.01 %, 2026 0.44 %.
  The norm view uses 0.96 % (today's ratio, as in `gold_db.py`), i.e. 2010-19 is priced at TODAY's cost, not the cost of the time.
- Outputs: `results_gold16.csv` (65,544 rows = new + old), `trades_gold16_new.pkl` / `trades_gold16_old.pkl` (configs with T1 n >= 80 & PF >= 1.25,
  12 + 7 MB), `gold16_select.py` -> `gold16_select.json`, `gold16_survivors_trades.pkl`, `gold16_select.log`, `gold16_nq_daily.pkl` (cached ultra_d4 daily P&L).

## 2. Counts and base rates

| gate | configs |
|---|---|
| all | 65,544 |
| 1 T1 n >= 80, PF >= 1.30, WR >= 50 | 146 |
| 1+2 T2 PF >= 1.20 | 31 |
| 1+2+3 A and B norm PF >= 1.00 | 6 |
| +4 (+4 ticks T2 PF >= 1.10) | 6 |
| +5 plateau | 1 |
| +6 one per signal | 1 (INSIDE_DAY#42) |
| +7 portfolio (gold AND NQ+gold) | **0** |

Base rates: P(T2 PF >= 1.2 | T1 pass) = 21.2 % vs 10.5 % for every config with T1 n >= 80 (17.8 % for configs with T1 PF 1.0-1.2).
P(A & B >= 1.0 | T1 & T2 pass) = 19.4 % vs 7.7 % base. T1 selection carries some information (x2), but 146 -> 6 is close to what
noise plus a mild post-2020 regime would give. Median PF per family (T1 / T2 / A / B) is below 1 for every family except INSIDE_DAY
(1.37 / 1.15 / 1.04 / 1.33, only 48 configs) and PIVOT_FADE(_X) in T1 only. Families with the most T1 passes: RVOL_DRIVE 34 (1 passes T2),
NQ_DRIVE 28 (7), ENGULF_4H 15 (6), CISD_TRITON 11 (1), G_DRIVE 10 (6, none passes A/B), DAY_MR 10 (2), ROUND_NUM 9 (1), INSIDE_DAY 7 (1).
New families (families5-10) contribute DAY_MR, TREND_SCALP (gate 1-4) only; OR_FAIL / RVOL / VOL_CLIMAX / NGA / SQZ / PD_ACCEPT / ER_PERSIST /
ON_POS / PERIOD_OPEN / NDAY_BRK / ZMR / LEG2 / EXH1 / ONHL / SETTLE / STRETCH_SNAP / VWAP_BAND2 / OR_FAIL_X / PIVOT_FADE_X: 0 past gate 3.

## 3. Configs that pass gates 1-4 (T1 / T2 real, A / B norm, +4 ticks T2; plateau)

| fam#j | rule | T1 | T2 | A | B | +4t T2 | plateau (n, median, <1) | g5 |
|---|---|---|---|---|---|---|---|---|
| DAY_MR#47 | IBS <= 0.15 long at 09:30, stop 0.5 ATR, time exit | 126 tr WR 50.8 PF 1.49 | 68 WR 48.5 PF 1.50 | 1.15 | 1.21 | 1.44 | 18, 1.00, 50 % | no |
| NQ_DRIVE#4235 | 10:00 + 120 min move >= 0.35 ATR, continuation w/ trend, stop 0.35 ATR, 2R | 126 WR 52.4 PF 1.44 | 91 WR 56.0 PF 1.44 | 1.01 | 1.01 | 1.34 | 20, 0.91, 60 % | no |
| LATE_MOM#191 | 14:30 RTH move >= 0.5 ATR w/ trend, stop 1.0 ATR, time exit | 120 WR 53.3 PF 1.39 | 75 WR 58.7 PF 1.70 | 1.18 | 1.45 | 1.53 | 15, 0.91, 53 % | no |
| LATE_MOM#190 | same, 1R | 120 WR 53.3 PF 1.32 | 75 WR 58.7 PF 1.70 | 1.18 | 1.50 | 1.53 | 15, 0.99, 53 % | no |
| TREND_SCALP#266 | 12:00 EMA9 pullback scalp w/ trend, stop 0.4 ATR, 0.5R | 103 WR 58.3 PF 1.35 | 55 WR 63.6 PF 2.09 | 1.12 | 1.16 | 1.90 | 9, 1.06, 0 % | no |
| INSIDE_DAY#42 | inside day -> stop entry 1 tick beyond PDH/PDL until 15:00, any dir, stop = min(PD range, 0.25 ATR), 2R, 400 min | 95 WR 56.8 PF 1.38 | 42 WR 57.1 PF 1.42 | 1.04 | 1.34 | 1.32 | 6, 1.36, 0 % | yes |

LATE_MOM 14:30 is the same idea as the gold LATE1430 module tested on 2026-10-05 (gold_curated: rejected then, "LATE_MOM 14:30 DAY x0.5").
Its neighbours are below 1 in half the cells -> isolated cell, as before.

## 4. Current GoldMaster modules through the same gates (regenerated on mgcdb, no FOMC skip, same executor)

| module | T1 real | T2 real | A norm | B norm | +4t T2 | plateau (n, median, <1) | gates passed |
|---|---|---|---|---|---|---|---|
| OD1030 | 140 tr WR 62.1 PF 1.13 | 70 WR 68.6 PF 2.09 | 1.36 | 1.08 | 1.91 | 9, 1.02, 44 % | 2, 3, 4 (fails T1 PF, plateau) |
| ENG0408 | 130 WR 62.3 PF 1.28 | 96 WR 66.7 PF 1.92 | 0.99 | 0.72 | 1.79 | 14, 0.92, 57 % | 2, 4 |
| SVWAP22 | 30 WR 66.7 PF 1.36 | 45 WR 66.7 PF 1.42 | n/a (17) | 1.63 (23) | 1.31 | 8, 0.77, 75 % | 2, 4 (too few trades: 30 in 4 years) |
| ASIA1R | 497 WR 49.9 PF 0.94 | 327 WR 54.4 PF 1.22 | 1.35 | 1.11 | 1.17 | 11, 0.91, 100 % | 2, 3, 4 |
| ENG0206 | 144 WR 64.6 PF 1.36 | 95 WR 61.1 PF 1.19 | 0.80 | 1.04 | 1.12 | 15, 1.23, 47 % | 1, 4 |

None of the five would pass today's protocol (they were chosen on CFD XAU in 2026-10-05, partly with 2024-26 in view). The set lives on
2024-26: gold Robust on mgcdb real $, FOMC skipped, conflict filter: T1 Sharpe 0.49 ($42/month, maxDD $1,671), T2 Sharpe 1.53 ($386/month,
maxDD $1,503). Leave-one-out (dSharpe when the module is removed, gold-only T1/T2 real; NQ+gold T1/T2):
OD1030 -0.06/-0.24 (-0.02/-0.07), ENG0408 -0.22/-0.32 (-0.05/-0.10), SVWAP22 -0.03/-0.09 (+0.01/-0.03), ENG0206 -0.22/+0.00 (-0.02/+0.04),
**ASIA1R +0.58/+0.17 (+0.05/+0.02)** -> in real $ 2020-26 ASIA1R subtracts. But in the cost-normalised view it is the only module that holds
2010-19: Robust norm Sharpe A/B/T1n/T2n 1.01/0.45/0.78/1.13 vs without ASIA1R -0.12/-0.16/1.32/0.96 (WinRate 0.39/-0.23/1.18/1.51).
So removing ASIA1R improves 2020-26 (both periods, real $) and breaks 2010-19 (norm). Not a clean call; no change recommended from this round
(it stays the diversifier that makes Robust "robust" across eras, at the cost of 2020-26 Sharpe).

## 5. Portfolio tests for the one survivor (INSIDE_DAY#42)

Standalone (FOMC skipped): 358 trades 2020-26, WR 55.6 %, PF 1.22, ~$25/month in T2 at 1 MGC, correlation with gold Robust 0.06 / 0.04,
0.1 trades/day.
- gold-only: T1 Sharpe 0.49 -> 0.60 (dSharpe +0.12) but maxDD $1,671 -> $1,790 (**+7.1 % > 5 %**); T2 1.53 -> 1.58 (+0.05), maxDD -7.7 %.
  Block bootstrap (21-day blocks, 1,000 draws) of dSharpe: T1 median +0.09 [p5 -0.19, p95 +0.36], P(gain) 71 %; T2 +0.09 [-0.07, +0.27], 81 %.
- NQ (ultra_d4) + gold Robust: T1 Sharpe 3.518 -> 3.543 (+0.025), T2 4.251 -> 4.267 (+0.016); bootstrap T1 +0.02 [-0.03, +0.06] P(gain) 78 %,
  T2 +0.03 [-0.03, +0.09] 81 %.
Fails gate 7 (gold maxDD T1). Even if accepted it would add ~$25/month and +0.02 Sharpe to NQ+gold: not worth a GoldMaster module.
For the record, the rule in GoldMaster terms: trade only when yesterday's RTH range (09:30-16:00) is inside the day before's range;
from 09:30 to 15:00 ET place a buy stop 1 tick above yesterday's RTH high and a sell stop 1 tick below yesterday's low (first one hit,
one trade per day, no trend filter); stop = min(yesterday's range, 0.25 x daily ATR) from entry; target 2R; time exit 400 min; flat 16:50.

Reference numbers (same engine, FOMC skipped): NQ ultra_d4 alone T1 Sharpe 3.49 / T2 4.06; NQ + gold Robust 3.52 / 4.25 (corr 0.03 / 0.06,
+$47 / +$385 per month, maxDD +7 % / +6 %).

## 6. Verdict

- 65,544 configs on 16 years of real GC futures, every family including the ones added after the original gold mining: **no robust new gold
  module**. 146 pass the T1 gate, 31 survive T2, 6 survive 2010-19, 1 sits on a plateau, 0 pass the portfolio test. The base rate
  P(T2 pass | T1 pass) is 21 % vs 10.5 % for any config, so T1 selection on gold carries little information.
- The current GoldMaster modules would not pass this protocol either: OD1030 / ENG0408 / SVWAP22 are 2024-26 edges (T1 PF 1.13-1.36 with
  30-140 trades, ENG0408 negative in 2010-19), ASIA1R is the only one with 2010-19 support and it loses in 2020-23. Gold remains a
  diversifier (corr ~0.03-0.06 with NQ, +0.03 / +0.19 NQ+gold Sharpe in T1 / T2), not an edge in its own right. Nothing to add; nothing
  to change on the basis of this round.
- Lower drawdown / more trades at the same WR-PF for the whole system will not come from gold mining; this is the second full re-mine
  (2026-10-05 CFD, 2026-10-07 anchored drives, now 2026-10-19 real 16y) with the same answer. Do not re-mine gold without a new ingredient
  (new data type or a different execution model).
