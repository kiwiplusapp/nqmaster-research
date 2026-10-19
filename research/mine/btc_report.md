# Bitcoin (CME micro BTC, MBT) as a third instrument — research report, 2026-10-19

Goal (Federico): lower drawdown, more trades, same-or-better WR / PF for the whole system without overfitting, through an
uncorrelated instrument (gold raised the portfolio Sharpe 3.61 -> 3.89). Candidate: micro Bitcoin futures (MBT), proxied by
free Binance spot BTCUSDT 1-minute data (spot tracks CME BTC futures at ~0.99 one-minute correlation).

**Verdict: nothing survives. 65,544 configurations of 50 families (every NQ family plus the gold / clock / anchored-drive
families) and a 6,768-cell time-of-day map produce ZERO Bitcoin modules that pass the pre-registered protocol. The reason is
cost: at $3.00 commission + 1 tick per side, the round trip is 1.47 % of the daily ATR in 2024-26 (MNQ 0.42 %; MES 1.27 %, where
nothing survived either), 4.0 % in 2020-23 and 12.6 % in 2017-19. The zero-cost run shows that the gross patterns are also
weaker than on NQ (section 6). Lucid does not list MBT at all; MFFU allows it at $3.50 round trip but counts it as a MINI
contract. No change to NQMaster / GoldMaster is proposed.**

## 1. Data

| item | value |
|---|---|
| source | data.binance.vision, spot BTCUSDT 1m klines, monthly zips 2017-08 .. 2026-09 + daily zips 2026-10-01..18 (128 files, 226 MB raw, 4,815,199 bars) |
| conversion | `research/mine/btc_prep.py` (run with `python3 -I`): bar OPEN time UTC -> ET; session date = ET + 6 h (18:00 ET start, like NQ); 17:00-18:00 ET and Sat/Sun dropped; sessions absent from `nqdb.npz` (CME holidays, 23 days) dropped so the calendar equals NQ's; 0 bad OHLC rows |
| output | `research/data/btc_1m.npz` (3,261,503 bars, 2,370 sessions 2017-08-17 -> 2026-10-19, 1,380 bars per session, 209 MB; stored as `btc_1m.npz.xz` 40 MB, manifest + .gitignore updated by `tools/compress_data.py`) |
| scale | price / 20: one research tick 0.25 = $5 of BTC price = one MBT tick ($0.50); one research point = $2.00 per MBT (pv 2.0, like MNQ) |
| costs | `core.Data`: `comm = 3.00` for names starting with `btc` (others stay $1.90), slippage 1 tick per side as everywhere; `split_stats` got a `btc` branch (A < 2020 / T1 2020-23 / T2 2024+). No behaviour change for any other instrument |
| sanity | every session opens at 18:00 ET and ends 16:59; sessions Mon-Fri 470-477 each; prices match the record (2021-04-14 high $64,854, 2024-03-14 high $73,777, 2025-01-23 high $106,850); 0 NQ sessions missing in the BTC calendar |
| caveats | Binance spot ≠ CME: no basis / funding, no CME settlement and roll behaviour, no exchange outages / halts, and Binance volume is not CME volume (volume-based families RVOL_DRIVE / VOL_CLIMAX / VOL_BREAK use it). Fills are 1-minute OHLC fills, the same optimistic model as the rest of the research |

### Daily ATR and the cost ratio (the key number)

ATR = the project's RTH-anchored 14-day EWM true range (`ict.day_levels`), same definition behind MNQ 0.42 % / MES 1.27 % / gold 0.96 %.
Round-trip cost per MBT = $3.00 + 2 x $0.50 = $4.00.

| year | sessions | ATR $/MBT (median) | ATR in BTC $ | full-session range $/MBT | cost / ATR | cost / full range |
|---|---|---|---|---|---|---|
| 2017 (Aug-) | 94 | 32 | 319 | 43 | 12.6 % | 9.3 % |
| 2018 | 258 | 32 | 323 | 37 | 12.4 % | 10.9 % |
| 2019 | 258 | 31 | 310 | 31 | 12.9 % | 12.8 % |
| 2020 | 259 | 35 | 355 | 43 | 11.3 % | 9.2 % |
| 2021 | 259 | 258 | 2,581 | 303 | 1.55 % | 1.32 % |
| 2022 | 258 | 132 | 1,316 | 133 | 3.04 % | 3.01 % |
| 2023 | 258 | 86 | 864 | 91 | 4.63 % | 4.39 % |
| 2024 | 259 | 245 | 2,450 | 266 | 1.63 % | 1.50 % |
| 2025 | 258 | 341 | 3,410 | 345 | 1.17 % | 1.16 % |
| 2026 (-Oct) | 207 | 231 | 2,310 | 246 | 1.73 % | 1.63 % |

