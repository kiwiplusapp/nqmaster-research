# Parameter-perturbation robustness audit of the 2027 NQMaster default (2026-10-19)

Trade set audited: `nt_compare --set ultra_d4` (Ultra + SO04 / RV11 / ORFAIL / CAM3; MOM1030 and CPI09 x4, ICT x2, confluence and context rules, MinATR 150). Rebuilt here from every module's ORIGINAL signal code on real Databento NQ 2010-06..2026-10 (`perturb_lib.py`); the rebuild reproduces the committed set row for row (3,895 / 3,897 keys in 2020-10..2023 and 3,359 / 3,360 in 2024-26; the 3 missing rows are CPI09 trades on FOMC/CPI overlap days, u and w identical on every matched row).

## Methods

* Periods: A 2010-14 and B 2015-19 cost-normalised (cost 0.345 % of the daily ATR, P&L in % of ATR, no MinATR), T1 2020-23 and T2 2024-26 real $ per MNQ ($1.90 + 1 tick per side, MinATR 150). FOMC days excluded everywhere.
* Per module 3-5 key parameters (`perturb_lib.SPEC`): anchor / entry time, threshold x ATR, stop fraction, target R, window / lookback. Three perturbation designs:
  * one-at-a-time (OAT): -20 / -10 / +10 / +20 % (clock parameters -30 / -15 / +15 / +30 min; integer parameters rounded);
  * a 5^3 factorial of the first three parameters (same steps) for the plateau search;
  * 200 random joint draws per module (every parameter at once, uniform +-20 % / +-30 min, seeded per module and draw).
* Every cell is re-simulated through the same pipeline as the live set (exit engine, 0.10 ATR minimum stop on structure modules, ORB prior-close trigger, VOLB break-even, MOM1030/MOM13 agreement, confluence A/B, pruned context rules, conflict filter) and evaluated (i) standalone and (ii) inside the portfolio with only that module replaced. MSEQS keeps the base ORB60 short fills as its gate in every cell.
* Whole-system sensitivity: 200 draws with EVERY module at its draw j simultaneously; slippage +1 / +2 / +4 ticks per side on the base.
* Pre-registered scores: frag_IS = mean(share of draws with module PF < 1 in A, in B, in T1; share with portfolio T1 Sharpe > 0.1 below base) -> drop ranking. frag_T2 (T2 PF < 1 share, T2 portfolio Sharpe drop share) is reported, never used to choose. Plateau centre = factorial cell with the highest minimum T1 PF over its 3x3x3 neighbourhood (cells with T1 n < 20 excluded). Smoothing = 3 best centres at 1/3 lot each.
* Acceptance of any change (fixed before looking): T2 Sharpe not lower, T2 maxDD not higher by > 5 %, T2 PF and WR not lower, trade count not lower by > 5 %.

## Base portfolio (2027 default, 1 base contract)

| period | trades | tr/day | WR % | PF | Sharpe | maxDD | net | worst month |
|---|---|---|---|---|---|---|---|---|
| A | 5545.0 | 4.92 | 59.3 | 1.061 | 0.62 | 2146 | 3175 | -563 |
| B | 6011.0 | 4.82 | 60.7 | 1.144 | 1.30 | 1258 | 7702 | -699 |
| T1 | 4804.0 | 5.08 | 66.1 | 1.480 | 3.68 | 4668 | 90892 | -1176 |
| T2 | 3420.0 | 4.93 | 64.8 | 1.506 | 4.07 | 3586 | 87559 | -2182 |

A / B in % of ATR per contract (cost-normalised), T1 / T2 in $ per MNQ.

## Per-module perturbation table (200 joint draws per module)

