# Fill gap: Off v4.1 (2024-hoy, fills 1 min) vs Tick1 v4.1 (jun-hoy, ticks + 1 tick sintético) (20260622-20261023) | B + 1 tick(s) synthetic slippage on all

- Trades: A 392, B 388, matched 388 (99.0% of A, 100.0% of B); tolerance 3 min inside (date, module, direction). Dates excluded: [20260625].
- $ per contract on the matched trades: A 4,431, B 5,053, B - A +622 (+14.0% of A); per trade +1.60 (95% CI -0.99 .. +4.20); outcome flips 1.0%.
- Entry fill B - A: mean -0.07 ticks (median +0.00); exit fill B - A: mean -3.13 ticks; entry minute B - A +0.00, hold B - A +1.59 min. (+ = worse for the trade in B).
- Unmatched $: only A 370 (4 trades), only B 0 (0 trades).

## Slippage: how it is counted (once)
- A (Standard, 1-minute fills): NinjaTrader's Slippage = 1 tick is inside the export: market and stop-market entries +1 tick, stop-loss and market exits -1 tick, limit fills 0.
- B (fills on the tick series): NinjaTrader applies no slippage on a secondary series (measured 2026-10-26), so this report adds 1 tick(s) to B's market / stop-market fills on entries, stop-loss exits and market exits, 0 on limit fills. B - A is therefore the price path alone (H1 / H2), with the same 1-tick assumption on both sides.
- Real slippage (H5, slip_model.py) is measured against the order level in live / sim exports and replaces the 1-tick assumption only per cell with n >= 15; it is never added on top of this table.

## By order type
```
 otype   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  31          -0.26          0.0          0.06   0.10  -0.20   0.39        0.0   2637   2640            3         0.0         0.00
market 274          -0.08          0.0         -4.22   2.15  -1.53   5.82        1.5   2673   3261          588         0.0         2.21
  stop  83           0.02          0.0         -0.76   0.37  -0.16   0.89        0.0   -879   -848           30         0.0         0.13
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
MOM1030 17           0.12          0.0          3.24  -1.68  -6.73   3.38        0.0    182    154          -28         0.0         0.35
  MOM11 64           0.08          0.0        -18.61   9.27  -5.06  23.59        1.6     89    682          593         0.0         5.81
  MOM13 14           0.00          0.0         -5.71   2.86  -2.19   7.90        0.0   1042   1082           40         0.0         1.14
   MSEQ 11           0.00          0.0          0.27  -0.14  -0.56   0.28        0.0   -252   -254           -2         0.0         0.00
  MSEQS  1           0.00          0.0          0.00   0.00    NaN    NaN        0.0   -125   -125            0         0.0         0.00
   NF05 23           0.13          0.0         -5.74   2.80 -10.93  16.53        8.7    801    865           64         0.0         1.78
   ON07 34          -0.21          0.0          3.12  -1.46  -7.13   4.22        2.9   -883   -932          -50         0.0         0.79
  ORB60 14           0.07          0.0         -4.21   2.07  -0.08   4.22        0.0    289    318           29         0.0         0.07
  ORB90 10           0.00          0.0         -3.60   1.80  -0.89   4.49        0.0    122    140           18         0.0         1.00
 ORFAIL  7          -0.14          0.0          0.14   0.00  -0.48   0.48        0.0    420    420            0         0.0         0.14
  REV06 31          -0.19          0.0          2.26  -1.03  -3.75   1.69        0.0   -609   -641          -32         0.0         3.65
   RV11  3          -1.00         -1.0          3.00  -1.00  -1.98  -0.02        0.0   -387   -390           -3         0.0         0.00
   SO04 14          -0.64         -0.5          3.79  -1.57  -4.06   0.92        0.0     20     -2          -22         0.0         0.71
   VOLB 59           0.02          0.0          0.54  -0.28  -0.40  -0.16        0.0  -1289  -1306          -16         0.0         0.00
   VW13  9           0.11          0.0         -0.78   0.33  -3.42   4.08        0.0    357    360            3         0.0         0.00
```

## By order type and ET band (entry bar)
```
 otype         band   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  09:30-10:30  11           0.00          0.0          0.00   0.00   0.00   0.00        0.0   -112   -112            0         0.0         0.00
 limit  10:30-12:00   1           0.00          0.0          0.00   0.00    NaN    NaN        0.0    128    128            0         0.0         0.00
 limit noche <09:30  19          -0.42          0.0          0.11   0.16  -0.32   0.64        0.0   2621   2624            3         0.0         0.00
market  09:30-10:30   8          -0.12          0.0         -2.62   1.38  -1.42   4.17        0.0    752    763           11         0.0         0.12
market  10:30-12:00  91           0.05          0.0        -12.37   6.16  -3.98  16.30        1.1    -34    526          560         0.0         4.15
market  12:00-14:00  32          -0.09          0.0         -2.12   1.11  -1.35   3.57        0.0   2870   2906           36         0.0         0.50
market  14:00-18:00  16           0.06          0.0          0.06  -0.06  -0.33   0.20        0.0   -873   -874           -1         0.0         0.00
market noche <09:30 127          -0.18          0.0          0.46  -0.14  -3.21   2.92        2.4    -42    -60          -18         0.0         1.65
  stop  09:30-10:30  45           0.02          0.0          0.60  -0.31  -0.45  -0.17        0.0  -1331  -1345          -14         0.0         0.00
  stop  10:30-12:00  27           0.04          0.0         -2.81   1.39  -0.04   2.82        0.0    321    358           38         0.0         0.41
  stop  12:00-14:00  10           0.00          0.0         -1.40   0.70  -0.83   2.23        0.0    129    136            7         0.0         0.00
  stop  14:00-18:00   1           0.00          0.0          0.00   0.00    NaN    NaN        0.0      3      3            0         0.0         0.00
```

## Exit kind A (rows) vs B (columns)
```
xkind_b    stop  target  time/flat
xkind_a                           
stop        111       1          2
target        0     168          0
time/flat     0       0        106
```

## Fills outside the 1-minute bar (+/- 1 tick), bars = research/data/mnq_fut.npz
```
side  what  checked  no_bar  feed_offset  outside
   A entry      283     109            0        0
   A  exit      283     109            0        0
side  what  checked  no_bar  feed_offset  outside
   B entry      279     109            0        0
   B  exit      279     109            0        0
```

## Which series filled the orders (seconds != 0 = tick / second series; a Tick1 run needs ~100% in every kind, stops and targets included)
```
side  what      kind   n  seconds_nonzero_pct
   A entry     limit  31                  0.0
   A entry    market 278                  0.0
   A entry      stop  83                  0.0
   A  exit      stop 114                  0.0
   A  exit    target 170                  0.0
   A  exit time/flat 108                  0.0
A: exits at/after 15:58 ET 0 (flatten fills are stamped 15:57:00), exits named by NinjaTrader itself (session close) 0
side  what      kind   n  seconds_nonzero_pct
   B entry     limit  31                 96.8
   B entry    market 274                  0.0
   B entry      stop  83                 96.4
   B  exit      stop 111                 96.4
   B  exit    target 169                 97.6
   B  exit time/flat 108                  0.9
B: exits at/after 15:58 ET 0 (flatten fills are stamped 15:57:00), exits named by NinjaTrader itself (session close) 0
```
