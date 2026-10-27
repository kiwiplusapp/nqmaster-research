# Fill gap: A (Standard) vs B (Tick1) (20260622-20261023) | B + 1 tick(s) synthetic slippage on all

- Trades: A 392, B 392, matched 392 (100.0% of A, 100.0% of B); tolerance 3 min inside (date, module, direction).
- $ per contract on the matched trades: A 5,162, B 5,183, B - A +20 (+0.4% of A); per trade +0.05 (95% CI +0.00 .. +0.10); outcome flips 0.0%.
- Delta net / net Standard per trade: +0.4% (95% CI +0.0% .. +0.8%); rule 5A.4 (-15%): CI entirely above -15%: the 1-minute fill model stands.
- Entry fill B - A: mean -0.07 ticks (median +0.00); exit fill B - A: mean -0.04 ticks; entry minute B - A +0.00, hold B - A -0.02 min. (+ = worse for the trade in B).
- Unmatched $: only A 0 (0 trades), only B 0 (0 trades).

## Slippage: how it is counted (once)
- A (Standard, 1-minute fills): NinjaTrader's Slippage = 1 tick is inside the export: market and stop-market entries +1 tick, stop-loss and market exits -1 tick, limit fills 0.
- B (fills on the tick series): NinjaTrader applies no slippage on a secondary series (measured 2026-10-26), so this report adds 1 tick(s) to B's market / stop-market fills on entries, stop-loss exits and market exits, 0 on limit fills; B's fill-relative bracket levels move with the slipped entry (1 tick for Ticks-mode stops / targets and VOLB's break-even stop, 1 + R ticks for a PriceTarget target, 0 for an absolute stop), as the strategy would have placed them. B - A is therefore the price path alone (H1 / H2), with the same 1-tick assumption on both sides.
- Real slippage (H5, slip_model.py) is measured against the order level in live / sim exports and replaces the 1-tick assumption only per cell with n >= 15; it is never added on top of this table.

## By order type
```
 otype   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  31          -0.26          0.0          0.06   0.10  -0.20   0.39        0.0   2637   2640            3         0.0         0.00
market 277          -0.08          0.0         -0.01   0.04  -0.01   0.10        0.0   3300   3312           12         0.0        -0.03
  stop  84           0.02          0.0         -0.15   0.07  -0.06   0.19        0.0   -775   -770            6         0.0         0.00
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
MOM1030 18           0.11          0.0         -0.11   0.00   0.00   0.00        0.0   -129   -129            0         0.0        -0.06
  MOM11 65           0.09          0.0         -0.08  -0.01  -0.02   0.01        0.0    820    819            0         0.0        -0.02
  MOM13 14           0.00          0.0          0.00   0.00  -0.23   0.23        0.0   1086   1086            0         0.0         0.43
   MSEQ 11           0.00          0.0          0.00   0.00  -0.38   0.38        0.0   -252   -252            0         0.0         0.00
  MSEQS  1           0.00          0.0          0.00   0.00    NaN    NaN        0.0   -125   -125            0         0.0         0.00
   NF05 23           0.13          0.0         -0.09  -0.02  -0.32   0.28        0.0    849    849            0         0.0        -0.04
   ON07 35          -0.23          0.0         -0.31   0.27   0.05   0.49        0.0   -823   -813           10         0.0         0.03
  ORB60 14           0.07          0.0         -0.93   0.43  -0.28   1.14        0.0    317    323            6         0.0         0.00
  ORB90 10           0.00          0.0         -0.20   0.10  -0.03   0.23        0.0    142    143            1         0.0         0.00
 ORFAIL  7          -0.14          0.0         -0.57   0.36  -0.24   0.95        0.0    420    423            2         0.0         0.00
  REV06 31          -0.19          0.0          0.19   0.00   0.00   0.00        0.0   -626   -626            0         0.0        -0.06
   RV11  3          -1.00         -1.0          1.00   0.00   0.00   0.00        0.0   -389   -389            0         0.0         0.00
   SO04 14          -0.64         -0.5          0.29   0.18  -0.06   0.42        0.0     17     20            2         0.0        -0.64
   VOLB 60           0.02          0.0          0.03  -0.02  -0.08   0.03        0.0  -1233  -1235           -2         0.0         0.00
   VW13  9           0.11          0.0         -0.11   0.00   0.00   0.00        0.0    365    365            0         0.0         0.00
```

## By order type and ET band (entry bar)
```
 otype         band   n  d_entry_ticks  d_entry_med  d_exit_ticks  d_usd  ci_lo  ci_hi  flips_pct  usd_a  usd_b  d_usd_total  d_tin_mean  d_hold_mean
 limit  09:30-10:30  11           0.00          0.0          0.00   0.00   0.00   0.00        0.0   -112   -112            0         0.0         0.00
 limit  10:30-12:00   1           0.00          0.0          0.00   0.00    NaN    NaN        0.0    128    128            0         0.0         0.00
 limit noche <09:30  19          -0.42          0.0          0.11   0.16  -0.32   0.64        0.0   2621   2624            3         0.0         0.00
market  09:30-10:30   8          -0.12          0.0          0.00   0.06  -0.23   0.35        0.0    766    767            0         0.0         0.00
market  10:30-12:00  93           0.06          0.0         -0.09   0.01  -0.03   0.05        0.0    383    384            1         0.0        -0.02
market  12:00-14:00  32          -0.09          0.0          0.19  -0.05  -0.21   0.12        0.0   2920   2919           -2         0.0         0.19
market  14:00-18:00  16           0.06          0.0         -0.06   0.00  -0.25   0.25        0.0   -873   -873            0         0.0         0.00
market noche <09:30 128          -0.19          0.0          0.00   0.09  -0.00   0.19        0.0    104    116           12         0.0        -0.09
  stop  09:30-10:30  46           0.02          0.0         -0.02   0.00  -0.04   0.04        0.0  -1276  -1276            0         0.0         0.00
  stop  10:30-12:00  27           0.04          0.0         -0.41   0.19  -0.19   0.56        0.0    361    366            5         0.0         0.00
  stop  12:00-14:00  10           0.00          0.0         -0.10   0.05  -0.26   0.36        0.0    137    138            0         0.0         0.00
  stop  14:00-18:00   1           0.00          0.0          0.00   0.00    NaN    NaN        0.0      3      3            0         0.0         0.00
```

## Exit kind A (rows) vs B (columns)
```
xkind_b    stop  target  time/flat
xkind_a                           
stop        113       0          0
target        0     170          0
time/flat     0       0        109
```

## Fills outside the 1-minute bar (+/- 1 tick), bars = research/data/mnq_fut.npz
```
side  what  checked  no_bar  feed_offset  outside
   A entry      283     109            0        0
   A  exit      283     109            0        0
side  what  checked  no_bar  feed_offset  outside
   B entry      283     109            0        0
   B  exit      283     109            0        0
```

## Which series filled the orders (seconds != 0 = tick / second series; a Tick1 run needs ~100% in every kind, stops and targets included)
```
side  what      kind   n  seconds_nonzero_pct
   A entry     limit  31                  0.0
   A entry    market 277                  0.0
   A entry      stop  84                  0.0
   A  exit      stop 113                  0.0
   A  exit    target 170                  0.0
   A  exit time/flat 109                  0.0
A: exits at/after 15:58 ET 0 (flatten fills are stamped 15:57:00), exits named by NinjaTrader itself (session close) 0
side  what      kind   n  seconds_nonzero_pct
   B entry     limit  31                 96.8
   B entry    market 277                  0.0
   B entry      stop  84                 96.4
   B  exit      stop 113                 96.5
   B  exit    target 170                 97.6
   B  exit time/flat 109                  0.0
B: exits at/after 15:58 ET 0 (flatten fills are stamped 15:57:00), exits named by NinjaTrader itself (session close) 0
```
