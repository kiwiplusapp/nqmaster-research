# Fill gap: Off v4.2 vs Off v4.3 (parche paridad S2) (20240122-20261023)

- Trades: A 3295, B 3387, matched 3269 (99.2% of A, 96.5% of B); tolerance 3 min inside (date, module, direction).
- $ per contract on the matched trades: A 67,192, B 67,192, B - A +0 (+0.0% of A); per trade +0.00 (95% CI -0.00 .. +0.00); outcome flips 0.0%.
- Delta net / net Standard per trade: +0.0% (95% CI -0.0% .. +0.0%); rule 5A.4 (-15%): CI entirely above -15%: the 1-minute fill model stands.
- 1 time exits were decided on another bar in B (hold B - A +1.00 min; strategy mechanics, not price path; their B - A -2 $). Without them: 3268 pairs, B - A +3 $ (+0.0% of A), per trade +0.00 (95% CI -0.00 .. +0.00) = +0.0% (CI -0.0% .. +0.0%); flips 0.0%.
- Entry fill B - A: mean +0.00 ticks (median +0.00); exit fill B - A: mean -0.00 ticks; entry minute B - A +0.00, hold B - A +0.00 min. (+ = worse for the trade in B).
- Unmatched $: only A 3,717 (26 trades), only B 436 (118 trades).

## Slippage: how it is counted (once)
- A (Standard, 1-minute fills): NinjaTrader's Slippage = 1 tick is inside the export: market and stop-market entries +1 tick, stop-loss and market exits -1 tick, limit fills 0.
- B: NO synthetic slippage added (--slip-b 0): if B is a tick-series run, its market / stop fills are 1 tick better than Standard by construction and B - A overstates B.
- Real slippage (H5, slip_model.py) is measured against the order level in live / sim exports and replaces the 1-tick assumption only per cell with n >= 15; it is never added on top of this table.

## By order type
```
 otype    n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  227            0.0          0.0           0.0    0.0    0.0    0.0        0.0   5609   5609            0         0.0          0.0
market 2312            0.0          0.0          -0.0    0.0   -0.0    0.0        0.0  33643  33643            0        -0.0          0.0
  stop  730            0.0          0.0           0.0    0.0    0.0    0.0        0.0  27940  27940            0         0.0         -0.0
```

## By module
```
    mod   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
   CAM3  26           0.00          0.0          0.00   0.00   0.00   0.00        0.0    287    287            0        0.00         0.00
  CPI09  28           0.00          0.0          0.00   0.00   0.00   0.00        0.0   1725   1725            0        0.00         0.00
  CRT11  62           0.08          0.0          0.00  -0.04  -0.12   0.04        0.0   4385   4382           -2       -0.02         0.02
    ICT  55           0.00          0.0          0.00   0.00   0.00   0.00        0.0   1078   1078            0        0.00         0.00
 LATE15 103           0.00          0.0          0.00   0.00   0.00   0.00        0.0   1424   1424            0        0.00         0.00
 LF0430  90           0.00          0.0          0.00   0.00   0.00   0.00        0.0   1806   1806            0        0.00         0.00
   LF06  77           0.00          0.0          0.00   0.00   0.00   0.00        0.0    988    988            0        0.00         0.00
    LON 172           0.00          0.0          0.00   0.00   0.00   0.00        0.0   4531   4531            0        0.00         0.00
MOM1030 118           0.00          0.0          0.00   0.00   0.00   0.00        0.0   1873   1873            0        0.00         0.00
  MOM11 516          -0.02          0.0          0.02   0.00   0.00   0.00        0.0   4610   4610            0        0.00        -0.00
  MOM13 199           0.00          0.0          0.00   0.00   0.00   0.00        0.0   3979   3979            0        0.00         0.00
   MSEQ 167           0.07          0.0         -0.10   0.02  -0.02   0.05        0.0   2400   2403            3       -0.01         0.03
  MSEQS  15           0.00          0.0          0.00   0.00   0.00   0.00        0.0   1078   1078            0        0.00         0.00
   NF05 106           0.00          0.0          0.00   0.00   0.00   0.00        0.0   3002   3002            0        0.00         0.00
   ON07 274           0.00          0.0          0.00   0.00   0.00   0.00        0.0   1138   1138            0        0.00         0.00
  ORB60 137           0.00          0.0          0.00   0.00   0.00   0.00        0.0   6717   6717            0        0.00         0.00
  ORB90 114           0.00          0.0          0.00   0.00   0.00   0.00        0.0   3666   3666            0        0.00         0.00
 ORFAIL  41           0.00          0.0          0.00   0.00   0.00   0.00        0.0   1799   1799            0        0.00         0.00
  REV06 231           0.00          0.0          0.00   0.00   0.00   0.00        0.0   -101   -101            0        0.00         0.00
   RV11  28           0.00          0.0          0.00   0.00   0.00   0.00        0.0   1251   1251            0        0.00         0.00
   SO04  69           0.00          0.0          0.00   0.00   0.00   0.00        0.0   1199   1199            0        0.00         0.00
   VOLB 479           0.00          0.0          0.00   0.00   0.00   0.00        0.0  17557  17557            0        0.01        -0.01
   VW13 162           0.00          0.0          0.00   0.00   0.00   0.00        0.0    799    799            0        0.00         0.00
```

