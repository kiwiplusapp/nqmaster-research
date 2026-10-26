# Fill gap: Off (fills 1 min) vs Tick1 (fills de ticks) (20260622-20261023)

- Trades: A 397, B 392, matched 392 (98.7% of A, 100.0% of B); tolerance 3 min inside (date, module, direction).
- $ per contract on the matched trades: A 4,380, B 4,977, B - A +598 (+13.7% of A); per trade +1.52 (95% CI -1.33 .. +4.38); outcome flips 0.8%.
- Entry fill B - A: mean -0.99 ticks (median -1.00); exit fill B - A: mean -2.06 ticks; entry minute B - A +0.00, hold B - A +2.29 min. (+ = worse for the trade in B).
- Unmatched $: only A 558 (5 trades), only B 0 (0 trades).

## By order type
```
 otype   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  31          -0.26          0.0         -0.16   0.21  -0.11   0.53        0.0   2637   2644            6         0.0         0.71
market 277          -1.08         -1.0         -2.62   1.85  -2.19   5.89        1.1   2566   3078          512         0.0         2.90
  stop  84          -0.98         -1.0         -0.89   0.93   0.43   1.44        0.0   -823   -745           78         0.0         0.83
```

## By module
```
    mod  n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
   CAM3  3          -1.00         -1.0          1.33  -0.17  -1.03   0.70        0.0   -260   -261            0         0.0         1.67
  CPI09  4          -1.50         -1.5         -5.75   3.62  -1.70   8.95        0.0    649    663           14         0.0         1.00
  CRT11  6          -1.33         -1.0          2.33  -0.50  -1.57   0.57        0.0   1292   1289           -3         0.0         0.50
    ICT 12           0.00          0.0          0.00   0.00   0.00   0.00        0.0     16     16            0         0.0         1.00
 LATE15  8          -0.75         -1.0         -0.75   0.75   0.38   1.12        0.0   -291   -285            6         0.0         0.25
 LF0430 13          -1.46         -1.0         -4.77   3.12  -2.35   8.58        0.0    340    381           40         0.0         1.46
   LF06 12          -0.83         -1.0         -2.58   1.71  -1.29   4.71        0.0    289    309           20         0.0         1.42
    LON 19          -0.42          0.0         -0.26   0.34  -0.18   0.86        0.0   2621   2628            6         0.0         0.53
MOM1030 18          -0.89         -1.0         41.11 -20.11 -53.53  13.31        5.6    -73   -435         -362         0.0         3.33
  MOM11 65          -0.91         -1.0        -18.72   9.82  -4.30  23.93        1.5    182    820          638         0.0         6.78
  MOM13 14          -1.00         -1.0         -6.14   3.57  -1.44   8.58        0.0   1042   1092           50         0.0         1.71
   MSEQ 11          -1.00         -1.0         -0.45   0.73   0.26   1.19        0.0   -252   -244            8         0.0         0.27
  MSEQS  1          -1.00         -1.0         -1.00   1.00    NaN    NaN        0.0   -125   -124            1         0.0         0.00
   NF05 23          -0.87         -1.0         -4.61   2.74  -1.27   6.75        4.3    801    864           63         0.0         1.48
   ON07 35          -1.23         -1.0         -1.14   1.19   0.44   1.93        0.0   -828   -786           42         0.0         0.26
  ORB60 14          -0.93         -1.0         -3.64   2.29   0.15   4.42        0.0    289    321           32         0.0         0.79
  ORB90 10          -1.00         -1.0         -4.00   2.50  -0.15   5.15        0.0    122    147           25         0.0         1.60
 ORFAIL  7          -1.14         -1.0         -0.29   0.71   0.24   1.19        0.0    420    425            5         0.0         0.71
  REV06 31          -1.19         -1.0          2.23  -0.52  -3.24   2.21        0.0   -609   -625          -16         0.0         4.65
   RV11  3          -2.00         -2.0          3.00  -0.50  -1.48   0.48        0.0   -387   -389           -2         0.0         1.00
   SO04 14          -1.64         -1.5          1.64   0.00  -1.68   1.68        0.0     20     20            0         0.0         1.57
   VOLB 60          -0.98         -1.0          0.27   0.36   0.21   0.51        0.0  -1233  -1212           22         0.0         0.72
   VW13  9          -0.89         -1.0         -0.78   0.83  -2.92   4.58        0.0    357    365            8         0.0         1.00
```

