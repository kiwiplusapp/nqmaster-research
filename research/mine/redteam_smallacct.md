# Red team: small-account eval study (smallacct_*.py, 2026-10-13)

Reviewer: independent re-implementation, written from the rules only. Code: `research/mine/redteam_smallacct.py`. Numbers: `research/mine/redteam_smallacct.json`.
The run takes about 10 s. The full calendar used for the elapsed-days check is `scratchpad/redteam_cal.npz`, all RTH days 2020-26 taken from `wrq_lib.getD`.

Same inputs as the study: the `smallacct_paths.pkl` day paths (intraday low, close MTM and realized P&L per base contract), the same start days and the same horizon (120 days).

- **T1:** starts 2020-03 to 2023-10.
- **T2:** starts 2024-01 to the end of the data minus 50 days.

"Serial" means a new eval starts the day after each bust. "Funded ≤ 22 d" means the pass day falls within 22 days of the first start.

## Verdict in one table

| Claim | Status | Corrected number |
|---|---|---|
| (1) 25K ≈ 72% vs 50K ≈ 44% funded ≤ 22 d (2024-26), 69% vs 29% (2020-23) | **Holds in direction and size; levels overstated by about 2-4 pts** | Strict 22 days on the real calendar: 25K **69.8% / 68.1%** vs 50K **41.2% / 27.2%** (T2 / T1). With +1 tick: 25K 69.1 / 65.3, 50K 39.5 / 25.8. The 25K minus 50K gap is +28 pts (T2) and +42 pts (T1). Block-bootstrap 95% CI: T2 [+17, +40], T1 [+32, +54]. |
| (2) Daily profit stop best near 0.9 × cons × target (50K $1,350, not $700) | **Holds, but $1,350 sits on a flat plateau, not at a sharp optimum** | 50K: $1,200 to $1,500 lie within 0-2 pts of each other. No stop at all costs -0.4 / -2.5 pts. $700 costs **-7.3 / -8.7 pts** (CI excludes 0). 25K: the plateau is $500-625, and $562 is fine. |
| (3) Start-day timing rules and concurrency caps do not help | **Holds** (timing re-tested; the concurrency result was checked from their JSON but not re-simulated) | The ATR ≤ 1.15 start filter changes sign between periods. On 25K T1 it is significantly *worse* (-23 pts, CI [-38, -7]). On T2 it is +12 (CI [-8, +31]). |

The study's main hidden caveat is not a code bug: **T2 is not an out-of-sample test of the edge**. UltraR was assembled with 2020-26 data, so T2 tests only the eval policy. Under the study's own 35% edge haircut, the claim becomes 25K ≈ 54-56% vs 50K ≈ 19-27% (still a large gap). At zero edge it becomes 31-37% vs 11-18%.

## A. Clean-room reproduction

The reimplementation (`run_eval`, `serial` in the .py) works as follows:

- The threshold is `min(maxEODbalance − D, +100)`.
- An account busts if `balance + intraday low ≤ threshold`.
- An account passes at the close of a day when profit ≥ T and the best day ≤ cons × profit.
- The daily profit stop G ends the day at the first minute where the close MTM is ≥ G, and exits at that close.
- The two-gear gating uses the cushion at the start of the day.

| Setup (no extra tick unless stated) | Single eval ≤ 22 d T1 / T2 | Eventual pass T1 / T2 | Bust T1 / T2 | Serial ≤ 22 d, **their counting** T1 / T2 | Study JSON T1 / T2 | Serial, strict 22 d | Serial, strict 22 **calendar** days |
|---|---|---|---|---|---|---|---|
| 25K pick (Estable below cushion 250) | 54.5 / 49.4 | 61.5 / 51.7 | 38.5 / 48.3 | **72.0 / 72.8** | 72.0 / 72.8 | 69.7 / 71.1 | 68.1 / 69.8 |
| 25K no gating | 53.3 / 49.6 | 56.2 / 52.0 | 43.8 / 48.0 | 71.1 / 72.9 | – | 69.0 / 71.1 | 67.5 / 69.7 |
| 25K no gating +1 tick | 49.4 / 46.4 | 53.0 / 49.7 | 47.0 / 50.3 | 69.0 / 72.0 | 69.0 / 72.0 (G-study / haircut-0) | 66.6 / 70.1 | 65.3 / 69.1 |
| 50K (pick = no gating) | 26.6 / 36.8 | 82.7 / 79.8 | 17.3 / 20.2 | **29.6 / 44.3** | 29.6 / 44.3 | 27.9 / 42.5 | 27.2 / 41.2 |
| 50K +1 tick | 25.4 / 35.4 | 79.1 / 75.2 | 20.9 / 24.8 | 28.3 / 42.8 | 28.3 / 42.8 | 26.6 / 41.2 | 25.8 / 39.5 |

