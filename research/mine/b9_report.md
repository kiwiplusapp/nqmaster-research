# Batch 9: high win rate / negative reward-to-risk families on 16 years of real NQ futures (2026-10-19)

Federico's request: new modules with a HIGH win rate and a NEGATIVE reward-to-risk (target smaller than stop) that would hold in 2026-27.

Files:
- `families9.py`: the generators.
- `run_mine_db.py`: now imports `FAMILIES9` the same way as `FAMILIES8`.
- `results_b9.csv` and `trades_b9.pkl`: the mining output.
- `b9_select.py` writes `b9_select.json` and `results_b9_staged.csv` (stage flags, plateau, +4-tick PF).

Run: `MINE_TAG=b9 MINE_PROCS=3 python3 run_mine_db.py ROUND_NUM ONHL_TEST SETTLE TREND_SCALP STRETCH_SNAP` (2,196 configs, 0 errors, 38 s), then `python3 b9_select.py`.

Data: `nqdb.npz` (real Databento NQ 2010-06..2026-10, forward roll-adjusted). P&L is $ per MNQ after $1.90 commission + 1 tick per side.
- T1 = 2020-01..2023-12 (real $). This is the only period used to choose.
- T2 = 2024-01..2026-10 (real $).
- A = 2010-14 and B = 2015-19, cost-normalised (0.345% of daily ATR).

Every config uses a target of r x risk with r in {0.2, 0.3, 0.5}. Break-even WR before costs is 83 / 77 / 67%. All stops are wide: 0.25-0.6 daily ATR, or day structure.

## Lookahead checks

Every check below passed with 0 violations. The check script is in the session scratchpad (`b9_lookahead.py`) and is not part of the repo.

- **Roll carry.** Every roll switch is at 00:00 UTC, before 09:30 ET of the same session, so the carry is constant through RTH.
- **Round levels.** Raw round levels are multiples of the step after adding the carry (300 random days). They are built only from the 09:30 bar open, and signals start at 09:35.
- **Overnight high/low.** ONH/ONL match an independent pandas computation over 18:00-09:29 bars on 400 random days. Every bar used is before the 09:30 bar.
- **Settlement.** It equals the close of the prior session's 15:59 bar (400 random days).
- **Level events.** Checked on 500 random events each for ONHL_TEST bl / bl / br, SETTLE bl / bm / br and ROUND_NUM bl x2:
  - the level was not touched by any RTH bar from 09:30 through the arming bar;
  - a `bl` arming bar does not itself touch the level;
  - a `bm` signal bar is the first RTH touch;
  - every signal is at or after 09:35.
- **5-minute EMA9.** At each 1m bar it equals the EMA of the last COMPLETED 5m bar (2,000 random bars).
- **STRETCH_SNAP mean and sigma.** Both use only the bars before the signal bar.

All entries go through `core.execute` and start from the next bar or a resting order. Limits need a 1-tick trade-through and are cancelled if the target trades first.

## Families