## By order type and ET band (entry bar)
```
 otype         band   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  09:30-10:30  11           0.00          0.0          0.00   0.00   0.00   0.00        0.0   -112   -112            0         0.0         1.00
 limit  10:30-12:00   1           0.00          0.0          0.00   0.00    NaN    NaN        0.0    128    128            0         0.0         1.00
 limit noche <09:30  19          -0.42          0.0         -0.26   0.34  -0.18   0.86        0.0   2621   2628            6         0.0         0.53
market  09:30-10:30   8          -1.12         -1.0         -2.88   2.00  -0.75   4.75        0.0    752    768           16         0.0         0.88
market  10:30-12:00  93          -0.94         -1.0         -5.03   2.98  -8.95  14.92        2.2   -197     81          278         0.0         5.48
market  12:00-14:00  32          -1.09         -1.0         -2.41   1.75  -0.71   4.21        0.0   2870   2926           56         0.0         1.16
market  14:00-18:00  16          -0.94         -1.0         -0.75   0.84   0.54   1.15        0.0   -873   -859           14         0.0         0.31
market noche <09:30 128          -1.19         -1.0         -1.15   1.17  -0.02   2.35        0.8     13    162          150         0.0         1.91
  stop  09:30-10:30  46          -0.98         -1.0          0.46   0.26   0.09   0.43        0.0  -1276  -1264           12         0.0         0.85
  stop  10:30-12:00  27          -0.96         -1.0         -2.74   1.85   0.45   3.25        0.0    321    371           50         0.0         1.04
  stop  12:00-14:00  10          -1.00         -1.0         -2.10   1.55   0.07   3.03        0.0    129    145           16         0.0         0.30
  stop  14:00-18:00   1          -1.00         -1.0         -1.00   1.00    NaN    NaN        0.0      3      4            1         0.0         0.00
```

## Exit kind A (rows) vs B (columns)
```
xkind_b    stop  target  time/flat
xkind_a                           
stop        113       1          2
target        1     168          0
time/flat     0       0        107
```

## Fills outside the 1-minute bar (+/- 1 tick), bars = research/data/mnq_fut.npz
```
side  what  checked  no_bar  feed_offset  outside
   A entry      288     109            0        0
   A  exit      288     109            0        0
side  what  checked  no_bar  feed_offset  outside
   B entry      283     109            0        0
   B  exit      283     109           20       52
```

## Which series filled the orders (seconds != 0 = tick / second series; a Tick1 run needs ~100% in every kind, stops and targets included)
```
side  what      kind   n  seconds_nonzero_pct
   A entry     limit  31                  0.0
   A entry    market 282                  0.0
   A entry      stop  84                  0.0
   A  exit      stop 116                  0.0
   A  exit    target 172                  0.0
   A  exit time/flat 109                  0.0
A: exits at/after 15:58 ET 0 (flatten fills are stamped 15:57:00), exits named by NinjaTrader itself (session close) 0
side  what      kind   n  seconds_nonzero_pct
   B entry     limit  31                 96.8
   B entry    market 277                  0.0
   B entry      stop  84                 96.4
   B  exit      stop 114                  0.0
   B  exit    target 169                  0.0
   B  exit time/flat 109                  0.0
B: exits at/after 15:58 ET 0 (flatten fills are stamped 15:57:00), exits named by NinjaTrader itself (session close) 0
```