| module | base PF A/B/T1/T2 | n T1 | n T2 | A PF med (p10) | B PF med (p10) | T1 PF med (p10) | T2 PF med (p10) | % draws PF<1 A/B/T1/T2 | % draws port Sharpe -0.1 T1/T2 | frag_IS | frag_T2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MOM11 | 0.98/0.94/1.17/1.29 | 748 | 556 | 0.99 (0.89) | 0.96 (0.87) | 1.13 (0.98) | 1.19 (0.95) | 52/57/12/20 | 48/61 | 0.42 | 0.41 |
| MOM1030 | 0.91/0.92/1.18/1.13 | 451 | 318 | 0.92 (0.79) | 0.92 (0.82) | 0.88 (0.78) | 1.03 (0.86) | 74/88/85/42 | 76/82 | 0.81 | 0.62 |
| MOM13 | 0.94/0.84/1.28/1.18 | 468 | 310 | 0.93 (0.87) | 0.94 (0.84) | 1.18 (1.09) | 1.16 (0.98) | 88/87/0/12 | 26/24 | 0.50 | 0.18 |
| ON07 | 0.93/0.91/1.15/1.18 | 483 | 328 | 0.97 (0.89) | 1.01 (0.93) | 1.02 (0.92) | 1.01 (0.92) | 64/39/43/42 | 13/38 | 0.40 | 0.41 |
| REV06 | 0.93/0.86/1.18/0.98 | 434 | 326 | 0.95 (0.84) | 0.91 (0.82) | 1.03 (0.87) | 0.97 (0.86) | 68/88/39/66 | 4/1 | 0.50 | 0.34 |
| ORB60 | 1.08/0.98/2.11/1.97 | 209 | 138 | 1.08 (0.98) | 1.02 (0.96) | 2.14 (1.86) | 1.59 (1.36) | 14/32/0/0 | 6/56 | 0.13 | 0.28 |
| ORB90 | 1.18/1.01/1.93/1.64 | 181 | 115 | 1.16 (1.04) | 0.97 (0.91) | 1.85 (1.51) | 1.36 (1.18) | 6/69/0/0 | 2/43 | 0.19 | 0.21 |
| MSEQ | 0.94/1.18/1.55/1.20 | 263 | 187 | 1.03 (0.85) | 1.16 (1.05) | 1.63 (1.16) | 1.01 (0.89) | 39/2/1/47 | 26/58 | 0.17 | 0.53 |
| MSEQS | 1.31/1.24/2.96/1.82 | 31 | 27 | 1.40 (0.85) | 1.31 (0.94) | 1.85 (1.23) | 2.02 (1.30) | 14/16/0/0 | 2/0 | 0.08 | 0.00 |
| CRT11 | 1.19/1.33/1.48/1.86 | 113 | 94 | 1.16 (0.92) | 1.02 (0.91) | 1.10 (0.83) | 1.06 (0.80) | 18/45/28/40 | 56/96 | 0.37 | 0.68 |
| ICT | 0.73/1.15/1.17/1.22 | 87 | 60 | 0.71 (0.59) | 1.12 (0.94) | 1.15 (1.01) | 1.15 (0.98) | 100/18/8/15 | 0/2 | 0.32 | 0.08 |
| LON | 0.89/1.12/1.16/1.49 | 271 | 181 | 0.84 (0.77) | 1.13 (1.05) | 1.11 (1.00) | 1.37 (1.18) | 100/1/10/0 | 0/22 | 0.28 | 0.11 |
| VW13 | 0.71/0.84/1.45/1.28 | 347 | 221 | 0.90 (0.77) | 1.00 (0.88) | 1.18 (1.02) | 1.04 (0.82) | 70/50/7/40 | 26/37 | 0.38 | 0.39 |
| VOLB | 1.24/1.32/1.28/1.55 | 693 | 523 | 1.25 (1.12) | 1.33 (1.27) | 1.25 (1.15) | 1.52 (1.35) | 0/0/0/0 | 34/24 | 0.08 | 0.12 |
| LATE15 | 0.93/1.59/1.55/1.28 | 160 | 99 | 0.83 (0.64) | 1.23 (1.03) | 1.35 (1.00) | 0.94 (0.73) | 96/6/10/62 | 0/12 | 0.28 | 0.37 |
| NF05 | 1.20/1.65/1.60/1.31 | 163 | 141 | 1.17 (1.04) | 1.38 (1.25) | 1.25 (1.06) | 1.09 (0.89) | 6/0/3/31 | 1/31 | 0.02 | 0.31 |
| LF06 | 1.17/1.02/1.37/1.36 | 137 | 96 | 1.11 (0.95) | 1.04 (0.93) | 1.20 (1.02) | 1.12 (0.93) | 19/34/9/24 | 0/14 | 0.15 | 0.19 |
| LF0430 | 0.71/0.88/1.51/1.36 | 106 | 90 | 0.94 (0.77) | 1.02 (0.76) | 1.27 (0.88) | 0.98 (0.64) | 61/48/20/54 | 6/32 | 0.34 | 0.43 |
| SO04 | 1.05/1.26/1.64/1.48 | 83 | 67 | 0.85 (0.73) | 1.18 (0.97) | 1.07 (0.79) | 1.37 (1.10) | 84/16/38/2 | 12/0 | 0.38 | 0.01 |
| RV11 | 1.20/1.06/1.99/1.64 | 75 | 45 | 1.14 (0.93) | 1.06 (0.85) | 1.26 (0.94) | 1.18 (0.93) | 20/34/14/24 | 2/2 | 0.17 | 0.13 |
| ORFAIL | 1.27/1.19/1.34/1.22 | 170 | 141 | 1.24 (1.16) | 1.12 (1.06) | 1.17 (1.04) | 1.06 (0.91) | 0/0/6/32 | 3/6 | 0.02 | 0.18 |
| CAM3 | 1.20/1.44/1.56/0.78 | 79 | 59 | 0.86 (0.61) | 1.32 (1.13) | 1.36 (0.89) | 0.83 (0.53) | 88/2/16/56 | 0/0 | 0.27 | 0.28 |
| CPI09 | 1.57/0.97/1.86/3.13 | 38 | 26 | 1.29 (0.97) | 1.08 (0.86) | 1.54 (1.11) | 2.46 (1.32) | 15/37/4/1 | 30/46 | 0.21 | 0.23 |

## One-at-a-time sensitivity (standalone PF range over the 4 levels; portfolio T2 Sharpe change range)

