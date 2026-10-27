# Fill gap: Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada) vs Tick1 v4.2 (jun-hoy, sin tick sintetico) (20260622-20261023)

- Trades: A 394, B 388, matched 387 (98.2% of A, 99.7% of B); tolerance 3 min inside (date, module, direction). Dates excluded: [20260625].
- $ per contract on the matched trades: A 5,277, B 5,299, B - A +22 (+0.4% of A); per trade +0.06 (95% CI +0.00 .. +0.11); outcome flips 0.3%.
- Delta net / net Standard per trade: +0.4% (95% CI +0.0% .. +0.8%); rule 5A.4 (-15%): CI entirely above -15%: the 1-minute fill model stands.
- Entry fill B - A: mean -0.08 ticks (median +0.00); exit fill B - A: mean -0.03 ticks; entry minute B - A +0.00, hold B - A +0.01 min. (+ = worse for the trade in B).
- Unmatched $: only A 620 (7 trades), only B 119 (1 trades).

## Slippage: how it is counted (once)
- A (Standard, 1-minute fills): NinjaTrader's Slippage = 1 tick is inside the export: market and stop-market entries +1 tick, stop-loss and market exits -1 tick, limit fills 0.
- B: NO synthetic slippage added (--slip-b 0): if B is a tick-series run, its market / stop fills are 1 tick better than Standard by construction and B - A overstates B.
- Real slippage (H5, slip_model.py) is measured against the order level in live / sim exports and replaces the 1-tick assumption only per cell with n >= 15; it is never added on top of this table.

## By order type
```
 otype   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  30          -0.27          0.0          0.03   0.12  -0.21   0.44        0.0   2526   2530            4         0.0         0.00
market 274          -0.09          0.0          0.01   0.04  -0.01   0.09        0.4   3530   3541           11         0.0         0.01
  stop  83           0.01          0.0         -0.18   0.08  -0.04   0.21        0.0   -780   -773            7         0.0         0.00
```

## By module
```
    mod  n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
   CAM3  3           0.00          0.0          0.00   0.00   0.00   0.00        0.0   -259   -259            0         0.0         0.00
  CPI09  4          -0.50         -0.5          0.50   0.00   0.00   0.00        0.0    663    663            0         0.0         0.00
  CRT11  6          -0.33          0.0          0.83  -0.25  -0.86   0.36        0.0   1291   1290           -2         0.0         0.00
    ICT 11           0.00          0.0          0.00   0.00   0.00   0.00        0.0   -100   -100            0         0.0         0.00
 LATE15  8           0.25          0.0         -0.25   0.00  -0.19   0.19        0.0   -285   -285            0         0.0         0.00
 LF0430 13          -0.46          0.0          0.38   0.04  -0.34   0.41        0.0    381    382            0         0.0        -0.08
   LF06 12           0.17          0.0         -0.17   0.00   0.00   0.00        0.0    311    311            0         0.0         0.08
    LON 19          -0.42          0.0          0.05   0.18  -0.34   0.70        0.0   2627   2630            4         0.0         0.00
MOM1030 17           0.12          0.0         -0.12   0.00   0.00   0.00        0.0    162    162            0         0.0         0.00
  MOM11 64           0.08          0.0         -0.06  -0.01  -0.02   0.01        0.0    721    721            0         0.0        -0.02
  MOM13 14          -0.07          0.0          0.07   0.00  -0.23   0.23        0.0   1093   1093            0         0.0         0.43
   MSEQ 11          -0.09          0.0         -0.09   0.09  -0.28   0.46        0.0   -245   -244            1         0.0         0.00
  MSEQS  1           0.00          0.0          0.00   0.00    NaN    NaN        0.0   -124   -124            0         0.0         0.00
   NF05 23           0.13          0.0         -0.09  -0.02  -0.32   0.28        4.3    867    866            0         0.0         0.00
   ON07 34          -0.24          0.0         -0.29   0.26   0.06   0.47        0.0   -850   -841            9         0.0         0.00
  ORB60 14           0.07          0.0         -0.93   0.43  -0.28   1.14        0.0    322    328            6         0.0         0.00
  ORB90 10           0.00          0.0         -0.20   0.10  -0.03   0.23        0.0    147    148            1         0.0         0.00
 ORFAIL  7          -0.14          0.0          0.00   0.07  -0.32   0.47        0.0    426    427            0         0.0         0.00
  REV06 31          -0.19          0.0          0.19   0.00   0.00   0.00        0.0   -621   -621            0         0.0        -0.06
   RV11  3          -1.00         -1.0          1.00   0.00   0.00   0.00        0.0   -387   -387            0         0.0         0.00
   SO04 14          -0.64         -0.5          0.29   0.18  -0.06   0.42        0.0     21     24            2         0.0         0.07
   VOLB 59           0.00          0.0          0.00   0.00  -0.05   0.05        0.0  -1249  -1249            0         0.0         0.00
   VW13  9           0.11          0.0         -0.11   0.00   0.00   0.00        0.0    365    365            0         0.0         0.00
```

