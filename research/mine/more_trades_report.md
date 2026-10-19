# More trades at the same quality (2026-10-19)

Base = the 2027 default set (nt_compare `ultra_d4`: Ultra + SO04/RV11/ORFAIL/CAM3, opposite-position conflicts removed), real Databento NQ, $ per MNQ incl. $1.90 + 1 tick; T1 2020-10-15..2023 (choose), T2 2024-01..2026-10 (check), A 2010-14 / B 2015-19 cost-normalised (0.345% ATR) regime check. Script `research/mine/more_trades.py` (+ `families10.py`, mined into `results_b10.csv` / `trades_b10.pkl`); numbers in `more_trades.json`.

## Pre-registered protocol (fixed before any candidate was run)

- Standalone: T1 n >= 60, PF >= 1.3, WR >= 55.0; T2 PF >= 1.2; +4 ticks ($3.0 per trade) T2 PF >= 1.1; norm A PF >= 0.95 and B PF >= 1.05.
- Plateau: every one-step neighbour on each numeric grid axis (other params equal) has T1 PF >= 1.15.
- Portfolio (candidate added to the raw base and run through `wrq_port.conflict_filter`): Sharpe up in T1 AND T2; max DD and worst month not worse by > 5.0% in either; set WR not lower by > 0.5 pt; set PF not lower by > 0.02; daily-P&L correlation with the base < 0.3.
- Grid parts: cells passing the standalone rules on the mined csv (T1 as mined = 2020-01..2023) that are a NEW signal (different anchor / window / threshold / mode from every module already in the set; trend-filter-only or exit-only variants of an existing signal are the same signal), one representative per signal (best T1 PF), top 3 per family, then everything re-run on regenerated trades with T1 = 2020-10-15..2023 and NQMaster's day filter (ATR >= 150, no FOMC).
- Base rate P(T2 pass | T1 pass) is reported per family against the whole 54,558-cell archive so selection bias can be judged.
- Re-arm (part B): one stop order back at the original entry level after a stop-loss exit, same direction, same stop and target distance, until the module's own deadline (the rule accepted for VOLB on 2026-10-17); ORFAIL also gets its family re-arm (next failed break after the stop-out).

## Base set

| period | trades/day | WR | PF | Sharpe | net | max DD | worst month |
|---|---|---|---|---|---|---|---|
| T1 | 5.086 | 65.7 | 1.462 | 3.533 | 73148 | 4667 | -1176 |
| T2 | 4.929 | 64.8 | 1.500 | 4.026 | 86936 | 3586 | -2182 |
| A (norm, % ATR) | 4.869 | 58.7 | 1.044 | 0.441 | 2300 | 2381 | -525 |
| B (norm, % ATR) | 4.805 | 60.0 | 1.136 | 1.225 | 7459 | 1234 | -599 |

(The 2010-19 base view uses the db_long 'Ultra' norm rows (pre-overhaul exits, MOM1030 x4, ENG10/LATEFH off) plus the four durable six-year modules, as in six_oos.py.)

## Cells scanned and base rates