| module | parameter | T1 PF range | T2 PF range | A PF range | B PF range | port dSharpe T1 | port dSharpe T2 | worst level (T1) |
|---|---|---|---|---|---|---|---|---|
| MOM11 | R (pct, base 0.3) | 1.12..1.22 | 1.14..1.25 | 1.00..1.01 | 0.92..0.95 | -0.07..+0.05 | -0.17..-0.03 | +0.2 (T1 PF 1.12) |
| MOM11 | sk (pct, base 0.25) | 1.10..1.16 | 1.15..1.25 | 0.98..1.00 | 0.95..0.96 | -0.12..-0.04 | -0.18..-0.03 | +0.2 (T1 PF 1.10) |
| MOM11 | t (time, base 660) | 0.91..1.29 | 0.96..1.43 | 0.95..1.30 | 0.91..1.16 | -0.23..-0.08 | -0.48..+0.09 | +15 (T1 PF 0.91) |
| MOM1030 | H (int, base 60) | 1.18..1.19 | 1.09..1.10 | 0.89..0.92 | 0.93..0.93 | +0.00..+0.01 | -0.01..+0.00 | -0.1 (T1 PF 1.18) |
| MOM1030 | R (pct, base 0.3) | 1.10..1.24 | 1.08..1.16 | 0.88..0.93 | 0.89..0.95 | -0.15..+0.01 | -0.01..+0.05 | +0.1 (T1 PF 1.10) |
| MOM1030 | sk (pct, base 0.2) | 1.07..1.30 | 1.05..1.14 | 0.90..0.97 | 0.91..1.05 | -0.23..+0.08 | -0.14..-0.05 | +0.1 (T1 PF 1.07) |
| MOM1030 | t (time, base 630) | 0.84..1.11 | 0.92..1.14 | 0.91..1.00 | 0.96..1.01 | -0.35..-0.03 | -0.39..-0.18 | +15 (T1 PF 0.84) |
| MOM13 | H (int, base 240) | 1.28..1.28 | 1.18..1.18 | 0.94..0.94 | 0.84..0.84 | +0.00..+0.00 | +0.00..+0.00 | -0.2 (T1 PF 1.28) |
| MOM13 | R (pct, base 1.0) | 1.26..1.32 | 1.16..1.26 | 0.93..0.96 | 0.81..0.82 | -0.03..-0.01 | -0.01..+0.02 | -0.2 (T1 PF 1.26) |
| MOM13 | sk (pct, base 0.2) | 1.16..1.24 | 1.10..1.33 | 0.91..0.95 | 0.83..0.86 | -0.05..-0.01 | -0.04..+0.03 | -0.2 (T1 PF 1.16) |
| MOM13 | t (time, base 780) | 1.13..1.30 | 0.91..1.37 | 0.91..1.05 | 0.93..1.06 | -0.16..+0.02 | -0.20..-0.02 | -30 (T1 PF 1.13) |
| ON07 | L (int, base 30) | 1.02..1.11 | 0.98..1.09 | 0.94..1.00 | 0.88..0.96 | -0.01..-0.00 | -0.07..-0.03 | -0.1 (T1 PF 1.02) |
| ON07 | R (pct, base 1.0) | 1.13..1.18 | 1.10..1.17 | 0.93..0.93 | 0.89..0.91 | +0.00..+0.00 | -0.03..+0.00 | -0.2 (T1 PF 1.13) |
| ON07 | sk (pct, base 0.2) | 1.13..1.15 | 1.10..1.13 | 0.93..0.95 | 0.88..0.92 | -0.00..+0.01 | -0.02..+0.00 | -0.1 (T1 PF 1.13) |
| ON07 | t (time, base 420) | 0.94..1.12 | 0.91..1.09 | 0.80..1.10 | 0.94..1.08 | -0.14..-0.01 | -0.24..+0.00 | +30 (T1 PF 0.94) |
| REV06 | L (int, base 30) | 1.08..1.21 | 0.92..1.00 | 0.94..0.97 | 0.84..0.92 | -0.02..+0.04 | -0.06..-0.01 | +0.1 (T1 PF 1.08) |
| REV06 | R (pct, base 0.3) | 1.19..1.30 | 0.88..1.04 | 0.91..0.98 | 0.81..0.89 | +0.01..+0.04 | -0.03..+0.02 | +0.1 (T1 PF 1.19) |
| REV06 | sk (pct, base 0.2) | 1.10..1.25 | 0.85..0.97 | 0.84..0.92 | 0.84..0.91 | +0.00..+0.04 | -0.04..-0.00 | -0.1 (T1 PF 1.10) |
| REV06 | t (time, base 360) | 0.91..1.13 | 0.93..1.00 | 0.81..1.22 | 0.82..0.91 | -0.05..+0.04 | +0.01..+0.03 | -30 (T1 PF 0.91) |
| ORB60 | cap (pct, base 0.35) | 1.89..2.23 | 1.45..1.98 | 1.00..1.18 | 1.00..1.02 | -0.06..+0.03 | -0.10..-0.01 | -0.2 (T1 PF 1.89) |
| ORB60 | pb (pct, base 0.44) | 1.98..2.22 | 1.82..2.03 | 1.08..1.16 | 0.97..1.05 | -0.05..+0.02 | -0.06..-0.01 | +0.2 (T1 PF 1.98) |
| ORB60 | rm (int, base 60) | 1.86..2.54 | 1.47..1.93 | 0.98..1.28 | 0.94..0.99 | -0.09..+0.03 | -0.21..-0.04 | -0.2 (T1 PF 1.86) |
| ORB60 | t1 (pct, base 0.6) | 2.08..2.14 | 1.75..2.14 | 1.06..1.16 | 0.96..1.05 | -0.03..+0.01 | -0.05..+0.03 | -0.2 (T1 PF 2.08) |
| ORB90 | cap (pct, base 0.35) | 1.50..2.10 | 1.17..1.65 | 1.05..1.15 | 0.93..1.08 | -0.07..+0.03 | -0.07..-0.00 | -0.2 (T1 PF 1.50) |
| ORB90 | pb (pct, base 0.44) | 1.83..1.95 | 1.55..1.64 | 1.15..1.22 | 0.97..1.05 | -0.02..+0.02 | -0.04..-0.01 | -0.2 (T1 PF 1.83) |
| ORB90 | rm (int, base 90) | 1.84..2.54 | 1.40..1.51 | 1.06..1.36 | 0.87..1.01 | -0.01..+0.11 | -0.10..-0.06 | +0.2 (T1 PF 1.84) |
| ORB90 | t1 (pct, base 0.6) | 1.80..1.96 | 1.44..1.76 | 1.08..1.17 | 1.01..1.04 | -0.02..+0.01 | -0.04..+0.02 | -0.2 (T1 PF 1.80) |
| MSEQ | N (int, base 5) | 1.16..2.08 | 0.90..0.99 | 1.06..1.13 | 1.13..1.41 | -0.21..+0.00 | -0.23..-0.18 | -0.2 (T1 PF 1.16) |
| MSEQ | R (pct, base 0.5) | 1.48..1.67 | 1.09..1.23 | 0.89..1.04 | 1.24..1.31 | -0.02..+0.04 | -0.04..-0.03 | -0.1 (T1 PF 1.48) |
| MSEQ | sk (pct, base 1.75) | 1.53..1.71 | 0.98..1.27 | 0.88..1.10 | 1.18..1.32 | -0.02..+0.04 | -0.08..-0.03 | -0.1 (T1 PF 1.53) |
| MSEQ | ws (time, base 630) | 1.41..1.68 | 1.00..1.13 | 0.81..1.01 | 1.03..1.14 | -0.07..+0.01 | -0.28..-0.00 | -30 (T1 PF 1.41) |
| MSEQS | N (int, base 5) | 1.19..1.30 | 1.27..2.44 | 0.85..2.52 | 1.04..1.77 | -0.10..-0.03 | -0.09..-0.01 | +0.1 (T1 PF 1.19) |
| MSEQS | R (pct, base 0.75) | 2.54..3.00 | 1.65..2.45 | 1.29..1.44 | 1.26..1.33 | -0.00..+0.00 | -0.01..+0.01 | +0.1 (T1 PF 2.54) |
| MSEQS | sk (pct, base 1.75) | 1.65..3.14 | 1.63..2.29 | 1.34..1.73 | 1.43..1.49 | -0.04..+0.00 | -0.01..+0.01 | -0.2 (T1 PF 1.65) |
| MSEQS | ws (time, base 630) | 2.65..2.96 | 1.82..2.26 | 1.31..2.56 | 1.12..1.24 | +0.00..+0.01 | +0.00..+0.02 | +15 (T1 PF 2.65) |
| CRT11 | R (pct, base 2.0) | 1.39..1.51 | 1.69..1.96 | 1.16..1.27 | 1.26..1.29 | -0.01..+0.02 | -0.05..+0.03 | -0.2 (T1 PF 1.39) |
| CRT11 | mr (pct, base 0.5) | 1.36..1.57 | 1.69..1.94 | 1.09..1.30 | 1.26..1.33 | -0.06..+0.03 | -0.05..+0.00 | -0.1 (T1 PF 1.36) |
| CRT11 | off (time, base 0) | 0.83..1.21 | 0.71..1.32 | 0.96..1.45 | 0.97..1.08 | -0.27..-0.04 | -0.71..-0.33 | -30 (T1 PF 0.83) |
| ICT | M (int, base 20) | 1.13..1.17 | 1.18..1.22 | 0.71..0.74 | 1.12..1.15 | -0.01..+0.00 | -0.01..+0.00 | -0.2 (T1 PF 1.13) |
| ICT | R (pct, base 1.0) | 1.09..1.18 | 1.08..1.17 | 0.58..0.65 | 1.05..1.18 | -0.01..+0.01 | -0.04..-0.03 | -0.2 (T1 PF 1.09) |
| ICT | mr (pct, base 0.25) | 0.94..1.13 | 0.96..1.22 | 0.69..0.84 | 0.73..1.18 | -0.03..-0.00 | -0.09..+0.01 | -0.2 (T1 PF 0.94) |
| ICT | we (time, base 630) | 1.07..1.33 | 1.04..1.43 | 0.74..0.84 | 1.14..1.39 | -0.01..+0.05 | -0.01..+0.04 | +30 (T1 PF 1.07) |
| LON | R (pct, base 2.0) | 1.11..1.22 | 1.41..1.45 | 0.85..0.88 | 1.11..1.13 | -0.02..+0.04 | -0.02..-0.01 | -0.2 (T1 PF 1.11) |
| LON | mr (pct, base 0.25) | 1.15..1.24 | 1.13..1.59 | 0.88..0.95 | 1.05..1.10 | -0.02..+0.04 | -0.13..+0.04 | +0.2 (T1 PF 1.15) |
| LON | re (time, base 180) | 0.91..1.19 | 1.27..1.45 | 0.76..0.86 | 1.08..1.23 | -0.08..+0.02 | -0.07..-0.04 | -30 (T1 PF 0.91) |
| LON | we (time, base 360) | 1.14..1.16 | 1.45..1.51 | 0.88..0.89 | 1.11..1.13 | -0.01..+0.00 | -0.02..+0.01 | -15 (T1 PF 1.14) |
| VW13 | R (pct, base 0.5) | 1.29..1.35 | 1.19..1.43 | 0.62..0.80 | 0.86..0.92 | -0.04..-0.02 | -0.02..+0.01 | +0.2 (T1 PF 1.29) |
| VW13 | T (time, base 1300) | 0.86..1.40 | 0.76..1.10 | 0.84..1.22 | 0.88..1.08 | -0.14..-0.01 | -0.25..-0.09 | -30 (T1 PF 0.86) |
| VW13 | s (pct, base 0.15) | 1.30..1.39 | 1.21..1.32 | 0.58..0.82 | 0.82..0.91 | -0.06..-0.01 | -0.02..+0.03 | +0.2 (T1 PF 1.30) |
| VW13 | x (pct, base 1.0) | 1.35..1.46 | 1.15..1.35 | 0.73..0.76 | 0.83..0.86 | -0.01..+0.00 | -0.03..+0.03 | -0.2 (T1 PF 1.35) |
| VOLB | R (pct, base 2.0) | 1.24..1.30 | 1.52..1.61 | 1.23..1.27 | 1.28..1.34 | -0.03..-0.01 | -0.07..+0.12 | -0.2 (T1 PF 1.24) |
| VOLB | hold (int, base 400) | 1.28..1.29 | 1.55..1.56 | 1.24..1.26 | 1.32..1.33 | +0.00..+0.01 | +0.00..+0.02 | -0.2 (T1 PF 1.28) |
| VOLB | k (pct, base 0.45) | 1.11..1.25 | 1.17..1.61 | 1.08..1.39 | 1.21..1.37 | -0.24..-0.06 | -0.21..+0.24 | -0.2 (T1 PF 1.11) |
| VOLB | w1 (time, base 1500) | 1.27..1.30 | 1.52..1.55 | 1.23..1.25 | 1.31..1.34 | -0.02..+0.02 | -0.06..+0.00 | -30 (T1 PF 1.27) |
| LATE15 | R (pct, base 0.5) | 1.53..1.67 | 1.15..1.27 | 0.87..1.04 | 1.45..1.69 | +0.00..+0.01 | -0.01..-0.01 | -0.1 (T1 PF 1.53) |
| LATE15 | T (time, base 1500) | 0.90..2.07 | 0.75..0.88 | 0.67..0.90 | 1.08..1.36 | -0.05..+0.05 | -0.12..-0.05 | +15 (T1 PF 0.90) |
| LATE15 | k (pct, base 0.3) | 1.48..1.77 | 1.07..1.26 | 0.87..1.01 | 1.39..1.66 | +0.00..+0.02 | -0.02..-0.00 | -0.2 (T1 PF 1.48) |
| LATE15 | x (pct, base 0.5) | 1.52..1.73 | 1.15..1.30 | 0.91..1.01 | 1.36..1.66 | -0.00..+0.01 | -0.04..-0.01 | -0.1 (T1 PF 1.52) |
| NF05 | A (time, base 2000) | 1.19..1.43 | 0.89..1.22 | 0.96..1.19 | 1.38..1.40 | -0.05..+0.01 | -0.06..+0.03 | +30 (T1 PF 1.19) |
| NF05 | R (pct, base 2.0) | 1.51..1.65 | 1.27..1.30 | 1.15..1.20 | 1.57..1.62 | -0.01..+0.00 | -0.02..+0.01 | -0.2 (T1 PF 1.51) |
| NF05 | k (pct, base 0.2) | 1.34..1.74 | 1.19..1.39 | 1.12..1.18 | 1.54..1.60 | -0.03..+0.03 | -0.04..+0.04 | -0.2 (T1 PF 1.34) |
| NF05 | x (pct, base 0.35) | 1.34..1.61 | 1.17..1.34 | 1.18..1.36 | 1.55..1.84 | -0.05..+0.02 | -0.06..+0.00 | -0.2 (T1 PF 1.34) |
| LF06 | A (time, base 400) | 1.08..1.42 | 0.79..1.49 | 0.89..1.32 | 0.97..1.17 | -0.02..-0.01 | -0.11..+0.03 | +15 (T1 PF 1.08) |
| LF06 | R (pct, base 0.5) | 1.42..1.48 | 1.12..1.44 | 1.07..1.20 | 0.95..1.05 | +0.01..+0.02 | -0.05..-0.01 | -0.1 (T1 PF 1.42) |
| LF06 | k (pct, base 0.2) | 1.34..1.48 | 1.14..1.33 | 1.04..1.16 | 1.00..1.10 | +0.00..+0.01 | -0.06..-0.02 | +0.2 (T1 PF 1.34) |
| LF06 | x (pct, base 0.2) | 1.47..1.67 | 1.00..1.59 | 1.10..1.24 | 0.93..1.20 | +0.01..+0.06 | -0.06..+0.00 | -0.1 (T1 PF 1.47) |
| LF0430 | A (time, base 400) | 0.70..1.40 | 0.65..1.28 | 0.83..1.12 | 0.63..1.42 | -0.08..-0.01 | -0.12..-0.01 | +30 (T1 PF 0.70) |
| LF0430 | R (pct, base 0.5) | 1.42..1.72 | 1.34..1.47 | 0.67..0.73 | 0.84..0.93 | -0.01..+0.02 | -0.02..+0.01 | -0.1 (T1 PF 1.42) |
| LF0430 | k (pct, base 0.35) | 1.39..1.74 | 1.34..1.45 | 0.71..0.77 | 0.85..0.96 | -0.02..+0.02 | -0.02..+0.01 | -0.2 (T1 PF 1.39) |
| LF0430 | x (pct, base 0.1) | 1.36..2.15 | 0.95..1.41 | 0.69..0.85 | 0.90..0.95 | +0.00..+0.02 | -0.06..+0.05 | -0.1 (T1 PF 1.36) |
| SO04 | R (pct, base 1.0) | 1.63..1.76 | 1.22..1.55 | 0.88..1.02 | 1.17..1.25 | -0.01..+0.00 | -0.03..-0.00 | +0.1 (T1 PF 1.63) |
| SO04 | T (time, base 400) | 0.71..1.47 | 1.15..1.61 | 0.87..1.02 | 1.00..1.66 | -0.09..-0.01 | -0.01..+0.04 | -30 (T1 PF 0.71) |
| SO04 | s (pct, base 0.15) | 1.53..1.71 | 1.11..1.76 | 0.88..0.99 | 1.10..1.19 | -0.03..-0.00 | -0.05..+0.01 | -0.2 (T1 PF 1.53) |
| SO04 | x (pct, base 0.35) | 0.93..2.03 | 1.15..2.11 | 1.02..1.28 | 1.25..1.33 | -0.10..+0.01 | -0.01..+0.03 | -0.2 (T1 PF 0.93) |
| RV11 | R (pct, base 1.0) | 1.84..2.06 | 1.51..1.66 | 1.18..1.29 | 0.96..1.16 | -0.01..+0.01 | -0.01..-0.00 | -0.1 (T1 PF 1.84) |
| RV11 | T (time, base 1100) | 0.94..1.62 | 1.40..1.65 | 0.98..1.27 | 0.87..1.24 | -0.07..-0.02 | -0.03..+0.02 | -30 (T1 PF 0.94) |
| RV11 | k (pct, base 0.15) | 1.83..2.17 | 1.12..1.60 | 1.14..1.31 | 0.96..1.15 | -0.00..+0.01 | -0.03..+0.00 | +0.2 (T1 PF 1.83) |
| RV11 | lim (pct, base 0.8) | 1.21..1.52 | 1.02..1.38 | 1.09..1.28 | 0.83..1.20 | -0.05..-0.01 | -0.03..+0.01 | +0.2 (T1 PF 1.21) |
| RV11 | x (pct, base 0.25) | 1.84..2.13 | 1.45..1.86 | 1.15..1.38 | 1.01..1.07 | -0.00..+0.00 | -0.01..+0.01 | -0.2 (T1 PF 1.84) |
| ORFAIL | T (int, base 15) | 1.11..1.34 | 0.94..1.22 | 1.14..1.32 | 1.06..1.12 | -0.07..+0.01 | -0.08..+0.01 | +0.2 (T1 PF 1.11) |
| ORFAIL | bk (pct, base 0.1) | 1.20..1.34 | 0.95..1.22 | 1.17..1.27 | 1.15..1.23 | -0.05..+0.01 | -0.10..+0.03 | +0.2 (T1 PF 1.20) |
| ORFAIL | w1 (time, base 1400) | 1.34..1.34 | 1.22..1.23 | 1.27..1.27 | 1.18..1.19 | +0.00..+0.00 | +0.00..+0.01 | -30 (T1 PF 1.34) |
| CAM3 | camf (pct, base 0.275) | 0.80..1.65 | 0.41..1.43 | 0.73..1.04 | 1.27..1.40 | -0.04..+0.02 | -0.05..+0.04 | +0.2 (T1 PF 0.80) |
| CAM3 | conf (int, base 10) | 1.52..1.62 | 0.78..0.81 | 1.14..1.22 | 1.44..1.51 | -0.01..+0.00 | +0.00..+0.00 | +0.2 (T1 PF 1.52) |
| CAM3 | w0 (time, base 1000) | 1.32..1.84 | 0.69..0.97 | 0.85..1.16 | 1.33..1.54 | -0.02..+0.01 | -0.01..+0.00 | -15 (T1 PF 1.32) |
| CAM3 | w1 (time, base 1530) | 1.56..1.59 | 0.49..0.78 | 1.16..1.23 | 1.37..1.43 | +0.00..+0.00 | -0.03..+0.00 | -15 (T1 PF 1.56) |
| CPI09 | R (pct, base 0.5) | 1.51..1.85 | 2.44..2.81 | 1.34..1.51 | 0.93..1.01 | -0.07..-0.01 | -0.09..-0.04 | -0.2 (T1 PF 1.51) |
| CPI09 | T (int, base 60) | 1.05..1.73 | 1.23..4.42 | 0.70..1.59 | 0.96..1.45 | -0.14..-0.02 | -0.39..-0.01 | +0.2 (T1 PF 1.05) |
| CPI09 | k (pct, base 0.35) | 1.34..1.73 | 1.22..2.31 | 1.27..1.42 | 0.89..0.96 | -0.09..-0.04 | -0.27..-0.07 | -0.2 (T1 PF 1.34) |
| CPI09 | x (pct, base 0.05) | 1.71..1.97 | 3.13..3.34 | 1.21..1.81 | 0.97..0.97 | -0.04..+0.01 | +0.00..+0.03 | +0.2 (T1 PF 1.71) |