## By order type and ET band (entry bar)
```
 otype         band   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  09:30-10:30  10           0.00          0.0          0.00   0.00   0.00   0.00        0.0   -229   -229            0         0.0         0.00
 limit  10:30-12:00   1           0.00          0.0          0.00   0.00    NaN    NaN        0.0    128    128            0         0.0         0.00
 limit noche <09:30  19          -0.42          0.0          0.05   0.18  -0.34   0.70        0.0   2627   2630            4         0.0         0.00
market  09:30-10:30   8          -0.12          0.0          0.25  -0.06  -0.18   0.06        0.0    770    769            0         0.0         0.00
market  10:30-12:00  91           0.05          0.0         -0.07   0.01  -0.02   0.03        0.0    581    581            0         0.0        -0.01
market  12:00-14:00  32          -0.12          0.0          0.19  -0.03  -0.20   0.13        0.0   2930   2929           -1         0.0         0.19
market  14:00-18:00  16           0.00          0.0         -0.06   0.03  -0.21   0.28        0.0   -859   -859            0         0.0         0.00
market noche <09:30 127          -0.19          0.0          0.01   0.09  -0.00   0.18        0.8    109    121           12         0.0        -0.01
  stop  09:30-10:30  45           0.00          0.0         -0.04   0.02  -0.01   0.05        0.0  -1303  -1302            1         0.0         0.00
  stop  10:30-12:00  27           0.04          0.0         -0.41   0.19  -0.19   0.56        0.0    375    380            5         0.0         0.00
  stop  12:00-14:00  10           0.00          0.0         -0.20   0.10  -0.18   0.38        0.0    145    146            1         0.0         0.00
  stop  14:00-18:00   1           0.00          0.0          0.00   0.00    NaN    NaN        0.0      4      4            0         0.0         0.00
```

## Exit kind A (rows) vs B (columns)
```
xkind_b    stop  target  time/flat
xkind_a                           
stop        111       0          0
target        0     168          0
time/flat     0       0        108
```

## Fills outside the 1-minute bar (+/- 1 tick), bars = research/data/mnq_fut.npz; no_bar = fills on dates the bar file does not cover (not checked)
```
side  what  checked  no_bar  feed_offset  outside
   A entry      282     112            0        0
   A  exit      282     112            0        0
side  what  checked  no_bar  feed_offset  outside
   B entry      279     109            0        0
   B  exit      279     109            0        0
```

## Which series filled the orders (seconds != 0 = tick / second series; a Tick1 run needs ~100% in every kind, stops and targets included)
```
side  what      kind   n  seconds_nonzero_pct
   A entry     limit  31                  0.0
   A entry    market 280                  0.0
   A entry      stop  83                  0.0
   A  exit      stop 112                  0.0
   A  exit    target 173                  0.0
   A  exit time/flat 109                  0.0
A: exits at/after 15:58 ET 0 (flatten fills are stamped 15:57:00), exits named by NinjaTrader itself (session close) 0
side  what      kind   n  seconds_nonzero_pct
   B entry     limit  31                 96.8
   B entry    market 274                  0.0
   B entry      stop  83                 96.4
   B  exit      stop 111                 96.4
   B  exit    target 169                 97.6
   B  exit time/flat 108                  0.0
B: exits at/after 15:58 ET 0 (flatten fills are stamped 15:57:00), exits named by NinjaTrader itself (session close) 0
```