| Family | Idea | Grid | Configs |
|---|---|---|---|
| ROUND_NUM | First RTH touch of a round number of the RAW price (step 50 / 100 / 250 points; raw = adjusted + roll carry). Levels lie within RTH open +- 2.5 ATR. Approach: price was >= x ATR away from the level in the last 60 min. Bounce entry: a resting limit at the level (`bl`, armed when a non-touching bar closes within 0.5 x target, valid 30 min) or the next bar open after the touch (`bm`). Window 09:35-12:00 / 15:30. Hold 120 min, max 2 a day. | step 3 x mode 2 x x 0.15/0.3/0.5 x tf 2 x k 0.25/0.4/0.6 ATR x r 3 x win 2 | 648 |
| ONHL_TEST | First RTH test of the overnight high/low (18:00-09:29) in 09:35-11:00 / 12:00, after being >= x ATR away since 09:30. Bounce limit (`bl`), bounce at market after the touch (`bm`), or a continuation stop entry 1 tick through the level (`br`). | mode 3 x x 0/0.15/0.3 x tf 2 x k 3 x r 3 x win 2 | 324 |
| SETTLE | First RTH touch of the prior session's 16:00 settlement (prior complete RTH close) after being >= x ATR away since 09:30. Same `bl` / `bm` / `br` entries. Window to 12:00 / 15:30. 1 a day. | mode 3 x x 0.1/0.25/0.4 x tf 2 x k 3 x r 3 x win 2 | 324 |
| TREND_SCALP | Trend day so far: at T the RTH move is >= x ATR and the last close is on the same side of the RTH VWAP. Then buy (sell) the pullback to the 5m EMA9 or the VWAP with a 1-bar limit, re-issued on every 1m bar that closes 0-0.05 ATR on the trend side of the reference. Stop k ATR, or 1 tick beyond the day's opposite RTH extreme (risk 0.1-1.0 ATR). First fill only, entries until 15:00, flat 15:55. | T 10:30/11:00/12:00 x x 0.3/0.5/0.75 x ref 2 x tf 2 x stop k0.25/k0.4/ext x r 3 | 324 |
| STRETCH_SNAP | 11:00-14:30, 5m bars. Signal: dev = close - mean of the previous M closes (30 / 60 min) is >= z x sigma (std of the previous 24 five-minute changes), and >= 75% of dev was made in the last q bars. Fade at the next bar. Re-armed after \|dev\| < 1 sigma. Stop k ATR, hold 30 / 60 min, max 2 a day. | M 2 x z 2/2.5/3/3.5 x q 2/3 x tf 2 x k 0.2/0.3/0.45 x r 3 x hold 2 | 576 |

`tf 1` means the trade direction must agree with the daily trend (prior RTH close vs SMA20). `tf 0` means any direction.

## Protocol

Fixed in `b9_select.py` before the run and not changed afterwards.

- s1: T1 n >= 100, WR >= 70, PF >= 1.25. This is the only choosing stage.
- s2: T2 PF >= 1.15 and WR >= 68.
- s3: B PF >= 1.05 and A PF >= 0.95 (cost-normalised). A missing PF (< 20 trades) counts as a fail.
- s4: plateau. At least half of the grid neighbours one numeric step away have T1 PF >= 1.10. mode, tf, win, ref and stop are categorical, not steps.
- s5: T2 with +4 ticks per side (usd - $3 per trade) PF >= 1.05.
- If there are no survivors, the 3 best near-survivors go to `six_lib.add_test` at w = 1. Near-survivors are the s1 passers ranked by later stages passed, then T2 PF.

## Results per family

| Family | configs | median PF T1 / T2 | median PF A / B (norm) | share PF > 1 T1 / T2 / A / B | median WR T1 / T2 | s1 | s2 | s3 | s4 | s5 | P(T2 passes s2) all | P(T2 passes s2 \| s1) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ROUND_NUM | 648 | 0.936 / 0.859 | 0.873 / 0.878 | 32% / 7% / 25% / 19% | 68.5 / 67.1 | 17 | 1 | 0 | 0 | 0 | 0.3% | 1 of 17 (5.9%) |
| ONHL_TEST | 324 | 0.881 / 1.044 | 0.881 / 0.907 | 8% / 59% / 13% / 21% | 68.7 / 70.1 | 0 | 0 | 0 | 0 | 0 | 22.2% | - |
| SETTLE | 324 | 0.996 / 0.965 | 0.855 / 0.943 | 48% / 46% / 17% / 28% | 71.2 / 68.0 | 18 | 1 | 0 | 0 | 0 | 29.9% | 1 of 18 (5.6%) |
| TREND_SCALP | 324 | 1.001 / 1.006 | 0.809 / 0.808 | 42% / 43% / 14% / 19% | 74.5 / 71.5 | 9 | 1 | 0 | 0 | 0 | 16.7% | 1 of 9 (11.1%) |
| STRETCH_SNAP | 576 | 0.762 / 0.889 | 0.725 / 0.791 | 0% / 11% / 0% / 0% | 58.3 / 62.3 | 0 | 0 | 0 | 0 | 0 | 0.2% | - |
| ALL | 2,196 | 0.883 / 0.902 | 0.801 / 0.844 | 24% / 27% / 14% / 16% | 67.5 / 66.7 | 44 | 3 | 0 | 0 | 0 | 10.3% | 3 of 44 (6.8%) |

**Survivors: none.** Choosing on T1 gives no lift: P(T2 passes | s1) is 6.8%, against a 10.3% base rate.

### WR vs break-even