## Fragility ranking (frag_IS, pre-registered; frag_T2 for information)

| rank | module | frag_IS | frag_IS (relative, PF < 0.9 x base) | frag_T2 | base cell rank among plateau candidates | candidates | plateau centre (eps) | min T1 PF around base | min T1 PF around centre | centre T2 PF vs base |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | MOM1030 | 0.810 | 0.484 | 0.622 | 22 | 27 | {"sk": -0.1, "t": -15} | 0.79 | 0.87 | 0.85 vs 1.13 |
| 2 | MOM13 | 0.503 | 0.170 | 0.185 | 11 | 27 | {"R": 0.1, "sk": 0.1, "t": 15} | 1.12 | 1.16 | 1.08 vs 1.18 |
| 3 | REV06 | 0.498 | 0.191 | 0.338 | 8 | 27 | {"L": -0.1, "sk": -0.1, "t": 15} | 0.96 | 1.04 | 0.90 vs 0.98 |
| 4 | MOM11 | 0.424 | 0.207 | 0.405 | 20 | 27 | {"R": 0.1, "sk": 0.1, "t": -15} | 0.86 | 1.09 | 1.48 vs 1.29 |
| 5 | ON07 | 0.399 | 0.171 | 0.405 | 16 | 27 | {"L": -0.1, "sk": 0.1, "t": -15} | 0.89 | 0.97 | 0.94 vs 1.18 |
| 6 | VW13 | 0.384 | 0.266 | 0.385 | 13 | 27 | {"T": 15, "x": 0.1} | 0.93 | 1.15 | 1.02 vs 1.28 |
| 7 | SO04 | 0.375 | 0.531 | 0.010 | 11 | 27 | {"T": 15, "s": 0.1, "x": 0.1} | 0.81 | 1.14 | 1.26 vs 1.48 |
| 8 | CRT11 | 0.369 | 0.667 | 0.682 | 5 | 27 | {"R": 0.1, "mr": 0.1} | 1.13 | 1.17 | 1.76 vs 1.86 |
| 9 | LF0430 | 0.340 | 0.195 | 0.427 | 5 | 27 | {"k": 0.1, "x": 0.1} | 1.06 | 1.21 | 1.04 vs 1.36 |
| 10 | ICT | 0.316 | 0.175 | 0.082 | 2 | 27 | {"we": -15} | 1.11 | 1.11 | 1.43 vs 1.22 |
| 11 | LATE15 | 0.281 | 0.491 | 0.367 | 17 | 27 | {"T": -15, "k": 0.1, "x": 0.1} | 0.84 | 1.23 | 0.90 vs 1.28 |
| 12 | LON | 0.278 | 0.121 | 0.110 | 15 | 27 | {"R": 0.1, "re": 15, "we": 15} | 1.01 | 1.07 | 1.29 vs 1.49 |
| 13 | CAM3 | 0.266 | 0.478 | 0.278 | 21 | 27 | {"w0": 15, "w1": 15} | 1.30 | 1.54 | 0.96 vs 0.78 |
| 14 | CPI09 | 0.214 | 0.427 | 0.235 | 4 | 27 | {"x": -0.1} | 1.50 | 1.61 | 3.34 vs 3.13 |
| 15 | ORB90 | 0.193 | 0.149 | 0.215 | 14 | 27 | {"cap": 0.1, "rm": -0.1, "t1": 0.1} | 1.52 | 1.85 | 1.47 vs 1.64 |
| 16 | RV11 | 0.175 | 0.402 | 0.130 | 6 | 27 | {"lim": 0.1, "x": 0.1} | 1.00 | 1.21 | 1.42 vs 1.64 |
| 17 | MSEQ | 0.170 | 0.180 | 0.527 | 16 | 27 | {"N": 0.1, "R": 0.1, "sk": 0.1} | 1.14 | 1.55 | 0.92 vs 1.20 |
| 18 | LF06 | 0.154 | 0.241 | 0.190 | 22 | 27 | {"A": -15, "k": 0.1} | 0.94 | 1.04 | 1.03 vs 1.36 |
| 19 | ORB60 | 0.133 | 0.075 | 0.280 | 11 | 27 | {"cap": 0.1, "rm": 0.1, "t1": 0.1} | 1.91 | 2.11 | 2.02 vs 1.97 |
| 20 | VOLB | 0.084 | 0.129 | 0.117 | 10 | 27 | {"R": 0.1, "k": 0.1, "w1": 15} | 1.21 | 1.24 | 1.54 vs 1.55 |
| 21 | MSEQS | 0.080 | 0.318 | 0.003 | None | 9 | {"N": -0.1, "R": 0.1, "sk": 0.1} | -inf | 1.30 | 1.31 vs 1.82 |
| 22 | NF05 | 0.024 | 0.463 | 0.310 | 9 | 27 | {"x": -0.1} | 1.09 | 1.18 | 1.20 vs 1.31 |
| 23 | ORFAIL | 0.021 | 0.228 | 0.185 | 5 | 27 | {"bk": -0.1, "w1": 15} | 1.16 | 1.16 | 1.12 vs 1.22 |