| family | cells | median PF T1 / T2 / A / B | pass T1 (csv) | P(T2 pass) all cells | P(T2 pass given T1 pass) | P(T2 and A/B pass given T1 pass) | new signals tested |
|---|---|---|---|---|---|---|---|
| ALL (whole archive) | 54558 | 0.960 / 0.919 / 0.900 / 0.961 | 971 | 9.3% | 21.0% | 6.6% | - (- cells pass all csv rules) |
| CLOCK_ANCHOR | 1728 | 0.963 / 0.952 / 0.937 / 0.954 | 79 | 12.0% | 25.3% | 8.9% | 3 (7 cells pass all csv rules) |
| G_DRIVE | 7200 | 0.955 / 0.908 / 0.917 / 0.938 | 143 | 13.5% | 21.7% | 7.7% | 4 (11 cells pass all csv rules) |
| NQ_DRIVE | 5760 | 0.950 / 0.937 / 0.928 / 0.957 | 123 | 9.0% | 14.6% | 2.4% | 3 (3 cells pass all csv rules) |
| RVOL_DRIVE | 4608 | 0.908 / 0.910 / 0.931 / 0.961 | 80 | 11.3% | 43.8% | 8.8% | 4 (7 cells pass all csv rules) |
| LATE_MOM | 2304 | 0.989 / 0.867 / 0.847 / 0.969 | 78 | 4.6% | 10.3% | 1.3% | 1 (1 cells pass all csv rules) |
| OPEN_DRIVE | 288 | 1.034 / 1.082 / 1.066 / 1.056 | 16 | 14.6% | 37.5% | 0.0% | 0 (0 cells pass all csv rules) |
| OR_FAIL | 432 | 0.940 / 0.952 / 0.941 / 0.976 | 2 | 4.9% | 0.0% | 0.0% | 0 (0 cells pass all csv rules) |
| PIVOT_FADE | 512 | 0.885 / 1.108 / 0.974 / 0.982 | 0 | 37.7% | -% | -% | 0 (0 cells pass all csv rules) |
| VOL_BREAK | 192 | 1.134 / 1.162 / 1.088 / 1.093 | 4 | 45.8% | 100.0% | 50.0% | 0 (2 cells pass all csv rules) |
| OR_FAIL_X | 288 | 0.995 / 0.942 / 0.989 / 1.002 | 2 | 7.3% | 0.0% | 0.0% | 0 (0 cells pass all csv rules) |
| PIVOT_FADE_X | 256 | 0.938 / 0.848 / 0.836 / 0.984 | 6 | 8.2% | 0.0% | 0.0% | 0 (0 cells pass all csv rules) |
| VWAP_BAND2 | 528 | 0.969 / 0.984 / 0.925 / 0.956 | 1 | 16.7% | 100.0% | 0.0% | 0 (0 cells pass all csv rules) |

## Part A: second instances of the durable modules' families (other cells)