Period medians: **T2 2024-26 cost/ATR 1.47 %** (mean-based 1.41 %), T1 2020-23 4.04 %, A 2017-19 12.6 %. MNQ 2024-26 on the same
definition: 0.42 %. MBT is 3.5x more expensive to trade than MNQ relative to its daily range today, and was 10-30x more
expensive before 2021. With MFFU's $3.50 commission the T2 ratio is 1.65 %. The cost-normalised runs below use 1.47 % of ATR
(BTC's own current ratio, the analogue of NQ's 0.345 %).

## 2. Mining (`run_mine_btc.py`, thin wrapper over `run_mine_db.py`)

- 65,544 configurations, 50 families (all NQ families 1-10 incl. the gold families G_DRIVE / G_ORB, the clock families
  CLOCK_ANCHOR / NQ_DRIVE / NQ_ORB / LATE_MOM / OPEN_DRIVE; `families10` was added to `run_mine_db.py` by another agent during
  this session and ran too), 2 processes, 641 s, 0 errors. Flat 15:55 ET, max 1 trade per day per config (per family rule).
- Columns per config: real $ per MBT T1 2020-23 / T2 2024-26; cost-normalised (1.47 % ATR, P&L in % of ATR) A 2017-08..2019,
  T1n, T2n. Outputs `results_btc.csv`, `trades_btc.pkl` (trade lists of configs with T1 n >= 80 and PF >= 1.25).
- Median PF: A 0.77 (norm), T1 0.66, T2 0.83, T1n 0.78, T2n 0.81. For reference the NQ real-futures run has median T1 / T2 PF ~0.9-1.0.

### Time-of-day map (`btc_tmap.py`, 6,768 cells, like `tmom.py` / `gold_tmom.py`)

29 clock times x lookback (30/60/120/240 min, session open, RTH open) x momentum/reversal x stop 0.15/0.30 ATR x target
0.5/1/2 R x hold 120/unlimited x trend filter. Median PF: A 0.29 (real), 0.83 (norm), T1 0.66, T2 0.82. Share of cells with a
positive net: A 0 %, T1 0.3 %, T2 7.3 %. Cells with PF >= 1.3 and n >= 100: A 0, T1 0, T2 0. Stage-1 passes: 0. No clock time
is special (per-hour median T1 PF 0.46-0.73, T2 0.69-0.87); the 16:00 settlement, 18:00 reopen, Sunday reopen, Asian / London
opens and the US open show nothing after costs.

## 3. Selection protocol (fixed before looking at T2, `btc_select.py`)

1. T1 (real 2020-23): n >= 100, WR >= 55 %, PF >= 1.30.
2. T2 (real 2024-26) PF >= 1.20 (n >= 30); A 2017-19 cost-normalised PF >= 1.00 (n >= 30); +4 ticks per round trip ($2 extra per
   trade) T2 PF >= 1.10; plateau: every one-step neighbour cell has T1 PF >= 1.15.
3. Luck check: P(stage 2 | stage 1) vs the unconditional rate.
4. Portfolio: daily $ per MBT added to the 2027 NQ default (`nt_compare` set `ultra_d4`, 1 base contract, 2020-10-15..2026-10);
   accept only if Sharpe rises in T1 AND T2, max DD and worst month not worse by > 5 %, daily correlation < 0.3; 21-day block
   bootstrap of the Sharpe gain.

| stage | configs |
|---|---|
| all | 65,544 |
| 1 (T1) | 52 (G_DRIVE 13, ENGULF_4H 9, NQ_DRIVE 7, ONHL_TEST 6, RVOL_DRIVE 5, OPEN_DRIVE 4, ER_PERSIST 4, TREND_SCALP 3, ROUND_NUM 1) |
| 1 + 2 (T2 and A) | 2 (G_DRIVE 405, NQ_DRIVE 3616) |
| 1 + 2 + 3 (+4 ticks, plateau) | **0** |

Base rates: P(T2 PF >= 1.2 | stage 1) = 13.5 % vs P(T2 PF >= 1.2) = 4.9 % over all configs — but 13.8 % for configs whose T1 PF
was merely 1.0-1.2. Passing T1 strongly therefore predicts T2 no better than a mediocre T1 does: the T1 winners are noise.
P(full stage 2 | stage 1) = 3.9 % vs 1.4-1.8 % unconditional (2 configs).

### The two near-survivors (both fail the plateau and are not accepted)