## Walk-forward tests (decided on T1 / A / B, evaluated on T2)

| test | modules | T1 Sharpe | T2 Sharpe | T2 PF | T2 WR | T2 maxDD | T2 trades | T2 net | A Sharpe | B Sharpe | accepted |
|---|---|---|---|---|---|---|---|---|---|---|---|
| base |  | 3.682 | 4.069 | 1.506 | 64.8 | 3586 | 3420 | 87559 | 0.623 | 1.305 |  |
| drop 1 most fragile | MOM1030 | 3.648 | 4.034 | 1.502 | 64.3 | 4166 | 3318 | 82265 | 0.543 | 1.204 | False |
| drop 2 most fragile | MOM1030, MOM13 | 3.669 | 3.991 | 1.499 | 64.5 | 3595 | 3131 | 77785 | 0.625 | 1.328 | False |
| drop 3 most fragile | MOM1030, MOM13, REV06 | 3.659 | 4.034 | 1.518 | 63.5 | 3748 | 2924 | 77433 | 0.678 | 1.323 | False |
| plateau centre, top-3 fragile | MOM1030, MOM13, REV06 | 3.517 | 3.716 | 1.460 | 64.3 | 4202 | 3447 | 82012 | 0.562 | 1.211 | False |
| plateau centre, all changed modules | 23 modules | 3.368 | 3.224 | 1.400 | 62.8 | 4853 | 3279 | 72358 | 0.751 | 1.670 | False |
| smoothing (3 centres x 1/3 lot), top-3 fragile | MOM1030, MOM13, REV06 | 3.510 | 3.715 | 1.457 | 65.3 | 4189 | 4495 | 81612 | 0.621 | 1.233 | False |
| smoothing, all modules | fractional lots: diversification idea only | 3.226 | 3.078 | 1.372 | 62.9 | 4549 | 9832 | 67273 | 0.661 | 1.608 | False |

