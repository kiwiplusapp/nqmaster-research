# Batch 13: double top / bottom liquidity sweep and IB to VWAP (2026-10-21)

Federico brought two strategies from videos. This batch tests them with the same protocol as batch 11, on real Databento NQ futures (`research/data/nqdb.npz`, 2010-06..2026-10).
- Costs: $ per MNQ including $1.90 commission and 1 tick per side.
- 2010-18: a cost-normalised view (0.345% of the daily ATR).
- Generators: `research/mine/families13.py`, 5 families, 3,600 cells, registered in `run_mine_db.py` as `FAMILIES13`.
- Mining run: `MINE_TAG=b13 MINE_PROCS=2 MINE_T1=20190101 MINE_T2=20230101 MINE_KEEP_N=60 python3 run_mine_db.py DT_CONT DT_REV IB_FADE IB_BREAK IB_RECLAIM`. It took 62 s with 0 errors and wrote `results_b13.csv` and `trades_b13.pkl` (19 MB).
- Selection: `b13_select.py` -> `b13_select.json`, `results_b13_staged.csv`.
- Lookahead check: `b13_lookahead.py` -> `b13_lookahead.json`.

## Pre-registered protocol (fixed in `b13_select.py` before `results_b13.csv` was opened; identical to batch 11)

- **Periods.**
  - T1 = 2019-01..2022-12: used to choose, on real $ and on the cost-normalised view T1n.
  - T2 = 2023-01..2026-10: used to check.
  - A = 2010-14 and B = 2015-18, cost-normalised: regime check.
- **Stages.**
  - s1 (choose): T1 n >= 80, PF >= 1.30, WR >= 50, and T1n PF >= 1.15.
  - s2: T2 PF >= 1.20.
  - s3: A PF >= 1.0 and B PF >= 1.0.
  - s4: T2 PF >= 1.10 with +4 ticks per side.
  - s5 (plateau): at least 2/3 of the one-step numeric neighbours have T1 PF >= 1.15.
  - s6: one representative per signal. Exits (st / R / tgt / sk / tg / wait) and the context filters (filt / ctx / tf) do not count as a separate signal.
- **Portfolio test**, run for each representative on NQMaster days (ATR >= 150, no FOMC):
  - Base: raw `ultra_d4`, passed through `wrq_port.conflict_filter`.
  - T1p = 2020-10-15..2022-12, T2p = 2023-01..
  - Pass needs all of: Sharpe up in both periods; max DD and worst month no more than 5% worse; daily-P&L correlation < 0.3.
  - Also reported: a 21-day block bootstrap of the Sharpe gain (1,000 draws).
- **Also reported:**
  - base rates P(T2 PF >= 1.2) overall and given s1;
  - continuation vs reversal;
  - each filter (none / VWAP / SMA200 / daily trend);
  - the base system on sweep days vs other days.

## What was tested (families13.py)