| candidate | cell | n T1/T2 | WR T1/T2 | PF T1 / T2 / T2+4t | A / B PF (norm) | plateau | port dSharpe T1/T2 | dWR T1/T2 | dPF T1/T2 | dDD% T1/T2 | dWorstMo% T1/T2 | corr | same-min overlap | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CLOCK_ANCHOR#948 | {anc:SVWAP,T:400,x:0.3,mode:1,s:0.15,R:1.0,tg:0,tf:0,hold:120} | 38/51 | 63.2/54.9 | 2.019 / 1.285 / 1.212 | 1.028 / 1.151 | False | 0.023/0.017 | -0.05/-0.08 | 0.002/-0.002 | 0.0/-6.2 | 0.0/0.0 | 0.036 | 39.3% | T1_n, plateau |
| CLOCK_ANCHOR#1277 | {anc:PDC,T:1030,x:0.4,mode:1,s:0.25,R:1.0,tg:0,tf:1,hold:240} | 148/132 | 56.1/55.3 | 1.262 / 1.307 / 1.256 | 0.973 / 1.055 | True | -0.034/-0.055 | -0.29/-0.29 | -0.002/-0.002 | -1.9/12.7 | 10.3/-7.7 | 0.273 | 2.9% | T1_pf, port:sharpe_up, port:maxdd, port:worst_month |
| CLOCK_ANCHOR#255 | {anc:VWAP,T:1230,x:0.3,mode:1,s:0.25,R:1.0,tg:1,tf:1,hold:120} | 73/67 | 54.8/58.2 | 1.264 / 1.422 / 1.357 | 1.214 / 1.221 | False | -0.028/-0.002 | -0.20/-0.13 | -0.003/-0.001 | 2.9/5.5 | -0.3/0.2 | 0.170 | 0.0% | T1_pf, T1_wr, plateau, port:sharpe_up, port:maxdd |
| G_DRIVE#6857 | {A:930,T:60,x:0.35,mode:1,tf:1,k:0.35,stop:0,R:2.0,hold:600} | 118/94 | 61.0/51.1 | 1.951 / 1.290 / 1.258 | 1.057 / 1.218 | False | 0.013/-0.197 | -0.14/-0.37 | 0.022/-0.011 | -0.9/7.0 | 33.7/-5.9 | 0.351 | 77.8% | plateau, port:sharpe_up, port:maxdd, port:worst_month, port:corr |
| G_DRIVE#3924 | {A:300,T:120,x:0.2,mode:-1,tf:1,k:0.35,stop:0,R:0.5,hold:240} | 82/69 | 67.1/62.3 | 1.461 / 1.415 / 1.346 | 0.979 / 1.052 | False | 0.044/0.010 | 0.02/-0.06 | 0.000/-0.002 | -0.1/-3.2 | 10.2/-3.2 | 0.060 | 44.4% | plateau, port:worst_month |
| G_DRIVE#6766 | {A:930,T:60,x:0.2,mode:1,tf:1,k:0.35,stop:1,R:2.0,hold:240} | 208/173 | 56.2/56.1 | 1.372 / 1.286 / 1.250 | 1.158 / 1.074 | False | -0.115/-0.233 | -0.46/-0.42 | -0.006/-0.018 | 9.2/14.5 | 28.1/-15.5 | 0.381 | 63.3% | plateau, port:sharpe_up, port:maxdd, port:worst_month, port:corr |
| NQ_DRIVE#3780 | {A:700,T:60,x:0.2,mode:-1,tf:0,k:0.2,stop:0,R:0.5,hold:240} | 54/47 | 74.1/72.3 | 1.526 / 1.208 / 1.135 | 1.069 / 1.065 | False | 0.027/0.000 | 0.10/0.10 | 0.001/-0.003 | 1.3/5.5 | -3.1/5.0 | -0.016 | 0.0% | T1_n, plateau, port:sharpe_up, port:maxdd |
| NQ_DRIVE#2133 | {A:100,T:240,x:0.2,mode:-1,tf:1,k:0.35,stop:0,R:0.5,hold:240} | 99/96 | 63.6/61.5 | 1.746 / 1.313 / 1.249 | 1.322 / 1.283 | False | 0.098/0.013 | -0.06/-0.09 | 0.005/-0.005 | 2.8/-4.3 | 10.2/4.7 | 0.054 | 48.2% | plateau, port:worst_month |
| NQ_DRIVE#3947 | {A:700,T:240,x:0.35,mode:1,tf:1,k:0.35,stop:0,R:2.0,hold:240} | 153/126 | 55.6/55.6 | 1.354 / 1.324 / 1.284 | 0.999 / 1.087 | False | -0.130/-0.146 | -0.38/-0.32 | -0.009/-0.010 | -5.3/8.5 | 26.4/-2.3 | 0.307 | 93.5% | plateau, port:sharpe_up, port:maxdd, port:worst_month, port:corr |
| RVOL_DRIVE#778 | {T:1000,cond:(lo,0.8),ref:pdc,x:0.25,dm:1,tf:0,k:0.4,R:1.0} | 37/36 | 62.2/47.2 | 2.130 / 1.275 / 1.234 | 1.173 / 1.083 | True | 0.059/0.050 | 0.04/-0.11 | 0.011/0.014 | -1.7/0.0 | 0.1/10.6 | 0.095 | 2.7% | T1_n, port:worst_month |
| RVOL_DRIVE#1926 | {T:1015,cond:(lo,0.8),ref:pdc,x:0.25,dm:1,tf:0,k:0.25,R:1.0} | 33/41 | 69.7/63.4 | 2.283 / 2.070 / 1.989 | 1.065 / 1.059 | False | 0.081/0.023 | 0.09/-0.05 | 0.013/0.008 | -2.2/0.0 | 13.9/5.9 | 0.095 | 0.0% | T1_n, plateau, port:worst_month |
| RVOL_DRIVE#2168 | {T:1015,cond:(lo,0.65),ref:pdc,x:0.1,dm:1,tf:0,k:0.4,R:0.3} | 38/31 | 65.8/71.0 | 1.072 / 2.900 / 2.667 | 1.322 / 1.274 | False | -0.044/0.034 | -0.08/0.02 | -0.008/0.004 | 0.0/0.0 | 20.7/6.6 | 0.012 | 0.0% | T1_n, T1_pf, plateau, port:sharpe_up, port:worst_month |
| LATE_MOM#1033 | {T:1500,sig:VW,x:0.5,tf:0,k:0.1,R:1.0} | 64/45 | 65.6/57.8 | 1.625 / 1.535 / 1.398 | 1.038 / 1.142 | False | 0.020/0.006 | 0.00/-0.09 | 0.001/0.001 | 0.2/0.0 | 0.5/4.1 | 0.134 | 48.6% | plateau |

**Information only: all part-A representatives added together** (2153 candidate trades, 2085 kept after the conflict filter, 67 base trades blocked, corr 0.451):

