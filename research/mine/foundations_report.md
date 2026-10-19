# Global foundations audit of the 2027 NQMaster default (2026-10-19)

Rebuilt with `perturb_lib.py` (reproduces `nt_compare --set ultra_d4` row for row) on real Databento NQ 2010-06..2026-10. Every module inherits the daily trend filter, the daily ATR (stops, thresholds, cost normalisation, MinATR guard), the ORB pullback threshold and the flat time; they were set in 2026-09 on CFD data and are varied here one at a time, the whole portfolio rebuilt for each value (conflict filter, agreement, confluence, context rules, MinATR 150, MOM1030 / CPI09 x4, ICT x2). A / B = 2010-14 / 2015-19 cost-normalised (0.345 % ATR, P&L in % ATR); T1 / T2 = 2020-23 / 2024-26 real $ per MNQ ($1.90 + 1 tick). `python3 foundations.py check` verified that the default configuration reproduces every original array (ict.day_levels, nt_v2_replica.daily_stats, crt ATRD/TREND, wr60 up20) and the base portfolio.

## Protocol (pre-registered)

```
(written before any result was looked at):
  decide on T1 + A + B: an alternative is a candidate only if its portfolio Sharpe is higher than the base in ALL three of A, B, T1;
  confirm on T2: T2 Sharpe not lower, T2 PF not lower, T2 WR not lower, T2 maxDD not higher by more than 5 %, trade count (T1 and T2)
  not lower by more than 5 %;
  plateau: the adjacent levels of the candidate (previous / next value of the same knob) must not be worse than the base by more than
  0.10 Sharpe in T1, and at least one adjacent level must also beat the base in T1 (a candidate that only wins at one isolated value is
  a spike and is rejected).
  Plateau verdict for the CURRENT choice of each knob: 'plateau' if every adjacent level is within 0.15 Sharpe (T1) and 0.15 (T2) of
  the base and within 0.03 PF; 'edge' if the base is at one end of the tested range and only the inner neighbour qualifies;
  'spike' if an adjacent level loses more than 0.15 Sharpe in T1 or T2.
```

## Base

| configuration | trades (tr/day) A / B / T1 / T2 | WR % | PF | Sharpe | maxDD | worst month |
|---|---|---|---|---|---|---|
| BASE (SMA20 / ATR14 RTH / MinATR 150 / pb 0.44 / flat 15:55) | 5545 (4.92) / 6011 (4.82) / 4804 (5.08) / 3420 (4.93) | 59.2 / 60.7 / 66.1 / 64.8 | 1.062 / 1.144 / 1.480 / 1.504 | 0.63 / 1.30 / 3.68 / 4.06 | 2140 / 1262 / 4636 / 3586 | -562 / -704 / -1176 / -2172 |

## F1 trend

