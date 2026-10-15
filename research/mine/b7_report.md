# Batch 7: five new intraday families on real NQ futures (2026-10-16)

Files: `families7.py` (generators), `run_mine_db.py` (now imports `FAMILIES7`; new env `MINE_KEEP_N`, default 80), `results_b7.csv`, `trades_b7.pkl`, `b7_select.py` -> `b7_select.json`.
Run: `MINE_TAG=b7 MINE_KEEP_N=60 python3 run_mine_db.py SQZ_BOX PD_ACCEPT ER_PERSIST ON_POS PERIOD_OPEN` (4,764 configs, 0 errors, 40 s), then `python3 b7_select.py`.
Data: `nqdb.npz` (real Databento NQ). The results are in $ per MNQ, net of $1.90 commission and 1 tick per side. The CSV uses T1 = 2020-01..2023-12 and T2 = 2024-01..2026-10. A/B are cost-normalised 2010-14 / 2015-19, shown for information only and not used for selection. The final check recomputes T1 from 2020-10-15 with `six_lib`.

## Families

| Family | Idea | Generator | Grid |
|---|---|---|---|
| SQZ_BOX | **Time-of-day-normalised squeeze.** The box is the range of the last N min (30/60/120). It is compared with the median range of the same 15-min clock slot over the prior 20 sessions; a ratio <= q (0.5/0.65/0.8) is a squeeze. An OCO stop 1 tick beyond the box is valid for E min (30/90). If both sides trade in the same 1m bar, the side nearer the bar open is taken, and the stop is still checked inside that bar. Stop: other side of the box, box mid, or 0.2 ATR. Target 0.5/1/2R. Windows: night 19:00-07:00, am 10-12, pm 12-15. Trend filter on/off. Max 2 trades a day. | `gen_sqz` / `_sqz`, `_boxes` | 972 |
| PD_ACCEPT | **Acceptance beyond the prior day's range.** Signal: K (2/3/6) consecutive RTH 5-min closes beyond the prior complete RTH high/low, plus bk (0/0.1) ATR, before w1 (10:00/10:30/11:30/13:00). Open-location filter: any / opened inside / opened outside. Continuation at market. Stop: level -0.1 ATR or 0.25 ATR. Target 0.5/1/2R or time exit. Trend filter on/off. | `gen_pdacc` / `_pdacc` | 1,152 |
| ER_PERSIST | **Efficiency ratio of the RTH path.** At T (10:30-14:30 hourly), ER = \|close - RTH open\| / sum of \|5m close changes\|. High ER (>= 0.30/0.45/0.60) trades continuation; low ER (<= 0.10/0.20) trades reversion. Minimum move x (0/0.15/0.3 ATR). Stop 0.15/0.3 ATR. Target 0.5/1/2R or time exit. Trend filter on/off. | `gen_er` / `_er` | 1,200 |
| ON_POS | **Position inside the 18:00-09:29 overnight range** at 09:29, 09:44 or 09:59. Price in the bottom/top z (0.15/0.25/0.35) of the range triggers either a fade toward the far end or a continuation out of the range. Option to require price inside the range. Stop 0.2/0.35 ATR or structure. Target: far end / range projection, or 0.5/1/2R. Trend filter on/off. | `gen_onpos` / `_onpos` | 864 |
| PERIOD_OPEN | **Weekly / monthly open price** (open of the first Globex session of the week / month). On the first touch after w0 (09:30/10:00) and before w1 (12:00/15:30), either a resting limit bounce or a stop entry 0.05 ATR through the level. Minimum distance at w0: 0/0.2 ATR. Stop 0.1/0.2 ATR beyond the level. Target 0.5/1/2R. Trend filter on/off. Up to 2 trades a day. | `gen_popen` / `_popen` | 576 |

All signals use only bars up to the signal bar, and entries start on the next bar (`core.execute`).

## Protocol and results per family

