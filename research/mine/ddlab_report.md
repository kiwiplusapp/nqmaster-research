# Portfolio drawdown lab (ddlab) — 2026-10-19

Objective (Federico): lower the max drawdown and the worst month of the whole system **without** lowering PF, WR, trade count
or net $, and without overfitting. Trade set: `nt_compare --set ultra_d4` (2027 default: Ultra + durable six-year modules
SO04 / RV11 / ORFAIL / CAM3), real Databento NQ 2020-10-15..2026-10-08, $ per MNQ incl. $1.90 commission + 1 tick, `w` = lots
(MOM1030 and CPI09 x4, ICT x2, context / confluence boosts x2).

## 1. Pre-registration (written before any rule was run)

**Data.** Per-trade entry / stop / target / time-exit specs rebuilt from `wrq_entries_db.pkl` (Ultra modules) and from the family
generators of the six-year modules and CPI09 (`fills_core` = the entry part of `core.execute`). Every trade of the set is re-simulated
with `wrq_lib.xsim`; the rebuilt P&L must match the set's `u` exactly (check printed by `ddlab.py build`). Daily ATR = `core.Data.atr`
of the fill day (the same array every other study uses). Trading-day index = RTH days with ATR >= 150 and no FOMC (NQMaster's rules).

**Periods.** T1 = 2020-10-15..2023-12-31 (choose), T2 = 2024-01-01..2026-10-08 (check, never used to choose). Extra out-of-sample view:
2010-06..2019-12 cost-normalised (cost 0.345% of ATR, P&L in % of ATR; A = 2010-14, B = 2015-19, N = both), built from the same
specs (cand16 `UltraR` norm view + CPI09 + six-year modules, conflict filter), thresholds converted to ATR units.

**Rule families and grids (all cells run, none added after seeing results).**

| Family | Rule | Grid | Cells |
|---|---|---|---|
| R1 | stop distance = min(structure stop, k x ATR), target unchanged in price, exits re-simulated (VOLB, ORB60, ORB90, MSEQ, MSEQS, CRT11, ICT, LON, ORFAIL) | k in 0.15, 0.2, 0.25, 0.3, 0.35, 0.4 | 6 |
| R2 | skip the entry when its initial stop distance per lot > k x ATR | same k grid | 6 |
| R3 | no new entry while sum of open initial risks (lots x stop distance / ATR) > H | H in 0.4, 0.6, 0.8, 1.0, 1.5 | 5 |
| R4a | daily loss stop: once realized + open P&L (1-min closes) <= -L x ATR x $2 per base contract, no new entries that day | L in 0.5, 0.75, 1.0, 1.5 | 4 |
| R4b | as R4a but open positions are flattened at the close of the breach minute (-1 tick) | same L grid | 4 |
| R5 | no new entry in a direction when open lots (variant 'lots') or open trades (variant 'trades') in that direction >= N | N in 2, 3, 4 | 6 |
| R6 | no new entries in the session after K consecutive full stop-outs (initial stop hit; break-even stops do not count) | K in 2, 3, 4 | 3 |
| R8 | skip the whole day when the week-to-date (W) / month-to-date (M) realized P&L of the previous days <= -X x ATR x $2 | W in 2, 3, 4; M in 4, 6, 8 | 6 |
| R9 | combination of the best T1-passing cell (largest T1 maxDD reduction) of R1, R3 and R4 (a or b) | 2- and 3-way combinations | <= 4 |

Total: **40 single cells** (+ up to 4 R9 combinations). Not tested (rejected earlier): trend-day sizing, equity-curve switching,
fixed-$ daily stops ($300 / $500), concurrency caps by count, vol-targeted sizing, VIX / ATR regime filters, time stops,
break-even on time modules, risk parity, intraday liquidation buffer, high-vol guard.

**Simulation conventions.** Gates (R3-R6) are sequential within the day in fill order: only taken trades count as open, skipped trades
never open a position. Blocked or skipped trades do not un-block opposite-direction trades that the original conflict filter removed
(conservative: no new trades are ever created). R1 changes exits only; the conflict filter is not re-applied after the earlier
exits (again no new trades). Open P&L for R4 uses 1-minute closes (NQMaster checks at bar close). Thresholds "per base contract"
compare against the real $ P&L of the base-size portfolio (x4 / x2 lots included).

**Metrics per period.** n trades, WR (share of trades with u > 0, unweighted, as in `six_base.stats`), PF on w x u, net $, Sharpe
(daily P&L, sqrt 252, zero on no-trade days), max DD on the cumulative daily closed equity, worst calendar month.

**Acceptance (fixed).** A cell is accepted only if ALL hold:
T1 maxDD <= 90% of base AND T2 maxDD <= 95% of base AND worst month >= base (T1 and T2) AND Sharpe >= base - 0.005 (T1 and T2)
AND net >= 95% of base (T1 and T2) AND n >= 97% of base (T1 and T2; R2 exempt, reported separately) AND WR >= base - 0.05 pts
(T1 and T2). Selection is on T1 only; T2 is a check. Reported in addition: P(T2 pass | T1 pass) over the 40 cells; a 21-day paired
block bootstrap (500 resamples) of the DD change for every T1-passing cell; the 2010-19 cost-normalised DD / Sharpe / net change;
the MFFU Rapid EOD 50K 1-contract lifecycle (copy of `robust2_life` / `mffu_rapid.life_m`: eval with $800 daily profit stop and 30%
consistency, funded keeping $4,100, 1,000 ten-day block bootstrap years per period) for R1 / R3 / R4 cells and R9 combinations.
One survivor among ~40 cells is treated as suspicious (expected false positives at the 5% level ~2).

**Expected direction (prior, written before running).** With no edge in the timing of losses (autocorrelation ~0, robust2 study),
daily / weekly / monthly loss stops cannot lower the DD without lowering the net $ by about the same share; R1 (tighter stops) raises
the stop-out rate of structure modules and tends to cut WR; R3 / R5 remove the largest concurrent exposures (the tail of the
bad months comes from VOLB / ORB60 / MSEQ risk) and are the only families expected to pass if anything does.

---

(Results are appended below by `ddlab.py run`.)
## 2. Results (run 2026-10-19, `python3 ddlab.py build` + `run` + `supp`; 40 cells, 0 R9 combinations because no cell passed T1)

**Reproduction.** 7,398 trades (real view) and 11,608 trades (2010-19 cost-normalised view) re-simulated with `xsim`: 0 P&L mismatches vs the stored sets.

**Base (ultra_d4, 1 base contract):**

| Period | trades | WR % | PF | net | Sharpe | maxDD | worst month | neg months |
|---|---|---|---|---|---|---|---|---|
| T1 2020-10..2023 real $ | 3977 | 65.7 | 1.462 | 73,148 | 3.52 | 4,667 | -1,176 | 7/39 |
| T2 2024-01..2026-10 real $ | 3421 | 64.8 | 1.500 | 86,936 | 4.02 | 3,586 | -2,182 | 3/34 |
| A 2010-14 norm (%ATR) | 5570 | 59.1 | 1.061 | 3,144 | 0.61 | 2,168 | -563 | 23/55 |
| B 2015-19 norm | 6038 | 60.6 | 1.152 | 8,144 | 1.37 | 1,243 | -685 | 20/60 |
| N 2010-19 norm | 11608 | 59.9 | 1.107 | 11,289 | 1.02 | 2,168 | -685 | 43/115 |

MFFU Rapid EOD 50K 1-contract lifecycle (bootstrap years): T1 $1,142/month, funded busts 0.34/yr, accounts lost 0.76/yr, P(neg year) 3.0%; T2 $1,781/month, busts 0.53, lost 1.01, P(neg) 0.7%.

### 2.1 Full grid (change vs base; DD and net in %, Sharpe / WR absolute; 'fails' = acceptance parts failed: dd, wm = worst month, sh = Sharpe, net, n = trade count, wr)

| Cell | T1 dDD | T1 dNet | T1 Sharpe | T1 WR | T1 n | T1 wMo | T1 fails | T2 dDD | T2 dNet | T2 Sharpe | T2 WR | T2 n | T2 wMo | T2 fails | 2010-19 dDD | 2010-19 Sharpe | 2010-19 dNet |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 stop<=k ATR k=0.15 | -13.7% | -29.6% | 3.11 | 62.1 | 3977 | -1,286 | wm,sh,net,wr | -6.6% | -29.6% | 3.41 | 61.9 | 3421 | -2,232 | wm,sh,net,wr | -16.4% | 1.02 | -20.2% |
| R1 stop<=k ATR k=0.2 | -16.2% | -15.6% | 3.46 | 64.0 | 3977 | -1,206 | wm,sh,net,wr | -19.3% | -18.0% | 3.71 | 63.3 | 3421 | -1,903 | sh,net,wr | -37.0% | 1.11 | -6.6% |
| R1 stop<=k ATR k=0.25 | -4.9% | -11.7% | 3.43 | 64.8 | 3977 | -1,115 | dd,sh,net,wr | -2.3% | -11.5% | 3.85 | 64.0 | 3421 | -2,158 | dd,sh,net,wr | -30.6% | 1.19 | +6.2% |
| R1 stop<=k ATR k=0.3 | +0.7% | -3.1% | 3.57 | 65.4 | 3977 | -1,088 | dd,wr | -1.9% | -5.5% | 3.99 | 64.4 | 3421 | -2,362 | dd,wm,sh,net,wr | -23.6% | 1.22 | +12.9% |
| R1 stop<=k ATR k=0.35 | +5.0% | -4.0% | 3.47 | 65.5 | 3977 | -1,052 | dd,sh,wr | -4.4% | -1.8% | 4.06 | 64.7 | 3421 | -2,127 | dd,wr | -18.6% | 1.12 | +6.8% |
| R1 stop<=k ATR k=0.4 | +1.5% | -1.8% | 3.50 | 65.6 | 3977 | -1,106 | dd,sh,wr | +1.5% | -1.4% | 4.01 | 64.7 | 3421 | -2,229 | dd,wm,sh,wr | -9.2% | 1.09 | +5.1% |
| R2 skip risk>k ATR k=0.15 | -84.4% | -92.4% | 1.74 | 55.0 | 351 | -422 | sh,net,wr | -56.2% | -96.7% | 0.71 | 47.6 | 290 | -517 | sh,net,wr | -60.4% | -0.05 | -100.9% |
| R2 skip risk>k ATR k=0.2 | -24.1% | -69.5% | 2.61 | 62.4 | 1830 | -1,727 | wm,sh,net,wr | -3.0% | -73.8% | 2.24 | 60.8 | 1534 | -1,577 | dd,sh,net,wr | -44.6% | 0.40 | -82.9% |
| R2 skip risk>k ATR k=0.25 | -3.6% | -60.4% | 2.75 | 65.7 | 2722 | -1,837 | dd,wm,sh,net | -31.6% | -57.6% | 2.94 | 65.3 | 2352 | -1,211 | sh,net | -21.6% | 0.71 | -62.1% |
| R2 skip risk>k ATR k=0.3 | -10.9% | -53.3% | 2.86 | 65.5 | 2922 | -1,705 | wm,sh,net,wr | -25.8% | -50.2% | 3.22 | 65.2 | 2526 | -1,444 | sh,net | -19.1% | 0.80 | -53.3% |
| R2 skip risk>k ATR k=0.35 | -17.9% | -32.7% | 3.17 | 65.7 | 3353 | -1,367 | wm,sh,net | +3.1% | -26.8% | 3.80 | 65.4 | 2889 | -1,479 | dd,sh,net | +14.4% | 0.74 | -41.1% |
| R2 skip risk>k ATR k=0.4 | -11.8% | -16.7% | 3.40 | 65.6 | 3678 | -1,302 | wm,sh,net,wr | +2.2% | -17.0% | 3.97 | 65.1 | 3148 | -2,081 | dd,sh,net | +2.7% | 0.91 | -23.9% |
| R3 heat cap H=0.4 ATR | -21.3% | -33.6% | 3.16 | 63.7 | 3022 | -1,087 | sh,net,n,wr | -25.6% | -25.9% | 3.78 | 63.1 | 2710 | -1,436 | sh,net,n,wr | -48.9% | 1.11 | -14.2% |
| R3 heat cap H=0.6 ATR | -16.8% | -25.2% | 3.32 | 64.3 | 3335 | -1,414 | wm,sh,net,n,wr | -4.9% | -24.0% | 3.55 | 63.9 | 2964 | -1,868 | dd,sh,net,n,wr | -33.9% | 1.05 | -12.6% |
| R3 heat cap H=0.8 ATR | -17.9% | -13.7% | 3.45 | 64.9 | 3568 | -1,606 | wm,sh,net,n,wr | -0.3% | -17.7% | 3.69 | 64.0 | 3148 | -1,769 | dd,sh,net,n,wr | -28.5% | 0.97 | -14.5% |
| R3 heat cap H=1.0 ATR | -8.1% | -11.6% | 3.45 | 65.0 | 3681 | -1,572 | dd,wm,sh,net,n,wr | -0.3% | -11.7% | 3.86 | 64.2 | 3217 | -1,710 | dd,sh,net,n,wr | -12.8% | 1.03 | -5.7% |
| R3 heat cap H=1.5 ATR | -7.6% | -3.6% | 3.52 | 65.4 | 3867 | -1,237 | dd,wm,wr | +0.0% | -4.4% | 3.95 | 64.5 | 3359 | -2,022 | dd,sh,wr | -0.8% | 1.04 | +0.6% |
| R4a daily loss block L=0.5 ATR | -13.8% | -7.6% | 3.42 | 65.9 | 3564 | -1,779 | wm,sh,net,n | -0.3% | -8.1% | 3.80 | 64.6 | 3118 | -2,028 | dd,sh,net,n,wr | -14.5% | 1.18 | +7.7% |
| R4a daily loss block L=0.75 ATR | -8.8% | -5.0% | 3.39 | 65.9 | 3770 | -1,430 | dd,wm,sh,n | +0.0% | -3.9% | 3.93 | 64.6 | 3275 | -1,885 | dd,sh,n,wr | -11.3% | 1.11 | +6.0% |
| R4a daily loss block L=1.0 ATR | -6.4% | -0.3% | 3.55 | 65.9 | 3857 | -1,219 | dd,wm,n | +0.0% | -0.7% | 3.99 | 64.7 | 3369 | -2,038 | dd,sh,wr | -13.6% | 1.10 | +6.1% |
| R4a daily loss block L=1.5 ATR | -2.7% | +0.3% | 3.53 | 65.8 | 3943 | -1,131 | dd | +0.0% | -0.8% | 3.98 | 64.7 | 3403 | -2,182 | dd,sh,wr | -3.8% | 1.05 | +3.0% |
| R4b daily loss flatten L=0.5 ATR | -39.3% | -18.0% | 3.19 | 64.5 | 3477 | -1,885 | wm,sh,net,n,wr | -5.4% | -28.2% | 3.08 | 62.2 | 3048 | -1,947 | sh,net,n,wr | -50.6% | 1.29 | +6.9% |
| R4b daily loss flatten L=0.75 ATR | -22.7% | -10.9% | 3.26 | 65.3 | 3713 | -1,804 | wm,sh,net,n,wr | -0.1% | -18.2% | 3.35 | 63.3 | 3247 | -1,733 | dd,sh,net,n,wr | -12.6% | 1.16 | +4.7% |
| R4b daily loss flatten L=1.0 ATR | -8.4% | -9.4% | 3.23 | 65.4 | 3832 | -1,558 | dd,wm,sh,net,n,wr | +10.0% | -3.8% | 3.91 | 64.4 | 3355 | -1,830 | dd,sh,wr | -17.1% | 1.05 | -1.7% |
| R4b daily loss flatten L=1.5 ATR | +5.0% | -2.9% | 3.39 | 65.6 | 3933 | -1,279 | dd,wm,sh,wr | -4.4% | -1.9% | 3.94 | 64.6 | 3400 | -2,126 | dd,sh,wr | +2.1% | 1.05 | +2.1% |
| R5 dir cap lots N=2 | -21.0% | -25.5% | 3.33 | 64.3 | 3237 | -1,567 | wm,sh,net,n,wr | -2.4% | -23.8% | 3.63 | 63.9 | 2871 | -1,644 | dd,sh,net,n,wr | -39.0% | 1.04 | -15.5% |
| R5 dir cap lots N=3 | -5.1% | -11.4% | 3.45 | 65.0 | 3605 | -1,637 | dd,wm,sh,net,n,wr | -0.3% | -15.3% | 3.73 | 64.1 | 3152 | -2,187 | dd,wm,sh,net,n,wr | -29.2% | 0.98 | -12.4% |
| R5 dir cap lots N=4 | -4.6% | -5.0% | 3.50 | 65.3 | 3809 | -1,659 | dd,wm,sh,n,wr | +0.0% | -7.8% | 3.89 | 64.3 | 3299 | -2,022 | dd,sh,net,n,wr | -3.0% | 1.02 | -3.6% |
| R5 dir cap trades N=2 | -2.1% | -22.1% | 3.29 | 64.4 | 3369 | -1,795 | dd,wm,sh,net,n,wr | -4.9% | -18.4% | 3.75 | 63.9 | 2976 | -2,304 | dd,wm,sh,net,n,wr | -35.8% | 1.07 | -8.5% |
| R5 dir cap trades N=3 | -5.2% | -6.2% | 3.48 | 65.2 | 3739 | -1,613 | dd,wm,sh,net,n,wr | +0.0% | -6.7% | 3.91 | 64.4 | 3257 | -2,338 | dd,wm,sh,net,n,wr | -12.3% | 1.03 | -2.8% |
| R5 dir cap trades N=4 | +1.7% | -2.7% | 3.48 | 65.4 | 3912 | -1,527 | dd,wm,sh,wr | +0.0% | -2.8% | 3.96 | 64.6 | 3382 | -2,182 | dd,sh,wr | -1.2% | 1.01 | -1.8% |
| R6 session kill K=2 stop-outs | +2.6% | -9.3% | 3.24 | 65.6 | 3679 | -1,768 | dd,wm,sh,net,n,wr | +1.7% | -5.8% | 3.90 | 64.8 | 3156 | -1,956 | dd,sh,net,n | +22.9% | 0.96 | -10.4% |
| R6 session kill K=3 stop-outs | -5.4% | -1.8% | 3.46 | 65.7 | 3925 | -1,138 | dd,sh | +0.0% | -4.2% | 3.84 | 64.7 | 3343 | -2,004 | dd,sh,wr | +27.8% | 0.97 | -5.8% |
| R6 session kill K=4 stop-outs | -0.2% | -0.2% | 3.51 | 65.8 | 3954 | -1,176 | dd | +0.0% | -0.7% | 3.99 | 64.7 | 3398 | -2,182 | dd,sh | +3.9% | 0.99 | -3.1% |
| R8 weekly loss stop W=2 ATR | -23.2% | +2.3% | 3.63 | 65.9 | 3885 | -1,330 | wm | +0.0% | -0.9% | 4.00 | 64.7 | 3389 | -1,830 | dd,sh | +1.1% | 0.96 | -7.6% |
| R8 weekly loss stop W=3 ATR | -3.2% | +0.0% | 3.53 | 65.7 | 3952 | -1,176 | dd | +0.0% | +0.2% | 4.03 | 64.8 | 3418 | -2,048 | dd | -3.7% | 1.00 | -2.1% |
| R8 weekly loss stop W=4 ATR | +0.0% | +0.0% | 3.52 | 65.7 | 3977 | -1,176 | dd | +0.0% | +0.0% | 4.02 | 64.8 | 3421 | -2,182 | dd | -3.5% | 1.02 | -0.2% |
| R8 monthly loss stop M=4 ATR | +46.3% | -5.9% | 3.36 | 65.5 | 3776 | -2,087 | dd,wm,sh,net,n,wr | +0.0% | +0.1% | 4.02 | 64.8 | 3403 | -2,138 | dd | -17.5% | 0.95 | -8.4% |
| R8 monthly loss stop M=6 ATR | +0.0% | +0.0% | 3.52 | 65.7 | 3977 | -1,176 | dd | +0.0% | +0.0% | 4.02 | 64.8 | 3421 | -2,182 | dd | -0.8% | 0.97 | -5.4% |
| R8 monthly loss stop M=8 ATR | +0.0% | +0.0% | 3.52 | 65.7 | 3977 | -1,176 | dd | +0.0% | +0.0% | 4.02 | 64.8 | 3421 | -2,182 | dd | +0.0% | 1.02 | +0.0% |

Base Sharpe T1 3.52 / T2 4.02 / 2010-19 norm 1.02; base WR 65.7 / 64.8; base worst month -1,176 / -2,182.

### 2.2 Survivors

- Cells tested: **40**. T1 passes: **0**. T2 passes (unconditional): **0**. Both: **0**. P(T2 pass | T1 pass): undefined (no T1 pass). R9 combinations: none possible.
- The pre-registered bootstrap of accepted cells is therefore empty (`boot` in ddlab.json). The supplement (section 2.4) bootstraps the near-misses instead, as a diagnostic, not as a selection.

### 2.3 What the grid shows

- **DD reduction is bought with net $**: correlation between the DD change and the net change over the 40 cells is 0.63 (T1) and 0.77 (T2). Only one cell cuts the DD by more percentage points than the net in both periods: R1 stop<=k ATR k=0.2 (DD -16 / -19%, net -16 / -18%, Sharpe 3.46 / 3.71 vs 3.52 / 4.02, WR -1.7 / -1.5 pts) — a proportional shrink, not a risk improvement.
- Cells meeting the DD part alone (T1 >= 10% and T2 >= 5%): 6 of 40 (R1 stop<=k ATR k=0.15, R1 stop<=k ATR k=0.2, R2 skip risk>k ATR k=0.15, R2 skip risk>k ATR k=0.3, R3 heat cap H=0.4 ATR, R4b daily loss flatten L=0.5 ATR); every one of them loses 15-96% of the net and lowers the Sharpe in at least one period.
- Cells meeting DD + Sharpe in T1: only `R8 weekly loss stop W=2 ATR` (T1 DD -23%, Sharpe 3.63 vs 3.52, net +2.3%), which fails the T1 worst month (-1,296 vs -1,176) and does nothing in T2 (5 days changed, DD +0.0%, Sharpe 4.00 vs 4.02, net -0.9%). In T2 no cell meets DD + Sharpe.
- Worst month improved in both periods by 6 cells (R1 stop<=k ATR k=0.25, R1 stop<=k ATR k=0.35, R2 skip risk>k ATR k=0.15, R3 heat cap H=0.4 ATR, R4a daily loss block L=1.5 ATR, R6 session kill K=3 stop-outs), each failing DD or net / Sharpe elsewhere; worst-month changes of a few hundred $ are single-month events, not a property of the rule.
- R2 (skip by risk, exempt from the trade-count criterion) is the worst family: skipping trades with risk > 0.3 ATR removes 26% of the trades and 50-53% of the net (VOLB / MSEQ / ORB60 carry the large stops AND the profits). R2 k=0.4 keeps 92% of the trades but loses 17% of the net in both periods with the DD lower only in T1.
- R4a (block entries after -L x ATR) is the only family that is nearly neutral at L >= 1.0: T1 DD -6% / net -0.3% / Sharpe +0.03, T2 DD 0% / net -0.7% / Sharpe -0.03. It rarely triggers (T1 42 days, T2 21 days) and when it does the skipped afternoon is on average as profitable as any other (consistent with the 2026-10-12 finding: no autocorrelation of intraday losses).
- R4b (flatten at the breach) is worse than R4a everywhere: flattening at the loss turns open trades that would have recovered into realized losses (T2 L=1.0: DD +10%).
- R6 (session kill after K stop-outs) is neutral at K=4 (7-8 days per period) and harmful at K=2-3 in the 2010-19 view (DD +23-28%).
- R8 monthly stops are never triggered at M >= 6 (no month loses 6 ATR); at M=4 the one T1 trigger (2022) cost 46% more DD.
- R3 / R5 (heat and direction caps): monotone net loss with the cap, DD reduction only in T1 (T2 DD flat at every H / N), WR down 0.3-2 pts: the concurrent exposures they remove are mostly MOM1030 x4 + another module in the same trend, i.e. the trend-day profits.
- 2010-19 cost-normalised view: DD reductions there (R1 k=0.2 -37%, R3 H=0.4 -49%, R4b L=0.5 -51%) are proportional shrinks of a strategy with almost no edge in that decade (base Sharpe 1.02), and they all lower the net there too (R1 k=0.2 is the exception with Sharpe 1.11 vs 1.02 in norm units — not enough to override the real-$ failure).

### 2.4 Supplement: 21-day paired block bootstrap of the near-miss cells (500 resamples; diagnostic only)

| Cell | T1 DD change median [p10, p90] | P(T1 DD >5% lower) | T1 dSharpe med / P(up) | T1 days changed / trades dropped | T2 DD change median [p10, p90] | P(T2 DD >5% lower) | T2 dSharpe med / P(up) | T2 days changed / trades dropped |
|---|---|---|---|---|---|---|---|---|
| R8 weekly loss stop W=2 ATR | -8.4% [-23.4, +1.4] | 0.59 | +0.10 / 0.94 | 19 / 92 | +0.0% [-10.7, +4.4] | 0.23 | -0.02 / 0.35 | 5 / 32 |
| R4a daily loss block L=1.0 ATR | -4.6% [-12.5, +1.4] | 0.47 | +0.01 / 0.61 | 42 / 120 | +0.0% [-3.8, +1.0] | 0.01 | -0.06 / 0.12 | 21 / 52 |
| R1 stop<=k ATR k=0.3 | +0.3% [-11.0, +15.1] | 0.26 | +0.06 / 0.70 | 274 / 0 | -6.6% [-12.7, +3.9] | 0.56 | -0.03 / 0.45 | 227 / 0 |
| R3 heat cap H=1.5 ATR | -2.6% [-8.8, +2.0] | 0.30 | +0.01 / 0.63 | 52 / 110 | +0.0% [-2.4, +1.2] | 0.00 | -0.07 / 0.00 | 31 / 62 |
| R6 session kill K=4 stop-outs | +0.0% [-1.1, +0.0] | 0.00 | +0.00 / 0.53 | 7 / 23 | +0.0% [-1.2, +0.0] | 0.01 | -0.02 / 0.37 | 8 / 23 |
| R1 stop<=k ATR k=0.2 | -13.2% [-28.3, +3.5] | 0.75 | -0.02 / 0.45 | 488 / 0 | -15.0% [-24.2, +2.4] | 0.81 | -0.27 / 0.14 | 417 / 0 |

Reading: the weekly stop W=2 and the daily block L=1.0 have a bootstrap median DD change of 0% in T2 with P(Sharpe up) 0.35 / 0.12; the T1 DD reductions come from the few resamples that contain the specific 2022 weeks they skipped. R1 k=0.2 lowers the DD in ~80% of resamples but lowers the Sharpe in 86% of the T2 resamples (median -0.27): it is a smaller strategy, not a safer one.

### 2.5 MFFU Rapid EOD 50K, 1 contract, lifecycle (R1 / R3 / R4 cells; 1,000 bootstrap years per period; base in the first row)

| Cell | T1 $/month | T1 funded busts/yr | T1 accounts lost/yr | T1 P(neg yr) % | T2 $/month | T2 busts | T2 lost | T2 P(neg) % |
|---|---|---|---|---|---|---|---|---|
| **base ultra_d4** | 1,142 | 0.34 | 0.76 | 3.0 | 1,781 | 0.53 | 1.01 | 0.7 |
| R1 stop<=k ATR k=0.15 | 663 | 0.24 | 0.56 | 8.0 | 1,138 | 0.43 | 0.85 | 2.5 |
| R1 stop<=k ATR k=0.2 | 907 | 0.24 | 0.52 | 3.4 | 1,393 | 0.41 | 0.78 | 0.8 |
| R1 stop<=k ATR k=0.25 | 969 | 0.29 | 0.65 | 3.8 | 1,531 | 0.45 | 0.86 | 0.7 |
| R1 stop<=k ATR k=0.3 | 1,106 | 0.33 | 0.71 | 3.0 | 1,673 | 0.44 | 0.82 | 0.7 |
| R1 stop<=k ATR k=0.35 | 1,073 | 0.40 | 0.86 | 3.7 | 1,749 | 0.48 | 0.85 | 0.5 |
| R1 stop<=k ATR k=0.4 | 1,108 | 0.39 | 0.85 | 3.9 | 1,754 | 0.49 | 0.89 | 0.5 |
| R3 heat cap H=0.4 ATR | 614 | 0.25 | 0.58 | 7.2 | 1,240 | 0.30 | 0.60 | 1.1 |
| R3 heat cap H=0.6 ATR | 749 | 0.27 | 0.60 | 5.4 | 1,261 | 0.49 | 0.93 | 1.4 |
| R3 heat cap H=0.8 ATR | 934 | 0.28 | 0.64 | 3.5 | 1,410 | 0.51 | 0.95 | 1.1 |
| R3 heat cap H=1.0 ATR | 968 | 0.29 | 0.69 | 3.5 | 1,534 | 0.50 | 0.94 | 0.9 |
| R3 heat cap H=1.5 ATR | 1,091 | 0.32 | 0.72 | 3.1 | 1,689 | 0.54 | 1.02 | 0.7 |
| R4a daily loss block L=0.5 ATR | 1,014 | 0.29 | 0.65 | 3.9 | 1,575 | 0.47 | 0.85 | 0.7 |
| R4a daily loss block L=0.75 ATR | 1,057 | 0.35 | 0.78 | 4.0 | 1,695 | 0.45 | 0.86 | 0.7 |
| R4a daily loss block L=1.0 ATR | 1,135 | 0.33 | 0.70 | 3.3 | 1,754 | 0.54 | 1.02 | 0.5 |
| R4a daily loss block L=1.5 ATR | 1,146 | 0.34 | 0.76 | 3.1 | 1,756 | 0.54 | 1.03 | 0.9 |
| R4b daily loss flatten L=0.5 ATR | 851 | 0.17 | 0.38 | 4.2 | 1,075 | 0.61 | 1.27 | 4.8 |
| R4b daily loss flatten L=0.75 ATR | 963 | 0.26 | 0.62 | 4.5 | 1,298 | 0.57 | 1.20 | 3.0 |
| R4b daily loss flatten L=1.0 ATR | 970 | 0.39 | 0.89 | 5.4 | 1,664 | 0.54 | 1.02 | 0.8 |
| R4b daily loss flatten L=1.5 ATR | 1,090 | 0.42 | 0.96 | 4.0 | 1,721 | 0.55 | 1.02 | 1.0 |

No cell lowers the funded bust rate in both periods without cutting the income: R1 k=0.2 cuts T1 busts 0.34 -> 0.24 and T2 0.53 -> 0.41 but the income by 21-22% (the $2k trailing drawdown is hit by the same bad weeks, only with smaller trades); R3 H=0.4 cuts T2 busts to 0.30 at -30% income and raises P(neg year) in T1 to 7%; R4b L=0.5 cuts T1 busts to 0.17 but raises T2 busts to 0.61 and P(neg year) to 4.8%. The cells that keep the income (R4a L>=1.0, R1 k>=0.35, R3 H=1.5) leave the bust rate unchanged (+-0.02).

## 3. Verdict

**Nothing is accepted.** 0 of 40 pre-registered cells pass the T1 part of the acceptance, so there is nothing to verify on T2, and no R9 combination exists. The structure of the grid is the familiar one: every rule that lowers the max drawdown of this portfolio does it by removing part of the P&L (correlation 0.6-0.8 between the DD change and the net change), because the drawdowns are made of the same trades as the profits (large-stop structure trades on trend days and the x4 clock modules), and the losses are not clustered in a way a stop can exploit (daily / weekly stops rarely trigger and the days they skip are average days). The cheapest DD reductions seen (R1 k=0.2, R3 H=0.4, R4b L=0.5) are proportional shrinks with a lower Sharpe; the rules that preserve the Sharpe (R4a L>=1, R6 K=4, R8 W>=3, M>=6) do not change the drawdown. This confirms, on a wider and pre-registered grid, the 2026-10-12 and 2026-10-13 rejections (fixed-$ daily stops, concurrency caps, risk cap in evals) and the audit's conclusion that the losing months are not predictable.

What this means for Federico: the max drawdown per base contract (~$4.7k in 2020-23, ~$3.6k in 2024-26, worst month -$2.2k) is a property of the edge, not of the risk layer. The only levers that lower it without lowering PF / WR / trades are the ones already in use or already rejected: fewer contracts per account (linear), more accounts (diversification over time, not over trades), or a different edge. A tighter trailing-drawdown account can only be made safer by trading smaller.

## 4. Implementation notes (for the record; NO change to NQMaster.cs is recommended)

- R4a would be `DailyLossPerContract` expressed in ATR units (a `DailyLossAtr` property, threshold = L x ATR x $2 x base contracts, same `PropDailyCheck` hook, block entries only, no flatten). Neutral at L >= 1.0; not worth the parameter.
- R1 would be a `RiskCapPerContract` variant that tightens the stop to k x ATR instead of skipping the trade (`MinStopAtr` is the opposite guard; the stop price would be `entry -/+ min(structure, k x ATR)` in the ORB / VOLB / MSEQ / CRT11 / ICT / LON setups). Rejected: lowers WR and net in both periods.
- R3 would need a new 'open initial risk' accumulator (lots x stop distance / ATR) next to `MaxOpenContracts` (which counts contracts). Rejected: cuts net 4-34%.
- R5 / R6 / R8 have no existing analogue and are rejected.

## 5. Files

- `research/mine/ddlab.py` (build / run / supp; __main__ guard; threads <= 2; ~25 s per full grid), `research/mine/ddlab.json` (summary, grid, supplement), `research/mine/ddlab_grid.csv`, this report. Per-trade specs cached in the session scratchpad (`ddlab_specs.pkl`, rebuilt by `ddlab.py build` in ~10 s).
- Known simplifications: gates never create trades (a skipped or earlier-exited trade does not un-block an opposite entry removed by the original conflict filter); R4 uses 1-minute closes for the open P&L; the 2010-19 view uses the cost-normalised Ultra of cand16 (same rules as the real view).