| configuration | trades (tr/day) A / B / T1 / T2 | WR % | PF | Sharpe | maxDD | worst month |
|---|---|---|---|---|---|---|
| trend_sma10 | 5552 (4.93) / 6095 (4.88) / 4761 (5.04) / 3432 (4.95) | 58.6 / 60.9 / 65.1 / 64.1 | 1.040 / 1.152 / 1.404 / 1.444 | 0.41 / 1.36 / 3.26 / 3.62 | 1975 / 1231 / 4968 / 4918 | -610 / -573 / -1141 / -3235 |
| trend_sma15 | 5537 (4.91) / 6037 (4.84) / 4795 (5.07) / 3427 (4.95) | 59.0 / 60.3 / 65.9 / 64.6 | 1.055 / 1.122 / 1.468 / 1.473 | 0.55 / 1.12 / 3.65 / 3.83 | 1886 / 1306 / 4958 / 4059 | -606 / -633 / -1176 / -2654 |
| BASE (SMA20 / ATR14 RTH / MinATR 150 / pb 0.44 / flat 15:55) | 5545 (4.92) / 6011 (4.82) / 4804 (5.08) / 3420 (4.93) | 59.2 / 60.7 / 66.1 / 64.8 | 1.062 / 1.144 / 1.480 / 1.504 | 0.63 / 1.30 / 3.68 / 4.06 | 2140 / 1262 / 4636 / 3586 | -562 / -704 / -1176 / -2172 |
| trend_sma25 | 5531 (4.91) / 5991 (4.80) / 4789 (5.07) / 3409 (4.92) | 59.5 / 60.7 / 66.4 / 64.8 | 1.074 / 1.150 / 1.488 / 1.486 | 0.75 / 1.35 / 3.77 / 4.00 | 1873 / 1260 / 3667 / 3606 | -537 / -701 / -1176 / -2008 |
| trend_sma30 | 5472 (4.86) / 6028 (4.83) / 4702 (4.98) / 3434 (4.96) | 59.5 / 60.8 / 66.2 / 64.7 | 1.072 / 1.149 / 1.450 / 1.458 | 0.72 / 1.33 / 3.56 / 3.88 | 2020 / 1445 / 3667 / 3401 | -659 / -902 / -1176 / -1634 |
| trend_sma50 | 5445 (4.83) / 6011 (4.82) / 4581 (4.85) / 3347 (4.83) | 59.5 / 60.8 / 65.6 / 63.8 | 1.057 / 1.144 / 1.397 / 1.372 | 0.56 / 1.27 / 3.18 / 3.12 | 1946 / 1505 / 3542 / 4059 | -816 / -852 / -1394 / -1936 |
| EMA20 | 5709 (5.07) / 6140 (4.92) / 4819 (5.10) / 3519 (5.08) | 59.2 / 60.8 / 65.8 / 65.2 | 1.069 / 1.152 / 1.462 / 1.512 | 0.71 / 1.38 / 3.63 / 4.09 | 1670 / 1245 / 3879 / 5253 | -610 / -701 / -1176 / -1634 |
| trend_mom5 | 5610 (4.98) / 6160 (4.94) / 4788 (5.07) / 3517 (5.08) | 58.8 / 60.5 / 64.8 / 64.5 | 1.064 / 1.127 / 1.385 / 1.478 | 0.63 / 1.17 / 3.15 / 3.88 | 2031 / 1339 / 5511 / 4918 | -813 / -572 / -1603 / -2056 |
| trend_mom10 | 5593 (4.96) / 6052 (4.85) / 4872 (5.16) / 3500 (5.05) | 59.2 / 60.2 / 65.8 / 63.7 | 1.054 / 1.120 / 1.486 / 1.416 | 0.55 / 1.12 / 3.75 / 3.47 | 2212 / 1408 / 4031 / 4350 | -650 / -665 / -1176 / -2495 |
| trend_mom20 | 5662 (5.02) / 6093 (4.88) / 4826 (5.11) / 3509 (5.06) | 59.9 / 60.8 / 65.3 / 64.3 | 1.077 / 1.181 / 1.411 / 1.425 | 0.77 / 1.60 / 3.32 / 3.59 | 2093 / 1271 / 4035 / 3301 | -733 / -796 / -1607 / -1531 |
| SMA20 & SMA50 agree | 4792 (4.25) / 5322 (4.26) / 4162 (4.40) / 2990 (4.32) | 60.3 / 61.0 / 66.4 / 64.8 | 1.077 / 1.145 / 1.455 / 1.471 | 0.72 / 1.24 / 3.37 / 3.62 | 1396 / 1179 / 3680 / 3105 | -583 / -703 / -1653 / -1856 |
| no trend filter (union +1 / -1) | 8168 (7.25) / 8788 (7.04) / 6866 (7.27) / 4932 (7.12) | 57.3 / 59.0 / 62.4 / 61.4 | 0.998 / 1.091 / 1.261 / 1.281 | -0.03 / 0.99 / 2.73 / 2.94 | 3292 / 1542 / 4807 / 6039 | -849 / -635 / -2431 / -2890 |

Current choice: **spike** (neighbours ['trend_sma15', 'trend_sma25']: worst dSharpe -0.23, max |dPF| 0.032).

| alternative | candidate (Sharpe up A, B, T1) | T2 confirmed | plateau | accepted | dSharpe A/B/T1/T2 | dPF T1/T2 | dWR T1/T2 | dN T1/T2 | dDD T2 |
|---|---|---|---|---|---|---|---|---|---|
| trend_sma10 | no | no | no | **no** | -0.22 / +0.06 / -0.42 / -0.44 | -0.076 / -0.060 | -1.0 / -0.7 | -43 / +12 | +37.1% |
| trend_sma15 | no | no | no | **no** | -0.08 / -0.18 / -0.03 / -0.23 | -0.012 / -0.032 | -0.2 / -0.2 | -9 / +7 | +13.2% |
| trend_sma25 | yes | no | no | **no** | +0.12 / +0.05 / +0.08 / -0.06 | +0.008 / -0.019 | +0.3 / +0.0 | -15 / -11 | +0.5% |
| trend_sma30 | no | no | no | **no** | +0.09 / +0.03 / -0.12 / -0.17 | -0.030 / -0.046 | +0.1 / -0.1 | -102 / +14 | -5.2% |
| trend_sma50 | no | no | no | **no** | -0.07 / -0.03 / -0.51 / -0.94 | -0.083 / -0.132 | -0.5 / -1.0 | -223 / -73 | +13.2% |
| EMA20 | no | no | n/a | **no** | +0.08 / +0.08 / -0.05 / +0.03 | -0.018 / +0.007 | -0.2 / +0.5 | +15 / +99 | +46.5% |
| trend_mom5 | no | no | yes | **no** | +0.00 / -0.13 / -0.54 / -0.18 | -0.095 / -0.027 | -1.3 / -0.3 | -16 / +97 | +37.1% |
| trend_mom10 | no | no | no | **no** | -0.09 / -0.18 / +0.07 / -0.59 | +0.006 / -0.088 | -0.2 / -1.1 | +68 / +80 | +21.3% |
| trend_mom20 | no | no | yes | **no** | +0.14 / +0.30 / -0.36 / -0.47 | -0.070 / -0.080 | -0.7 / -0.5 | +22 / +89 | -7.9% |
| SMA20 & SMA50 agree | no | no | n/a | **no** | +0.09 / -0.07 / -0.32 / -0.43 | -0.025 / -0.034 | +0.4 / -0.1 | -642 / -430 | -13.4% |
| no trend filter (union +1 / -1) | no | no | n/a | **no** | -0.66 / -0.31 / -0.95 / -1.12 | -0.219 / -0.223 | -3.6 / -3.4 | +2062 / +1512 | +68.4% |