The protocol was fixed before looking at the results:
- **a)** T1 n >= 60 and PF >= 1.3.
- **b)** T2 PF >= 1.2, n >= 40, and T2 PF >= 1.1 after -$3 per trade (+4 ticks).
- **c)** Plateau: at least half of the neighbours one numeric grid step away have T1 PF >= 1.15. Categorical parameters (window, stop type, trend filter, mode, level, target type, open location, ER condition) are not steps.
- **d)** Null check: P(T2 PF >= 1.2) over all configs vs among the a-passers.
- **e)** The top 10 survivors by T1 Sharpe go through `six_lib.add_test` at weight 1. A survivor is accepted only if Ultra's Sharpe rises in both T1 and T2, max DD is not worse by more than 5%, and the worst month is not worse by more than 5%.

| Family | configs | median PF T1 | median PF T2 | share PF>1 T1 | share PF>1 T2 | median norm PF A / B | a | a+b | a+b+c | P(T2 PF>=1.2) all | P(T2 PF>=1.2 given a) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ER_PERSIST | 1200 | 1.119 | 1.002 | 42.5% | 32.7% | 1.019 / 1.135 | 273 | 84 | 84 | 18.7% | 42.5% |
| ON_POS | 864 | 0.946 | 0.956 | 34.1% | 39.0% | 0.924 / 0.950 | 6 | 1 | 1 | 5.6% | 16.7% |
| PD_ACCEPT | 1152 | 1.064 | 0.942 | 65.9% | 33.9% | 0.909 / 1.006 | 49 | 5 | 4 | 7.7% | 12.2% |
| PERIOD_OPEN | 576 | 0.940 | 0.929 | 38.2% | 34.7% | 0.830 / 0.855 | 24 | 6 | 6 | 14.1% | 25.0% |
| SQZ_BOX | 972 | 0.956 | 0.891 | 35.6% | 21.4% | 0.876 / 0.935 | 12 | 0 | 0 | 3.0% | 0.0% |
| **ALL** | 4764 | 0.993 | 0.937 | 44.7% | 32.1% | 0.906 / 0.973 | 364 | 96 | 95 | 9.9% | 35.4% |

The "share PF>1" columns count configs with fewer than 20 trades (PF missing) as not > 1.

**Null check:**
- **ER_PERSIST** is the only family where T1 selection clearly carries into T2 (42.5% vs 18.7%). That is the known 10:30-11:30 momentum effect.
- **PD_ACCEPT** (12.2% vs 7.7%) and **PERIOD_OPEN** (25% vs 14.1%) have small samples and weak lift.
- **SQZ_BOX** has none (0/12 vs 3.0%).
- **ON_POS** rests on 1 of 6 configs.

**ER_PERSIST stage-a passers by checkpoint and condition:**

| T | hi30 | hi45 | hi60 | lo10 | lo20 |
|---|---|---|---|---|---|
| 10:30 | 23 | 33 | 48 | 2 | 0 |
| 11:30 | 10 | 33 | 0 | 0 | 0 |
| 12:30 | 33 | 0 | 0 | 0 | 4 |
| 13:30 | 48 | 0 | 0 | 0 | 0 |
| 14:30 | 39 | 0 | 0 | 0 | 0 |

- Median PF by T, T1 / T2: 10:30 1.353 / 1.110, 11:30 1.166 / 1.271, 12:30 1.087 / 0.991, 13:30 0.888 / 0.871, 14:30 0.861 / 0.810.
- Low-ER reversion loses: median PF 0.81-0.87 in both periods.

## Survivors tested on the portfolio (e): top 10 by T1 Sharpe, all ER_PERSIST at 10:30