| config | T1 | T2 | A norm | +4 ticks T2 | neighbours |
|---|---|---|---|---|---|
| G_DRIVE 405: 18:00-19:00 move >= 0.2 ATR, continue, stop = window extreme capped 0.35 ATR, 1R, hold 600 | 134 tr WR 57.5 PF 1.49 | 82 tr WR 57.3 PF 1.48 | 1.01 | 1.41 | anchor 20:00 / 03:00 / 08:20 / 09:30 T1 PF 1.11 / 1.20 / 0.67 / 1.13; T 30 / 120 min 1.25 / 0.69; x 0.1 0.96 |
| NQ_DRIVE 3616: 07:00-07:15 move >= 0.1 ATR, FADE, stop 0.35 ATR, 1R, hold 240 | 128 tr WR 61.7 PF 1.36 | 58 tr WR 67.2 PF 2.11 | 1.00 | 2.01 | anchors 06:00 / 05:00 / 04:00 T1 PF 1.11 / 0.96 / 0.73; T 30 / 60 min 1.09 / 1.10; mode +1 0.45 |

Yearly P&L per MBT: G_DRIVE 405 = 2018 -145, 2019 -102, 2020 -186, **2021 +1,139**, 2022 +76, 2023 -3, 2024 -502, **2025 +1,607**,
2026 +148 (two years carry everything, 2017-19 real PF 0.5-1.1). NQ_DRIVE 3616 = 2017-19 all negative, 2020 +127, 2021 +586,
2022 -17, 2023 +57, 2024 +844, 2025 +785, 2026 +51 (~30 trades per year; 2024-25 carry it; 58 T2 trades in 2.8 years).
Portfolio effect of either (daily correlation with NQ -0.04..+0.05): Sharpe T1 3.52 -> 3.56, T2 4.02 -> 4.08-4.10, +$21-51
per month per base contract, block bootstrap of the gain p05 -0.01..+0.03 — i.e. an isolated cell worth $20-50/month that
no honest test can distinguish from zero. Not implemented.

## 4. Portfolio base used (`ultra_d4`, 1 base contract)

| | Sharpe | net | max DD | worst month |
|---|---|---|---|---|
| T1 2020-10-15..2023 | 3.54 | $73,148 | $4,667 | -$1,176 |
| T2 2024..2026-10 | 4.03 | $86,936 | $3,586 | -$2,182 |

No BTC survivor set exists, so there is no "survivor set WR / PF / trades per day / max DD" to report; the two near-survivors
above are the whole candidate list and they are rejected.

## 5. Prop-firm rules for crypto micros (checked 2026-10-19)

| firm | MBT / MET | commission | notes | source |
|---|---|---|---|---|
| Lucid Trading | **not on the approved list** (34 CME contracts: indices, FX, energy, metals, grains; "no BTC, MBT, ETH or MET row") | n/a | Lucid's own FAQ returned 403 to the fetch; the proptradingvibes table was checked against Lucid's page on 2026-10-11 (article first published 2025-12-28) | https://proptradingvibes.com/blog/lucid-trading-approved-products |
| MyFundedFutures (MFFU) | **allowed** (Micro Bitcoin and Micro Ethereum on the official Futures Instrument List; hours Sun-Fri 17:00-16:00 CT with the 16:00-17:00 break; MFFU trading window 18:00-16:10 ET) | **MBT $3.50 round trip**, MET $1.16 RT (MNQ $1.90, MGC $2.20) | "due to volatility, MBT is treated as a MINI contract": it counts toward the mini limit (a 50K account with 3 minis max can hold 3 MBT), not toward the 30-micro allowance; last updated 2026-08-24; the page does not distinguish evaluation from funded | https://help.myfundedfutures.com/en/articles/9735811-futures-instrument-list |

So even with an edge, MBT would only be usable at MFFU, at $3.50 + slippage (1.65 % of ATR), and each MBT would consume one of
the few mini slots the Tier-1 window and the 30-micro cap leave for NQ.

## 6. Zero-cost (gross) run — is it the cost or is there no pattern?

Same 65,544 configs re-run with `MINE_NORM=0` (`results_btc_gross.csv`; the *n columns are then gross P&L in % of ATR, no
commission, no slippage; `btc_gross.py` -> `btc_gross.json`):

| | A 2017-19 | T1 2020-23 | T2 2024-26 |
|---|---|---|---|
| median gross PF | 0.96 | 0.97 | 1.01 |
| share of configs gross PF >= 1 | 31 % | 38 % | 43 % |
| configs gross PF >= 1.3 and n >= 100 | 1,703 (2.6 %) | 2,712 (4.1 %) | 2,573 (3.9 %) |