## NT vs research (ultra_d4, 20260622-20261008): $ per trade NT - research on matched trades (H3; + = NT better)
```
                                                 side  module  research  nt  matched   pct  nt_minus_research_usd     t  research_usd  nt_usd
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)    CAM3         1   3        1 100.0                  -1.31   NaN          -189    -190
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)   CPI09         3   3        3 100.0                   5.81  1.52           520     537
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)   CRT11         5   5        5 100.0                  -6.70 -0.81          1184    1150
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)     ICT         8   9        7  87.5                   1.07  0.68           172     179
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)  LATE15         8   6        6  75.0                   0.84  2.70          -264    -259
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)  LF0430        13  11       11  84.6                   7.30  1.58           360     441
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)    LF06         9  10        9 100.0                   4.05  1.45           264     301
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)     LON        19  17       17  89.5                   0.32  0.19          2438    2443
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada) MOM1030        14  15       13  92.9                  19.76  0.83          -317     -60
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)   MOM11        58  55       54  93.1                   8.25  1.02           233     678
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)   MOM13        12  12       12 100.0                   3.64  1.20           823     866
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)    MSEQ        10  10       10 100.0                   1.03  2.89          -340    -330
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)   MSEQS         1   1        1 100.0                  -0.50   NaN          -124    -124
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)    NF05        21  20       20  95.2                   4.40  0.61           397     485
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)    ON07        31  30       30  96.8                   2.82  1.04          -652    -567
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)   ORB60        11  11       11 100.0                   3.75  2.49          -261    -220
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)   ORB90         8   8        8 100.0                   3.85  2.08          -239    -208
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)  ORFAIL         9   9        8  88.9                  -6.75 -1.52           874     820
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)   REV06        23  25       23 100.0                  -0.63 -0.34          -365    -380
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)    RV11         1   3        1 100.0                  -0.92   NaN          -111    -112
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)    SO04        10  11       10 100.0                   2.37  1.26            34      58
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)    VOLB        57  50       49  86.0                   1.03  4.11         -1341   -1291
Off v4.3 Slippage=0 (jun-hoy, comision 1,90 agregada)    VW13         8   7        7  87.5                   1.98  0.89           227     241
             Tick1 v4.2 (jun-hoy, sin tick sintetico)    CAM3         1   3        1 100.0                  -1.31   NaN          -189    -190
             Tick1 v4.2 (jun-hoy, sin tick sintetico)   CPI09         3   3        3 100.0                   5.81  1.52           520     537
             Tick1 v4.2 (jun-hoy, sin tick sintetico)   CRT11         5   5        5 100.0                  -6.90 -0.81          1184    1149
             Tick1 v4.2 (jun-hoy, sin tick sintetico)     ICT         8   9        7  87.5                   1.07  0.68           172     179
             Tick1 v4.2 (jun-hoy, sin tick sintetico)  LATE15         8   6        6  75.0                   0.84  3.33          -264    -259
             Tick1 v4.2 (jun-hoy, sin tick sintetico)  LF0430        13  11       11  84.6                   7.25  1.55           360     440
             Tick1 v4.2 (jun-hoy, sin tick sintetico)    LF06         9  10        9 100.0                   4.05  1.45           264     301
             Tick1 v4.2 (jun-hoy, sin tick sintetico)     LON        19  17       17  89.5                   0.32  0.19          2438    2443
             Tick1 v4.2 (jun-hoy, sin tick sintetico) MOM1030        14  14       13  92.9                  19.76  0.83          -317     -60
             Tick1 v4.2 (jun-hoy, sin tick sintetico)   MOM11        58  55       54  93.1                   8.24  1.02           233     678
             Tick1 v4.2 (jun-hoy, sin tick sintetico)   MOM13        12  12       12 100.0                   3.55  1.17           823     865
             Tick1 v4.2 (jun-hoy, sin tick sintetico)    MSEQ        10  10       10 100.0                   1.18  3.04          -340    -328
             Tick1 v4.2 (jun-hoy, sin tick sintetico)   MSEQS         1   1        1 100.0                  -0.50   NaN          -124    -124
             Tick1 v4.2 (jun-hoy, sin tick sintetico)    NF05        21  20       20  95.2                   4.28  0.59           397     482
             Tick1 v4.2 (jun-hoy, sin tick sintetico)    ON07        31  30       30  96.8                   3.15  1.14          -652    -557
             Tick1 v4.2 (jun-hoy, sin tick sintetico)   ORB60        11  11       11 100.0                   3.84  2.58          -261    -219
             Tick1 v4.2 (jun-hoy, sin tick sintetico)   ORB90         8   8        8 100.0                   3.97  2.18          -239    -207
             Tick1 v4.2 (jun-hoy, sin tick sintetico)  ORFAIL         9   6        5  55.6                   1.40  2.62           414     420
             Tick1 v4.2 (jun-hoy, sin tick sintetico)   REV06        23  25       23 100.0                  -0.63 -0.34          -365    -380
             Tick1 v4.2 (jun-hoy, sin tick sintetico)    RV11         1   3        1 100.0                  -0.92   NaN          -111    -112
             Tick1 v4.2 (jun-hoy, sin tick sintetico)    SO04        10  11       10 100.0                   2.52  1.26            34      59
             Tick1 v4.2 (jun-hoy, sin tick sintetico)    VOLB        57  50       49  86.0                   1.03  4.12         -1341   -1291
             Tick1 v4.2 (jun-hoy, sin tick sintetico)    VW13         8   7        7  87.5                   1.98  0.89           227     241
```
