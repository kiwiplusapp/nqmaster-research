# Fill gap: Tick1 v3 (Set* en 1 min) vs Tick1 v4.1 (brackets en ticks) (20260622-20261023)

- Trades: A 392, B 392, matched 392 (100.0% of A, 100.0% of B); tolerance 3 min inside (date, module, direction).
- $ per contract on the matched trades: A 4,977, B 5,279, B - A +302 (+6.1% of A); per trade +0.77 (95% CI -1.04 .. +2.57); outcome flips 0.8%.
- Entry fill B - A: mean +0.00 ticks (median +0.00); exit fill B - A: mean -1.54 ticks; entry minute B - A +0.00, hold B - A -0.66 min. (+ = worse for the trade in B).
- Unmatched $: only A 0 (0 trades), only B 0 (0 trades).

## Slippage: how it is counted (once)
- A (Standard, 1-minute fills): NinjaTrader's Slippage = 1 tick is inside the export: market and stop-market entries +1 tick, stop-loss and market exits -1 tick, limit fills 0.
- B: NO synthetic slippage added (--slip-b 0): if B is a tick-series run, its market / stop fills are 1 tick better than Standard by construction and B - A overstates B.
- Real slippage (H5, slip_model.py) is measured against the order level in live / sim exports and replaces the 1-tick assumption only per cell with n >= 15; it is never added on top of this table.

## By order type
```
 otype   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  31            0.0          0.0         -0.35   0.18   0.08   0.27        0.0   2644   2649            6         0.0        -0.71
market 277            0.0          0.0         -1.94   0.97  -1.59   3.52        1.1   3078   3346          268         0.0        -0.65
  stop  84            0.0          0.0         -0.67   0.33   0.21   0.46        0.0   -745   -717           28         0.0        -0.70
```

## By module
```
    mod  n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
   CAM3  3            0.0          0.0         -1.00   0.50   0.50   0.50        0.0   -261   -259            2         0.0        -1.67
  CPI09  4            0.0          0.0          0.00   0.00   0.00   0.00        0.0    663    663            0         0.0        -1.00
  CRT11  6            0.0          0.0         -0.33   0.17  -0.16   0.49        0.0   1289   1290            1         0.0        -0.50
    ICT 12            0.0          0.0         -0.50   0.25   0.10   0.40        0.0     16     19            3         0.0        -1.00
 LATE15  8            0.0          0.0          0.00   0.00   0.00   0.00        0.0   -285   -285            0         0.0        -0.25
 LF0430 13            0.0          0.0          3.77  -1.88  -6.54   2.77        0.0    381    356          -24         0.0        -0.38
   LF06 12            0.0          0.0         -0.25   0.12  -0.00   0.25        0.0    309    311            2         0.0        -1.00
    LON 19            0.0          0.0         -0.26   0.13   0.01   0.26        0.0   2628   2630            2         0.0        -0.53
MOM1030 18            0.0          0.0        -34.56  17.28 -16.18  50.74        5.6   -435   -124          311         0.0        -2.00
  MOM11 65            0.0          0.0         -0.18   0.09   0.04   0.14        0.0    820    826            6         0.0        -1.05
  MOM13 14            0.0          0.0         -0.14   0.07  -0.02   0.17        0.0   1092   1093            1         0.0        -0.57
   MSEQ 11            0.0          0.0         -0.09   0.05  -0.04   0.13        0.0   -244   -244            0         0.0        -0.27
  MSEQS  1            0.0          0.0          0.00   0.00    NaN    NaN        0.0   -124   -124            0         0.0         0.00
   NF05 23            0.0          0.0         -2.00   1.00 -12.72  14.72        4.3    864    887           23         0.0         0.30
   ON07 35            0.0          0.0          2.80  -1.40  -6.97   4.17        2.9   -786   -835          -49         0.0         0.54
  ORB60 14            0.0          0.0         -1.07   0.54  -0.16   1.23        0.0    321    328            8         0.0        -0.71
  ORB90 10            0.0          0.0         -0.20   0.10  -0.03   0.23        0.0    147    148            1         0.0        -0.60
 ORFAIL  7            0.0          0.0         -0.29   0.14  -0.14   0.42        0.0    425    426            1         0.0        -0.57
  REV06 31            0.0          0.0         -0.29   0.15   0.06   0.23        0.0   -625   -621            4         0.0        -1.00
   RV11  3            0.0          0.0         -1.00   0.50   0.50   0.50        0.0   -389   -387            2         0.0        -1.00
   SO04 14            0.0          0.0          1.64  -0.82  -3.04   1.40        0.0     20      8          -12         0.0        -0.86
   VOLB 60            0.0          0.0         -0.65   0.32   0.26   0.39        0.0  -1212  -1192           20         0.0        -0.72
   VW13  9            0.0          0.0         -0.11   0.06  -0.05   0.16        0.0    365    365            0         0.0        -1.00
```

