# Re-entry (second attempt) after a stop-out — NQMaster Ultra, real NQ 2020-10..2026-10

Protocol: six_lib (T1 2020-10-15..2023 choose, T2 2024.. check; T1 n>=60 & PF>=1.3, T2 PF>=1.2, +4 ticks T2 PF>=1.1, Sharpe up in T1 and T2, maxDD / worst month not worse by >5%).
All candidates start after a base trade that exited by stop loss, same session, same rules, 1 contract, $1.90 + 1 tick per side.

## What exists today (research = NQMaster.cs)

| Module | Trades/day allowed | Re-arm rule |
|---|---|---|
| ORB60 / ORB90 | 2 | after any exit, when a close is back inside the range (nt_v3_replica orb_max 2 = NQMaster o.Trades < 2) |
| MSEQ / MSEQS | unlimited | next valid 5-candle sequence (wr60.sim; NQMaster has no per-day flag) |
| ICT | 3 | another sweep of a different level (max_day 3 / ictTrades < 3); only 1 per day survives in the final set |
| VOLB, CRT11, LON, time modules | 1 | none (volbDone, crt.Done, m.Done) |

Base check: 6911 base rows, 6911 matched to recomputed exits, exit bar equal 6911, P&L equal 6911.

## 1. Core-family generators with maxday 2 / 3

| Module | events | days | max events/day | fills maxday 1 / 2 / 3 |
|---|---|---|---|---|
| VW13 | 392 | 392 | 1 | 392 / 392 / 392 |
| VW13b | 1045 | 1045 | 1 | 1045 / 1045 / 1045 |
| VOLB | 3198 | 3198 | 1 | 3198 / 3198 / 3198 |
| LATE15 | 604 | 604 | 1 | 604 / 604 / 604 |
| LATEFH | 1000 | 1000 | 1 | 1000 / 1000 / 1000 |
| ENG10 | 1227 | 1227 | 1 | 890 / 890 / 890 |
| NF05 | 767 | 767 | 1 | 767 / 767 / 767 |
| LF06 | 692 | 692 | 1 | 692 / 692 / 692 |
| LF0430 | 444 | 444 | 1 | 444 / 444 / 444 |

Every core-family generator emits at most one event per day (the first break / the clock bar), so maxday > 1 adds nothing; a re-entry needs a re-armed generator (VOLB_RE below).

## 2. Existing second attempts in the base (ORB rank 2, MSEQ rank 2+), by the exit of the previous trade

**ORB60**: first trades 270, second+ 35
- after_stop: T1: n 0 WR None PF None $0 / T2: n 2 WR 100.0 PF None $117
- after_target: T1: n 18 WR 88.9 PF 4.051 $1,340 / T2: n 15 WR 73.3 PF 1.498 $523
- all_second: T1: n 18 WR 88.9 PF 4.051 $1,340 / T2: n 17 WR 76.5 PF 1.609 $641
- all_second_plus4t: T1: n 18 WR 88.9 PF 3.888 $1,286 / T2: n 17 WR 76.5 PF 1.554 $590
- portfolio WITHOUT them: Sharpe T1 3.467 -> 3.418, T2 3.955 -> 3.923, maxDD 4582 -> 4999

**ORB90**: first trades 247, second+ 10
- after_target: T1: n 5 WR 100.0 PF None $521 / T2: n 5 WR 80.0 PF 126.386 $552
- all_second: T1: n 5 WR 100.0 PF None $521 / T2: n 5 WR 80.0 PF 126.386 $552
- all_second_plus4t: T1: n 5 WR 100.0 PF None $506 / T2: n 5 WR 80.0 PF 73.527 $537
- portfolio WITHOUT them: Sharpe T1 3.467 -> 3.449, T2 3.955 -> 3.939, maxDD 4582 -> 4582

