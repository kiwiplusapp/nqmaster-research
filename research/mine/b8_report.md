# Batch 8: four new intraday families on 16 years of real NQ futures (2026-10-17)

Files: `families8.py` (generators), `run_mine_db.py` (now imports `FAMILIES8`), `results_b8.csv`, `trades_b8.pkl`, `b8_select.py` -> `b8_select.json`, `results_b8_staged.csv` (results + stage flags, plateau, +4-tick PF).
Run: `MINE_TAG=b8 MINE_PROCS=3 python3 run_mine_db.py NDAY_BRK ZMR LEG2 EXH1` (2,856 configs, 0 errors, 57 s), then `python3 b8_select.py`.
Data: `nqdb.npz` (real Databento NQ 2010-06..2026-10, forward roll-adjusted). $ per MNQ net of $1.90 commission + 1 tick per side. T1 = 2020-01..2023-12 (real $, the only period used to choose), T2 = 2024-01..2026-10 (real $), A = 2010-14 and B = 2015-19 cost-normalised (0.345% of daily ATR). The portfolio check recomputes T1 from 2020-10-15 with `six_lib` (Ultra base = `six_trades.pkl`).

Lookahead check: every signal uses bars up to the signal bar and the entry is on the next bar through `core.execute`. NDAY_BRK levels were verified against an independent computation on 400 random days (0 mismatches): the level for day d is the max/min of the last N *complete* RTH sessions (last RTH bar open >= 15:59) strictly before d; early-close days are excluded from the window without blocking it.

## Families

| Family | Idea | Grid | Configs |
|---|---|---|---|
| NDAY_BRK | Breakout of the prior N complete RTH days' high/low. Signal: 1m or 5m close beyond level + bk ATR, inside 09:35-11:30 or 09:35-15:00, trend filter on/off. Entry market at the next bar (`mkt`) or resting limit at the level valid 60 min (`rt60`). Stop: level - 0.1 ATR, or fixed 0.2 / 0.3 ATR from the entry price. Target 0.5 / 1 / 2R or time only (15:55). One signal per side per day, max 2 trades. | mkt: N 3/5/10/20 x bk 0/0.05/0.10 x tfb 1/5 x win 2 x tf 2 x stop 3 x R 4; rt60: N 4 x bk 0/0.10 x 1m x win 2 x tf 2 x stop 2 x R 0.5/1/2 | 1,344 |
| ZMR | Midday z-score fade (11:00-14:30, 1m): z = (close - mean of last W closes) / std; first bar with \|z\| >= zt after a reset. Fade toward the mean, any side or only when the fade is with the daily trend. Stop k ATR; target the W-mean or 0.5 / 1 / 2R; hold 90 / 180 min; max 2 a day. | W 30/60/120 x zt 2/2.5/3 x side 2 x k 0.15/0.25/0.35 x tg 4 x hold 2 | 432 |
| LEG2 | First-leg continuation: by T the RTH move >= x ATR; pullback >= p of the leg from its extreme, starting within P min; stop entry 1 tick beyond the high/low of the last 5 one-minute bars (re-issued on every deeper pullback bar), valid E min; stop at the pullback extreme (skip if risk > 0.3 ATR); target 1R / 2R / measured move; flat 15:55; 1 a day. | T 10:15/10:30/11:00 x x 0.25/0.4/0.6 x p 0.3/0.5/0.7 x P 60/120 x tg 3 x tf 2 x E 30/90 | 648 |
| EXH1 | Exhaustion-bar fade (09:34-15:30, 1m or 5m): bar range >= m x median range of the last 60 bars of that timeframe, close within 25% of the extreme, after >= kc consecutive same-direction bars. Fade at the next bar; stop 1 tick beyond the bar extreme (skip if > 0.25 ATR); target 0.5R / 1R / bar midpoint; hold 30 / 60 min; with / against / any daily trend; max 2 a day. | tfb 1/5 x m 2/2.5/3.5/5 x kc 2/3/5 x tg 3 x hold 2 x tf 3 | 432 |

## Protocol (fixed in `b8_select.py` before the run, unchanged afterwards)

- s1: T1 n >= 100, WR >= 55%, PF >= 1.30 (the only stage used to choose).
- s2: T2 PF >= 1.20 and WR >= 53%.
- s3: B (2015-19 norm) PF >= 1.05 and A (2010-14 norm) PF >= 0.95.
- s4: plateau: >= half of the grid neighbours one numeric step away have T1 PF >= 1.15 (ent, tfb, win, tf, stop, side, tg are categorical, not steps).
- s5: stress: T2 with +4 ticks per side (usd - $3 per trade) PF >= 1.10.
- Survivor = s1..s5. If none: the 3 best near-survivors (s1 passers ranked by later stages passed, then T2 PF) go through `six_lib.add_test` at weight 1 (accept only if Ultra Sharpe rises in T1 and T2, 6-year max DD and worst month not worse by > 5%).