Plateau centre applied one module at a time (modules whose T1 plateau centre is not the base cell):

| module | centre eps | module T1 PF | module T2 PF | port dSharpe T1 | port dSharpe T2 | port dPF T2 | port dmaxDD T2 | accepted |
|---|---|---|---|---|---|---|---|---|
| MOM11 | {"R": 0.1, "sk": 0.1, "t": -15} | 1.17 -> 1.16 | 1.29 -> 1.48 | -0.141 | +0.136 | +0.021 | -337 | True |
| MOM1030 | {"sk": -0.1, "t": -15} | 1.18 -> 0.91 | 1.13 -> 0.85 | -0.029 | -0.256 | -0.035 | +992 | False |
| MOM13 | {"R": 0.1, "sk": 0.1, "t": 15} | 1.28 -> 1.19 | 1.18 -> 1.08 | -0.152 | -0.105 | -0.012 | +4 | False |
| ON07 | {"L": -0.1, "sk": 0.1, "t": -15} | 1.15 -> 1.15 | 1.18 -> 0.94 | -0.024 | -0.016 | -0.007 | -119 | False |
| REV06 | {"L": -0.1, "sk": -0.1, "t": 15} | 1.18 -> 1.09 | 0.98 -> 0.90 | +0.011 | -0.012 | -0.003 | -31 | False |
| ORB60 | {"cap": 0.1, "rm": 0.1, "t1": 0.1} | 2.11 -> 2.51 | 1.97 -> 2.02 | +0.037 | -0.036 | +0.001 | +5 | False |
| ORB90 | {"cap": 0.1, "rm": -0.1, "t1": 0.1} | 1.93 -> 2.21 | 1.64 -> 1.47 | +0.058 | -0.103 | -0.012 | +309 | False |
| MSEQ | {"N": 0.1, "R": 0.1, "sk": 0.1} | 1.55 -> 1.99 | 1.20 -> 0.92 | +0.010 | -0.179 | -0.018 | +866 | False |
| MSEQS | {"N": -0.1, "R": 0.1, "sk": 0.1} | 2.96 -> 1.52 | 1.82 -> 1.31 | -0.074 | -0.077 | -0.013 | +0 | False |
| CRT11 | {"R": 0.1, "mr": 0.1} | 1.48 -> 1.57 | 1.86 -> 1.76 | +0.019 | -0.033 | -0.004 | +0 | False |
| ICT | {"we": -15} | 1.17 -> 1.27 | 1.22 -> 1.43 | +0.048 | +0.037 | +0.008 | +0 | True |
| LON | {"R": 0.1, "re": 15, "we": 15} | 1.16 -> 1.08 | 1.49 -> 1.29 | +0.004 | -0.040 | -0.007 | +58 | False |
| VW13 | {"T": 15, "x": 0.1} | 1.45 -> 1.24 | 1.28 -> 1.02 | -0.072 | -0.114 | -0.010 | +208 | False |
| VOLB | {"R": 0.1, "k": 0.1, "w1": 15} | 1.28 -> 1.28 | 1.55 -> 1.54 | -0.048 | -0.090 | -0.012 | +14 | False |
| LATE15 | {"T": -15, "k": 0.1, "x": 0.1} | 1.55 -> 1.88 | 1.28 -> 0.90 | +0.025 | -0.079 | -0.009 | +0 | False |
| NF05 | {"x": -0.1} | 1.60 -> 1.61 | 1.31 -> 1.20 | +0.021 | -0.003 | -0.002 | +0 | False |
| LF06 | {"A": -15, "k": 0.1} | 1.37 -> 1.14 | 1.36 -> 1.03 | -0.009 | -0.056 | -0.011 | +206 | False |
| LF0430 | {"k": 0.1, "x": 0.1} | 1.51 -> 1.80 | 1.36 -> 1.04 | +0.013 | -0.043 | -0.007 | -102 | False |
| SO04 | {"T": 15, "s": 0.1, "x": 0.1} | 1.64 -> 1.67 | 1.48 -> 1.26 | -0.014 | -0.016 | -0.006 | +256 | False |
| RV11 | {"lim": 0.1, "x": 0.1} | 1.99 -> 1.50 | 1.64 -> 1.42 | -0.015 | +0.014 | +0.001 | +0 | True |
| ORFAIL | {"bk": -0.1, "w1": 15} | 1.34 -> 1.32 | 1.22 -> 1.12 | +0.005 | -0.020 | -0.005 | +0 | False |
| CAM3 | {"w0": 15, "w1": 15} | 1.56 -> 1.74 | 0.78 -> 0.96 | +0.008 | -0.009 | -0.001 | +0 | False |
| CPI09 | {"x": -0.1} | 1.86 -> 1.86 | 3.13 -> 3.34 | +0.000 | +0.027 | +0.004 | +0 | True |