| period | set | trades/day | WR | PF | Sharpe | net $ | max DD | worst month |
|---|---|---|---|---|---|---|---|---|
| T1 | base | 5.086 | 65.7 | 1.462 | 3.533 | 73148 | 4667 | -1176 |
| T1 | comb | 6.488 | 64.5 | 1.475 | 3.419 | 100220 | 5865 | -2452 |
| T2 | base | 4.929 | 64.8 | 1.500 | 4.026 | 86936 | 3586 | -2182 |
| T2 | comb | 6.256 | 63.3 | 1.470 | 3.466 | 110633 | 6548 | -2225 |

Near-misses (at most two failed rules) and their grid neighbours (T1 PF as mined; the plateau rule needs every neighbour >= 1.15):

- CLOCK_ANCHOR#948: fails T1_n, plateau; neighbours T=200: 0.31 (n 24), T=2000: - (n 3), x=0.2: 1.86 (n 157), s=0.25: 1.32 (n 66), R=0.5: 1.69 (n 66)
- G_DRIVE#3924: fails plateau, port:worst_month; neighbours A=1800: 0.86 (n 64), T=60: 0.98 (n 65), T=320: 1.00 (n 154), x=0.1: 1.15 (n 243), x=0.35: 1.52 (n 27), k=0.2: 1.38 (n 111), R=1.0: 2.03 (n 111), hold=600: 1.25 (n 111)
- NQ_DRIVE#2133: fails plateau, port:worst_month; neighbours A=0: 0.98 (n 114), A=200: 1.32 (n 151), T=120: 0.73 (n 51), x=0.1: 1.10 (n 282), x=0.35: 2.36 (n 52), k=0.2: 1.25 (n 149), R=1.0: 1.73 (n 149)
- RVOL_DRIVE#778: fails T1_n, port:worst_month; neighbours T=1015: 1.32 (n 63), x=0.1: 1.30 (n 113), x=0.4: 1.46 (n 42), k=0.25: 1.75 (n 66), R=0.5: 1.92 (n 66), R=99.0: 1.81 (n 66)
- LATE_MOM#1033: fails plateau; neighbours T=1430: 0.99 (n 74), T=1515: 0.80 (n 99), x=0.25: 1.21 (n 362), k=0.2: 1.77 (n 87), R=0.5: 1.46 (n 87), R=99.0: 1.68 (n 87)

## Part B: one re-arm after a stop-out

Stop-outs in the base (T1+T2): {'NF05': 69, 'LF06': 43, 'LF0430': 22, 'CRT11': 48, 'LATE15': 17, 'SO04': 49, 'RV11': 31, 'ORFAIL': 134, 'CAM3': 95}