## Results per family

| Family | configs | median PF T1 | median PF T2 | median PF A / B (norm) | share PF > 1 T1 / T2 | median WR T1 / T2 | median n T1 | s1 | s2 | s3 | s4 | s5 | P(T2 PF >= 1.2) all | P(T2 PF >= 1.2 given T1 PF >= 1.3, n >= 100) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NDAY_BRK | 1,344 | 0.964 | 1.071 | 0.946 / 1.160 | 32.9% / 70.8% | 48.6 / 50.9 | 299 | 1 | 0 | 0 | 0 | 0 | 15.1% | 0 of 1 |
| ZMR | 432 | 0.915 | 0.986 | 0.832 / 0.907 | 18.1% / 40.0% | 51.0 / 52.3 | 1,018 | 0 | 0 | 0 | 0 | 0 | 0.5% | - (0 configs) |
| LEG2 | 648 | 0.677 | 0.656 | 0.681 / 0.730 | 8.8% / 8.5% | 33.3 / 26.7 | 52 | 0 | 0 | 0 | 0 | 0 | 4.5% | - (0 configs) |
| EXH1 | 432 | 0.783 | 0.655 | 0.631 / 0.688 | 12.0% / 4.6% | 35.5 / 31.2 | 63 | 0 | 0 | 0 | 0 | 0 | 0.0% | - (0 configs) |
| ALL | 2,856 | 0.918 | 0.993 | 0.844 / 0.956 | 22.0% / 42.0% | | | 1 | 0 | 0 | 0 | 0 | 8.2% | 0 of 1 |

"share PF > 1" counts configs with fewer than 20 trades (PF missing) as not > 1. The conditional rate cannot be estimated: only one config in the whole batch has T1 PF >= 1.3 with n >= 100 (the earlier batches had ~20% conditional vs ~6.5% base). Relaxing to T1 PF >= 1.2 (n >= 100) gives 16 configs (14 NDAY_BRK, 2 EXH1) of which 0 reach T2 PF >= 1.2.

**Survivors: none.** Stage counts: s1 = 1, s2..s5 = 0.

### The only s1 passer and the near-survivors (portfolio test, `six_lib.add_test`, w = 1)

The protocol's near-survivor set is the s1 passers, so only one config entered the formal portfolio test (first row). The next four rows are the best remaining NDAY_BRK configs by T1 PF with trades kept (T1 PF >= 1.25) and are shown for information only, outside the protocol. Standalone stats below are the `six_lib` ones (T1 from 2020-10-15); the CSV T1 stats (2020-01..) are in `b8_select.json`.

| j | params | T1 n / WR / PF | T2 n / WR / PF | T2 PF +4 ticks | A / B norm PF | plateau | $/month T1 / T2 | corr | Ultra Sharpe T1 base -> +cand | T2 base -> +cand | maxDD | worst month | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1192 | rt60, N 3, bk 0.10, 1m, 09:35-15:00, no trend, stop fix 0.2 ATR, R 1 | 111 / 59.5 / 1.436 (CSV 133 / 59.4 / 1.421) | 93 / 52.7 / 1.037 | 0.993 | 0.838 / 1.138 | 0.67 | 53 / 7 | -0.004 | 3.453 -> 3.527 | 3.949 -> 3.944 | 4,582 -> 4,607 | -2,210 -> -2,124 | fails s2, s3, s5; Sharpe T2 down |
| 305 | mkt, N 5, bk 0, 1m, 09:35-11:30, with trend, fix 0.2, R 1 | 256 / 59.0 / 1.379 (CSV 333 / 57.1 / 1.288) | 211 / 53.1 / 1.169 | 1.119 | 1.025 / 1.087 | n/a | 107 / 68 | 0.111 | 3.441 -> 3.546 | 3.940 -> 3.923 | 4,582 -> 4,600 | -2,210 -> -2,188 | fails s1 (CSV PF 1.288) and s2 (T2 PF 1.169); Sharpe T2 down |
| 1193 | rt60, N 3, bk 0.10, 1m, 09:35-15:00, no trend, fix 0.2, R 2 | 194 / 44.3 / 1.337 | 155 / 37.4 / 0.899 | 0.868 | 1.001 / 0.869 | n/a | 98 / -41 | 0.054 | 3.441 -> 3.533 | 3.949 -> 3.788 | 4,582 -> 5,053 | -2,210 -> -2,332 | loses in T2 |
| 329 | mkt, N 5, bk 0, 1m, 09:35-15:00, with trend, fix 0.2, R 1 | 302 / 58.3 / 1.374 | 252 / 49.6 / 1.046 | 1.000 | 0.964 / 1.040 | n/a | 123 / 23 | 0.126 | 3.434 -> 3.532 | 3.937 -> 3.849 | 4,582 -> 4,414 | -2,210 -> -2,474 | flat in T2 |
| 594 | mkt, N 10, bk 0, 1m, 09:35-11:30, with trend, fix 0.2, R 2 | 225 / 44.0 / 1.319 | 176 / 37.5 / 1.044 | 1.008 | 0.995 / 1.110 | n/a | 108 / 19 | 0.182 | 3.441 -> 3.452 | 3.943 -> 3.783 | 4,582 -> 4,503 | -2,210 -> -2,239 | flat in T2 |

