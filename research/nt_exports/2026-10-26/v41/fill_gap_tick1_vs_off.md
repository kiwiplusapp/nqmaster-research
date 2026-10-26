# Fill gap: Off v4.1 (fills 1 min) vs Tick1 v4.1 (ticks + 1 tick sintético) (20260622-20261023) | B + 1 tick(s) synthetic slippage on all

- Trades: A 397, B 392, matched 392 (98.7% of A, 100.0% of B); tolerance 3 min inside (date, module, direction).
- $ per contract on the matched trades: A 4,380, B 4,987, B - A +608 (+13.9% of A); per trade +1.55 (95% CI -1.03 .. +4.13); outcome flips 1.0%.
- Entry fill B - A: mean -0.07 ticks (median +0.00); exit fill B - A: mean -3.03 ticks; entry minute B - A +0.00, hold B - A +1.62 min. (+ = worse for the trade in B).
- Unmatched $: only A 558 (5 trades), only B 0 (0 trades).

## Slippage: how it is counted (once)
- A (Standard, 1-minute fills): NinjaTrader's Slippage = 1 tick is inside the export: market and stop-market entries +1 tick, stop-loss and market exits -1 tick, limit fills 0.
- B (fills on the tick series): NinjaTrader applies no slippage on a secondary series (measured 2026-10-26), so this report adds 1 tick(s) to B's market / stop-market fills on entries, stop-loss exits and market exits, 0 on limit fills. B - A is therefore the price path alone (H1 / H2), with the same 1-tick assumption on both sides.
- Real slippage (H5, slip_model.py) is measured against the order level in live / sim exports and replaces the 1-tick assumption only per cell with n >= 15; it is never added on top of this table.

## By order type
```
 otype   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  31          -0.26          0.0          0.06   0.10  -0.20   0.39        0.0   2637   2640            3         0.0         0.00
market 277          -0.08          0.0         -4.07   2.07  -1.57   5.72        1.4   2566   3140          574         0.0         2.26
  stop  84           0.02          0.0         -0.74   0.36  -0.16   0.88        0.0   -823   -793           30         0.0         0.13
```

## By module
```
    mod  n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
   CAM3  3           0.00          0.0          1.33  -0.67  -1.53   0.20        0.0   -260   -262           -2         0.0         0.00
  CPI09  4          -0.50         -0.5         -5.75   3.12  -2.20   8.45        0.0    649    661           12         0.0         0.00
  CRT11  6          -0.33          0.0          2.50  -1.08  -1.97  -0.19        0.0   1292   1285           -6         0.0         0.00
    ICT 12           0.00          0.0          0.00   0.00   0.00   0.00        0.0     16     16            0         0.0         0.00
 LATE15  8           0.25          0.0          0.00  -0.12  -0.37   0.12        0.0   -291   -292           -1         0.0         0.00
 LF0430 13          -0.46          0.0         -0.54   0.50  -6.84   7.84        0.0    340    347            6         0.0         1.08
   LF06 12           0.17          0.0         -2.58   1.21  -1.79   4.21        0.0    289    303           14         0.0         0.42
    LON 19          -0.42          0.0          0.11   0.16  -0.32   0.64        0.0   2621   2624            3         0.0         0.00
MOM1030 18           0.11          0.0          6.83  -3.47  -9.40   2.45        0.0    -73   -135          -62         0.0         1.33
  MOM11 65           0.09          0.0        -18.71   9.31  -4.80  23.41        1.5    182    787          605         0.0         5.74
  MOM13 14           0.00          0.0         -5.71   2.86  -2.19   7.90        0.0   1042   1082           40         0.0         1.14
   MSEQ 11           0.00          0.0          0.27  -0.14  -0.56   0.28        0.0   -252   -254           -2         0.0         0.00
  MSEQS  1           0.00          0.0          0.00   0.00    NaN    NaN        0.0   -125   -125            0         0.0         0.00
   NF05 23           0.13          0.0         -5.74   2.80 -10.93  16.53        8.7    801    865           64         0.0         1.78
   ON07 35          -0.23          0.0          2.57  -1.17  -6.71   4.37        2.9   -828   -869          -41         0.0         0.80
  ORB60 14           0.07          0.0         -4.21   2.07  -0.08   4.22        0.0    289    318           29         0.0         0.07
  ORB90 10           0.00          0.0         -3.60   1.80  -0.89   4.49        0.0    122    140           18         0.0         1.00
 ORFAIL  7          -0.14          0.0          0.14   0.00  -0.48   0.48        0.0    420    420            0         0.0         0.14
  REV06 31          -0.19          0.0          2.26  -1.03  -3.75   1.69        0.0   -609   -641          -32         0.0         3.65
   RV11  3          -1.00         -1.0          3.00  -1.00  -1.98  -0.02        0.0   -387   -390           -3         0.0         0.00
   SO04 14          -0.64         -0.5          3.79  -1.57  -4.06   0.92        0.0     20     -2          -22         0.0         0.71
   VOLB 60           0.02          0.0          0.55  -0.28  -0.40  -0.17        0.0  -1233  -1250          -17         0.0         0.00
   VW13  9           0.11          0.0         -0.78   0.33  -3.42   4.08        0.0    357    360            3         0.0         0.00
```