## Whole-system sensitivity (every module perturbed at once, 200 draws)

| period | metric | base | median | p10 | p90 | min | max |
|---|---|---|---|---|---|---|---|
| A | sharpe | 0.623 | 0.522 | 0.066 | 1.000 | -0.421 | 1.321 |
| A | pf | 1.061 | 1.052 | 1.006 | 1.099 | 0.959 | 1.135 |
| A | wr | 59.260 | 59.745 | 58.537 | 60.871 | 57.700 | 61.680 |
| A | maxdd | 2146.200 | 2125.350 | 1461.240 | 3190.910 | 1030.800 | 4274.700 |
| A | net | 3175.200 | 2610.000 | 350.760 | 5010.430 | -2137.900 | 6524.000 |
| A | n | 5545.000 | 5500.000 | 5318.600 | 5727.900 | 5056.000 | 5984.000 |
| B | sharpe | 1.305 | 1.142 | 0.838 | 1.445 | 0.159 | 1.748 |
| B | pf | 1.144 | 1.123 | 1.090 | 1.160 | 1.016 | 1.198 |
| B | wr | 60.660 | 60.995 | 60.189 | 61.925 | 59.190 | 63.090 |
| B | maxdd | 1257.600 | 1304.200 | 1021.390 | 1760.350 | 824.800 | 2492.900 |
| B | net | 7702.500 | 6631.250 | 4935.310 | 8285.640 | 849.400 | 10385.700 |
| B | n | 6011.000 | 6054.000 | 5831.700 | 6318.800 | 5491.000 | 6610.000 |
| T1 | sharpe | 3.682 | 2.489 | 2.096 | 2.818 | 1.819 | 3.236 |
| T1 | pf | 1.480 | 1.299 | 1.247 | 1.345 | 1.199 | 1.417 |
| T1 | wr | 66.070 | 64.345 | 63.529 | 65.364 | 62.180 | 66.580 |
| T1 | maxdd | 4667.500 | 4579.000 | 3603.700 | 5739.780 | 2656.800 | 8531.500 |
| T1 | net | 90892.200 | 60567.150 | 51765.460 | 68085.450 | 41902.100 | 79343.900 |
| T1 | n | 4804.000 | 4804.500 | 4634.000 | 5037.200 | 4444.000 | 5235.000 |
| T2 | sharpe | 4.069 | 2.449 | 1.860 | 2.907 | 1.178 | 3.468 |
| T2 | pf | 1.506 | 1.283 | 1.203 | 1.350 | 1.120 | 1.440 |
| T2 | wr | 64.800 | 62.485 | 61.287 | 63.590 | 60.060 | 64.920 |
| T2 | maxdd | 3586.200 | 5562.900 | 4137.210 | 7426.590 | 3127.300 | 10592.700 |
| T2 | net | 87559.000 | 54083.650 | 40914.220 | 65074.610 | 23912.800 | 82958.000 |
| T2 | n | 3420.000 | 3433.000 | 3302.900 | 3594.200 | 3141.000 | 3743.000 |

| period | draws with Sharpe below base | draws with Sharpe > 0.1 below base | draws with PF < 1 |
|---|---|---|---|
| A | 58 % | 50 % | 7 % |
| B | 77 % | 64 % | 0 % |
| T1 | 100 % | 100 % | 0 % |
| T2 | 100 % | 100 % | 0 % |

Correlation across the 200 whole-system draws between T1 and T2 Sharpe: 0.073; between T1 and T2 PF: 0.143.

## Slippage (base set, real views)