| candidate | cell | n T1/T2 | WR T1/T2 | PF T1 / T2 / T2+4t | A / B PF (norm) | plateau | port dSharpe T1/T2 | dWR T1/T2 | dPF T1/T2 | dDD% T1/T2 | dWorstMo% T1/T2 | corr | same-min overlap | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NF05_RE | re-arm | 10/14 | 30.0/28.6 | 0.723 / 0.121 / 0.107 | 2.186 / 1.238 | None | -0.004/-0.058 | -0.10/-0.15 | -0.002/-0.008 | 0.0/0.0 | -0.6/0.0 | 0.031 | -% | T1_n, T1_pf, T1_wr, T2_pf, T2_plus4, port:sharpe_up |
| LF06_RE | re-arm | 14/9 | 78.6/66.7 | 2.453 / 1.121 / 1.053 | 0.942 / 0.669 | None | 0.013/-0.001 | 0.04/0.00 | 0.001/-0.001 | 0.5/0.0 | 0.0/0.0 | 0.017 | -% | T1_n, T2_pf, T2_plus4, A_pf, B_pf, port:sharpe_up |
| LF0430_RE | re-arm | 0 trades | | | | | | | | | | | | no re-entry fired |
| CRT11_RE | re-arm | 12/6 | 41.7/66.7 | 1.090 / 5.195 / 4.830 | 2.712 / 1.322 | None | 0.002/0.025 | -0.07/0.02 | -0.001/0.003 | -1.1/0.0 | -0.4/0.0 | -0.021 | -% | T1_n, T1_pf, T1_wr |
| LATE15_RE | re-arm | 2/1 | 50.0/100.0 | 0.440 / - / - | 1.106 / 0.000 | None | -0.001/0.007 | -0.01/0.01 | -0.001/0.001 | 0.0/0.0 | 0.0/0.0 | -0.037 | -% | T1_n, T1_pf, T1_wr, T2_pf, T2_plus4, B_pf, port:sharpe_up |
| SO04_RE | re-arm | 14/14 | 50.0/35.7 | 1.213 / 0.586 / 0.551 | 0.771 / 0.684 | None | 0.001/-0.028 | -0.06/-0.11 | 0.000/-0.004 | 0.0/0.0 | 4.1/-3.3 | 0.030 | -% | T1_n, T1_pf, T1_wr, T2_pf, T2_plus4, A_pf, B_pf, port:sharpe_up |
| RV11_RE | re-arm | 11/10 | 63.6/40.0 | 1.417 / 0.656 / 0.623 | 0.942 / 1.004 | None | 0.002/0.000 | -0.02/-0.06 | 0.000/-0.001 | 0.0/0.0 | 5.1/0.0 | -0.004 | -% | T1_n, T2_pf, T2_plus4, A_pf, B_pf, port:sharpe_up, port:worst_month |
| ORFAIL_RE | re-arm | 35/37 | 40.0/46.0 | 1.289 / 1.160 / 1.110 | 1.065 / 0.801 | None | 0.016/0.012 | -0.11/-0.16 | 0.002/-0.004 | 0.3/1.5 | 3.8/5.1 | -0.008 | -% | T1_n, T1_pf, T1_wr, T2_pf, B_pf, port:worst_month |
| CAM3_RE | re-arm | 42/42 | 23.8/21.4 | 1.518 / 0.752 / 0.686 | 0.315 / 0.389 | None | 0.015/0.009 | -0.25/-0.26 | 0.001/-0.002 | -0.8/0.0 | 0.0/0.0 | -0.053 | -% | T1_n, T1_wr, T2_pf, T2_plus4, A_pf, B_pf |
| ORFAIL_RE2 | re-arm | 15/18 | 66.7/38.9 | 3.012 / 0.652 / 0.625 | 0.433 / 1.288 | None | 0.016/-0.062 | -0.03/-0.17 | 0.002/-0.009 | 0.0/0.0 | 2.8/6.2 | -0.001 | -% | T1_n, T2_pf, T2_plus4, A_pf, port:sharpe_up, port:worst_month |

**Information only: all level re-arms added together** (273 candidate trades, 210 kept after the conflict filter, 12 base trades blocked, corr -0.022):

| period | set | trades/day | WR | PF | Sharpe | net $ | max DD | worst month |
|---|---|---|---|---|---|---|---|---|
| T1 | base | 5.086 | 65.7 | 1.462 | 3.533 | 73148 | 4667 | -1176 |
| T1 | comb | 5.215 | 65.1 | 1.461 | 3.576 | 74253 | 4613 | -1118 |
| T2 | base | 4.929 | 64.8 | 1.500 | 4.026 | 86936 | 3586 | -2182 |
| T2 | comb | 5.069 | 64.1 | 1.482 | 3.989 | 86369 | 3640 | -2222 |

## Part C/D: OR_FAIL 5/10-minute ranges, Camarilla L2/H2 and L4/H4, NEW VWAP_BAND2 family