## By order type and ET band (entry bar)
```
 otype         band   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  09:30-10:30  11           0.00          0.0          0.00   0.00   0.00   0.00        0.0   -112   -112            0         0.0         0.00
 limit  10:30-12:00   1           0.00          0.0          0.00   0.00    NaN    NaN        0.0    128    128            0         0.0         0.00
 limit noche <09:30  19          -0.42          0.0          0.11   0.16  -0.32   0.64        0.0   2621   2624            3         0.0         0.00
market  09:30-10:30   8          -0.12          0.0         -2.62   1.38  -1.42   4.17        0.0    752    763           11         0.0         0.12
market  10:30-12:00  93           0.06          0.0        -11.65   5.79  -4.17  15.75        1.1   -197    342          538         0.0         4.27
market  12:00-14:00  32          -0.09          0.0         -2.12   1.11  -1.35   3.57        0.0   2870   2906           36         0.0         0.50
market  14:00-18:00  16           0.06          0.0          0.06  -0.06  -0.33   0.20        0.0   -873   -874           -1         0.0         0.00
market noche <09:30 128          -0.19          0.0          0.34  -0.07  -3.12   2.97        2.3     13      3          -10         0.0         1.65
  stop  09:30-10:30  46           0.02          0.0          0.61  -0.32  -0.45  -0.18        0.0  -1276  -1290          -14         0.0         0.00
  stop  10:30-12:00  27           0.04          0.0         -2.81   1.39  -0.04   2.82        0.0    321    358           38         0.0         0.41
  stop  12:00-14:00  10           0.00          0.0         -1.40   0.70  -0.83   2.23        0.0    129    136            7         0.0         0.00
  stop  14:00-18:00   1           0.00          0.0          0.00   0.00    NaN    NaN        0.0      3      3            0         0.0         0.00
```

## Exit kind A (rows) vs B (columns)
```
xkind_b    stop  target  time/flat
xkind_a                           
stop        113       1          2
target        0     169          0
time/flat     0       0        107
```

## Fills outside the 1-minute bar (+/- 1 tick), bars = research/data/mnq_fut.npz
```
side  what  checked  no_bar  feed_offset  outside
   A entry      288     109            0        0
   A  exit      288     109            0        0
side  what  checked  no_bar  feed_offset  outside
   B entry      283     109            0        0
   B  exit      283     109            0        0
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
   B  exit      stop 113                 96.5
   B  exit    target 170                 97.6
   B  exit time/flat 109                  0.9
B: exits at/after 15:58 ET 0 (flatten fills are stamped 15:57:00), exits named by NinjaTrader itself (session close) 0
```