## F2 ATR window

| configuration | trades (tr/day) A / B / T1 / T2 | WR % | PF | Sharpe | maxDD | worst month |
|---|---|---|---|---|---|---|
| atr_7 | 5569 (4.94) / 6052 (4.85) / 4696 (5.08) / 3409 (4.92) | 59.3 / 60.8 / 65.7 / 64.3 | 1.071 / 1.155 / 1.438 / 1.472 | 0.72 / 1.41 / 3.36 / 3.78 | 2266 / 1292 / 4696 / 3864 | -586 / -735 / -1349 / -2642 |
| atr_10 | 5540 (4.92) / 6028 (4.83) / 4758 (5.09) / 3413 (4.92) | 59.3 / 60.7 / 65.8 / 64.7 | 1.066 / 1.140 / 1.461 / 1.489 | 0.67 / 1.27 / 3.50 / 3.95 | 2452 / 1289 / 4832 / 3642 | -565 / -733 / -1224 / -2582 |
| BASE (SMA20 / ATR14 RTH / MinATR 150 / pb 0.44 / flat 15:55) | 5545 (4.92) / 6011 (4.82) / 4804 (5.08) / 3420 (4.93) | 59.2 / 60.7 / 66.1 / 64.8 | 1.062 / 1.144 / 1.480 / 1.504 | 0.63 / 1.30 / 3.68 / 4.06 | 2140 / 1262 / 4636 / 3586 | -562 / -704 / -1176 / -2172 |
| atr_20 | 5535 (4.91) / 6006 (4.81) / 4863 (5.09) / 3429 (4.95) | 59.2 / 60.8 / 66.0 / 64.7 | 1.071 / 1.150 / 1.464 / 1.489 | 0.71 / 1.34 / 3.61 / 3.98 | 2268 / 1604 / 4445 / 3452 | -581 / -751 / -1291 / -1855 |
| atr_30 | 5510 (4.89) / 6000 (4.81) / 4866 (5.08) / 3437 (4.96) | 59.2 / 60.8 / 65.6 / 64.4 | 1.070 / 1.142 / 1.437 / 1.435 | 0.69 / 1.27 / 3.44 / 3.59 | 2816 / 1603 / 4448 / 4113 | -631 / -755 / -2456 / -1929 |
| ATR14 of the full Globex range | 5368 (4.76) / 5791 (4.64) / 4715 (4.90) / 3274 (4.72) | 59.5 / 61.1 / 65.4 / 63.8 | 1.054 / 1.153 / 1.421 / 1.403 | 0.53 / 1.36 / 3.13 / 3.25 | 2656 / 1332 / 4508 / 4406 | -648 / -692 / -1495 / -2698 |

Current choice: **spike** (neighbours ['atr_10', 'atr_20']: worst dSharpe -0.18, max |dPF| 0.019).

| alternative | candidate (Sharpe up A, B, T1) | T2 confirmed | plateau | accepted | dSharpe A/B/T1/T2 | dPF T1/T2 | dWR T1/T2 | dN T1/T2 | dDD T2 |
|---|---|---|---|---|---|---|---|---|---|
| atr_7 | no | no | no | **no** | +0.09 / +0.10 / -0.33 / -0.28 | -0.042 / -0.033 | -0.3 / -0.5 | -108 / -11 | +7.7% |
| atr_10 | no | no | no | **no** | +0.04 / -0.03 / -0.18 / -0.11 | -0.019 / -0.015 | -0.3 / -0.1 | -46 / -7 | +1.6% |
| atr_20 | no | no | no | **no** | +0.08 / +0.04 / -0.08 / -0.08 | -0.017 / -0.016 | -0.1 / -0.1 | +59 / +9 | -3.7% |
| atr_30 | no | no | no | **no** | +0.06 / -0.03 / -0.24 / -0.47 | -0.043 / -0.069 | -0.5 / -0.4 | +62 / +17 | +14.7% |
| ATR14 of the full Globex range | no | no | n/a | **no** | -0.10 / +0.05 / -0.55 / -0.81 | -0.059 / -0.102 | -0.6 / -1.0 | -89 / -146 | +22.8% |

## F2 MinATR