**Every number reproduces exactly (0.0 pt mismatch) under the study's own counting.** No mismatch is larger than 3 pts, so no logic bug was found in `ev_m`, `vectors` or `serial`. The EOD-trailing lock, the touch-to-bust rule and the consistency check are all implemented as the rules say.

The differences I did find are in the counting conventions, not in the simulator:

1. **Off-by-one in `smallacct_protocol.protocol`.** It accepts `pass-day offset ≤ W`, which is W + 1 = 23 days including the start day. The single-eval statistic `stats()` uses `dd ≤ 22`, so the two are inconsistent. Effect: +1.7 to +2.3 pts on every "funded ≤ 22 d" figure.
2. **Excluded days.** FOMC days and ATR < 150 days are missing from the day list: 4.9% of T1 days and 3.1% of T2 days. On those days the account still exists and the bot is flat. So 22 list days equal 23.1 (T1) or 22.7 (T2) calendar trading days. Measuring on the real calendar removes another 0.7-1.6 pts.

Together the two conventions overstate funded ≤ 22 d by about **3 pts** (25K T2 72.8 → 69.8, 50K T2 44.3 → 41.2, 25K T1 72.0 → 68.1).

## B. Design biases

### B1. Overlapping start days

Consecutive starts share almost the whole 22-day window. The effective number of independent starts, estimated from the autocorrelation of the start indicator, is only **24-44 per period**, out of 643-902 start days.

Moving-block bootstrap of the paired difference (25K pick minus 50K, serial ≤ 22 d, study counting):

| Period | Difference | 95% CI, block 10 | block 22 | block 44 | block 66 | 25K CI (block 44) | 50K CI (block 44) |
|---|---|---|---|---|---|---|---|
| T1 | +41.8 | [34.1, 50.3] | [32.7, 52.5] | [31.7, 53.7] | [31.4, 52.8] | [58.5, 81.9] | [16.4, 40.7] |
| T2 | +28.6 | [19.9, 35.9] | [18.5, 37.9] | [16.6, 40.1] | [16.6, 41.2] | [58.0, 83.7] | [28.1, 59.6] |

Blocks of 10 days, as the brief asked, understate the uncertainty, because the indicator stays autocorrelated for more than 22 days. Use blocks of 44 or more. Even then the 25K advantage is far from zero.

The individual levels are imprecise. "72%" really means roughly 58-84%, and "44%" means roughly 28-60%.

### B2. Path-level block bootstrap

This resamples 10-day blocks of real days within each period, 150 synthetic histories, and runs both accounts on the same path:

| Period | 25K serial ≤ 22 d (2.5 / 50 / 97.5%) | 50K | Difference |
|---|---|---|---|
| T1 | 59.4 / 70.1 / 79.3 | 15.0 / 28.4 / 39.0 | 30.8 / 41.4 / 51.8 |
| T2 | 66.8 / 79.1 / 88.9 | 29.7 / 43.6 / 55.9 | 25.1 / 34.8 / 47.1 |

In 0 of 150 histories was the gap ≤ 10 pts. The T2 median for 25K (79%) is higher than the historical figure (71%). The 10-day resampling breaks up the summer-2026 losing cluster, so the historical path is the more conservative of the two.

### B3. Look-ahead and survivorship