Medians by target size:

| Family | r 0.2: WR T1 / T2, PF T1 / T2 | r 0.3 | r 0.5 |
|---|---|---|---|
| ROUND_NUM | 77.2 / 75.9, 0.89 / 0.85 | 69.9 / 68.1, 0.92 / 0.86 | 59.4 / 56.9, 0.97 / 0.87 |
| ONHL_TEST | 75.4 / 77.7, 0.83 / 1.03 | 68.9 / 70.7, 0.87 / 1.04 | 57.9 / 60.2, 0.93 / 1.05 |
| SETTLE | 79.3 / 77.7, 1.00 / 1.06 | 72.2 / 68.3, 0.97 / 0.99 | 62.2 / 56.3, 1.01 / 0.88 |
| TREND_SCALP | 80.4 / 80.2, 0.97 / 0.97 | 74.2 / 72.0, 0.98 / 0.99 | 65.9 / 63.0, 1.09 / 1.07 |
| STRETCH_SNAP | 68.5 / 70.3, 0.75 / 0.85 | 59.4 / 62.9, 0.76 / 0.89 | 53.0 / 54.5, 0.77 / 0.92 |

Win rates sit at or just under the break-even for each target size. A smaller target raises WR and lowers PF, which is the same pattern as `negrr_lab` on the existing modules.

### Near-survivors (portfolio test, `six_lib.add_test`, w = 1)

How to read this table:
- Standalone stats come from the CSV (T1 from 2020-01).
- "$/month" and the Ultra metrics come from `six_lib` (T1 from 2020-10-15).
- "A / B" is the cost-normalised PF for 2010-14 / 2015-19.
- None of these is a survivor. Each fails s3 (2010-19), so the portfolio column is information only.

| config | T1 n / WR / PF | T2 n / WR / PF | T2 PF +4t | A / B norm PF | plateau | avg win / loss T2 | $/month T1 / T2 | corr | Ultra Sharpe T1 | Ultra Sharpe T2 | max DD 6y | worst month | stages failed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TREND_SCALP j258: T 12:00, x 0.5, ref EMA9 5m, any side, stop beyond day's opposite extreme, r 0.2 | 200 / 79.0 / 1.569 | 133 / 73.7 / 1.402 | 1.339 | 0.794 / 0.974 | 0.75 | +$99 / -$198 | 73 / 84 | 0.128 | 3.441 -> 3.451 | 3.949 -> 3.988 | 4,582 -> 4,378 | -2,210 -> -2,177 | s3 (A and B) |
| ROUND_NUM j420: step 100, bounce at market after the first touch, approach >= 0.5 ATR in 60 min, with trend, stop 0.4 ATR, r 0.2, 09:35-12:00 | 216 / 84.3 / 1.301 | 209 / 82.3 / 1.158 | 1.083 | 1.040 (n 39) / 0.889 | 0.50 | +$57 / -$228 | 46 / 40 | -0.070 | 3.448 -> 3.533 | 3.952 -> 4.023 | 4,582 -> 4,438 | -2,210 -> -2,003 | s3 (B) |
| SETTLE j79: bounce limit at the prior settlement after being >= 0.4 ATR away, any side, stop 0.4 ATR, r 0.2, 09:35-15:30 | 115 / 81.7 / 1.394 | 69 / 85.5 / 1.815 | 1.685 | 0.648 / 0.798 | 0.25 | +$54 / -$176 | 26 / 43 | -0.022 | 3.462 -> 3.521 | 3.946 -> 3.998 | 4,582 -> 4,453 | -2,210 -> -2,277 | s3 (A and B), s4 |

**Yearly PF.** 2010-19 is cost-normalised; 2020-26 is real.
- TREND_SCALP j258: 0.61 / 0.80 / 0.97 / 0.82 / 0.70 / 0.88 / 1.02 / 0.58 / 1.67 / 0.97, then 3.04 / 1.93 / 1.81 / 0.87 / 1.98 / 1.69 / 0.98.
- ROUND_NUM j420 (2-27 trades a year before 2020): 0.41 / 1.11 / 0.81 / 1.02 / 2.27 / 3.17 / 0.36 / 0.54 / 3.21 / 0.74, then 1.01 / 1.01 / 2.55 / 0.98 / 0.94 / 1.42 / 1.16.
- SETTLE j79: 0.51 / 0.49 / 1.51 / 0.36 / 0.90 / 0.33 / 0.87 / 0.56 / 1.20 / 1.16, then 1.28 / 1.27 / 3.61 / 0.79 / 1.35 / 1.09 / no losses in 15 trades.