| configuration | trades (tr/day) A / B / T1 / T2 | WR % | PF | Sharpe | maxDD | worst month |
|---|---|---|---|---|---|---|
| minatr_100 | 5545 (4.92) / 6011 (4.82) / 4992 (5.10) / 3420 (4.93) | 59.2 / 60.7 / 66.0 / 64.8 | 1.062 / 1.144 / 1.477 / 1.504 | 0.63 / 1.30 / 3.66 / 4.06 | 2140 / 1262 / 4636 / 3586 | -562 / -704 / -1176 / -2172 |
| BASE (SMA20 / ATR14 RTH / MinATR 150 / pb 0.44 / flat 15:55) | 5545 (4.92) / 6011 (4.82) / 4804 (5.08) / 3420 (4.93) | 59.2 / 60.7 / 66.1 / 64.8 | 1.062 / 1.144 / 1.480 / 1.504 | 0.63 / 1.30 / 3.68 / 4.06 | 2140 / 1262 / 4636 / 3586 | -562 / -704 / -1176 / -2172 |
| minatr_200 | 5545 (4.92) / 6011 (4.82) / 3588 (4.98) / 3325 (4.91) | 59.2 / 60.7 / 66.9 / 65.0 | 1.062 / 1.144 / 1.536 / 1.506 | 0.63 / 1.30 / 4.03 / 4.06 | 2140 / 1262 / 2948 / 3586 | -562 / -704 / -1326 / -2172 |
| minatr_250 | 5545 (4.92) / 6011 (4.82) / 2158 (5.10) / 2586 (4.83) | 59.2 / 60.7 / 67.7 / 65.4 | 1.062 / 1.144 / 1.632 / 1.544 | 0.63 / 1.30 / 4.70 / 4.36 | 2140 / 1262 / 2313 / 3586 | -562 / -704 / -909 / -1830 |

Current choice: **plateau (PF moves > 0.03)** (neighbours ['minatr_100', 'minatr_200']: worst dSharpe -0.02, max |dPF| 0.056).

| alternative | candidate (Sharpe up A, B, T1) | T2 confirmed | plateau | accepted | dSharpe A/B/T1/T2 | dPF T1/T2 | dWR T1/T2 | dN T1/T2 | dDD T2 |
|---|---|---|---|---|---|---|---|---|---|
| minatr_100 | no | no | no | **no** | +0.00 / +0.00 / -0.02 / +0.00 | -0.003 / +0.000 | -0.1 / +0.0 | +188 / +0 | +0.0% |
| minatr_200 | no | no | yes | **no** | +0.00 / +0.00 / +0.34 / +0.00 | +0.056 / +0.001 | +0.8 / +0.2 | -1216 / -95 | +0.0% |
| minatr_250 | no | no | yes | **no** | +0.00 / +0.00 / +1.01 / +0.30 | +0.152 / +0.039 | +1.6 / +0.6 | -2646 / -834 | +0.0% |

## F2 MinATR, fixed day index (flat days = 0; A / B unchanged)

| configuration | trades (tr/day) A / B / T1 / T2 | WR % | PF | Sharpe | maxDD | worst month |
|---|---|---|---|---|---|---|
| minatrF_100 | 5545 (4.92) / 6011 (4.82) / 4992 (4.99) / 3420 (4.93) | 59.2 / 60.7 / 66.0 / 64.8 | 1.062 / 1.144 / 1.477 / 1.504 | 0.63 / 1.30 / 3.62 / 4.06 | 2140 / 1262 / 4636 / 3586 | -562 / -704 / -1176 / -2172 |
| MinATR 150 (= base, fixed day index) | 5545 (4.92) / 6011 (4.82) / 4804 (4.80) / 3420 (4.93) | 59.2 / 60.7 / 66.1 / 64.8 | 1.062 / 1.144 / 1.480 / 1.504 | 0.63 / 1.30 / 3.58 / 4.06 | 2140 / 1262 / 4636 / 3586 | -562 / -704 / -1176 / -2172 |
| minatrF_200 | 5545 (4.92) / 6011 (4.82) / 3588 (3.59) / 3325 (4.80) | 59.2 / 60.7 / 66.9 / 65.0 | 1.062 / 1.144 / 1.536 / 1.506 | 0.63 / 1.30 / 3.39 / 4.01 | 2140 / 1262 / 2948 / 3586 | -562 / -704 / -1326 / -2172 |
| minatrF_250 | 5545 (4.92) / 6011 (4.82) / 2158 (2.16) / 2586 (3.73) | 59.2 / 60.7 / 67.7 / 65.4 | 1.062 / 1.144 / 1.632 / 1.544 | 0.63 / 1.30 / 2.98 / 3.80 | 2140 / 1262 / 2313 / 3586 | -562 / -704 / -909 / -1830 |