**MSEQ**: first trades 315, second+ 30
- after_stop: T1: n 1 WR 0.0 PF 0.0 $-94 / T2: n 3 WR 33.3 PF 0.532 $-96
- after_target: T1: n 17 WR 64.7 PF 2.102 $345 / T2: n 9 WR 44.4 PF 0.821 $-35
- all_second: T1: n 18 WR 61.1 PF 1.618 $251 / T2: n 12 WR 41.7 PF 0.674 $-131
- all_second_plus4t: T1: n 18 WR 61.1 PF 1.461 $197 / T2: n 12 WR 41.7 PF 0.605 $-167
- portfolio WITHOUT them: Sharpe T1 3.467 -> 3.456, T2 3.955 -> 3.969, maxDD 4582 -> 4582

Unfiltered orb_max 3 run (2020-10..): ORB60 first-trade stop-outs 56, second trades by previous exit (0 stop / 1 target / 2 time) {'1': 33, '0': 2}; ORB90 48 / {'1': 10}. After a stop the price sits beyond the opposite side of the range, so a close back inside the range plus a new break of the trend side before 13:00 almost never happens: the ORB second attempt after a stop-out is a non-event; the existing second trades follow targets.

## 3. New second-attempt candidates

| Candidate | n | T1 n / WR / PF / $ | T2 n / WR / PF / $ | +4t T2 PF | avg $ T1 / T2 | Sharpe T1 base->comb | Sharpe T2 base->comb | maxDD base->comb | worst mo base->comb | corr | open opp % | base entries blocked ($) | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ORB60_3RD | 1 | 1 / 100.0 / None / 108 | 0 / None / None / 0 | None | 107.9 / nan | 3.467 -> 3.473 | 3.955 -> 3.955 | 4,582 -> 4,582 | -2,210 -> -2,210 | -0.018 | 0.0 | 0 (0) | no |
| VOLB_RE_E | 181 | 93 / 61.3 / 1.524 / 2,264 | 88 / 54.5 / 1.324 / 1,989 | 1.275 | 24.3 / 22.6 | 3.467 -> 3.525 | 3.955 -> 4.016 | 4,582 -> 4,859 | -2,210 -> -1,918 | 0.005 | 1.7 | 6 (-72) | no |
| VOLB_RE_S | 88 | 40 / 60.0 / 1.612 / 1,195 | 48 / 52.1 / 0.982 / -58 | 0.939 | 29.9 / -1.2 | 3.467 -> 3.504 | 3.955 -> 3.953 | 4,582 -> 5,008 | -2,210 -> -2,247 | -0.021 | 4.5 | 4 (-72) | no |
| VOLB_RE_E_k60 | 131 | 68 / 60.3 / 2.367 / 3,747 | 63 / 66.7 / 2.454 / 4,322 | 2.361 | 55.1 / 68.6 | 3.467 -> 3.62 | 3.955 -> 4.112 | 4,582 -> 4,936 | -2,210 -> -2,220 | 0.005 | 0.8 | 7 (403) | no |
| LON_RE | 5 | 4 / 75.0 / 16.899 / 157 | 1 / 100.0 / None / 1 | 0.0 | 39.3 / 0.6 | 3.467 -> 3.475 | 3.955 -> 3.955 | 4,582 -> 4,582 | -2,210 -> -2,210 | -0.014 | 0.0 | 2 (99) | no |
| LON_RE_anydir | 76 | 45 / 37.8 / 0.871 / -274 | 31 / 48.4 / 1.538 / 772 | 1.457 | -6.1 / 24.9 | 3.467 -> 3.453 | 3.955 -> 3.997 | 4,582 -> 4,599 | -2,210 -> -2,348 | -0.046 | 21.1 | 47 (-139) | no |
| NAIVE_S_struct | 718 | 407 / 46.4 / 0.959 / -919 | 311 / 46.9 / 0.872 / -2,918 | 0.835 | -2.3 / -9.4 | 3.467 -> 3.295 | 3.955 -> 3.625 | 4,582 -> 5,710 | -2,210 -> -2,888 | 0.064 | 1.1 | 144 (3,443) | no |
| NAIVE_O_struct | 719 | 408 / 51.7 / 1.072 / 1,537 | 311 / 55.0 / 1.334 / 6,212 | 1.277 | 3.8 / 20.0 | 3.467 -> 3.427 | 3.955 -> 4.217 | 4,582 -> 4,584 | -2,210 -> -1,836 | -0.06 | 15.7 | 176 (4,074) | no |
| NAIVE_S_all | 1509 | 843 / 53.4 / 0.865 / -5,113 | 666 / 55.7 / 0.905 / -3,604 | 0.856 | -6.1 / -5.4 | 3.467 -> 3.002 | 3.955 -> 3.498 | 4,582 -> 6,174 | -2,210 -> -2,732 | 0.106 | 0.7 | 178 (5,909) | no |
| NAIVE_O_all | 1510 | 844 / 57.2 / 1.031 / 1,090 | 666 / 59.9 / 1.177 / 5,906 | 1.115 | 1.3 / 8.9 | 3.467 -> 3.404 | 3.955 -> 4.202 | 4,582 -> 4,870 | -2,210 -> -1,570 | -0.098 | 29.8 | 231 (4,444) | no |