| slippage | T1 Sharpe | T1 PF | T1 net | T2 Sharpe | T2 PF | T2 net | T2 maxDD |
|---|---|---|---|---|---|---|---|
| base (1 tick) | 3.682 | 1.480 | 90892 | 4.069 | 1.506 | 87559 | 3586 |
| +1 ticks per side | 3.525 | 1.455 | 86927 | 3.944 | 1.486 | 84807 | 3625 |
| +2 ticks per side | 3.332 | 1.424 | 82176 | 3.822 | 1.467 | 82126 | 3663 |
| +4 ticks per side | 3.010 | 1.375 | 74099 | 3.587 | 1.431 | 76996 | 3896 |


## Honest conclusion

1. **The exact parameter cells are a sharp optimum in 2020-26 and an ordinary cell in 2010-19.** With every parameter of every module
   perturbed at once (+-20 % / +-30 min, 200 draws) the portfolio stays profitable in all 200 draws, but T1 Sharpe falls from 3.68 to a
   median 2.49 (p10 2.10) and T2 from 4.07 to 2.45 (p10 1.86); PF 1.48 -> 1.30 and 1.51 -> 1.28; T2 maxDD $3.6k -> $5.6k median.
   100 % of the draws are below the base by more than 0.1 Sharpe in both T1 and T2. In A 2010-14 and B 2015-19 (never used to choose
   anything) the base cell sits near the middle of the perturbation cloud (50 % / 64 % of draws below it). That is the signature of
   parameters selected with 2020-26 in view: the base cell "knows" 2020-26, not 2010-19. The correlation across draws between T1 and
   T2 Sharpe is 0.07: which perturbation hurts is not predictable from 2020-23.
2. **The fragility is in the clock parameters, not in stops / targets.** Stop fractions, targets and thresholds mostly sit on plateaus
   (OAT PF ranges of a few hundredths). Moving an entry / anchor time by 15 min costs the most: CRT11 candle offset (portfolio T2 Sharpe
   -0.33..-0.71), MOM11 (-0.48), MOM1030 (-0.39), CPI09 window (-0.39), MSEQ window start (-0.28), VW13 (-0.25), ON07 (-0.24).
   This is a real operational risk, not only a statistical one: a 15-minute clock error in NinjaTrader (session template, DST, bar
   timestamps) would remove most of the edge of the time modules.
3. **Fragility ranking (frag_IS, decided on 2010-23 only):** MOM1030 0.81, MOM13 0.50, REV06 0.50, MOM11 0.42, ON07 0.40, VW13 0.38,
   SO04 0.38, CRT11 0.37, LF0430 0.34, ICT 0.32 ... robust: ORFAIL 0.02, NF05 0.02, MSEQS 0.08, VOLB 0.08, ORB60 0.13, LF06 0.15,
   MSEQ 0.17, RV11 0.18. The fragile group is the time-of-day momentum family that only works since 2020 (db_long 2026-10-09).
   Modules whose standalone T2 PF falls below 1 in more than 40 % of the draws: REV06 67 %, LATE15 62 %, CAM3 56 %, LF0430 54 %,
   MSEQ 47 %, MOM1030 43 %, ON07 43 %, CRT11 40 %, VW13 40 %.
4. **None of the pre-registered changes is accepted.**
   * Dropping the 1 / 2 / 3 most fragile modules (MOM1030, MOM13, REV06): T2 Sharpe 4.03 / 3.99 / 4.03 vs 4.07, PF 1.50 / 1.50 / 1.52,
     maxDD +16 % / 0 % / +5 %, net -6 % / -11 % / -12 %, trades -3 / -8 / -15 %. T1 maxDD falls from $4.7k to $3.9k / $3.2k / $3.0k and
     A / B Sharpe rise (drop 3: 0.62 -> 0.68, 1.31 -> 1.32). A robustness / drawdown trade-off, not an improvement: keep as the
     defensive variant (see actions).
   * Re-centring every module on the centre of its T1 plateau: worse everywhere (top-3 fragile: T2 Sharpe 3.72; all 23 modules: 3.22,
     PF 1.40, maxDD +35 %). Applied one module at a time, 4 of 23 centres pass the acceptance test (MOM11, ICT, RV11, CPI09) = chance.
   * Parameter smoothing (3 best plateau cells at 1/3 lot): T2 Sharpe 3.72 (top-3) / 3.08 (all). Rejected; fractional lots are not
     available anyway.
   The exact cells are also the best cells in T2, so "widening" them cannot help in-sample or out-of-sample; what it shows is how
   much of the 2020-26 result depends on the exact minute and threshold choices.
5. **Slippage is not the problem:** +1 / +2 / +4 ticks per side -> T2 Sharpe 3.94 / 3.82 / 3.59, PF 1.49 / 1.47 / 1.43, net
   $87.6k -> $84.8k / $82.1k / $77.0k per contract.

## Recommended 2027 action list

1. **Do not change any parameter.** No plateau re-centring, no smoothing, no drop. The 2027 default stays as is.
2. **Plan with the perturbation cloud, not with the base cell:** per base contract expect Sharpe ~2.5 (p10 ~1.9), PF ~1.3, maxDD
   ~$5.6k (p90 of the T2 draws: see table) instead of 4.1 / 1.51 / $3.6k. This matches the 35 % haircut already used in the account
   simulations; the cloud says ~40 % on Sharpe and +55 % on drawdown. Size accounts for that level.
3. **Verify the clock in NinjaTrader before going live and after every DST change** (bar timestamps of the 11:00 / 10:30 / 13:00 /
   12:00 CRT / 09:30 CPI bars on the chart vs the exchange clock; ModuleHealthReport per module). A 15-minute error silently removes
   most of the time-module edge.
4. **Defensive variant if the edge monitor warns or the January review flags the time modules:** DisableModules = MOM1030,MOM13,REV06
   (T2 Sharpe 4.03, PF 1.52, T1/T2 maxDD $3.0k / $3.7k, -12 % net). It loses little and removes the three most parameter-fragile modules.
5. **January 2027 review watch list** (standalone T2 PF < 1 in > 40 % of the draws): REV06 (already on the list), LATE15, CAM3, LF0430,
   MSEQ, MOM1030, ON07, CRT11, VW13. Review them with the yearly rule (robust16), not with this table alone.
6. Treat this audit as evidence that the 2020-26 Sharpe is partly selection: any future "improvement" that changes a time or threshold
   must beat the base on 2010-19 cost-normalised data as well as T2, otherwise it only moves the cell inside the same cloud.

Files: `perturb_lib.py` (simulators + assembly), `perturb_lab.py` (7,762 cells, 2 processes, 44 min), `perturb_cells.csv`,
`perturb_analysis.py` -> `perturb_lab.json`, `perturb_report.py` -> this file. Module trades per cell in the session scratchpad (not committed).