761 configs pass a gross T1 >= 1.3 / T2 >= 1.2 / A >= 1.0 screen (RVOL_DRIVE 143, PD_ACCEPT 132, G_DRIVE 69, ENGULF_4H 67,
VOL_BREAK 55, G_ORB 45, ...), and gross P(T2 | T1) = 42 % vs 20 % unconditional. So intraday patterns do exist on BTC before
costs (as they do on every instrument with 1-minute OHLC fills), but their size is small: the gross passers earn a median
3.5 % of ATR per trade in T2 and 4.4 % in T1 ($8.8 per MBT per trade in 2024-26, p90 $17), against a round trip of 1.47 %
of ATR today and 4.0 % in 2020-23. The NQ equivalents earn ~$20 gross per MNQ per trade against $2.90. At real cost the
same 761 configs have median PF T1 1.01 / T2 1.16, i.e. the cost takes more than half of the gross edge in the good
regime and all of it in 2020-23 and 2017-19. For reference, the NQ real-futures run has median net PF T1 0.96 / T2 0.92 and
2.1 % of its configs at net T1 PF >= 1.3 (n >= 100); BTC net: 0.35 %.

### Supplementary protocol: T1 judged at today's cost (`btc_select_norm.py` -> `btc_select_norm.json`)

Because the real-cost T1 (2020-23) is a 4 %-of-ATR regime, a second pre-stated pass chose on the cost-normalised T1 columns
(1.47 % of ATR = today's cost): n >= 100, WR >= 55, PF >= 1.3, plateau on the normalised T1; confirmation unchanged (T2 real
PF >= 1.2, A norm >= 1.0, +4 ticks T2 >= 1.1).

| stage | configs |
|---|---|
| 1 (T1 at today's cost) | 160 (ENGULF_4H 42, RVOL_DRIVE 21, ONHL_TEST 17, G_DRIVE 16, NQ_DRIVE 15, G_ORB 9, TREND_SCALP 9, ...) |
| 1 + 2 | 9 (ENGULF_4H 2, G_DRIVE 2, NQ_DRIVE 2, RVOL_DRIVE 2, PD_ACCEPT 1) |
| + plateau and +4 ticks | **0** |

P(T2 PF >= 1.2 | stage 1) = 11.9 % vs 12.9 % for configs with normalised T1 PF 1.0-1.2: again no predictive value. The four
stage-1+2 configs with stored trade lists are the same NQ_DRIVE 07:00 fade (j 3616 / 3617) and G_DRIVE 18:00 cells as above plus
G_DRIVE 3570 (03:00 London drive, T2 62 trades); every one is an isolated cell (neighbour fails), adds +0.02-0.08 Sharpe and
$12-51 per month per contract, and none is accepted. (86 of the 160 stage-1 configs have no stored trade list because the
miner keeps trades only for real-cost T1 PF >= 1.25; their T2 / A numbers come from the results table and none passes the
plateau either.)

## 7. Honest verdict

- Bitcoin at MBT cost cannot carry the project's 1-minute bracket modules: the round trip eats 1.5 % of the daily ATR today
  (3.5x MNQ) and 4-13 % before 2021, so the T1 selection period is already a cost-dominated regime and 2017-19 is unusable
  except cost-normalised. Of 65,544 + 6,768 configurations, 52 pass T1, 2 pass T2 + 2017-19, 0 pass the plateau; the T1
  winners predict T2 no better than mediocre configs (13.5 % vs 13.8 %).
- The expected diversification benefit is real in principle (daily correlation with the NQ book is ~0), but a diversifier
  needs its own positive expectancy; none was found, so adding BTC would add variance, not Sharpe.
- Firms: Lucid does not offer MBT; MFFU does, but as a mini-slot contract at $3.50 RT.
- Nothing is proposed for NQMaster. If BTC is revisited, it needs a different ingredient, not a re-run of these families:
  (a) lower-frequency holding (multi-day swing, where 1.5 % cost per trip is survivable) — outside the prop-firm intraday
  frame, or (b) CME-native effects that spot cannot show (basis, settlement prints, roll), which need real MBT data
  (BarExporterUTC from NinjaTrader or Databento MBT, not bought in this session).

## Files

- `research/mine/btc_download.py` (Binance monthly/daily zips -> scratchpad `btc_raw/`), `btc_prep.py` (zips -> `research/data/btc_1m.npz`),
  `research/data/btc_1m.npz.xz` (+ manifest / .gitignore entries), `research/mine/core.py` (btc pv / comm / split_stats; other instruments unchanged).
- `run_mine_btc.py` -> `results_btc.csv`, `trades_btc.pkl` (net), `results_btc_gross.csv`, `trades_btc_gross.pkl` (zero cost), `btc_gross.py` -> `btc_gross.json`.
- `btc_tmap.py` -> `btc_tmap.csv`.
- `btc_select.py` -> `btc_select.json`, `btc_finalists.csv`.
- This report `btc_report.md`. Nothing committed; NQMaster.cs / GoldMaster.cs untouched; no Databento credit used.