Direction split (same = same direction as the stopped trade):

- ORB60_3RD: same_dir: T1: n 1 WR 100.0 PF None $108 / T2: n 0 WR None PF None $0 | exits {1: 1}
- VOLB_RE_E: same_dir: T1: n 36 WR 58.3 PF 1.519 $1,001 / T2: n 47 WR 51.1 PF 0.978 $-71 | opp_dir: T1: n 57 WR 63.2 PF 1.528 $1,263 / T2: n 41 WR 58.5 PF 1.714 $2,059 | exits {2: 70, 0: 57, 3: 32, 1: 22}
  - NT-feasible subset (no opposite base position open): n 178, T1: n 93 WR 61.3 PF 1.524 $2,264 / T2: n 85 WR 55.3 PF 1.358 $2,115, Sharpe T1 3.467 -> 3.525, T2 3.955 -> 4.023, pass no
- VOLB_RE_S: same_dir: T1: n 40 WR 60.0 PF 1.612 $1,195 / T2: n 48 WR 52.1 PF 0.982 $-58 | exits {2: 39, 0: 28, 3: 15, 1: 6}
  - NT-feasible subset (no opposite base position open): n 84, T1: n 40 WR 60.0 PF 1.612 $1,195 / T2: n 44 WR 52.3 PF 1.018 $55, Sharpe T1 3.467 -> 3.504, T2 3.955 -> 3.959, pass no
- VOLB_RE_E_k60: same_dir: T1: n 27 WR 51.9 PF 1.777 $1,308 / T2: n 31 WR 58.1 PF 1.709 $1,163 | opp_dir: T1: n 41 WR 65.9 PF 3.305 $2,438 / T2: n 32 WR 75.0 PF 3.371 $3,159 | exits {2: 74, 0: 26, 3: 16, 1: 15}
  - NT-feasible subset (no opposite base position open): n 130, T1: n 68 WR 60.3 PF 2.367 $3,747 / T2: n 62 WR 66.1 PF 2.45 $4,312, Sharpe T1 3.467 -> 3.62, T2 3.955 -> 4.112, pass no
- LON_RE: same_dir: T1: n 4 WR 75.0 PF 16.899 $157 / T2: n 1 WR 100.0 PF None $1 | exits {2: 4, 1: 1}
- LON_RE_anydir: same_dir: T1: n 4 WR 75.0 PF 16.899 $157 / T2: n 1 WR 100.0 PF None $1 | opp_dir: T1: n 41 WR 34.1 PF 0.796 $-431 / T2: n 30 WR 46.7 PF 1.537 $772 | exits {0: 39, 2: 24, 1: 13}
  - NT-feasible subset (no opposite base position open): n 60, T1: n 37 WR 37.8 PF 0.938 $-113 / T2: n 23 WR 52.2 PF 1.493 $498, Sharpe T1 3.467 -> 3.459, T2 3.955 -> 3.972, pass no
