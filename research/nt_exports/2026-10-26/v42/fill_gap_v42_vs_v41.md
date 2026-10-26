# Fill gap: Tick1 v4.1 vs Tick1 v4.2 (20260622-20261023)

- Trades: A 392, B 392, matched 392 (100.0% of A, 100.0% of B); tolerance 3 min inside (date, module, direction).
- $ per contract on the matched trades: A 5,279, B 5,349, B - A +70 (+1.3% of A); per trade +0.18 (95% CI -0.77 .. +1.12); outcome flips 0.5%.
- Delta net / net Standard per trade: +1.3% (95% CI -5.7% .. +8.3%); rule 5A.4 (-15%): CI entirely above -15%: the 1-minute fill model stands.
- 49 time exits were decided on another bar in B (hold B - A -1.00 min; strategy mechanics, not price path; their B - A +70 $). Without them: 343 pairs, B - A +0 $ (+0.0% of A), per trade +0.00 (95% CI +0.00 .. +0.00) = +0.0% (CI +0.0% .. +0.0%); flips 0.0%.
- Entry fill B - A: mean +0.00 ticks (median +0.00); exit fill B - A: mean -0.36 ticks; entry minute B - A +0.00, hold B - A -0.12 min. (+ = worse for the trade in B).
- Unmatched $: only A 0 (0 trades), only B 0 (0 trades).

## Slippage: how it is counted (once)
- A (Standard, 1-minute fills): NinjaTrader's Slippage = 1 tick is inside the export: market and stop-market entries +1 tick, stop-loss and market exits -1 tick, limit fills 0.
- B: NO synthetic slippage added (--slip-b 0): if B is a tick-series run, its market / stop fills are 1 tick better than Standard by construction and B - A overstates B.
- Real slippage (H5, slip_model.py) is measured against the order level in live / sim exports and replaces the 1-tick assumption only per cell with n >= 15; it is never added on top of this table.

## By order type
```
 otype   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  31            0.0          0.0          0.00   0.00   0.00   0.00        0.0   2649   2649            0         0.0         0.00
market 277            0.0          0.0         -0.51   0.25  -1.09   1.59        0.7   3346   3416           70         0.0        -0.18
  stop  84            0.0          0.0          0.00   0.00   0.00   0.00        0.0   -717   -717            0         0.0         0.00
```

## By module
```
    mod  n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
   CAM3  3            0.0          0.0          0.00   0.00   0.00   0.00        0.0   -259   -259            0         0.0         0.00
  CPI09  4            0.0          0.0          0.00   0.00   0.00   0.00        0.0    663    663            0         0.0         0.00
  CRT11  6            0.0          0.0          0.00   0.00   0.00   0.00        0.0   1290   1290            0         0.0         0.00
    ICT 12            0.0          0.0          0.00   0.00   0.00   0.00        0.0     19     19            0         0.0         0.00
 LATE15  8            0.0          0.0          0.00   0.00   0.00   0.00        0.0   -285   -285            0         0.0         0.00
 LF0430 13            0.0          0.0         -3.92   1.96  -2.68   6.60        0.0    356    382           26         0.0        -0.31
   LF06 12            0.0          0.0          0.00   0.00   0.00   0.00        0.0    311    311            0         0.0         0.00
    LON 19            0.0          0.0          0.00   0.00   0.00   0.00        0.0   2630   2630            0         0.0         0.00
MOM1030 18            0.0          0.0          0.28  -0.14  -0.41   0.13        0.0   -124   -126           -2         0.0        -0.06
  MOM11 65            0.0          0.0          0.00   0.00   0.00   0.00        0.0    826    826            0         0.0         0.00
  MOM13 14            0.0          0.0          0.00   0.00   0.00   0.00        0.0   1093   1093            0         0.0         0.00
   MSEQ 11            0.0          0.0          0.00   0.00   0.00   0.00        0.0   -244   -244            0         0.0         0.00
  MSEQS  1            0.0          0.0          0.00   0.00    NaN    NaN        0.0   -124   -124            0         0.0         0.00
   NF05 23            0.0          0.0          1.78  -0.89 -14.61  12.83        4.3    887    866          -20         0.0        -0.65
   ON07 35            0.0          0.0         -2.94   1.47  -4.09   7.04        2.9   -835   -784           52         0.0        -0.77
  ORB60 14            0.0          0.0          0.00   0.00   0.00   0.00        0.0    328    328            0         0.0         0.00
  ORB90 10            0.0          0.0          0.00   0.00   0.00   0.00        0.0    148    148            0         0.0         0.00
 ORFAIL  7            0.0          0.0         -0.14   0.07  -0.07   0.21        0.0    426    427            0         0.0        -0.14
  REV06 31            0.0          0.0          0.00   0.00   0.00   0.00        0.0   -621   -621            0         0.0         0.00
   RV11  3            0.0          0.0          0.00   0.00   0.00   0.00        0.0   -387   -387            0         0.0         0.00
   SO04 14            0.0          0.0         -2.21   1.11  -1.06   3.28        0.0      8     24           16         0.0        -0.07
   VOLB 60            0.0          0.0          0.00   0.00   0.00   0.00        0.0  -1192  -1192            0         0.0         0.00
   VW13  9            0.0          0.0          0.00   0.00   0.00   0.00        0.0    365    365            0         0.0         0.00
```