- **No look-ahead inside the simulator.** The profit stop uses the close MTM up to that minute. Gating uses the cushion at the start of the day. The threshold uses only past end-of-day balances.
- **Policy selection is clean but irrelevant.** The 25K pick (Estable gear, f = 0.25) was chosen on T1 out of 21 combinations. It is equal to no gating in T2 (71.1 vs 71.1 strict), so selection bias from the gating is nil.
- **Strategy selection is the real bias.** UltraR's module set, the 2026-10-12 overhaul (ENG10/LATEFH off, MinStopAtr, context-boost removals) and the risk caps were all chosen with 2020-26 data in view. The 16-year Databento test says the edge is a post-2020 regime (cost-normalised PF about 1.0-1.1 in 2010-19). T2 is therefore an in-sample estimate of the *edge*.

Edge haircut, my reimplementation with +1 tick, strict 22 list days:

| Edge removed | 25K T1 / T2 | 50K T1 / T2 | Gap T1 / T2 |
|---|---|---|---|
| 0% | 66.6 / 70.1 | 26.6 / 41.2 | +40 / +29 |
| 35% | 54.0 / 56.1 | 19.4 / 27.1 | +35 / +29 |
| 60% | 43.3 / 48.8 | 15.1 / 22.4 | +28 / +26 |
| 100% (zero edge) | 31.4 / 36.9 | 11.1 / 18.5 | +20 / +18 |

So the *ranking* in claim (1) does not depend on the edge being real. Half to two thirds of the 25K advantage survives at zero edge (gap +18-20 pts vs +29-40 with the full edge), so it is structural:

- the target-to-drawdown ratio is lower (1.25 vs 1.5);
- each attempt resolves about 3 times faster (median 8-11 vs 24-32 days), so restarts fit inside 22 days.

The *level* "72%" does depend on the edge. A realistic forward estimate (35% haircut) is about **55%**.

### B4. Intraday low and bust measurement

The study's intraday low path (`robust2_life.full_paths`) is conservative, not optimistic:

- It adds every open trade's 1-minute bar extreme (low for longs, high for shorts) at the same minute, even when the extremes occurred at different seconds.
- It counts the entry bar's full range, including prices before the fill.
- On the exit bar it uses `min(bar extreme, realized P&L)`.
- It charges a $1.90 commission per open contract.

What it does not model is stop slippage beyond 1 tick on gap or news fills. I stressed that directly (+1 tick in all cases):

| Intraday low used | 25K serial ≤ 22 d T1 / T2 | 25K single-eval bust T2 | 50K serial T1 / T2 | 50K bust T2 |
|---|---|---|---|---|
| Close-only (most optimistic) | 65.9 / 72.9 | 36.5 | 26.5 / 41.2 | 14.5 |
| Study low | 66.6 / 70.1 | 50.3 | 26.6 / 41.2 | 24.8 |
| Low − $100 | 68.3 / 69.4 | 52.2 | 26.6 / 41.2 | 26.5 |
| Low − $200 | 69.3 / 68.0 | 61.3 | 26.6 / 41.2 | 27.2 |

The serial "funded ≤ 22 d" metric hardly moves (±3 pts), even though the single-eval bust rate goes from 37% to 61%. With instant restarts, an earlier bust mostly costs a fee, not time. **The cost side does move.** The number of evals bought rises, and the probability claim alone hides that.

Delaying the profit-stop exit by 1 or 3 minutes changes the 25K result by -0.4 to -0.6 pts and the 50K result by -0.4 pts.

### B5. Other caveats (not quantified here)

- **What you hold differs.** A 25K funded account has a $1,000 drawdown, payouts capped at $1,000, and a funded start of 10 micros. UltraR at 1 contract per module has a p99 of 7 simultaneous micros and a maximum of 11, so the 10-micro limit can bind on rare days. A 50K funded account has a $2,000 drawdown and a $2,000 cap. "Funded within 22 days" therefore does not measure the same asset in both cases. The 25K advantage in probability does not translate one-for-one into income.
- **Fees.** Expected evals bought per start, strict counting: 25K 1.6-2.0 (≈ $145-180) vs 50K 1.2-1.3 (≈ $180-190). At 35% haircut, the study's own table gives 25K 2.35 evals in T2. The cost is similar, so this is not a reason to doubt the claim.
- **Real rule risk.** The rule set (25K: $1,250 / $1,000 / 50% consistency) comes from third-party summaries dated 2026-10-03/07. Section C shows how much rule changes would matter.