All three raise Ultra's Sharpe in T1 and T2, but the gain is what any small positive, uncorrelated stream adds. They were also picked after T2 was visible: the near-survivor ranking uses the T2 stages. They are therefore not accepted.

## Verdict per family

**ROUND_NUM.** Rejected.
- Fading the first touch of a round number with a wide stop does not make money. Median PF is 0.94 / 0.86 / 0.87 / 0.88 (T1 / T2 / A / B), and only 7% of configs have T2 PF > 1. 17 configs pass T1; 1 holds T2.
- The best cell is j420: step 100, market bounce after a >= 0.5 ATR approach, with trend, r 0.2. It has WR 84 / 82% but PF only 1.30 / 1.16, +4t 1.08, B 0.89, about $40 a month per contract. The win/loss shape is +$57 / -$228, so 4 wins pay for 1 loss and the edge is a few ticks.
- In 2010-14 the 100/250-point levels sit far apart relative to an ATR of 30-50 points, so A has few trades.
- NQ does not respect round numbers more than any other price.

**ONHL_TEST.** Rejected.
- No config passes T1: 0 of 324, and only 8% have T1 PF > 1. Median PF is 0.88 / 1.04 / 0.88 / 0.91.
- T2 looks better (59% of configs > 1), mostly in the continuation (`br`, median T2 1.11 vs T1 0.86). That is the 2024-26 trend regime, not a level effect.
- Overnight-extreme bounces are break-even before costs at every target size.

**SETTLE.** Rejected.
- The settlement bounce has the highest WRs (79% median at r 0.2) but no edge: median PF 1.00 / 0.97 / 0.86 / 0.94.
- 18 configs pass T1; only 1 (j79, limit bounce, 115 / 69 trades) holds T2. It loses in 2010-19 (0.65 / 0.80) and is an isolated cell (plateau 0.25).
- The continuation through the settlement (`br`) flips from T1 0.85 to T2 1.41: the same trend regime again.

**TREND_SCALP.** Rejected.
- Pullback-to-EMA9/VWAP scalps on trend days so far: median PF 1.00 / 1.01 real, but 0.81 / 0.81 in 2010-19. Only 14-19% of configs have PF > 1 in 2010-19.
- The best cell (j258: 12:00, x 0.5, EMA9, stop beyond the day's opposite extreme, r 0.2) is the strongest in the batch: WR 79 / 74%, PF 1.57 / 1.40, +4t 1.34, plateau 0.75. It then fails every year 2010-17 except 2016 (PF 0.58-1.02), and 2023 and 2026 are below 1.
- It is another view of the post-2020 intraday-momentum regime that MOM11 / MOM1030 / VW13 already trade (corr 0.13 with Ultra), and adds about $80 a month.
- EMA9 beats VWAP as the reference (T1 median 1.11 vs 0.90). Shrinking r from 0.5 to 0.2 lowers PF.

**STRETCH_SNAP.** Rejected.
- The worst family: 0 of 576 configs have PF > 1 in T1, A or B. Median PF is 0.76 / 0.89 / 0.73 / 0.79, and median WR is 58%, far below break-even for every r.
- Fast midday 5-minute stretches keep going more often than they snap back. This repeats the batch-8 ZMR and the 2026-09-27 mean-reversion results, even with a wide stop and a small target.

## Overall

0 survivors from 2,196 configs. In every family the win rate lands at or below the break-even of its target, so a smaller target only trades PF for WR.

Choosing on T1 does not predict T2: 6.8% vs a 10.3% base rate. The few cells that hold in 2024-26 are post-2020-regime effects that fail 2010-19.

Nothing goes to NQMaster. Do not re-mine without a new ingredient:
- round-number fades;
- overnight-high/low tests;
- settlement touches;
- trend-day EMA/VWAP pullback scalps;
- midday stretch snaps.

This matches `negrr_lab` (2026-10-19): on NQ a negative reward-to-risk buys win rate, not edge.