## By order type and ET band (entry bar)
```
 otype         band   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  09:30-10:30  11            0.0          0.0         -0.55   0.27   0.12   0.43        0.0   -112   -109            3         0.0        -1.00
 limit  10:30-12:00   1            0.0          0.0          0.00   0.00    NaN    NaN        0.0    128    128            0         0.0        -1.00
 limit noche <09:30  19            0.0          0.0         -0.26   0.13   0.01   0.26        0.0   2628   2630            2         0.0        -0.53
market  09:30-10:30   8            0.0          0.0         -0.12   0.06  -0.16   0.28        0.0    768    769            0         0.0        -0.75
market  10:30-12:00  93            0.0          0.0         -6.88   3.44  -3.04   9.92        1.1     81    401          320         0.0        -1.22
market  12:00-14:00  32            0.0          0.0         -0.19   0.09   0.01   0.18        0.0   2926   2929            3         0.0        -0.66
market  14:00-18:00  16            0.0          0.0         -0.06   0.03  -0.03   0.09        0.0   -859   -859            0         0.0        -0.31
market noche <09:30 128            0.0          0.0          0.88  -0.44  -3.34   2.46        1.6    162    106          -56         0.0        -0.27
  stop  09:30-10:30  46            0.0          0.0         -0.76   0.38   0.32   0.44        0.0  -1264  -1246           18         0.0        -0.85
  stop  10:30-12:00  27            0.0          0.0         -0.70   0.35  -0.01   0.72        0.0    371    380           10         0.0        -0.63
  stop  12:00-14:00  10            0.0          0.0         -0.20   0.10  -0.03   0.23        0.0    145    146            1         0.0        -0.30
  stop  14:00-18:00   1            0.0          0.0          0.00   0.00    NaN    NaN        0.0      4      4            0         0.0         0.00
```

## Exit kind A (rows) vs B (columns)
```
xkind_b    stop  target  time/flat
xkind_a                           
stop        113       1          0
target        0     169          0
time/flat     0       0        109
```

## Fills outside the 1-minute bar (+/- 1 tick), bars = research/data/mnq_fut.npz
```
side  what  checked  no_bar  feed_offset  outside
   A entry      283     109            0        0
   A  exit      283     109           20       52
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
   A  exit      stop 114                  0.0
   A  exit    target 169                  0.0
   A  exit time/flat 109                  0.0
A: exits at/after 15:58 ET 0 (flatten fills are stamped 15:57:00), exits named by NinjaTrader itself (session close) 0
side  what      kind   n  seconds_nonzero_pct
   B entry     limit  31                 96.8
   B entry    market 277                  0.0
   B entry      stop  84                 96.4
   B  exit      stop 113                 96.5
   B  exit    target 170                 97.6
   B  exit time/flat 109                  0.9
B: exits at/after 15:58 ET 0 (flatten fills are stamped 15:57:00), exits named by NinjaTrader itself (session close) 0
```