## C. Rule sensitivity (Lucid Flex 25K, UltraR, no gating; profit stop G = 0.9 × cons × T unless stated)

| Variant | Single eval ≤ 22 d T1 / T2 | Serial ≤ 22 d (strict) T1 / T2 | Serial, calendar days T1 / T2 | Evals bought T2 |
|---|---|---|---|---|
| Base: T $1,250, D $1,000, cons 50%, +0 ticks | 53.3 / 49.6 | 69.0 / 71.1 | 67.5 / 69.7 | 1.97 |
| +1 tick per side | 49.4 / 46.4 | 66.6 / 70.1 | 65.3 / 69.1 | 2.02 |
| +2 ticks per side | 45.8 / 46.1 | 64.5 / 69.5 | 63.4 / 68.4 | 2.08 |
| D $900 | 49.3 / 46.4 | 69.8 / 72.0 | 68.7 / 70.5 | 2.10 |
| D $1,100 | 55.9 / 51.5 | 70.6 / 70.8 | 68.8 / 69.4 | 1.79 |
| T $1,500 (G $675) | 47.3 / 44.5 | 61.4 / 65.2 | 60.5 / 63.8 | 2.01 |
| cons 40% (G $450) | 52.8 / 52.7 | 67.1 / 71.1 | 66.2 / 69.5 | 1.82 |
| No consistency, no stop | 55.4 / 54.1 | 74.5 / 77.9 | 73.5 / 76.5 | 1.86 |
| No consistency, keep stop $562 | 53.5 / 49.7 | 69.2 / 71.1 | 67.7 / 69.7 | 1.96 |
| D $900 + 1 tick | 46.1 / 44.7 | 68.7 / 69.4 | 67.5 / 68.3 | 2.30 |
| T $1,500 + cons 40% + 1 tick | 43.8 / 41.4 | 56.7 / 63.0 | 55.5 / 61.9 | 2.13 |
| T $1,500 + D $900 + 2 ticks (bad case) | 39.3 / 38.9 | 58.4 / 62.7 | 57.5 / 60.2 | 2.36 |

What the table shows:

- The serial figure is robust to the drawdown size (±1 pt) and to costs (-1.5 to -4.5 pts for +2 ticks).
- The target matters most: $1,500 costs 6-8 pts.
- Consistency at 50% costs about 6 pts compared with no consistency.
- Even the bad case (58-63%) stays far above 50K at its base rules (27-41%).

## Claim (2): the profit stop, with a paired block bootstrap (block 44) against the claimed G (+1 tick, strict serial ≤ 22 d)

| 50K G | T1 | T2 | Δ vs $1,350 T1 [95% CI] | Δ T2 [95% CI] |
|---|---|---|---|---|
| 700 | 19.1 | 31.4 | -7.3 [-12.6, -2.9] | -8.7 [-16.2, -3.0] |
| 1,000 | 24.1 | 36.5 | -2.5 [-5.9, -0.1] | -4.5 [-8.9, -0.2] |
| 1,200 | 26.3 | 39.2 | -0.3 [-1.0, 0.1] | -2.0 [-4.2, -0.5] |
| **1,350** | 26.6 | 41.2 | 0 | 0 |
| 1,500 | 26.7 | 41.7 | +0.1 [-0.3, 0.7] | +0.3 [-0.2, 0.9] |
| 1,700 | 26.2 | 39.5 | -0.4 [-2.0, 0.6] | -1.7 [-3.4, -0.5] |
| 2,000 | 26.2 | 37.3 | -0.4 [-2.0, 0.6] | -3.6 [-6.4, -1.2] |
| None | 26.2 | 38.4 | -0.4 [-2.0, 0.6] | -2.5 [-4.7, -0.9] |