| alternative | candidate (Sharpe up A, B, T1) | T2 confirmed | plateau | accepted | dSharpe A/B/T1/T2 | dPF T1/T2 | dWR T1/T2 | dN T1/T2 | dDD T2 |
|---|---|---|---|---|---|---|---|---|---|
| minatrF_100 | no | no | no | **no** | +0.00 / +0.00 / -0.06 / +0.00 | -0.003 / +0.000 | -0.1 / +0.0 | +188 / +0 | +0.0% |
| MinATR 150 (= base, fixed day index) | no | no | no | **no** | +0.00 / +0.00 / -0.11 / +0.00 | +0.000 / +0.000 | +0.0 / +0.0 | +0 / +0 | +0.0% |
| minatrF_200 | no | no | no | **no** | +0.00 / +0.00 / -0.29 / -0.05 | +0.056 / +0.001 | +0.8 / +0.2 | -1216 / -95 | +0.0% |
| minatrF_250 | no | no | no | **no** | +0.00 / +0.00 / -0.70 / -0.26 | +0.152 / +0.039 | +1.6 / +0.6 | -2646 / -834 | +0.0% |

## F3 pullback

| configuration | trades (tr/day) A / B / T1 / T2 | WR % | PF | Sharpe | maxDD | worst month |
|---|---|---|---|---|---|---|
| pb_0.3 | 5507 (4.89) / 5921 (4.74) / 4742 (5.02) / 3387 (4.89) | 59.3 / 60.7 / 66.0 / 64.9 | 1.066 / 1.154 / 1.465 / 1.508 | 0.67 / 1.39 / 3.60 / 4.05 | 2159 / 1276 / 4661 / 3586 | -562 / -704 / -1643 / -2172 |
| pb_0.35 | 5522 (4.90) / 5961 (4.78) / 4758 (5.04) / 3394 (4.90) | 59.3 / 60.7 / 66.0 / 64.8 | 1.069 / 1.148 / 1.468 / 1.508 | 0.70 / 1.34 / 3.63 / 4.06 | 2159 / 1227 / 4636 / 3586 | -562 / -704 / -1176 / -2172 |
| BASE (SMA20 / ATR14 RTH / MinATR 150 / pb 0.44 / flat 15:55) | 5545 (4.92) / 6011 (4.82) / 4804 (5.08) / 3420 (4.93) | 59.2 / 60.7 / 66.1 / 64.8 | 1.062 / 1.144 / 1.480 / 1.504 | 0.63 / 1.30 / 3.68 / 4.06 | 2140 / 1262 / 4636 / 3586 | -562 / -704 / -1176 / -2172 |
| pb_0.5 | 5601 (4.97) / 6036 (4.84) / 4827 (5.11) / 3436 (4.96) | 59.3 / 60.7 / 66.1 / 64.8 | 1.066 / 1.149 / 1.472 / 1.506 | 0.67 / 1.34 / 3.63 / 4.06 | 2189 / 1262 / 4636 / 3586 | -562 / -704 / -1426 / -1892 |
| pb_0.6 | 5642 (5.01) / 6078 (4.87) / 4850 (5.13) / 3471 (5.01) | 59.0 / 60.8 / 66.0 / 64.8 | 1.056 / 1.153 / 1.459 / 1.497 | 0.58 / 1.38 / 3.54 / 4.04 | 2373 / 1262 / 5064 / 3586 | -597 / -704 / -1426 / -1892 |
| no pullback filter | 5875 (5.21) / 6328 (5.07) / 5081 (5.38) / 3609 (5.21) | 58.8 / 60.6 / 65.5 / 64.6 | 1.043 / 1.147 / 1.379 / 1.436 | 0.45 / 1.34 / 2.97 / 3.69 | 1929 / 1291 / 4541 / 3892 | -612 / -739 / -2535 / -2006 |

Current choice: **plateau** (neighbours ['pb_0.35', 'pb_0.5']: worst dSharpe -0.06, max |dPF| 0.013).

| alternative | candidate (Sharpe up A, B, T1) | T2 confirmed | plateau | accepted | dSharpe A/B/T1/T2 | dPF T1/T2 | dWR T1/T2 | dN T1/T2 | dDD T2 |
|---|---|---|---|---|---|---|---|---|---|
| pb_0.3 | no | no | no | **no** | +0.04 / +0.09 / -0.08 / -0.01 | -0.015 / +0.003 | -0.1 / +0.1 | -62 / -33 | +0.0% |
| pb_0.35 | no | no | no | **no** | +0.07 / +0.04 / -0.06 / +0.00 | -0.013 / +0.003 | -0.1 / +0.1 | -46 / -26 | +0.0% |
| pb_0.5 | no | no | no | **no** | +0.04 / +0.04 / -0.05 / -0.00 | -0.008 / +0.002 | +0.0 / -0.0 | +23 / +16 | +0.0% |
| pb_0.6 | no | no | no | **no** | -0.05 / +0.08 / -0.14 / -0.02 | -0.021 / -0.008 | -0.1 / -0.0 | +46 / +51 | +0.0% |
| no pullback filter | no | no | no | **no** | -0.18 / +0.04 / -0.72 / -0.37 | -0.101 / -0.069 | -0.6 / -0.2 | +277 / +189 | +8.5% |