- NAIVE_S_struct: same_dir: T1: n 407 WR 46.4 PF 0.959 $-919 / T2: n 311 WR 46.9 PF 0.872 $-2,918 | exits {0: 275, 2: 238, 1: 148, 3: 57}
  - NT-feasible subset (no opposite base position open): n 710, T1: n 402 WR 46.5 PF 0.952 $-1,040 / T2: n 308 WR 47.1 PF 0.878 $-2,742, Sharpe T1 3.467 -> 3.285, T2 3.955 -> 3.63, pass no
- NAIVE_O_struct: opp_dir: T1: n 408 WR 51.7 PF 1.072 $1,537 / T2: n 311 WR 55.0 PF 1.334 $6,212 | exits {2: 250, 0: 246, 1: 166, 3: 57}
  - NT-feasible subset (no opposite base position open): n 606, T1: n 342 WR 51.8 PF 1.128 $2,261 / T2: n 264 WR 54.9 PF 1.199 $3,263, Sharpe T1 3.467 -> 3.462, T2 3.955 -> 4.014, pass no
- NAIVE_S_all: same_dir: T1: n 843 WR 53.4 PF 0.865 $-5,113 / T2: n 666 WR 55.7 PF 0.905 $-3,604 | exits {1: 569, 0: 510, 2: 373, 3: 57}
  - NT-feasible subset (no opposite base position open): n 1498, T1: n 836 WR 53.5 PF 0.865 $-5,053 / T2: n 662 WR 55.7 PF 0.907 $-3,492, Sharpe T1 3.467 -> 3.0, T2 3.955 -> 3.499, pass no
- NAIVE_O_all: opp_dir: T1: n 844 WR 57.2 PF 1.031 $1,090 / T2: n 666 WR 59.9 PF 1.177 $5,906 | exits {1: 609, 0: 453, 2: 391, 3: 57}
  - NT-feasible subset (no opposite base position open): n 1060, T1: n 582 WR 56.4 PF 1.071 $1,779 / T2: n 478 WR 61.7 PF 1.183 $4,438, Sharpe T1 3.467 -> 3.415, T2 3.955 -> 4.009, pass no

VOLB re-arm plateau (first trade unchanged; re-armed break level k x prior range, target R; T1 -> T2 as n / WR / PF / $):

- k0.3_R1.0: T1 121 / 64.5 / 1.348 / 1,569 -> T2 103 / 57.3 / 0.995 / -29
- k0.3_R2.0: T1 121 / 64.5 / 1.466 / 2,099 -> T2 104 / 56.7 / 1.059 / 376
- k0.45_R1.0: T1 93 / 61.3 / 1.388 / 1,677 -> T2 88 / 55.7 / 1.118 / 715
- k0.45_R2.0: T1 93 / 61.3 / 1.524 / 2,264 -> T2 88 / 54.5 / 1.324 / 1,989
- k0.6_R1.0: T1 68 / 60.3 / 2.008 / 2,762 -> T2 63 / 66.7 / 2.146 / 3,406
- k0.6_R2.0: T1 68 / 60.3 / 2.367 / 3,747 -> T2 63 / 66.7 / 2.454 / 4,322
- k0.75_R1.0: T1 55 / 61.8 / 1.689 / 1,538 -> T2 53 / 66.0 / 2.032 / 3,080
- k0.75_R2.0: T1 55 / 61.8 / 2.214 / 2,711 -> T2 53 / 66.0 / 1.869 / 2,593
- k0.9_R1.0: T1 40 / 62.5 / 2.432 / 1,931 -> T2 43 / 60.5 / 1.649 / 1,638
- k0.9_R2.0: T1 40 / 62.5 / 3.135 / 2,879 -> T2 43 / 60.5 / 1.33 / 832

Yearly (n / WR / PF / $) of the main candidates:

- VOLB_RE_E: 2020: 5/40.0/0.11/-263, 2021: 21/71.4/2.1/638, 2022: 37/64.9/1.89/1,803, 2023: 30/53.3/1.06/86, 2024: 27/51.9/1.18/293, 2025: 35/54.3/1.23/613, 2026: 26/57.7/1.58/1,082
- VOLB_RE_E_k60: 2020: 5/40.0/2.31/228, 2021: 18/72.2/5.32/1,086, 2022: 22/63.6/2.73/1,930, 2023: 23/52.2/1.42/502, 2024: 19/57.9/1.43/518, 2025: 22/68.2/2.35/1,074, 2026: 22/72.7/3.85/2,730
- NAIVE_O_struct: 2020: 31/41.9/0.71/-412, 2021: 105/49.5/1.23/822, 2022: 131/51.1/1.02/196, 2023: 141/56.0/1.16/930, 2024: 126/57.1/1.31/1,805, 2025: 120/53.3/1.28/2,130, 2026: 65/53.8/1.45/2,277
- NAIVE_S_all: 2020: 59/61.0/1.04/72, 2021: 226/51.8/0.78/-1,846, 2022: 249/52.6/0.97/-539, 2023: 309/53.7/0.77/-2,800, 2024: 270/53.0/0.72/-3,627, 2025: 227/54.2/0.83/-2,580, 2026: 169/62.1/1.26/2,604

Per-module naive re-entry (same direction, market at the bar after the stop):

| Module | T1 n / WR / PF / $ | T2 n / WR / PF / $ |
|---|---|---|
| CRT11 | 26 / 34.6 / 0.643 / -579 | 21 / 19.0 / 0.307 / -1,257 |
| ICT | 28 / 57.1 / 1.244 / 275 | 23 / 47.8 / 0.945 / -78 |
| LATE15 | 9 / 55.6 / 0.788 / -96 | 8 / 37.5 / 0.392 / -272 |
| LF0430 | 7 / 71.4 / 1.468 / 65 | 12 / 66.7 / 1.566 / 227 |
| LF06 | 24 / 62.5 / 0.734 / -240 | 19 / 52.6 / 0.63 / -514 |
| LON | 113 / 43.4 / 0.957 / -206 | 81 / 39.5 / 0.909 / -415 |
| MOM1030 | 28 / 67.9 / 0.534 / -410 | 14 / 78.6 / 1.57 / 180 |
| MOM11 | 117 / 76.1 / 0.974 / -89 | 103 / 75.7 / 0.955 / -178 |
| MOM13 | 85 / 40.0 / 0.597 / -1,973 | 47 / 51.1 / 0.914 / -243 |
| MSEQ | 19 / 52.6 / 0.929 / -46 | 16 / 56.2 / 1.057 / 46 |
| MSEQS | 2 / 50.0 / 0.33 / -162 | 3 / 66.7 / 0.588 / -187 |
| NF05 | 34 / 50.0 / 1.122 / 129 | 41 / 43.9 / 1.572 / 992 |
| ON07 | 16 / 37.5 / 0.261 / -354 | 12 / 58.3 / 0.56 / -248 |
| ORB60 | 31 / 48.4 / 0.748 / -448 | 22 / 54.5 / 0.768 / -428 |
| ORB90 | 25 / 60.0 / 1.15 / 182 | 17 / 58.8 / 0.965 / -43 |
| REV06 | 42 / 69.0 / 0.771 / -241 | 46 / 65.2 / 0.553 / -984 |
| VOLB | 163 / 45.4 / 1.006 / 65 | 128 / 51.6 / 0.948 / -557 |
| VW13 | 20 / 55.0 / 0.551 / -298 | 13 / 76.9 / 2.012 / 245 |
| VW13b | 54 / 57.4 / 0.605 / -687 | 40 / 65.0 / 1.093 / 111 |

Per-module naive re-entry (opposite direction, stop-and-reverse):