| 25K G | T1 | T2 | Δ vs $562 T1 [95% CI] | Δ T2 [95% CI] |
|---|---|---|---|---|
| 350 | 61.3 | 65.2 | -5.0 [-9.9, -0.6] | -5.1 [-12.6, 2.0] |
| 450 | 64.5 | 65.5 | -2.0 [-6.9, 2.5] | -4.7 [-9.8, -0.6] |
| 500 | 64.2 | 71.1 | -2.5 [-6.9, 1.6] | +0.9 [-1.1, 3.7] |
| **562.5** | 66.6 | 70.1 | 0 | 0 |
| 625 | 66.6 | 69.4 | 0.0 [-1.6, 1.6] | -0.6 [-5.9, 3.9] |
| 700 | 63.1 | 66.1 | -3.5 [-7.9, -0.4] | -3.9 [-8.1, -0.8] |
| 900 | 63.6 | 65.2 | -3.0 [-6.3, 0.7] | -4.8 [-8.9, -1.2] |
| None | 61.3 | 61.0 | -5.1 [-9.2, -0.6] | -8.4 [-15.4, -2.5] |

Claim (2) is confirmed with these qualifications:

- **"Not $700" on 50K is real:** -7 to -9 pts, and the CI excludes 0.
- **"$1,350 is best" is not distinguishable** from $1,200-1,500. On 50K in T1 it is not distinguishable from no stop at all either.
- The stop matters more on 25K, where no stop costs 5-8 pts, than on 50K (0.4-2.5 pts).
- The 0.9 × cons × T rule is a good default, not a precise optimum. Read it as "use 0.8-1.0 × cons × T".

## Claim (3): start-day timing (serial ≤ 22 d, no gating; subset vs the other start days; block-22 bootstrap CI of the difference)

| Account | Rule | T1 subset / rest (Δ, CI) | T2 subset / rest (Δ, CI) |
|---|---|---|---|
| 25K | ATR ≤ 1.15 × 60-day median | 64.1 / 86.8 (-22.8, [-37.5, -7.4]) | 74.6 / 64.0 (+11.7, [-8.4, 31.1]) |
| 25K | Prior 10-day P&L ≤ 0 | 60.6 / 70.8 (-8.5, [-26.3, 9.3]) | 76.3 / 69.7 (+6.0, [-9.2, 20.1]) |
| 50K | ATR ≤ 1.15 | 26.1 / 31.4 (-4.2, [-31.6, 17.4]) | 44.1 / 39.3 (+7.4, [-16.0, 29.3]) |
| 50K | Prior 10-day P&L ≤ 0 | 26.4 / 27.3 (-1.6, [-17.0, 15.1]) | 38.5 / 43.5 (-6.1, [-24.2, 11.8]) |

The effects change sign between periods. Only one is significant, and it is the opposite of the intended rule: in 2020-23 the ATR filter would have *hurt* 25K. So claim (3) holds. Not re-checked independently: the open-contract cap (`smallacct_conc.json`). Their numbers are monotone (K = 3 to 5 lowers or ties in both periods), and the mechanism is plausible because a cap removes trades without removing risk-adjusted edge. I see no reason to doubt it.

## Bottom line

- **Simulator:** correct. All numbers reproduce exactly.
- **Counting:** claim (1)'s headline levels are about 3 pts too high, from the off-by-one (23 days counted as 22) plus FOMC and low-ATR days left out of the calendar.
- **Sampling uncertainty:** much larger than the tables suggest. There are only about 25-45 independent start windows per period, so a 95% CI on the 25K level is about ±12 pts and on the gap about ±12 pts.
- **Edge selection:** the levels are in-sample for the edge. With a 35% haircut they become 25K ≈ 55%, 50K ≈ 20-27%.
- **What survives:** the ranking 25K ≫ 50K for "funded within a month with instant restarts". It holds at zero edge (37% vs 18%) and under every rule and cost variant tried.
- **Claim (2):** survives as "use 0.8-1.0 × cons × target; $700 on 50K is clearly bad".
- **Claim (3):** survives.