Every candidate raises Ultra's Sharpe in T1 (where it was chosen) and lowers it in T2. None is accepted.

## Verdict per family

**NDAY_BRK** - The most "alive" family, but there is no robust cell. Median PF 0.96 in T1 and 1.07 in T2 (71% of configs > 1 in T2, mostly through the longs of 2024-26), B 1.16 and A 0.95 cost-normalised: a weak, regime-dependent continuation effect, in line with the known post-2020 trend regime. The market-entry/fixed-stop/no-break-buffer cells (bk 0, stop fix 0.2 ATR, 1m closes) sit at the top in T1 (PF 1.2-1.3, WR 55-59% at R 1) but decay to PF 1.04-1.17 in T2 and do not survive +4 ticks; the retest variant (resting limit) has the best T1 cell (j 1192, PF 1.42) that is flat in T2 (1.04) and loses in A. 5-minute closes and bk > 0 do not help (T1 median 0.93-0.95). The behaviour across N, window and R is flat (medians 0.91-1.00). It overlaps with ORB60/ORB90/PD_ACCEPT (same breakout-with-trend idea), which explains the T1-only Sharpe gain. Rejected.

**ZMR** - Midday z-score fading loses with costs: median PF 0.92 / 0.99 / 0.83 / 0.91 (T1 / T2 / A / B), 0 configs with T1 PF >= 1.2. The best cells are the ones that trade WITH the daily trend (side 1 median 0.96 vs 0.88) at zt 3 with R 2 targets, i.e. the least "mean reversion" in the grid, and even those reach only PF 1.10-1.16 in T1 and ~1.0 in T2 with 450-1,000 trades. The signal is a 1-minute noise fade (avg trade a few $) and the $1.90 + 2 ticks cost eats it. Rejected; consistent with the earlier mean-reversion research (2026-09-27, 840 configs) and DAY_MR.

**LEG2** - First-leg pullback continuation fails outright: median PF 0.68 / 0.66 / 0.68 / 0.73, 9% of configs > 1 in either period, WR 27-33%. The entry (stop above the last 5-minute swing after a 30-70% pullback) buys the top of the bounce and the structure stop at the pullback extreme is hit far more often than the 1R/2R/measured-move target. The only cells near break-even are T 10:15, x 0.25, measured-move target with trend (T1 PF 1.06-1.12, T2 0.9-1.2, A 0.65-0.9), with 100-170 trades and no plateau. Rejected; the project's ORB60-pullback-day and MOM1030 already capture the first-hour continuation with better fills.

**EXH1** - Exhaustion-bar fading is the worst family: median PF 0.78 / 0.66 / 0.63 / 0.69, 0 of 432 configs with T2 PF >= 1.2, and the only T1 cells above 1.2 (1m, m 2, kc 2, fade AGAINST the daily trend, midpoint target, 113 trades) are 0.65 in A and 1.09 in T2. Large bars that close on their extreme after a run are continuation, not exhaustion, on NQ (the against-trend fade is the least bad in T2 only because 2024-26 had many fast pullbacks). Rejected; same conclusion as VOL_CLIMAX (batch 5).

## Overall

0 survivors of 2,856 configs; the batch did not even produce a conditional-lift estimate because only one config met the T1 bar (1.3 PF with 55% WR and 100 trades), versus 364 of 4,764 in batch 7 and 195 of 45k in the 16-year miner. None of these four ideas adds to Ultra: the only mild positive (NDAY_BRK N 5, market entry with trend, fixed 0.2-ATR stop, 1R) is a weaker, correlated copy of the existing opening-range breakout modules and its T2 edge (PF 1.17, +$68/month per contract) disappears with 4 ticks of extra slippage and lowers Ultra's T2 Sharpe. Nothing to port to NQMaster. Do not re-mine N-day breakouts, midday z-score fades, first-leg pullback stops or exhaustion-bar fades on NQ without a new ingredient (e.g. order-flow confirmation with new data).
