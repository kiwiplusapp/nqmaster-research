# Fill gap: Off vs Tick1 trace ago-sep (20260821-20260915)

- Trades: A 70, B 74, matched 62 (88.6% of A, 83.8% of B); tolerance 3 min inside (date, module, direction).
- $ per contract on the matched trades: A -10, B 274, B - A +284 (-2840.0% of A); per trade +4.58 (95% CI -2.77 .. +11.93); outcome flips 1.6%.
- Entry fill B - A: mean -1.06 ticks (median -1.00); exit fill B - A: mean -8.10 ticks; entry minute B - A -0.73, hold B - A -3.42 min. (+ = worse for the trade in B).
- Unmatched $: only A 307 (8 trades), only B -164 (12 trades).

## By order type
```
 otype  n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  6           0.00          0.0          0.00   0.00  -0.25   0.25        0.0    535    535            0         0.0        -0.33
market 45          -1.22         -1.0        -11.20   6.21  -3.91  16.33        2.2   1011   1290          280        -1.0        -4.64
  stop 11          -1.00         -1.0          0.18   0.41   0.23   0.59        0.0  -1556  -1551            4         0.0        -0.09
```

## By module
```
   mod  n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
  CAM3  1          -1.00         -1.0         -3.00   2.00    NaN    NaN        0.0    -40    -38            2        -1.0         3.00
 CPI09  1          -2.00         -2.0         14.00  -6.00    NaN    NaN        0.0    122    116           -6        -1.0         1.00
 CRT11  1          -1.00         -1.0          0.00   0.50    NaN    NaN        0.0     98     98            0        -1.0         0.00
   ICT  3           0.00          0.0          0.00   0.00   0.00   0.00        0.0     84     84            0         0.0         0.00
LF0430  1          -1.00         -1.0         26.00 -12.50    NaN    NaN        0.0    150    138          -12        -1.0        -9.00
  LF06  5          -0.80         -1.0        -73.00  36.90 -47.68 121.48       20.0    187    372          184        -1.0       -31.60
   LON  3           0.00          0.0          0.00   0.00  -0.57   0.57        0.0    451    451            0         0.0        -0.67
 MOM11 12          -1.67         -1.0          2.25  -0.29  -4.48   3.90        0.0    -41    -44           -4        -1.0        -2.08
 MOM13  1          -1.00         -1.0        -86.00  43.50    NaN    NaN        0.0     96    139           44        -1.0        -3.00
  MSEQ  1          -2.00         -2.0          0.00   1.00    NaN    NaN        0.0   -441   -440            1        -1.0         1.00
  NF05  7          -0.43         -1.0        -23.71  12.07 -12.44  36.58        0.0    532    617           84        -1.0        -4.14
  ON07  5          -1.60         -1.0          2.40  -0.40  -3.40   2.60        0.0     24     22           -2        -1.0         0.20
ORFAIL  2          -0.50         -0.5         -0.50   0.50   0.50   0.50        0.0    142    143            1        -1.0         0.50
 REV06  4          -1.00         -1.0          7.75  -3.38  -4.72  -2.03        0.0    190    177          -14        -1.0         1.00
  RV11  2          -2.50         -2.5         -6.50   4.50   4.50   4.50        0.0   -221   -212            9        -1.0         1.00
  SO04  2          -1.00         -1.0         10.00  -4.50  -4.50  -4.50        0.0    213    204           -9        -1.0         1.00
  VOLB 11          -1.00         -1.0          0.18   0.41   0.23   0.59        0.0  -1556  -1551            4         0.0        -0.09
```

## By order type and ET band (entry bar)
```
 otype         band  n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  09:30-10:30  2           0.00          0.0          0.00   0.00   0.00   0.00        0.0    -44    -44            0         0.0         0.00
 limit  10:30-12:00  1           0.00          0.0          0.00   0.00    NaN    NaN        0.0    128    128            0         0.0         0.00
 limit noche <09:30  3           0.00          0.0          0.00   0.00  -0.57   0.57        0.0    451    451            0         0.0        -0.67
market  09:30-10:30  2          -1.00         -1.0          6.50  -2.75  -9.12   3.62        0.0    380    374           -6        -1.0         0.50
market  10:30-12:00 16          -1.75         -1.5          0.88   0.44  -2.77   3.65        0.0   -819   -812            7        -1.0        -1.31
market  12:00-14:00  2          -1.00         -1.0        -43.00  22.00 -20.14  64.14        0.0    193    237           44        -1.0        -1.50
market  14:00-18:00  1          -1.00         -1.0         -3.00   2.00    NaN    NaN        0.0    -40    -38            2        -1.0         3.00
market noche <09:30 24          -0.92         -1.0        -18.42   9.67  -8.93  28.26        4.2   1296   1528          232        -1.0        -7.88
  stop  09:30-10:30  8          -1.00         -1.0          0.38   0.31   0.13   0.49        0.0  -1016  -1014            2         0.0         0.00
  stop  10:30-12:00  3          -1.00         -1.0         -0.33   0.67   0.34   0.99        0.0   -540   -538            2         0.0        -0.33
```

## Exit kind A (rows) vs B (columns)
```
xkind_b    stop  target  time/flat
xkind_a                           
stop         22       1          0
target        0      27          0
time/flat     0       2         10
```

## Fills outside the 1-minute bar (+/- 1 tick), bars = research/data/mnq_fut.npz
```
side  what  checked  no_bar  feed_offset  outside
   A entry       70       0            0        0
   A  exit       70       0            0        0
side  what  checked  no_bar  feed_offset  outside
   B entry       74       0            0        2
   B  exit       74       0            0        0
```

## Which series filled the orders (seconds != 0 = tick / second series; a Tick1 run needs ~100% in every kind, stops and targets included)
```
side  what      kind  n  seconds_nonzero_pct
   A entry     limit  8                  0.0
   A entry    market 49                  0.0
   A entry      stop 13                  0.0
   A  exit      stop 23                  0.0
   A  exit    target 30                  0.0
   A  exit time/flat 17                  0.0
A: exits at/after 15:58 ET 0 (flatten fills are stamped 15:57:00), exits named by NinjaTrader itself (session close) 0
side  what      kind  n  seconds_nonzero_pct
   B entry     limit  6                100.0
   B entry    market 57                  0.0
   B entry      stop 11                100.0
   B  exit      stop 26                  0.0
   B  exit    target 37                  0.0
   B  exit time/flat 11                  0.0
B: exits at/after 15:58 ET 0 (flatten fills are stamped 15:57:00), exits named by NinjaTrader itself (session close) 0
```