## F4 flat

| configuration | trades (tr/day) A / B / T1 / T2 | WR % | PF | Sharpe | maxDD | worst month |
|---|---|---|---|---|---|---|
| flat_1545 | 5545 (4.92) / 6011 (4.82) / 4804 (5.08) / 3420 (4.93) | 59.3 / 60.4 / 65.9 / 64.7 | 1.073 / 1.140 / 1.471 / 1.499 | 0.73 / 1.27 / 3.66 / 3.96 | 1668 / 1274 / 4367 / 3533 | -476 / -731 / -1370 / -2092 |
| flat_1550 | 5545 (4.92) / 6011 (4.82) / 4804 (5.08) / 3420 (4.93) | 59.5 / 60.6 / 65.8 / 64.3 | 1.077 / 1.148 / 1.483 / 1.490 | 0.78 / 1.33 / 3.70 / 3.93 | 1726 / 1345 / 4422 / 3598 | -496 / -770 / -1230 / -2393 |
| BASE (SMA20 / ATR14 RTH / MinATR 150 / pb 0.44 / flat 15:55) | 5545 (4.92) / 6011 (4.82) / 4804 (5.08) / 3420 (4.93) | 59.2 / 60.7 / 66.1 / 64.8 | 1.062 / 1.144 / 1.480 / 1.504 | 0.63 / 1.30 / 3.68 / 4.06 | 2140 / 1262 / 4636 / 3586 | -562 / -704 / -1176 / -2172 |
| flat_1558 | 5545 (4.92) / 6011 (4.82) / 4804 (5.08) / 3420 (4.93) | 59.5 / 60.7 / 66.1 / 65.1 | 1.068 / 1.152 / 1.477 / 1.507 | 0.69 / 1.37 / 3.67 / 4.09 | 2043 / 1193 / 4557 / 3613 | -552 / -640 / -1115 / -2377 |
| flat 16:00 (first bar >= 16:00) | 5545 (4.92) / 6011 (4.82) / 4804 (5.08) / 3420 (4.93) | 59.5 / 60.7 / 66.0 / 64.8 | 1.072 / 1.151 / 1.467 / 1.477 | 0.72 / 1.37 / 3.62 / 3.92 | 1930 / 1327 / 4889 / 3712 | -477 / -747 / -1034 / -2489 |
| flat 16:14 (last bar before the halt) | 5545 (4.92) / 6011 (4.82) / 4804 (5.08) / 3420 (4.93) | 59.3 / 60.9 / 65.8 / 64.8 | 1.067 / 1.143 / 1.442 / 1.480 | 0.68 / 1.29 / 3.48 / 3.96 | 2115 / 1242 / 4762 / 3832 | -502 / -702 / -1156 / -2830 |

Current choice: **plateau** (neighbours ['flat_1550', 'flat_1558']: worst dSharpe -0.13, max |dPF| 0.014).

| alternative | candidate (Sharpe up A, B, T1) | T2 confirmed | plateau | accepted | dSharpe A/B/T1/T2 | dPF T1/T2 | dWR T1/T2 | dN T1/T2 | dDD T2 |
|---|---|---|---|---|---|---|---|---|---|
| flat_1545 | no | no | yes | **no** | +0.10 / -0.03 / -0.02 / -0.10 | -0.009 / -0.006 | -0.2 / -0.1 | +0 / +0 | -1.5% |
| flat_1550 | yes | no | no | **no** | +0.15 / +0.03 / +0.02 / -0.13 | +0.003 / -0.014 | -0.3 / -0.5 | +0 / +0 | +0.3% |
| flat_1558 | no | no | no | **no** | +0.06 / +0.07 / -0.01 / +0.03 | -0.003 / +0.003 | +0.0 / +0.3 | +0 / +0 | +0.7% |
| flat 16:00 (first bar >= 16:00) | no | no | no | **no** | +0.09 / +0.07 / -0.06 / -0.14 | -0.013 / -0.028 | -0.1 / -0.0 | +0 / +0 | +3.5% |
| flat 16:14 (last bar before the halt) | no | no | no | **no** | +0.05 / -0.01 / -0.20 / -0.10 | -0.038 / -0.025 | -0.3 / -0.0 | +0 / +0 | +6.8% |

## Accepted changes

None.

## Module standalone PF (T1 / T2) under the trend alternatives