## By order type and ET band (entry bar)
```
 otype         band   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  09:30-10:30  11            0.0          0.0          0.00   0.00   0.00   0.00        0.0   -109   -109            0         0.0         0.00
 limit  10:30-12:00   1            0.0          0.0          0.00   0.00    NaN    NaN        0.0    128    128            0         0.0         0.00
 limit noche <09:30  19            0.0          0.0          0.00   0.00   0.00   0.00        0.0   2630   2630            0         0.0         0.00
market  09:30-10:30   8            0.0          0.0         -0.12   0.06  -0.06   0.18        0.0    769    769            0         0.0        -0.12
market  10:30-12:00  93            0.0          0.0          0.05  -0.03  -0.08   0.03        0.0    401    398           -2         0.0        -0.01
market  12:00-14:00  32            0.0          0.0          0.00   0.00   0.00   0.00        0.0   2929   2929            0         0.0         0.00
market  14:00-18:00  16            0.0          0.0          0.00   0.00   0.00   0.00        0.0   -859   -859            0         0.0         0.00
market noche <09:30 128            0.0          0.0         -1.12   0.56  -2.34   3.46        1.6    106    178           72         0.0        -0.37
  stop  09:30-10:30  46            0.0          0.0          0.00   0.00   0.00   0.00        0.0  -1246  -1246            0         0.0         0.00
  stop  10:30-12:00  27            0.0          0.0          0.00   0.00   0.00   0.00        0.0    380    380            0         0.0         0.00
  stop  12:00-14:00  10            0.0          0.0          0.00   0.00   0.00   0.00        0.0    146    146            0         0.0         0.00
  stop  14:00-18:00   1            0.0          0.0          0.00   0.00    NaN    NaN        0.0      4      4            0         0.0         0.00
```

## Exit kind A (rows) vs B (columns)
```
xkind_b    stop  target  time/flat
xkind_a                           
stop        113       0          0
target        0     170          0
time/flat     0       0        109
```

## Fills outside the 1-minute bar (+/- 1 tick), bars = research/data/mnq_fut.npz
```
side  what  checked  no_bar  feed_offset  outside
   A entry      283     109            0        0
   A  exit      283     109            0        0
side  what  checked  no_bar  feed_offset  outside
   B entry      283     109            0        0
   B  exit      283     109            0        0
```

## Which series filled the orders (seconds != 0 = tick / second series; a Tick1 run needs ~100% in every kind, stops and targets included)
```
side  what      kind   n  seconds_nonzero_pct
   A entry     limit  31                 96.8
   A entry    market 277                  0.0
   A entry      stop  84                 96.4
   A  exit      stop 113                 96.5
   A  exit    target 170                 97.6
   A  exit time/flat 109                  0.9
A: exits at/after 15:58 ET 0 (flatten fills are stamped 15:57:00), exits named by NinjaTrader itself (session close) 0
side  what      kind   n  seconds_nonzero_pct
   B entry     limit  31                 96.8
   B entry    market 277                  0.0
   B entry      stop  84                 96.4
   B  exit      stop 113                 96.5
   B  exit    target 170                 97.6
   B  exit time/flat 109                  0.0
B: exits at/after 15:58 ET 0 (flatten fills are stamped 15:57:00), exits named by NinjaTrader itself (session close) 0
```
