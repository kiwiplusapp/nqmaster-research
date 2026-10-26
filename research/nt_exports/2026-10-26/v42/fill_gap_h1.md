# Fill gap: Off v4.2 (jun-hoy) vs Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético) (20260622-20261023) | B + 1 tick(s) synthetic slippage on all

- Trades: A 388, B 388, matched 388 (100.0% of A, 100.0% of B); tolerance 3 min inside (date, module, direction). Dates excluded: [20260625].
- $ per contract on the matched trades: A 5,235, B 5,254, B - A +19 (+0.4% of A); per trade +0.05 (95% CI -0.00 .. +0.10); outcome flips 0.0%.
- Delta net / net Standard per trade: +0.4% (95% CI -0.0% .. +0.7%); rule 5A.4 (-15%): CI entirely above -15%: the 1-minute fill model stands.
- Entry fill B - A: mean -0.07 ticks (median +0.00); exit fill B - A: mean -0.03 ticks; entry minute B - A +0.00, hold B - A -0.02 min. (+ = worse for the trade in B).
- Unmatched $: only A 0 (0 trades), only B 0 (0 trades).

## Slippage: how it is counted (once)
- A (Standard, 1-minute fills): NinjaTrader's Slippage = 1 tick is inside the export: market and stop-market entries +1 tick, stop-loss and market exits -1 tick, limit fills 0.
- B (fills on the tick series): NinjaTrader applies no slippage on a secondary series (measured 2026-10-26), so this report adds 1 tick(s) to B's market / stop-market fills on entries, stop-loss exits and market exits, 0 on limit fills; B's fill-relative bracket levels move with the slipped entry (1 tick for Ticks-mode stops / targets and VOLB's break-even stop, 1 + R ticks for a PriceTarget target, 0 for an absolute stop), as the strategy would have placed them. B - A is therefore the price path alone (H1 / H2), with the same 1-tick assumption on both sides.
- Real slippage (H5, slip_model.py) is measured against the order level in live / sim exports and replaces the 1-tick assumption only per cell with n >= 15; it is never added on top of this table.

## By order type
```
 otype   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  31          -0.26          0.0          0.06   0.10  -0.20   0.39        0.0   2637   2640            3         0.0         0.00
market 274          -0.08          0.0          0.00   0.04  -0.01   0.09        0.0   3428   3439           10         0.0        -0.03
  stop  83           0.02          0.0         -0.16   0.07  -0.06   0.20        0.0   -831   -825            6         0.0         0.00
```

## By module
```
    mod  n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
   CAM3  3           0.00          0.0          0.00   0.00   0.00   0.00        0.0   -262   -262            0         0.0         0.00
  CPI09  4          -0.50         -0.5          0.50   0.00   0.00   0.00        0.0    663    663            0         0.0         0.00
  CRT11  6          -0.33          0.0          1.00  -0.33  -0.94   0.27        0.0   1292   1290           -2         0.0         0.00
    ICT 12           0.00          0.0          0.00   0.00   0.00   0.00        0.0     16     16            0         0.0         0.00
 LATE15  8           0.25          0.0         -0.25   0.00  -0.19   0.19        0.0   -291   -291            0         0.0         0.00
 LF0430 13          -0.46          0.0          0.38   0.04  -0.34   0.41        0.0    376    377            0         0.0        -0.08
   LF06 12           0.17          0.0         -0.17   0.00   0.00   0.00        0.0    309    309            0         0.0         0.00
    LON 19          -0.42          0.0          0.11   0.16  -0.32   0.64        0.0   2621   2624            3         0.0         0.00
MOM1030 17           0.12          0.0         -0.12   0.00   0.00   0.00        0.0    159    159            0         0.0        -0.06
  MOM11 64           0.08          0.0         -0.06  -0.01  -0.02   0.01        0.0    714    714            0         0.0        -0.02
  MOM13 14           0.00          0.0          0.00   0.00  -0.23   0.23        0.0   1086   1086            0         0.0         0.43
   MSEQ 11           0.00          0.0          0.00   0.00  -0.38   0.38        0.0   -252   -252            0         0.0         0.00
  MSEQS  1           0.00          0.0          0.00   0.00    NaN    NaN        0.0   -125   -125            0         0.0         0.00
   NF05 23           0.13          0.0         -0.09  -0.02  -0.32   0.28        0.0    849    849            0         0.0        -0.04
   ON07 34          -0.21          0.0         -0.26   0.24   0.02   0.45        0.0   -878   -870            8         0.0         0.03
  ORB60 14           0.07          0.0         -0.93   0.43  -0.28   1.14        0.0    317    323            6         0.0         0.00
  ORB90 10           0.00          0.0         -0.20   0.10  -0.03   0.23        0.0    142    143            1         0.0         0.00
 ORFAIL  7          -0.14          0.0         -0.57   0.36  -0.24   0.95        0.0    420    423            2         0.0         0.00
  REV06 31          -0.19          0.0          0.19   0.00   0.00   0.00        0.0   -626   -626            0         0.0        -0.06
   RV11  3          -1.00         -1.0          1.00   0.00   0.00   0.00        0.0   -389   -389            0         0.0         0.00
   SO04 14          -0.64         -0.5          0.29   0.18  -0.06   0.42        0.0     17     20            2         0.0        -0.64
   VOLB 59           0.02          0.0          0.03  -0.03  -0.08   0.03        0.0  -1289  -1291           -2         0.0         0.00
   VW13  9           0.11          0.0         -0.11   0.00   0.00   0.00        0.0    365    365            0         0.0         0.00
```

## By order type and ET band (entry bar)
```
 otype         band   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  09:30-10:30  11           0.00          0.0          0.00   0.00   0.00   0.00        0.0   -112   -112            0         0.0         0.00
 limit  10:30-12:00   1           0.00          0.0          0.00   0.00    NaN    NaN        0.0    128    128            0         0.0         0.00
 limit noche <09:30  19          -0.42          0.0          0.11   0.16  -0.32   0.64        0.0   2621   2624            3         0.0         0.00
market  09:30-10:30   8          -0.12          0.0          0.00   0.06  -0.23   0.35        0.0    766    767            0         0.0         0.00
market  10:30-12:00  91           0.05          0.0         -0.08   0.01  -0.03   0.05        0.0    566    567            1         0.0        -0.02
market  12:00-14:00  32          -0.09          0.0          0.19  -0.05  -0.21   0.12        0.0   2920   2919           -2         0.0         0.19
market  14:00-18:00  16           0.06          0.0         -0.06   0.00  -0.25   0.25        0.0   -873   -873            0         0.0         0.00
market noche <09:30 127          -0.18          0.0          0.02   0.08  -0.01   0.17        0.0     49     59           10         0.0        -0.09
  stop  09:30-10:30  45           0.02          0.0         -0.02   0.00  -0.04   0.04        0.0  -1331  -1331            0         0.0         0.00
  stop  10:30-12:00  27           0.04          0.0         -0.41   0.19  -0.19   0.56        0.0    361    366            5         0.0         0.00
  stop  12:00-14:00  10           0.00          0.0         -0.10   0.05  -0.26   0.36        0.0    137    138            0         0.0         0.00
  stop  14:00-18:00   1           0.00          0.0          0.00   0.00    NaN    NaN        0.0      3      3            0         0.0         0.00
```

## Exit kind A (rows) vs B (columns)
```
xkind_b    stop  target  time/flat
xkind_a                           
stop        111       0          0
target        0     169          0
time/flat     0       0        108
```

## Fills outside the 1-minute bar (+/- 1 tick), bars = research/data/mnq_fut.npz
```
side  what  checked  no_bar  feed_offset  outside
   A entry      279     109            0        0
   A  exit      279     109            0        0
side  what  checked  no_bar  feed_offset  outside
   B entry      279     109            0        0
   B  exit      279     109            0        0
```

## Which series filled the orders (seconds != 0 = tick / second series; a Tick1 run needs ~100% in every kind, stops and targets included)
```
side  what      kind   n  seconds_nonzero_pct
   A entry     limit  31                  0.0
   A entry    market 274                  0.0
   A entry      stop  83                  0.0
   A  exit      stop 111                  0.0
   A  exit    target 169                  0.0
   A  exit time/flat 108                  0.0
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
                            Off v4.2 (jun-hoy)    CAM3         1   3        1 100.0                  -2.31   NaN          -189    -191
                            Off v4.2 (jun-hoy)   CPI09         3   3        3 100.0                   5.81  1.52           520     537
                            Off v4.2 (jun-hoy)   CRT11         5   5        5 100.0                  -6.40 -0.80          1184    1152
                            Off v4.2 (jun-hoy)     ICT         8   9        7  87.5                   0.86  0.56           172     178
                            Off v4.2 (jun-hoy)  LATE15         8   6        6  75.0                   0.01  0.03          -264    -264
                            Off v4.2 (jun-hoy)  LF0430        13  11       11  84.6                   6.93  1.51           360     437
                            Off v4.2 (jun-hoy)    LF06         9  10        9 100.0                   3.94  1.39           264     300
                            Off v4.2 (jun-hoy)     LON        19  17       17  89.5                   0.03  0.02          2438    2438
                            Off v4.2 (jun-hoy) MOM1030        14  14       13  92.9                  19.57  0.82          -317     -62
                            Off v4.2 (jun-hoy)   MOM11        58  55       54  93.1                   8.14  1.01           233     672
                            Off v4.2 (jun-hoy)   MOM13        12  12       12 100.0                   3.14  1.02           823     860
                            Off v4.2 (jun-hoy)    MSEQ        10  10       10 100.0                   0.38  1.46          -340    -336
                            Off v4.2 (jun-hoy)   MSEQS         1   1        1 100.0                  -1.50   NaN          -124    -125
                            Off v4.2 (jun-hoy)    NF05        21  20       20  95.2                   3.68  0.51           397     470
                            Off v4.2 (jun-hoy)    ON07        31  30       30  96.8                   2.00  0.74          -652    -592
                            Off v4.2 (jun-hoy)   ORB60        11  11       11 100.0                   3.25  2.07          -261    -225
                            Off v4.2 (jun-hoy)   ORB90         8   8        8 100.0                   3.22  1.65          -239    -213
                            Off v4.2 (jun-hoy)  ORFAIL         9   6        5  55.6                   0.60  1.24           414     416
                            Off v4.2 (jun-hoy)   REV06        23  25       23 100.0                  -0.79 -0.42          -365    -383
                            Off v4.2 (jun-hoy)    RV11         2   3        1  50.0                  -1.42   NaN          -111    -112
                            Off v4.2 (jun-hoy)    SO04        10  11       10 100.0                   2.07  1.11            34      55
                            Off v4.2 (jun-hoy)    VOLB        57  50       49  86.0                   0.37  1.45         -1341   -1323
                            Off v4.2 (jun-hoy)    VW13         8   7        7  87.5                   1.91  0.84           227     240
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)    CAM3         1   3        1 100.0                  -2.31   NaN          -189    -191
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)   CPI09         3   3        3 100.0                   5.81  1.52           520     537
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)   CRT11         5   5        5 100.0                  -6.70 -0.82          1184    1150
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)     ICT         8   9        7  87.5                   0.86  0.56           172     178
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)  LATE15         8   6        6  75.0                   0.01  0.03          -264    -264
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)  LF0430        13  11       11  84.6                   6.89  1.48           360     436
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)    LF06         9  10        9 100.0                   3.94  1.39           264     300
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)     LON        19  17       17  89.5                   0.03  0.02          2438    2438
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético) MOM1030        14  14       13  92.9                  19.57  0.82          -317     -62
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)   MOM11        58  55       54  93.1                   8.13  1.01           233     672
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)   MOM13        12  12       12 100.0                   3.05  0.98           823     859
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)    MSEQ        10  10       10 100.0                   0.43  1.31          -340    -336
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)   MSEQS         1   1        1 100.0                  -1.50   NaN          -124    -125
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)    NF05        21  20       20  95.2                   3.55  0.49           397     468
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)    ON07        31  30       30  96.8                   2.32  0.84          -652    -582
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)   ORB60        11  11       11 100.0                   3.34  2.14          -261    -224
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)   ORB90         8   8        8 100.0                   3.35  1.74          -239    -212
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)  ORFAIL         9   6        5  55.6                   1.00  3.65           414     418
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)   REV06        23  25       23 100.0                  -0.79 -0.42          -365    -383
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)    RV11         2   3        1  50.0                  -1.42   NaN          -111    -112
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)    SO04        10  11       10 100.0                   2.22  1.12            34      56
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)    VOLB        57  50       49  86.0                   0.35  1.36         -1341   -1324
Tick1 v4.2 (jun-hoy, ticks + 1 tick sintético)    VW13         8   7        7  87.5                   1.91  0.84           227     240
```