Mined with `MINE_TAG=b10 MINE_PROCS=2 python3 run_mine_db.py VWAP_BAND2 OR_FAIL_X PIVOT_FADE_X` (1,072 cells, 38 s). VWAP_BAND2 lookahead check (bands recomputed from bars <= t-1 and the signal bar's own volume/high perturbed): {'cells': ['GRID_VWB2[0]', 'GRID_VWB2[100]', 'GRID_VWB2[-1]'], 'results': [{'n': 4457, 'max_dvwap': 2.9103830456733704e-11, 'max_dsigma': 2.3651885783237958e-08, 'violations': 0}, {'n': 2392, 'max_dvwap': 2.9103830456733704e-11, 'max_dsigma': 2.0593187599615703e-08, 'violations': 0}, {'n': 4160, 'max_dvwap': 2.9103830456733704e-11, 'max_dsigma': 2.0101964537388994e-08, 'violations': 0}]}

| candidate | cell | n T1/T2 | WR T1/T2 | PF T1 / T2 / T2+4t | A / B PF (norm) | plateau | port dSharpe T1/T2 | dWR T1/T2 | dPF T1/T2 | dDD% T1/T2 | dWorstMo% T1/T2 | corr | same-min overlap | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## All accepted additions together

None accepted: the base set is unchanged (trades/day, WR, PF, Sharpe, max DD, worst month and the 2010-19 norm view are the base rows above).

## Verdict

- **Nothing is added.** 0 of the 23 candidates run under the pre-registered protocol passes it: 13 second-instance cells (part A), 10 re-arms (part B), 0 cells of the three new/extended families even reach the standalone bar (part C/D).
- Part A (other cells of the durable families): of 54,558 archived cells only 971 pass the T1 standalone rules, 21% of those pass T2 PF >= 1.2 and 6.6% also pass the 2010-19 regime check (the chance of a random T1 survivor holding up). The 13 new-signal representatives (one per signal, top 3 per family) split into (i) cells that are the SAME trades as a module already in the set on 39-94% of their entries (G_DRIVE 09:30 drives = MOM1030/ORB, NQ_DRIVE 07:00/01:00 = ON07/LF06, LATE_MOM 15:00 VW = LATE15, SVWAP 04:00 x0.3 = SO04/CA04V) - they raise correlation and DD, not trade count - and (ii) genuinely new cells (PDC 10:30, VWAP 12:30, RVOL 10:00/10:15, NQ_DRIVE 07:00 fade) that are thin (n 33-73 per period), sit on no plateau (a neighbour below PF 1.15 in every case but two) and lower the set's WR / Sharpe when added. Only 2 of 13 sit on a plateau (CLOCK_ANCHOR#1277 PDC 10:30 and RVOL_DRIVE#778) and both fail the standalone and portfolio rules. All 13 together: Sharpe -0.11 / -0.56 (T1/T2), WR -1.2 / -1.5 pt, max DD +26% / +83%.
- Part B (re-arm at the original entry level after a stop-out, the VOLB rule applied to NF05, LF06, LF0430, CRT11, LATE15, SO04, RV11, ORFAIL, CAM3, plus the ORFAIL family re-arm): the price rarely comes back to the entry level inside the module's own window (LF0430: 0 of 22 stop-outs; NF05 10/14 trades per period from 69 stop-outs), the re-entries that do fire lose out of sample (T2 PF 0.12-1.16 for every module but CRT11 with n = 6), and the 2010-19 regime view is below 1 for LF06, SO04, RV11, CAM3 and ORFAIL (NF05 and CRT11 are positive there but fail T1/T2). All level re-arms together: +101 / +97 trades, Sharpe +0.04 / -0.04, WR -0.55 / -0.68 pt. Consistent with reentry_lab (2026-10-17): the only re-arm with an edge is VOLB's, already available as VolbReArm.
- Part C (OR_FAIL on 5/10-minute ranges, 288 cells: median PF 0.995 / 0.942 / 0.989 / 1.002 (T1/T2/A/B), 2 T1 survivors, 0 pass T2; Camarilla L2/H2 and L4/H4 fades, 256 cells: median 0.938 / 0.848, 6 T1 survivors, 0 pass T2): nothing; the 15-minute range with the CAM3 level remain isolated cells.
- Part D (NEW VWAP_BAND2: session VWAP +- 2/3 sigma fades and band-1 momentum, bands strictly from bars <= t-1, lookahead check 0 violations on 3 cells / 11,009 signals; 528 cells): median PF 0.969 / 0.984 / 0.925 / 0.956, best T1 PF 1.80 (n < 60), exactly 1 cell passes the T1 rules (#375: fade of the 3rd band 11:00-15:00 with the trend, 0.25 ATR stop, 1R: n 67, PF 1.45 T1 / 1.60 T2) and it fails the 2010-19 check (A 0.96, B 0.79), i.e. a post-2020 cell with 1-in-16 base odds of holding. The session-VWAP bands carry no edge beyond what VW13 (13:00 RTH-VWAP distance) already captures.
- Honest reading: the base set already contains every robust cell of these families; its neighbours are either the same trades again (size, not frequency) or noise-level cells whose T1 PF is the selection artefact the base rates predict (P(T2 & regime | T1) = 7%). 'More trades per day at the same WR / PF / DD' is not available from second instances, re-arms or VWAP bands on this data; the trade-count lever remains size and the number of accounts (memory 2026-09-28, 2026-10-17). No change to NQMaster is proposed.