| family | rule | cells |
|---|---|---|
| DT_CONT | Double top / bottom on 5m or 15m pivots (k 2 / 5 bars each side). Pivots 3..60 bars apart and level-matched within 4 ticks or 0.02 / 0.05 / 0.10 ATR. The level is untouched between the pivots and the pattern is >= 0.10 ATR deep. Setups may start in the prior session. **The sweep is the move** (the video's reading): stop entry at level + 1 tick / 0.05 ATR, stop at the pattern mid or 0.25 ATR, target 1R / 2R / hold to 15:55. | 1,536 |
| DT_REV | Same patterns. **Sweep then fade**, two ways: a stop back through the level after the sweep bar, with the stop at the sweep extreme + 0.05 ATR; or a limit at the sweep level, with a 0.25 ATR stop. Target 0.5R / 1.5R / pattern mid. | 1,536 |
| (both DT) | Windows: RTH (sweep 09:35-15:29, flat 15:55) or overnight (18:00-09:28, out at 09:29). Context filters: none, VWAP side (RTH VWAP in RTH, session VWAP overnight), SMA200 of the tf bars, house daily trend. A setup lives 60 tf bars; the first sweep consumes it; max 2 trades per day. | |
| IB_FADE | IB = first 30 / 60 min. Touch of the IB high / low + 0 / 0.05 / 0.1 ATR, then fade with a limit target at the RTH VWAP. Only taken if the VWAP is >= 0.1 / 0.2 / 0.3 ATR away. Stop 0.15 / 0.25 / 0.35 ATR, or 2x the distance to VWAP capped at 0.5 ATR. Entry by limit or market; optional only-against-the-daily-trend filter. Until 15:00. | 288 |
| IB_BREAK | OCO break of the IB extreme by 1 tick / 0.05 / 0.1 ATR. Context: none / daily trend / price-vs-VWAP / both. Stop at the IB mid or the opposite side. Target 1R, 2R, or 1x the IB range. | 144 |
| IB_RECLAIM | IB break, then a 1m close back across the RTH VWAP within 60 / 120 min -> trade toward the other IB side (or 1R / 2R). Stop at the sweep extreme + 0.05 ATR or 0.25 ATR; optional with-trend filter. | 96 |

- **Fills.** Every fill goes through `core.execute`:
  - market orders fill at the next bar open + 1 tick;
  - stop entries fill at max(level, open) + 1 tick;
  - limit entries need a 1-tick trade-through;
  - stop losses fill 1 tick worse.
- **Pivots.** A pivot is confirmed only when tf bar p+k has completed. The setup is armed from the next 1m bar.

## Lookahead check

`b13_lookahead.py` sampled 360 events: 6 cells per family, 12 events each, seeded. For each event, every bar after the signal bar was perturbed (prices +137 points, ranges widened, volume x3). ATR, daily trend, RTH VWAP, session VWAP, tf bars and SMA200 were then recomputed from the perturbed data and the generator re-run. The event had to keep its direction, type, price, stop, target and expiry.

- **Touch-resolved events** keep the touch bar and are perturbed from i+2. These are the DT_CONT stop entries, DT_REV limit entries, IB_FADE limits and the IB_BREAK OCO, where the signal bar is the bar before the touch, meaning a resting order that exists from the arming bar.
- **Pivots** are therefore shown to use only bars up to the confirming bar p2+k.

**0 violations.**

## Results per family

| family | cells | median PF T1 / T2 / A / B | median WR T1 / T2 | s1 | s2 | s3 | s4 | s5 | P(T2 pass) all | P(T2 pass given s1) |
|---|---|---|---|---|---|---|---|---|---|---|
| DT_CONT | 1,536 | 0.98 / 0.92 / 0.89 / 0.94 | 44.1 / 42.1 | 60 | 0 | 0 | 0 | 0 | 3.0% | 0% (0 of 60) |
| DT_REV | 1,536 | 0.85 / 0.96 / 0.88 / 0.90 | 53.2 / 57.6 | 6 | 4 | 0 | 0 | 0 | 10.0% | 67% (4 of 6) |
| IB_FADE | 288 | 0.81 / 1.01 / 0.85 / 0.86 | 44.8 / 50.5 | 0 | 0 | 0 | 0 | 0 | 3.1% | - |
| IB_BREAK | 144 | 1.11 / 1.04 / 0.98 / 0.92 | 52.8 / 51.4 | 0 | 0 | 0 | 0 | 0 | 4.9% | - |
| IB_RECLAIM | 96 | 0.94 / 0.86 / 1.21 / 1.15 | 47.4 / 45.9 | 0 | 0 | 0 | 0 | 0 | 0% | - |
| ALL | 3,600 | 0.92 / 0.95 / 0.89 / 0.92 | 47.0 / 47.3 | 66 | 4 | 0 | 0 | 0 | 6.0% | 6.1% |

**0 survivors.** 66 cells pass s1 and 4 pass T2; none passes the 2010-18 regime check. Choosing on T1 adds nothing: P(T2 | s1) = 6.1% vs a base rate of 6.0%.

### F1: which reading of the sweep holds?

| reading | share of cells PF > 1, T1 / T2 / A / B | median PF T1 / T2 | median WR T1 / T2 |
|---|---|---|---|
| continuation (the video) | 46% / 24% / 13% / 27% | 0.98 / 0.92 | 44 / 42 |
| reversal (fade the sweep) | 17% / 33% / 14% / 23% | 0.85 / 0.96 | 53 / 58 |

**Neither reading holds.**
- **Continuation:**
  - In 2019-22, RTH continuation looked positive (median PF 1.10, 54 of the 60 s1 cells).
  - It flipped in 2023-26: median 0.87, only 15% of cells above 1, and the s1 cells reach T2 PF 0.83 median, 1.10 at best.
  - It was also below 1 in 2010-18.
- **Reversal:**
  - Reversal is the better side in 2023-26 (WR 57-59%), but loses in 2019-22 and 2010-18.
  - Its best T2 cells are overnight limit fades with the VWAP filter (see near misses).
- **Variants:** 5m vs 15m pivots, tolerance, and k change nothing systematically.

### F1: the role of the filters

| median PF T1 / T2 / A / B | none | VWAP side | SMA200 (tf bars) | daily trend |
|---|---|---|---|---|
| DT_CONT RTH | 1.09 / 0.86 / 0.94 / 0.88 | 1.10 / 0.85 / 0.95 / 0.88 | 1.15 / 0.82 / 0.95 / 0.88 | 0.98 / 1.01 / 0.97 / 0.92 |
| DT_CONT overnight | 0.88 / 0.96 / 0.85 / 0.98 | 0.89 / 0.99 / 0.85 / 0.98 | 0.88 / 0.98 / 0.84 / 0.99 | 0.90 / 0.91 / 0.89 / 0.98 |
| DT_REV RTH | 0.80 / 0.98 / 0.84 / 0.96 | 0.94 / 0.92 / 0.81 / 0.87 (n ~15 per period) | 0.92 / 0.99 / 0.82 / 0.98 | 0.74 / 1.07 / 0.88 / 1.03 |
| DT_REV overnight | 0.89 / 0.88 / 0.91 / 0.86 | 0.89 / 1.05 / 0.91 / 0.80 | 0.90 / 0.91 / 0.92 / 0.87 | 0.89 / 0.94 / 0.94 / 0.84 |

- The VWAP and SMA200 filters of the video add about +0.0..+0.06 of median PF in the period where the side already works, and nothing in the others.
- No filter turns a losing reading into a winning one in more than one period.
- The house daily trend makes RTH continuation flat (about 1.0) instead of negative, and RTH reversal slightly positive in T2 / B only.

### F2: IB to VWAP

- **IB-extreme fade to VWAP:** median PF 0.81 (T1), 1.01 (T2), 0.85 (A), 0.86 (B). Limit and market entries, and only-against-trend, are all the same. WR ~45-51%: the VWAP target is reached less often than the stop.
  - Already rejected as "IB fade" on 2026-09-28; the VWAP target does not rescue it.
- **IB break with context:** median 1.11 / 1.04 / 0.98 / 0.92. The trend or trend + VWAP version is about 1.13 / 1.08 but below 1 in 2010-18; 0 cells reach T1 PF 1.30.
  - It is the opening-range breakout already traded by ORB60 / ORB90 / VOLB, at lower quality.
- **VWAP reclaim after a failed IB break:** median 0.94 / 0.86 / 1.21 / 1.15. It worked in 2010-18 and has stopped working since 2019 (0% of cells pass T2).

## Near misses (best s1 cells, information only; none is a survivor)

| cell | T1 n / WR / PF | T2 n / WR / PF | +4t | A / B | plateau | corr | dSharpe T1p / T2p | bootstrap P > 0 T1p / T2p | portfolio rules |
|---|---|---|---|---|---|---|---|---|---|
| DT_REV#71 5m k2, 4-tick match, overnight, VWAP side, limit at level + 0.05 ATR, target pattern mid | 156 / 66.0 / 1.42 | 85 / 70.6 / 1.84 | 1.72 | 0.80 / 0.87 | 1/3 | -0.02 | +0.038 / +0.071 | 0.84 / 0.99 | pass (DD -14% / -7%) |
| DT_REV#69 same, 0.5R target | 156 / 64.7 / 1.32 | 85 / 69.4 / 1.82 | 1.70 | 0.80 / 0.95 | 1/3 | -0.03 | +0.014 / +0.065 | 0.68 / 0.97 | pass |
| DT_REV#1340 15m k5, 0.02 ATR match, overnight, daily trend, stop back through the level, target mid | 116 / 51.7 / 1.35 | 119 / 58.0 / 1.75 | 1.62 | 0.74 / 1.03 | 1/4 | 0.05 | +0.051 / +0.064 | 0.83 / 0.97 | fail (worst month T1p +16%) |

- **DT_REV#71 / #69: the portfolio test is not the gate.**
  - **Fails the regime check:** PF by year 2010-18 is 0.30 / 0.66 / 0.44 / 0.98 / 0.53 / 1.21 / 0.59 / 0.32 / 0.82, so it lost in 8 of 9 years.
  - **Recent years are mixed:** 2019-26 is 0.95 / 1.12 / 2.75 / 1.21 / 2.66 / 3.77 / 0.75 / 1.24.
  - **Fails the plateau:** only 1 of 3 neighbours holds. Matching at 0.02 ATR instead of 4 ticks gives PF 1.32 / 1.23 and A / B 0.83 / 0.84.
  - **Too rare:** about 25 trades per year.
  - **Why it passes the portfolio test:** it trades at night, when the base has few positions. That is not evidence of an edge.
- **DT_REV#1340** loses in 2010-15 (PF 0.16-0.58 each year) and sits on no plateau.
- **All three together (information only):**
  - Sharpe +0.05 / +0.18, max DD -7% / -13%, worst month -8% / -10%;
  - $867 + $6,021 per contract, almost all from 2023-24.

## The house system on double-sweep days

Sweep days are days with an RTH double top / bottom sweep, using the canonical cell: k 2, 0.05 ATR match, sweep by 1 tick, no filter. The base is `ultra_d4`, conflict-filtered, on NQMaster days.

| pivots | period | sweep days (share) | WR / PF / $ per day | other days | WR / PF / $ per day |
|---|---|---|---|---|---|
| 5m | T1p | 507 (95%) | 66.7 / 1.58 / 118 | 29 | 62.8 / 1.21 / 39 |
| 5m | T2p | 877 (93%) | 64.6 / 1.43 / 104 | 65 | 64.1 / 1.75 / 128 |
| 15m | T1p | 338 (63%) | 64.9 / 1.40 / 84 | 198 | 69.0 / 1.90 / 164 |
| 15m | T2p | 560 (59%) | 65.2 / 1.44 / 100 | 382 | 63.6 / 1.45 / 114 |

- On 5m pivots a double-top / bottom sweep happens on 93-95% of days, so it is not a day type.
- On 15m pivots the base did worse on sweep days in 2020-22 (PF 1.40 vs 1.90). In 2023-26 the two groups are equal (1.44 vs 1.45). **There is no stable day-filter effect.**

## Verdict

- **Nothing is added to NQMaster.** 0 of 3,600 cells survive the pre-registered protocol (66 pass s1, 4 pass T2, 0 pass the 2010-18 check).
- **Double top / bottom liquidity sweep:**
  - Continuation (the video's reading: break of the equal highs / lows = the move) loses on 16 years of real NQ: median PF 0.89-0.98 in 3 of 4 periods. Its 2019-22 RTH bump flipped in 2023-26.
  - Reversal (fade the sweep) is the better side only in 2023-26 and loses in 2010-22.
  - VWAP-side and SMA200 filters change PF by a few hundredths.
  - The equal-highs / equal-lows "liquidity pool" carries no exploitable direction on NQ. Choosing on 2019-22 predicted 2023-26 at chance (6.1% vs 6.0% base rate).
- **IB to VWAP:**
  - The IB-extreme fade with a VWAP target has median PF 0.81-1.01: no edge, consistent with the earlier IB fade rejection.
  - The IB break with trend / VWAP context is a weaker copy of ORB60 / ORB90 / VOLB.
  - The VWAP reclaim after a failed IB break was an edge only before 2019 (A / B 1.21 / 1.15, T1 / T2 0.94 / 0.86).
- **Watch list (no action):** the overnight double-bottom / top limit fade with the session-VWAP filter (DT_REV#71) gained in 2021-24. Its 2010-18 record is 8 losing years out of 9, its plateau is thin, and it gives about 25 trades per year: this is the pattern of the post-2020 artefacts rejected before.
- **Exact NQMaster rule:** none, because nothing survived.

**Do not re-mine:** equal highs / lows (double top / bottom) sweeps in either direction, with or without VWAP / SMA200 / trend filters; IB fade to VWAP; IB break with VWAP context; VWAP reclaim after an IB break.

Files in `research/mine/`:
- `families13.py`
- `b13_lookahead.py`, `b13_lookahead.json`
- `b13_select.py`, `b13_select.json`
- `results_b13.csv`, `results_b13_staged.csv`
- `trades_b13.pkl`
- `b13_report.md`

`run_mine_db.py` now registers `FAMILIES13`.