| module | BASE | trend_sma10 | trend_sma50 | EMA20 | trend_mom10 | SMA20 & SMA50 agree | no trend filter |
|---|---|---|---|---|---|---|---|
| MOM11 | 1.17 / 1.29 | 1.17 / 1.29 | 1.17 / 1.29 | 1.17 / 1.29 | 1.17 / 1.29 | 1.17 / 1.29 | 1.17 / 1.29 |
| MOM1030 | 1.18 / 1.13 | 1.11 / 1.01 | 1.01 / 0.87 | 1.01 / 1.05 | 1.12 / 1.01 | 1.18 / 1.03 | 1.05 / 1.01 |
| MOM13 | 1.28 / 1.18 | 1.19 / 1.28 | 1.28 / 0.90 | 1.26 / 1.19 | 1.32 / 1.10 | 1.32 / 0.99 | 1.09 / 1.12 |
| ON07 | 1.15 / 1.18 | 1.18 / 1.14 | 1.13 / 1.15 | 1.17 / 1.22 | 1.16 / 1.10 | 1.19 / 1.22 | 0.95 / 0.98 |
| REV06 | 1.18 / 0.98 | 1.27 / 0.97 | 1.13 / 1.08 | 1.20 / 1.08 | 1.20 / 1.01 | 1.11 / 1.06 | 1.15 / 0.93 |
| ORB60 | 2.11 / 1.97 | 1.81 / 1.79 | 1.92 / 1.56 | 2.25 / 2.21 | 2.55 / 1.58 | 2.05 / 2.11 | 1.33 / 1.33 |
| ORB90 | 1.93 / 1.64 | 1.67 / 1.39 | 1.66 / 1.38 | 1.97 / 1.47 | 2.27 / 1.12 | 1.76 / 1.71 | 1.36 / 1.23 |
| MSEQ | 1.55 / 1.20 | 1.46 / 1.17 | 1.60 / 0.99 | 1.59 / 1.18 | 1.67 / 1.11 | 1.48 / 1.16 | 1.39 / 1.10 |
| MSEQS | 2.96 / 1.82 | 2.19 / 1.42 | 3.70 / 1.53 | 2.86 / 1.63 | 2.95 / 1.52 | 3.53 / 1.80 | 1.97 / 1.45 |
| CRT11 | 1.48 / 1.86 | 1.87 / 1.62 | 1.20 / 1.60 | 1.62 / 2.14 | 1.67 / 1.76 | 1.37 / 1.56 | 1.12 / 1.75 |
| ICT | 1.17 / 1.22 | 0.92 / 1.22 | 0.90 / 1.21 | 0.96 / 1.27 | 0.96 / 1.32 | 0.99 / 1.33 | 0.96 / 1.16 |
| LON | 1.16 / 1.49 | 1.07 / 1.44 | 1.13 / 1.32 | 1.14 / 1.55 | 1.19 / 1.62 | 1.35 / 1.20 | 0.98 / 1.21 |
| VW13 | 1.45 / 1.28 | 1.28 / 1.32 | 1.48 / 1.18 | 1.41 / 1.45 | 1.39 / 1.11 | 1.58 / 1.30 | 1.07 / 0.98 |
| VOLB | 1.28 / 1.55 | 1.28 / 1.55 | 1.28 / 1.55 | 1.28 / 1.55 | 1.28 / 1.55 | 1.28 / 1.55 | 1.28 / 1.55 |
| LATE15 | 1.55 / 1.28 | 1.47 / 1.78 | 1.77 / 0.93 | 1.54 / 1.29 | 1.39 / 1.07 | 1.43 / 1.01 | 1.37 / 1.04 |
| NF05 | 1.60 / 1.31 | 1.60 / 1.31 | 1.60 / 1.31 | 1.60 / 1.31 | 1.60 / 1.31 | 1.60 / 1.31 | 1.60 / 1.31 |
| LF06 | 1.37 / 1.36 | 1.37 / 1.36 | 1.37 / 1.36 | 1.37 / 1.36 | 1.37 / 1.36 | 1.37 / 1.36 | 1.37 / 1.36 |
| LF0430 | 1.51 / 1.36 | 1.45 / 1.26 | 1.43 / 1.49 | 1.49 / 1.31 | 1.26 / 1.50 | 1.62 / 1.90 | 1.06 / 1.08 |
| SO04 | 1.64 / 1.48 | 1.48 / 1.08 | 1.60 / 1.16 | 1.65 / 1.39 | 1.51 / 1.39 | 1.72 / 1.40 | 1.34 / 1.19 |
| RV11 | 2.03 / 1.57 | 2.03 / 1.57 | 2.03 / 1.57 | 2.03 / 1.57 | 2.03 / 1.57 | 2.03 / 1.57 | 2.03 / 1.57 |
| ORFAIL | 1.32 / 1.22 | 1.32 / 1.21 | 1.23 / 1.13 | 1.18 / 1.22 | 1.24 / 1.23 | 1.32 / 1.15 | 1.18 / 1.03 |
| CAM3 | 1.52 / 0.76 | 1.37 / 0.59 | 1.69 / 0.41 | 1.47 / 0.70 | 1.53 / 0.54 | 1.77 / 0.46 | 1.21 / 0.96 |
| CPI09 | 1.86 / 3.13 | 1.86 / 3.13 | 1.86 / 3.13 | 1.86 / 3.13 | 1.86 / 3.13 | 1.86 / 3.13 | 1.86 / 3.13 |

## Plateau verdicts and conclusions