| Module | T1 n / WR / PF / $ | T2 n / WR / PF / $ |
|---|---|---|
| CRT11 | 26 / 50.0 / 1.424 / 467 | 21 / 57.1 / 1.803 / 771 |
| ICT | 28 / 42.9 / 0.731 / -396 | 23 / 52.2 / 1.013 / 17 |
| LATE15 | 9 / 55.6 / 0.886 / -49 | 8 / 100.0 / None / 588 |
| LF0430 | 7 / 42.9 / 1.269 / 36 | 12 / 58.3 / 4.206 / 595 |
| LF06 | 24 / 62.5 / 0.851 / -121 | 19 / 73.7 / 1.445 / 310 |
| LON | 113 / 39.8 / 0.973 / -122 | 81 / 46.9 / 1.502 / 1,857 |
| MOM1030 | 28 / 75.0 / 1.1 / 51 | 14 / 85.7 / 1.77 / 217 |
| MOM11 | 117 / 70.1 / 0.751 / -1,012 | 103 / 67.0 / 0.661 / -1,735 |
| MOM13 | 85 / 57.6 / 1.408 / 1,292 | 47 / 48.9 / 0.956 / -118 |
| MSEQ | 20 / 70.0 / 2.372 / 454 | 16 / 43.8 / 0.793 / -199 |
| MSEQS | 2 / 50.0 / 2.668 / 142 | 3 / 33.3 / 1.03 / 10 |
| NF05 | 34 / 41.2 / 0.693 / -366 | 41 / 48.8 / 0.799 / -491 |
| ON07 | 16 / 43.8 / 2.636 / 269 | 12 / 41.7 / 1.515 / 183 |
| ORB60 | 31 / 58.1 / 0.902 / -169 | 22 / 63.6 / 1.587 / 638 |
| ORB90 | 25 / 44.0 / 0.504 / -899 | 17 / 64.7 / 1.197 / 197 |
| REV06 | 42 / 69.0 / 0.744 / -289 | 46 / 89.1 / 2.392 / 982 |
| VOLB | 163 / 59.5 / 1.199 / 2,058 | 128 / 59.4 / 1.316 / 2,922 |
| VW13 | 20 / 70.0 / 1.064 / 29 | 13 / 46.2 / 0.382 / -435 |
| VW13b | 54 / 61.1 / 0.807 / -288 | 40 / 57.5 / 0.734 / -404 |

## 4. 2015-19 cost-normalised check (P&L in % of daily ATR, cost 0.345% ATR, no slippage)

- VOLB_base_norm: {'n': 945, 'wr': 60.3, 'pf': 1.272, 'mean_pct_atr': 3.236}
- LON_base_norm: {'n': 343, 'wr': 43.1, 'pf': 1.119, 'mean_pct_atr': 0.968}
- VOLB_RE_E: {'n': 159, 'wr': 61.0, 'pf': 1.556, 'mean_pct_atr': 5.495}
- VOLB_RE_S: {'n': 82, 'wr': 58.5, 'pf': 1.439, 'mean_pct_atr': 4.233}
- VOLB_RE_E_k60: {'n': 125, 'wr': 61.6, 'pf': 1.532, 'mean_pct_atr': 4.917}
- LON_RE: {'n': 7, 'wr': 71.4, 'pf': 3.891, 'mean_pct_atr': 11.263}

