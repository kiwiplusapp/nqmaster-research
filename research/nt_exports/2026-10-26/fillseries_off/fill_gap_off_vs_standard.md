# Fill gap: Standard (código pre-parche) vs FillSeries Off (parche v3) (20240122-20261023)

- Trades: A 3295, B 3295, matched 3295 (100.0% of A, 100.0% of B); tolerance 3 min inside (date, module, direction).
- $ per contract on the matched trades: A 70,908, B 70,908, B - A +0 (+0.0% of A); per trade +0.00 (95% CI +0.00 .. +0.00); outcome flips 0.0%.
- Entry fill B - A: mean +0.00 ticks (median +0.00); exit fill B - A: mean +0.00 ticks; entry minute B - A +0.00, hold B - A +0.00 min. (+ = worse for the trade in B).
- Unmatched $: only A 0 (0 trades), only B 0 (0 trades).

## By order type
```
 otype    n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  233            0.0          0.0           0.0    0.0    0.0    0.0        0.0   6166   6166            0         0.0          0.0
market 2325            0.0          0.0           0.0    0.0    0.0    0.0        0.0  34056  34056            0         0.0          0.0
  stop  737            0.0          0.0           0.0    0.0    0.0    0.0        0.0  30687  30687            0         0.0          0.0
```

## By module
```
    mod   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
   CAM3  26            0.0          0.0           0.0    0.0    0.0    0.0        0.0    287    287            0         0.0          0.0
  CPI09  28            0.0          0.0           0.0    0.0    0.0    0.0        0.0   1725   1725            0         0.0          0.0
  CRT11  62            0.0          0.0           0.0    0.0    0.0    0.0        0.0   4385   4385            0         0.0          0.0
    ICT  61            0.0          0.0           0.0    0.0    0.0    0.0        0.0   1635   1635            0         0.0          0.0
 LATE15 103            0.0          0.0           0.0    0.0    0.0    0.0        0.0   1424   1424            0         0.0          0.0
 LF0430  90            0.0          0.0           0.0    0.0    0.0    0.0        0.0   1806   1806            0         0.0          0.0
   LF06  77            0.0          0.0           0.0    0.0    0.0    0.0        0.0    988    988            0         0.0          0.0
    LON 172            0.0          0.0           0.0    0.0    0.0    0.0        0.0   4531   4531            0         0.0          0.0
MOM1030 118            0.0          0.0           0.0    0.0    0.0    0.0        0.0   1873   1873            0         0.0          0.0
  MOM11 528            0.0          0.0           0.0    0.0    0.0    0.0        0.0   4840   4840            0         0.0          0.0
  MOM13 199            0.0          0.0           0.0    0.0    0.0    0.0        0.0   3979   3979            0         0.0          0.0
   MSEQ 167            0.0          0.0           0.0    0.0    0.0    0.0        0.0   2400   2400            0         0.0          0.0
  MSEQS  15            0.0          0.0           0.0    0.0    0.0    0.0        0.0   1078   1078            0         0.0          0.0
   NF05 106            0.0          0.0           0.0    0.0    0.0    0.0        0.0   3002   3002            0         0.0          0.0
   ON07 274            0.0          0.0           0.0    0.0    0.0    0.0        0.0   1138   1138            0         0.0          0.0
  ORB60 137            0.0          0.0           0.0    0.0    0.0    0.0        0.0   6717   6717            0         0.0          0.0
  ORB90 114            0.0          0.0           0.0    0.0    0.0    0.0        0.0   3666   3666            0         0.0          0.0
 ORFAIL  41            0.0          0.0           0.0    0.0    0.0    0.0        0.0   1799   1799            0         0.0          0.0
  REV06 231            0.0          0.0           0.0    0.0    0.0    0.0        0.0   -101   -101            0         0.0          0.0
   RV11  29            0.0          0.0           0.0    0.0    0.0    0.0        0.0   1434   1434            0         0.0          0.0
   SO04  69            0.0          0.0           0.0    0.0    0.0    0.0        0.0   1199   1199            0         0.0          0.0
   VOLB 486            0.0          0.0           0.0    0.0    0.0    0.0        0.0  20304  20304            0         0.0          0.0
   VW13 162            0.0          0.0           0.0    0.0    0.0    0.0        0.0    799    799            0         0.0          0.0
```

## By order type and ET band (entry bar)
```
 otype         band   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  09:30-10:30  49            0.0          0.0           0.0    0.0    0.0    0.0        0.0    938    938            0         0.0          0.0
 limit  10:30-12:00  12            0.0          0.0           0.0    0.0    0.0    0.0        0.0    697    697            0         0.0          0.0
 limit noche <09:30 172            0.0          0.0           0.0    0.0    0.0    0.0        0.0   4531   4531            0         0.0          0.0
market  09:30-10:30  53            0.0          0.0           0.0    0.0    0.0    0.0        0.0   2963   2963            0         0.0          0.0
market  10:30-12:00 752            0.0          0.0           0.0    0.0    0.0    0.0        0.0  11865  11865            0         0.0          0.0
market  12:00-14:00 506            0.0          0.0           0.0    0.0    0.0    0.0        0.0   9485   9485            0         0.0          0.0
market  14:00-18:00 167            0.0          0.0           0.0    0.0    0.0    0.0        0.0   1710   1710            0         0.0          0.0
market noche <09:30 847            0.0          0.0           0.0    0.0    0.0    0.0        0.0   8033   8033            0         0.0          0.0
  stop  09:30-10:30 308            0.0          0.0           0.0    0.0    0.0    0.0        0.0  12699  12699            0         0.0          0.0
  stop  10:30-12:00 317            0.0          0.0           0.0    0.0    0.0    0.0        0.0  12447  12447            0         0.0          0.0
  stop  12:00-14:00  96            0.0          0.0           0.0    0.0    0.0    0.0        0.0   5424   5424            0         0.0          0.0
  stop  14:00-18:00  16            0.0          0.0           0.0    0.0    0.0    0.0        0.0    117    117            0         0.0          0.0
```

## Exit kind A (rows) vs B (columns)
```
xkind_b    stop  target  time/flat
xkind_a                           
stop        831       0          0
target        0    1569          0
time/flat     0       0        895
```

## Fills outside the 1-minute bar (+/- 1 tick), bars = research/data/mnq_fut.npz
```
side  what  checked  no_bar  feed_offset  outside
   A entry     3183     112            0        0
   A  exit     3183     112            0        0
side  what  checked  no_bar  feed_offset  outside
   B entry     3183     112            0        0
   B  exit     3183     112            0        0
```

## Which series filled the orders (seconds != 0 = tick / second series; a Tick1 run needs ~100% in every kind, stops and targets included)
```
side  what      kind    n  seconds_nonzero_pct
   A entry     limit  233                  0.0
   A entry    market 2325                  0.0
   A entry      stop  737                  0.0
   A  exit      stop  831                  0.0
   A  exit    target 1569                  0.0
   A  exit time/flat  895                  0.0
A: exits at/after 15:58 ET 0 (flatten fills are stamped 15:57:00), exits named by NinjaTrader itself (session close) 0
side  what      kind    n  seconds_nonzero_pct
   B entry     limit  233                  0.0
   B entry    market 2325                  0.0
   B entry      stop  737                  0.0
   B  exit      stop  831                  0.0
   B  exit    target 1569                  0.0
   B  exit time/flat  895                  0.0
B: exits at/after 15:58 ET 0 (flatten fills are stamped 15:57:00), exits named by NinjaTrader itself (session close) 0
```