Reading of the tables (base Sharpe A / B / T1 / T2 = 0.63 / 1.30 / 3.68 / 4.06; T2 is the only period never used to choose anything).

* **F1 daily trend filter.** Removing it (control 'none') costs 0.95 / 1.12 Sharpe in T1 / T2, 0.22 PF, 3.4 WR points and +68 % maxDD, and
  0.66 / 0.31 in 2010-14 / 2015-19: the filter is the single most valuable foundation of the system (ON07, LON, VW13, LF0430, ORFAIL go to
  PF ~1 without it). Its exact form is NOT finely tuned but the base sits on a shallow ridge, not a flat plateau: SMA15 / SMA25 / SMA30 are
  within -0.03 / +0.08 / -0.12 Sharpe in T1 and -0.23 / -0.06 / -0.17 in T2 (PF within 0.05), SMA10 and SMA50 lose 0.4-0.9, EMA20 is
  equivalent (-0.05 / +0.03) but with +46 % T2 maxDD, momentum references (close vs N days ago) and the SMA20 & SMA50 agreement lose 0.2-0.6.
  By the pre-registered rule the current choice is labelled **'spike'** (an adjacent level loses more than 0.15 in T2); the honest wording is
  'local optimum selected on 2020-23 (T1), one step away costs 0.1-0.2 Sharpe out of sample, every neighbour 15-30 is still PF >= 1.45 in
  both real periods'. In 2010-19 (never used for any choice) SMA25 / SMA30 beat SMA20 by +0.05..+0.12, i.e. the old data prefers a slightly
  longer average; SMA25 is the only candidate that wins T1 + A + B, and it fails the T2 confirmation by 0.06 Sharpe / 0.019 PF (DD +0.5 %).
  That is inside noise and is NOT adopted: the rule was fixed in advance and T2 is the only clean out-of-sample period.
* **F2 daily ATR.** The RTH-range definition is a real choice: the full Globex-session range loses 0.55 / 0.81 Sharpe and 0.06 / 0.10 PF
  (stops and thresholds become too wide). The window 14 is again a local optimum: 10 and 20 lose 0.08-0.18 in T1 / T2 (PF -0.02) while
  gaining 0.04-0.08 in 2010-14; 7 and 30 lose 0.25-0.5. Labelled **'spike'** by the rule (worst neighbour -0.18); in practice every window
  7-30 keeps PF >= 1.44 and all four periods positive. **MinATR 150**: a plateau. With a fixed day index (days below the guard count as flat,
  which perturb_lib's own metric does not do and which flatters a higher guard), T1 Sharpe is 3.62 / 3.58 / 3.39 / 2.98 for 100 / 150 /
  200 / 250 and T2 4.06 / 4.06 / 4.01 / 3.80: a higher guard raises PF (fewer, better trades) and lowers the daily Sharpe; 100 adds 188
  trades in 2018-20 for +0.04 Sharpe. Rows of that table must be compared with each other, not with the base row above them.
* **F3 ORB pullback threshold 0.44 ATR.** A genuine **plateau**: 0.30 / 0.35 / 0.50 / 0.60 are within -0.08..-0.14 Sharpe in T1 and
  within 0.02 in T2, PF within 0.02; without the filter ORB loses 0.72 / 0.37 Sharpe and 0.10 / 0.07 PF. The filter matters, its value
  does not.
* **F4 flat time 15:55.** A **plateau**: 15:45 / 15:50 / 15:58 / 16:00 are within -0.06..+0.02 in T1 and -0.14..+0.03 in T2 with
  identical trade counts; holding to 16:14 costs 0.20 / 0.10 Sharpe and +7 % maxDD. 15:50 wins T1 + A + B by 0.02-0.15 and loses T2 by
  0.13 (WR -0.5): noise. 15:58 is +0.03 T2 / -0.01 T1: noise. No reason to move; the live FlattenTime 15:56 sits inside this plateau.

**Accepted changes: none.** No NQMaster property changes from this audit. The foundations were set in 2026-09 on CFD 2020-23 data; on the
16-year real futures data none of the 34 alternatives beats them under the pre-registered rule, the two T1 + A + B candidates (SMA25,
flat 15:50) fail the 2024-26 confirmation by amounts inside noise, and the two controls (no trend filter, no pullback filter) show that
the filters themselves carry 0.4-1.1 Sharpe. What the audit does say is that SMA20 and ATR14 are the best values on the selection period
and only locally best elsewhere (a neighbour costs 0.1-0.2 Sharpe, the 2010-19 data would have picked SMA25 / ATR 7-20); treat them as
'chosen on 2020-23, robust to one step', not as plateau values, and do not re-tune them on 2024-26.

Audit note: the first run of this script left ICT at the base trend / ATR in every cell because `ict_fix.py` defines its own `day_levels`
(not imported from `ict`), so the identity-based patch missed it; the per-module table exposed it (ICT PF identical in every trend cell),
`install()` now patches `ict_fix` explicitly and `post_init()` asserts every patched entry point. The tables above are from the corrected run.