Drawdown windows (base max-DD window and the candidate's $ inside it):

- VOLB_RE_E: {'base': {'maxdd': 4582, 'peak': 20231013, 'trough': 20231208, 'cand_in_window': -277}, 'comb': {'maxdd': 4859, 'peak': 20231013, 'trough': 20231208, 'cand_in_window': -277}, 'cand_standalone_maxdd': 730}
- VOLB_RE_E_k60: {'base': {'maxdd': 4582, 'peak': 20231013, 'trough': 20231208, 'cand_in_window': -286}, 'comb': {'maxdd': 4936, 'peak': 20231013, 'trough': 20240402, 'cand_in_window': -384}, 'cand_standalone_maxdd': 499}

## 5. Verdict

- ORB60_3RD: fails T1_n60_pf13, T2_pf12, T2_plus4t_pf11, sharpe_up_T2
- VOLB_RE_E: fails maxdd_ok
- VOLB_RE_S: fails T1_n60_pf13, T2_pf12, T2_plus4t_pf11, sharpe_up_T2, maxdd_ok
- VOLB_RE_E_k60: fails maxdd_ok
- LON_RE: fails T1_n60_pf13, T2_pf12, T2_plus4t_pf11, sharpe_up_T2
- LON_RE_anydir: fails T1_n60_pf13, sharpe_up_T1, worst_month_ok
- NAIVE_S_struct: fails T1_n60_pf13, T2_pf12, T2_plus4t_pf11, sharpe_up_T1, sharpe_up_T2, maxdd_ok, worst_month_ok
- NAIVE_O_struct: fails T1_n60_pf13, sharpe_up_T1
- NAIVE_S_all: fails T1_n60_pf13, T2_pf12, T2_plus4t_pf11, sharpe_up_T1, sharpe_up_T2, maxdd_ok, worst_month_ok
- NAIVE_O_all: fails T1_n60_pf13, T2_pf12, sharpe_up_T1, maxdd_ok

Conclusions:

- ORB60/ORB90: a second attempt after a STOP almost never exists (56 ORB60 stop-outs, 2 re-entries after them in 6 years; ORB90 48 / 0). The existing second trades (after a target) are good (ORB60 4.051 / 1.609, ORB90 n 10) and removing them lowers Sharpe -> keep the 2-per-day rule as it is. A third trade per day: 1 trade(s) in 6 years -> nothing to gain.
- MSEQ: re-entries already allowed; only 4 second sequences after a stop in 6 years (the sequence needs 5 rising candles above the main low, which a stop-out destroys); second sequences after a target: T1 PF 2.102 / T2 0.821 (n 17 / 9); removing all second+ sequences changes Sharpe by -0.011 / +0.014 -> leave as is.
- VOLB re-arm, same rules (either side, k 0.45, stop at the RTH open, 2R, BE): T1 n 93 PF 1.524 / T2 n 88 PF 1.324, +4t T2 1.275, Sharpe 3.467->3.525 / 3.955->4.016, net 6y +4,253, maxDD 4,582->4,859 (+6.0%); 2015-19 cost-normalised PF 1.556 (base VOLB 1.272); opposite-open conflicts 1.7%. Passes every rule except max DD (+6%, limit +5%): the extra trades lose in the 2023 drawdown window. Same-side-only re-arm fails T2 (PF 0.982).
- VOLB re-arm with a wider second level (k 0.6, T1-best of the k grid, every year 2020-26 positive): T1 n 68 PF 2.367 / T2 n 63 PF 2.454, +4t T2 2.361, Sharpe 3.467->3.62 / 3.955->4.112, net 6y +8,069, maxDD 4,582->4,936 (+7.7%); 2015-19 norm PF 1.532. Also fails only the max-DD rule (+7.7%). It is a parameter choice on a 5x2 grid (plateau OK: all k cells T1 PF >= 1.35).
- LON re-arm (trend side, FVG limit): 5 trades in 6 years -> non-event; allowing the counter-trend side after the stop: T1 PF 0.871 / T2 1.538 -> fails T1, and 21.1% would be blocked by an opposite open position.
- CRT11 / ICT / time modules: no second trigger exists in the same session (CRT11 one candle pair, ICT other levels are already allowed but ~never fire, clock modules fire once). Naive same-direction re-entry at the bar after the stop loses everywhere (structure modules T1 PF 0.959 / T2 0.872; all modules 0.865 / 0.905, Sharpe down 0.2-0.5): the stop carries information. Stop-and-reverse (opposite): structure T1 1.072 / T2 1.334, all 1.031 / 1.177: positive only in T2 (T1 fails), 15.7% / 29.8% conflict with open positions and it would block 231 base entries -> rejected.
- Nothing passes the six_lib protocol. The only candidate worth a note is the VOLB re-arm (either side), +$58-110 per month per contract with a slightly deeper max DD; it could be re-checked after a year of new data, not added now.