Ultra base: Sharpe T1 3.42-3.46 / T2 3.93-3.95 (the T1 window varies slightly with the candidate's trading days), 6-year maxDD $4,582, worst month -$2,210.

| j | params | CSV T1 n/WR/PF | CSV T2 n/WR/PF | T2 PF +4t | norm A / B | six T1 n/WR/PF/$ | six T2 n/WR/PF/$ | $/mo T1/T2 | corr Ultra (top module corr) | dSharpe T1 / T2 | maxDD | worst month | plateau | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 30 | T1030 hi30 x0.15 k0.3 R99 tf0 | 438/49.8/1.428 | 334/45.8/1.229 | 1.193 | 1.093 / 1.203 | 358/50.6/1.457/10,751 | 334/45.8/1.229/7,134 | 283/214 | 0.366 (VOLB .431) | -0.087 / -0.295 | 4,790 | -2,237 | 1.0 (5) | reject |
| 81 | T1030 hi45 x0.3 k0.15 R0.5 tf1 | 125/79.2/1.768 | 70/75.7/1.560 | 1.429 | 1.290 / 1.045 | 111/79.3/1.811/1,482 | 70/75.7/1.560/989 | 40/30 | 0.199 (MOM1030 .477) | +0.035 / +0.007 | 4,662 (+1.7%) | -2,349 (-6.3%) | 0.5 (4) | reject (worst month) |
| 14 | T1030 hi30 x0 k0.3 R99 tf0 | 452/50.0/1.428 | 341/46.3/1.254 | 1.218 | 1.100 / 1.222 | 367/50.4/1.450/10,669 | 341/46.3/1.254/8,008 | 280/240 | 0.367 (VOLB .433) | -0.091 / -0.275 | 4,780 | -2,237 | 1.0 (4) | reject |
| 28 | T1030 hi30 x0.15 k0.3 R2 tf0 | 438/50.7/1.391 | 334/47.3/1.218 | 1.182 | 1.103 / 1.084 | 358/51.1/1.410/9,610 | 334/47.3/1.218/6,676 | 253/200 | 0.366 (VOLB .418) | -0.085 / -0.243 | 4,701 | -2,130 | 1.0 (6) | reject |
| 12 | T1030 hi30 x0 k0.3 R2 tf0 | 452/50.9/1.391 | 341/47.8/1.232 | 1.196 | 1.110 / 1.103 | 367/51.0/1.403/9,528 | 341/47.8/1.232/7,176 | 250/215 | 0.364 (VOLB .417) | -0.089 / -0.227 | 4,692 | -2,130 | 1.0 (5) | reject |
| 92 | T1030 hi45 x0.3 k0.3 R2 tf0 | 223/54.7/1.548 | 159/48.4/1.240 | 1.204 | 1.349 / 1.314 | 194/54.6/1.551/6,919 | 159/48.4/1.240/3,459 | 184/104 | 0.347 (VOLB .353) | -0.035 / -0.196 | 5,011 | -2,226 | 1.0 (5) | reject |
| 76 | T1030 hi45 x0.15 k0.3 R2 tf0 | 254/53.9/1.491 | 183/47.5/1.206 | 1.169 | 1.346 / 1.313 | 216/53.7/1.515/7,152 | 183/47.5/1.206/3,348 | 190/101 | 0.359 (VOLB .367) | -0.053 / -0.225 | 4,929 | -2,226 | 1.0 (6) | reject |
| 13 | T1030 hi30 x0 k0.3 R2 tf1 | 237/52.3/1.570 | 155/50.3/1.214 | 1.177 | 0.939 / 1.147 | 191/51.3/1.567/6,870 | 155/50.3/1.214/2,926 | 183/88 | 0.400 (VOLB .344) | -0.068 / -0.231 | 4,796 | -2,064 | 1.0 (5) | reject |
| 29 | T1030 hi30 x0.15 k0.3 R2 tf1 | 229/52.4/1.561 | 150/49.3/1.214 | 1.178 | 0.939 / 1.114 | 187/51.9/1.569/6,854 | 150/49.3/1.214/2,863 | 183/86 | 0.400 (VOLB .342) | -0.068 / -0.229 | 4,796 | -2,064 | 1.0 (6) | reject |
| 60 | T1030 hi45 x0 k0.3 R2 tf0 | 259/54.1/1.490 | 184/47.3/1.205 | 1.168 | 1.349 / 1.317 | 220/53.6/1.510/7,122 | 184/47.3/1.205/3,343 | 189/101 | 0.359 (VOLB .367) | -0.054 / -0.225 | 4,920 | -2,226 | 1.0 (5) | reject |

All 10 pass the standalone final check with T1 recomputed from 2020-10-15. None passes the portfolio test. Nine lower Ultra's Sharpe in both periods. #81 raises it slightly (+0.035 / +0.007) but worsens the worst month by 6.3%. #81 is a filtered copy of MOM1030 (daily corr 0.477), which already runs at x4 in Ultra.

### Supplementary (outside the top-10 rule, still chosen on T1 Sharpe only): best stage-c config per family / per ER checkpoint

| family | j | params | six T1 n/WR/PF/$ | six T2 n/WR/PF/$ | T2 PF +4t | norm A / B | corr (top module) | dSharpe T1 / T2 | maxDD | worst month |
|---|---|---|---|---|---|---|---|---|---|---|
| PD_ACCEPT | 755 | oloc1 K6 bk0.1 w1 1300 stop lvl R1 tf1 | 85/58.8/1.557/2,336 | 57/63.2/1.670/2,294 | 1.609 | 0.708 / 1.078 | 0.219 (ORB60 .204) | +0.004 / -0.002 | 4,293 | -2,229 |
| PERIOD_OPEN | 527 | BOTH break w0 930 w1 1530 dmin0.2 s0.2 R2 tf1 | 60/55.0/2.188/3,280 | 54/44.4/1.202/890 | 1.162 | 1.155 / 1.251 | 0.172 (VOLB .136) | +0.033 / -0.027 | 4,682 | -2,454 |
| ON_POS | 111 | z0.15 ins0 cont T945 stop0.35 R2 tf1 | 211/47.4/1.364/6,224 | 139/47.5/1.244/3,705 | 1.214 | 0.962 / 1.078 | 0.316 (ORB60 .263) | -0.167 / -0.189 | 4,469 | -2,402 |
| ER 11:30 | 269 | hi30 x0.15 k0.3 R2 tf1 | 126/56.3/1.641/4,799 | 111/58.6/1.798/5,122 | 1.731 | 1.048 / 1.299 | 0.347 (ORB90 .306) | -0.049 / -0.015 | 4,536 | -2,016 |
| ER 12:30 | 521 | hi30 x0.3 k0.3 R0.5 tf1 | 86/76.7/1.702/1,971 | 76/72.4/1.408/1,349 | 1.332 | 0.870 / 1.271 | 0.227 (VW13b .25) | -0.004 / -0.011 | 4,527 | -2,083 |
| ER 13:30 | 731 | hi30 x0 k0.3 R1 tf1 | 59/66.1/1.724/1,670 | 48/62.5/1.224/522 | 1.158 | 0.868 / 1.515 | 0.199 (MSEQS .264) | -0.020 / -0.017 | 4,404 | -2,163 |

None raises Ultra's Sharpe in both T1 and T2.
- **PD_ACCEPT j755** is the cleanest new standalone edge (T2 PF 1.67 out of sample). But it adds about $65/month, has dSharpe ~0, and loses 2010-14 (norm PF 0.708).
- The **PERIOD_OPEN weekly-open break cluster** (WO, break, with trend: j105/107/131/166/190) holds T2 PF 1.27-1.85. But 2010-19 norm PF is 0.72-0.96 for most of it, and the best T1 pick does not help the portfolio.

## Verdict

**No survivor is accepted.** None of the 5 new families adds to Ultra under the fixed protocol.

- **SQZ_BOX** (time-of-day-normalised squeeze OCO): no edge. Median PF 0.956 / 0.891, and 0 of 12 T1 passers hold in T2.
- **ON_POS** (overnight range position): no edge. Median 0.946 / 0.956; its one survivor hurts Ultra.
- **PD_ACCEPT** (prior-day range acceptance): a weak family. Median T2 0.942, and the T2 lift over the base rate is small (12% vs 8%). A narrow cell holds in 2024-26 (opened inside, 6 consecutive 5m closes beyond PDH/PDL +0.1 ATR, with trend, before 13:00) but fails 2010-14, adds no Sharpe, and goes on the watch list only.
- **PERIOD_OPEN** (weekly/monthly open): a weak family. Median 0.94 / 0.93. The weekly-open break with trend holds in T2, but it is not robust in 2010-19 and adds nothing to the portfolio.
- **ER_PERSIST** (efficiency-ratio persistence) is the only family with real out-of-sample persistence: P(T2 PF >= 1.2) is 42.5% given a T1 pass vs an 18.7% base rate. That persistence is the 10:30 / 11:30 RTH momentum Ultra already harvests through VOLB, MOM1030 (x4), MOM11 and ORB60/90 (daily corr 0.35-0.40). Every ER survivor lowers Ultra's Sharpe, except #81 (a MOM1030 duplicate) which fails the worst-month limit. Low-ER reversion has no edge.

This is consistent with earlier rounds: the robust intraday NQ edges are already in Ultra, and new families either have no edge or re-discover the same RTH momentum.