## By order type and ET band (entry bar)
```
 otype         band   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  09:30-10:30  45           0.00          0.0          0.00    0.0   0.00   0.00        0.0    478    478            0        0.00         0.00
 limit  10:30-12:00  10           0.00          0.0          0.00    0.0   0.00   0.00        0.0    600    600            0        0.00         0.00
 limit noche <09:30 172           0.00          0.0          0.00    0.0   0.00   0.00        0.0   4531   4531            0        0.00         0.00
market  09:30-10:30  53           0.00          0.0          0.00    0.0   0.00   0.00        0.0   2963   2963            0        0.00         0.00
market  10:30-12:00 739           0.00          0.0         -0.01    0.0  -0.00   0.01        0.0  11452  11455            3        0.00         0.01
market  12:00-14:00 506           0.01          0.0          0.00   -0.0  -0.01   0.00        0.0   9485   9483           -2       -0.00         0.00
market  14:00-18:00 167           0.00          0.0          0.00    0.0   0.00   0.00        0.0   1710   1710            0        0.00         0.00
market noche <09:30 847           0.00          0.0          0.00    0.0   0.00   0.00        0.0   8033   8033            0        0.00         0.00
  stop  09:30-10:30 304           0.00          0.0          0.00    0.0   0.00   0.00        0.0  12705  12705            0        0.00         0.00
  stop  10:30-12:00 315           0.00          0.0          0.00    0.0   0.00   0.00        0.0  12186  12186            0        0.01        -0.01
  stop  12:00-14:00  95           0.00          0.0          0.00    0.0   0.00   0.00        0.0   2931   2931            0        0.00         0.00
  stop  14:00-18:00  16           0.00          0.0          0.00    0.0   0.00   0.00        0.0    117    117            0        0.00         0.00
```

## Exit kind A (rows) vs B (columns)
```
xkind_b    stop  target  time/flat
xkind_a                           
stop        825       0          0
target        0    1553          0
time/flat     0       0        891
```

## Fills outside the 1-minute bar (+/- 1 tick), bars = research/data/mnq_fut.npz
```
side  what  checked  no_bar  feed_offset  outside
   A entry     3183     112            0        0
   A  exit     3183     112            0        0
side  what  checked  no_bar  feed_offset  outside
   B entry     3272     115            0        0
   B  exit     3272     115            0        0
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
   B entry     limit  240                  0.0
   B entry    market 2414                  0.0
   B entry      stop  733                  0.0
   B  exit      stop  882                  0.0
   B  exit    target 1605                  0.0
   B  exit time/flat  900                  0.0
B: exits at/after 15:58 ET 0 (flatten fills are stamped 15:57:00), exits named by NinjaTrader itself (session close) 0
```