## NT vs research (ultra_d4, 20260622-20261008): $ per trade NT - research on matched trades (H3; + = NT better)
```
                                 side  module  research  nt  matched   pct  nt_minus_research_usd     t  research_usd  nt_usd
               Off v4.1 (fills 1 min)    CAM3         1   3        1 100.0                  -1.81   NaN          -189    -191
               Off v4.1 (fills 1 min)   CPI09         3   3        3 100.0                   0.98  1.13           520     523
               Off v4.1 (fills 1 min)   CRT11         5   5        5 100.0                  -6.40 -0.80          1184    1152
               Off v4.1 (fills 1 min)     ICT         8   9        7  87.5                   0.86  0.56           172     178
               Off v4.1 (fills 1 min)  LATE15         8   8        8 100.0                   0.18  0.48            96      97
               Off v4.1 (fills 1 min)  LF0430        13  13       13 100.0                   3.44  1.09           466     511
               Off v4.1 (fills 1 min)    LF06         9  10        9 100.0                   1.66  1.46           264     279
               Off v4.1 (fills 1 min)     LON        19  17       17  89.5                   0.03  0.02          2438    2438
               Off v4.1 (fills 1 min) MOM1030        14  15       14 100.0                  19.88  0.92          -571    -293
               Off v4.1 (fills 1 min)   MOM11        58  56       55  94.8                  -3.26 -1.00           326     146
               Off v4.1 (fills 1 min)   MOM13        12  12       12 100.0                  -0.53 -1.32           823     816
               Off v4.1 (fills 1 min)    MSEQ        10  10       10 100.0                   0.38  1.46          -340    -336
               Off v4.1 (fills 1 min)   MSEQS         1   1        1 100.0                  -1.50   NaN          -124    -125
               Off v4.1 (fills 1 min)    NF05        21  20       20  95.2                   1.25  0.19           397     422
               Off v4.1 (fills 1 min)    ON07        31  31       31 100.0                   1.54  0.59          -590    -542
               Off v4.1 (fills 1 min)   ORB60        11  11       11 100.0                   0.70  0.78          -261    -253
               Off v4.1 (fills 1 min)   ORB90         8   8        8 100.0                   0.72  0.68          -239    -233
               Off v4.1 (fills 1 min)  ORFAIL         9   6        5  55.6                   0.60  1.24           414     416
               Off v4.1 (fills 1 min)   REV06        23  25       23 100.0                  -0.00 -0.06          -365    -365
               Off v4.1 (fills 1 min)    RV11         2   3        1  50.0                  -1.42   NaN          -111    -112
               Off v4.1 (fills 1 min)    SO04        10  11       10 100.0                   2.32  1.39            34      57
               Off v4.1 (fills 1 min)    VOLB        57  51       50  87.7                   0.36  1.46         -1286   -1267
               Off v4.1 (fills 1 min)    VW13         8   8        8 100.0                   0.68  1.31           313     319
Tick1 v4.1 (ticks + 1 tick sintético)    CAM3         1   3        1 100.0                  -2.31   NaN          -189    -191
Tick1 v4.1 (ticks + 1 tick sintético)   CPI09         3   3        3 100.0                   5.31  1.38           520     536
Tick1 v4.1 (ticks + 1 tick sintético)   CRT11         5   5        5 100.0                  -7.60 -0.90          1184    1146
Tick1 v4.1 (ticks + 1 tick sintético)     ICT         8   9        7  87.5                   0.86  0.56           172     178
Tick1 v4.1 (ticks + 1 tick sintético)  LATE15         8   6        6  75.0                  -0.07 -0.23          -264    -264
Tick1 v4.1 (ticks + 1 tick sintético)  LF0430        13  11       11  84.6                   3.66  1.04           360     401
Tick1 v4.1 (ticks + 1 tick sintético)    LF06         9  10        9 100.0                   3.44  1.22           264     295
Tick1 v4.1 (ticks + 1 tick sintético)     LON        19  17       17  89.5                   0.03  0.02          2438    2438
Tick1 v4.1 (ticks + 1 tick sintético) MOM1030        14  15       14 100.0                  15.49  0.69          -571    -355
Tick1 v4.1 (ticks + 1 tick sintético)   MOM11        58  56       55  94.8                   7.72  0.97           326     750
Tick1 v4.1 (ticks + 1 tick sintético)   MOM13        12  12       12 100.0                   2.76  0.90           823     856
Tick1 v4.1 (ticks + 1 tick sintético)    MSEQ        10  10       10 100.0                   0.28  0.79          -340    -337
Tick1 v4.1 (ticks + 1 tick sintético)   MSEQS         1   1        1 100.0                  -1.50   NaN          -124    -125
Tick1 v4.1 (ticks + 1 tick sintético)    NF05        21  20       20  95.2                   1.93  0.72           397     436
Tick1 v4.1 (ticks + 1 tick sintético)    ON07        31  31       31 100.0                   0.05  0.09          -590    -588
Tick1 v4.1 (ticks + 1 tick sintético)   ORB60        11  11       11 100.0                   3.02  1.96          -261    -228
Tick1 v4.1 (ticks + 1 tick sintético)   ORB90         8   8        8 100.0                   3.10  1.64          -239    -214
Tick1 v4.1 (ticks + 1 tick sintético)  ORFAIL         9   6        5  55.6                   0.50  1.20           414     416
Tick1 v4.1 (ticks + 1 tick sintético)   REV06        23  25       23 100.0                  -1.29 -0.69          -365    -395
Tick1 v4.1 (ticks + 1 tick sintético)    RV11         2   3        1  50.0                  -1.92   NaN          -111    -113
Tick1 v4.1 (ticks + 1 tick sintético)    SO04        10  11       10 100.0                   0.22  0.18            34      36
Tick1 v4.1 (ticks + 1 tick sintético)    VOLB        57  51       50  87.7                   0.06  0.26         -1286   -1282
Tick1 v4.1 (ticks + 1 tick sintético)    VW13         8   7        7  87.5                   1.41  0.62           227     237
```
