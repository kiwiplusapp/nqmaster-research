# Fill gap: Off (fills 1 min) vs Tick1 + 1 tick en entradas (20260622-20261023) | B + 1 tick(s) synthetic slippage on entries

- Trades: A 397, B 392, matched 392 (98.7% of A, 100.0% of B); tolerance 3 min inside (date, module, direction).
- $ per contract on the matched trades: A 4,380, B 4,797, B - A +417 (+9.5% of A); per trade +1.06 (95% CI -1.79 .. +3.92); outcome flips 0.5%.
- Entry fill B - A: mean -0.07 ticks (median +0.00); exit fill B - A: mean -2.06 ticks; entry minute B - A +0.00, hold B - A +2.29 min. (+ = worse for the trade in B).
- Unmatched $: only A 558 (5 trades), only B 0 (0 trades).

## By order type
```
 otype   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  31          -0.26          0.0         -0.16   0.21  -0.11   0.53        0.0   2637   2644            6         0.0         0.71
market 277          -0.08          0.0         -2.62   1.35  -2.69   5.39        0.7   2566   2940          374         0.0         2.90
  stop  84           0.02          0.0         -0.89   0.43  -0.07   0.94        0.0   -823   -787           36         0.0         0.83
```

## By module
```
    mod  n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
   CAM3  3           0.00          0.0          1.33  -0.67  -1.53   0.20        0.0   -260   -262           -2         0.0         1.67
  CPI09  4          -0.50         -0.5         -5.75   3.12  -2.20   8.45        0.0    649    661           12         0.0         1.00
  CRT11  6          -0.33          0.0          2.33  -1.00  -2.07   0.07        0.0   1292   1286           -6         0.0         0.50
    ICT 12           0.00          0.0          0.00   0.00   0.00   0.00        0.0     16     16            0         0.0         1.00
 LATE15  8           0.25          0.0         -0.75   0.25  -0.12   0.62        0.0   -291   -289            2         0.0         0.25
 LF0430 13          -0.46          0.0         -4.77   2.62  -2.85   8.08        0.0    340    374           34         0.0         1.46
   LF06 12           0.17          0.0         -2.58   1.21  -1.79   4.21        0.0    289    303           14         0.0         1.42
    LON 19          -0.42          0.0         -0.26   0.34  -0.18   0.86        0.0   2621   2628            6         0.0         0.53
MOM1030 18           0.11          0.0         41.11 -20.61 -54.03  12.81        5.6    -73   -444         -371         0.0         3.33
  MOM11 65           0.09          0.0        -18.72   9.32  -4.80  23.43        1.5    182    788          606         0.0         6.78
  MOM13 14           0.00          0.0         -6.14   3.07  -1.94   8.08        0.0   1042   1085           43         0.0         1.71
   MSEQ 11           0.00          0.0         -0.45   0.23  -0.24   0.69        0.0   -252   -250            2         0.0         0.27
  MSEQS  1           0.00          0.0         -1.00   0.50    NaN    NaN        0.0   -125   -125            0         0.0         0.00
   NF05 23           0.13          0.0         -4.61   2.24  -1.77   6.25        0.0    801    852           52         0.0         1.48
   ON07 35          -0.23          0.0         -1.14   0.69  -0.06   1.43        0.0   -828   -804           24         0.0         0.26
  ORB60 14           0.07          0.0         -3.64   1.79  -0.35   3.92        0.0    289    314           25         0.0         0.79
  ORB90 10           0.00          0.0         -4.00   2.00  -0.65   4.65        0.0    122    142           20         0.0         1.60
 ORFAIL  7          -0.14          0.0         -0.29   0.21  -0.26   0.69        0.0    420    422            2         0.0         0.71
  REV06 31          -0.19          0.0          2.23  -1.02  -3.74   1.71        0.0   -609   -641          -32         0.0         4.65
   RV11  3          -1.00         -1.0          3.00  -1.00  -1.98  -0.02        0.0   -387   -390           -3         0.0         1.00
   SO04 14          -0.64         -0.5          1.64  -0.50  -2.18   1.18        0.0     20     13           -7         0.0         1.57
   VOLB 60           0.02          0.0          0.27  -0.14  -0.29   0.01        0.0  -1233  -1242           -8         0.0         0.72
   VW13  9           0.11          0.0         -0.78   0.33  -3.42   4.08        0.0    357    360            3         0.0         1.00
```

## By order type and ET band (entry bar)
```
 otype         band   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  09:30-10:30  11           0.00          0.0          0.00   0.00   0.00   0.00        0.0   -112   -112            0         0.0         1.00
 limit  10:30-12:00   1           0.00          0.0          0.00   0.00    NaN    NaN        0.0    128    128            0         0.0         1.00
 limit noche <09:30  19          -0.42          0.0         -0.26   0.34  -0.18   0.86        0.0   2621   2628            6         0.0         0.53
market  09:30-10:30   8          -0.12          0.0         -2.88   1.50  -1.25   4.25        0.0    752    764           12         0.0         0.88
market  10:30-12:00  93           0.06          0.0         -5.03   2.48  -9.45  14.42        2.2   -197     34          231         0.0         5.48
market  12:00-14:00  32          -0.09          0.0         -2.41   1.25  -1.21   3.71        0.0   2870   2910           40         0.0         1.16
market  14:00-18:00  16           0.06          0.0         -0.75   0.34   0.04   0.65        0.0   -873   -867            6         0.0         0.31
market noche <09:30 128          -0.19          0.0         -1.15   0.67  -0.52   1.85        0.0     13     98           86         0.0         1.91
  stop  09:30-10:30  46           0.02          0.0          0.46  -0.24  -0.41  -0.07        0.0  -1276  -1287          -11         0.0         0.85
  stop  10:30-12:00  27           0.04          0.0         -2.74   1.35  -0.05   2.75        0.0    321    357           36         0.0         1.04
  stop  12:00-14:00  10           0.00          0.0         -2.10   1.05  -0.43   2.53        0.0    129    140           10         0.0         0.30
  stop  14:00-18:00   1           0.00          0.0         -1.00   0.50    NaN    NaN        0.0      3      3            0         0.0         0.00
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
