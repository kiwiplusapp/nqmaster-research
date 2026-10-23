# prop_wf: walk-forward optimizer for prop-account policies, 50K accounts, NQ only (2026-10-21)

Script: `research/mine/prop_wf.py`. Outputs: `prop_wf.json` (per firm: choice, bootstrap, seats, Q1/Q3, pay90) and `prop_wf_policies.csv` (12,084 rows: every eval and funded policy x haircut x period).
System: the 2027 default, NQ only (Ultra as coded + SO04/RV11/ORFAIL/CAM3, MOM1030/CPI09 x4). Data: `acct2027_paths.pkl` minus GoldMaster Robust. Real Databento NQ 2020-02..2026-10, with $1.90 commission + 1 tick per side and +1 extra tick. No new paths were built. The minute race reproduces `lucidpro_week.race` exactly (100% of starts), and the funded simulator reproduces `fu_pro` / `fu_flex` / `fu_m` exactly.

## 1. Pre-registration (written before looking at any result; also stored in the docstring and in `prop_wf.json` -> preregistration)

**Periods**
- T1 = starts 2020-02-26..2022-12-30. All choices are made here.
- T2 = starts 2023-01-03..2026-09-30. Check only; never used to choose.

**Haircut**
- hc = 0 / 35% / 100% of the mean daily P&L of the traded mix, per period.
- It is multiplied by the contracts traded, so it scales with size and with the MOM1030/CPI09 lot mix.

**EVAL policy space (per firm, 132-252 policies)**
- Size:
  - fixed k = 1..4 (MFFU at most 3: 30 micros);
  - cushion gear: kA if cushion >= C else kB, with C in {1000, 1500, 2500, 3000};
  - days gear: kA, then kB from eval day 5 or 10 while profit < 1,500.
- Intraday account stop L in {0, 600, 900, 1200}.
- Daily profit stop only where the eval has a consistency rule (Flex 1,350, MFFU 800).
- Serial restarts N in {1, 3}.
- Primary metric: **P(funded within 22 trading days, up to 3 evals)**.
- Other metrics: P(<= 10 d, 3 evals), P(<= 22 d, single eval), P(<= 120 d, 3 evals), fees of the 22-day plan.

**FUNDED policy space (48-160 per firm)**
- k in {1, 2}.
- Risk cap 300 below a cushion c in {0, 750, 1000, 1500} (MFFU also 2000).
- Account daily profit stop G in {0, 500, 700, 1000, 1500}, only where the funded account has a cycle-consistency rule.
- Payout request X: Pro amount >= 500 / full cap; Flex balance >= 2,500 / 4,000 / 5,000; MFFU keep 2,600 / 4,100 / 6,100.
- DailyLossPerContract in {0, 1500}.
- MFFU ladder recipe.
- Primary metric: **P(>= 1 payout within 62 trading days, about 90 calendar days, of the funded start)**.
- Other metrics: P(payout <= 41 / 124 td), P(survive 252 td), cash in 12 months, 12-month seat median $/month (eval + funded + re-buys, 300 block-bootstrap years).

**Selection and acceptance**
- The policy is the T1-best at full edge. A simpler policy within 1.0 pt on T1 wins.
- **Accept only if all of these hold:**
  - T2 bootstrap P(gain) >= 0.8 on the primary metric (21-day blocks, B = 300, the same paths for both policies);
  - no other metric is worse by more than 5% relative, including seat $/month;
  - at a 35% haircut the T2 primary is >= the current setup.

**Current setups**
- Lucid Pro: eval 4c, DLL OFF; funded 1c, FundedProfitStop 1000, cap 300 below 1000, payout at 4,100.
- Lucid Flex: preset Lucid50K at 2c.
- MFFU Rapid EOD: preset Mffu50K, eval 1c x8 + stop 800; funded 1c, cap below 2000, keep 4,100.
- Survey firms (Bulenox Opt1 intraday, FundedNext Rapid Pro, MFFU Builder; rules from `propfirms_2026-10-21.json`): the survey's fixed eval size and funded 1c with ASAP payout.

**Model notes (all optimistic unless stated)**
- MFFU minimum days: met with a token trade after the target.
- Intraday trailing in evals follows the minute-close peak, not the minute high (optimistic). In the funded account it is treated as EOD.
- Funded starts are unconditional, on every day of the period.
- MFFU news blackout is not modelled.
- Lucid Flex fee is $105.2 (screenshot); the survey uses the $146 list price.
- Max open lots on `ultra_d4` per base contract: p99 8, max 11. 4c > 40 micros on 1 day in 1,476; 3c > 30 micros on 0.07% of days.

## 2. Verdict

**No policy is ACCEPTED, for any firm.** The current setups stay.

The per-firm reason:

| Firm | Eval: T1 choice vs current, T2 P(funded <= 22 d, 3 evals), bootstrap P(gain) | Funded: T1 choice vs current, T2 P(payout <= 62 td), P(gain) | Why rejected |
|---|---|---|---|
| Lucid Pro 50K | cushion 4c/2c@1000: 84.5 vs 83.5, P 0.76 | 1c c1000 G500, payout ASAP (X500): 67.3 vs 58.7, P 0.98 | eval: noise. Funded: 12-month cash -41% ($3.3k vs $5.6k), seat $/mo -18% (929 vs 1,131) |
| Lucid Flex 50K | cushion 4c/3c@1000: 77.2 vs 75.9, P 0.61 | 1c c1500 X2500: 71.3 vs 49.5, P 1.00 | eval: noise and P(<= 120 d) 78 vs 88. Funded: seat $/mo -32% (973 vs 1,439) |
| MFFU Rapid EOD 50K | fixed 3c: **73.8 vs 48.1, P 1.00** | 1c no cap, keep 2,600: 67.8 vs 55.2, P 0.96 | eval: P(<= 120 d) 78 vs 97 and fees +42%. Funded: 12-month survival 7% vs 57% |
| Bulenox Opt1 50K | cushion 3c/4c@2500: 79.5 vs 78.0, P 0.75 | 1c G1000 ASAP: 72.6 vs 72.5, P 0.42 | noise |
| FundedNext Rapid Pro 50K | cushion 4c/2c@1000: 84.9 vs 83.7, P 0.78 | 1c c1000 G500 ASAP: 80.0 vs 69.4, P 1.00 | funded: survival 19% vs 49%, cash per account -24% (seat $/mo +42%, but the guard fails) |
| MFFU Builder 50K | fixed 3c = current | 1c c1000 G500: 63.5 vs 64.9, P 0.34 | noise |

**Overfitting check (base rate across the grid).**
- The share of T1 top-10% eval policies that stay in the T2 top 10% is near or below chance for most firms:

  | Firm | Lucid Pro | Lucid Flex | FundedNext | Bulenox |
  |---|---|---|---|---|
  | T1 top 10% still top 10% in T2 | 24% | 23% | 24% | 4% |

  The exception is the MFFU grids (86%, MFFU Builder 71%), because size dominates them.
- The Spearman rank correlation T1 vs T2 is still 0.82-0.96, because size explains most of the ranking. Fine-tuning beyond size is noise: the "best" schedule beats plain fixed size by about 1 pt.

**Plateaus.** The neighbours of every chosen eval policy are within about 1-2 pts on both T1 and T2. Example for Lucid Pro, P(funded <= 22 d), T1/T2:

| Policy | T1 | T2 |
|---|---|---|
| cu4/2@1000 | 90.7 | 84.9 |
| cu4/3@1000 | 90.2 | 84.3 |
| fix4 | 88.2 | 83.5 |
| cu2/4@2500 | 88.2 | 84.4 |

The surface is flat, so there is nothing to tune.

## 3. Full tables (history, T1 / T2)

### Eval, 35% haircut in brackets

| Firm / policy | P(<= 10 d, 3 evals) | P(<= 22 d, single) | **P(<= 22 d, 3 evals)** | P(<= 120 d, 3 evals) | Fees 22-day plan |
|---|---|---|---|---|---|
| Lucid Pro fix4 (current) | 77.2 / 77.0 | 47.7 / 44.3 | **88.2 / 83.5** (72.7 / 74.3) | 88.2 / 83.3 | $207 / $214 |
| Lucid Pro cu4/2@1000 | 74.4 / 77.1 | 47.7 / 46.0 | 90.7 / 84.9 (72.6 / 74.0) | 90.8 / 84.2 | $205 / $208 |
| Lucid Flex fix2 (current) | 38.9 / 41.2 | 52.3 / 51.0 | 74.3 / 74.5 (60.9 / 58.4) | 93.0 / 86.6 | $158 / $173 |
| Lucid Flex cu4/3@1000 | 68.2 / 66.6 | 43.8 / 41.8 | 91.4 / 76.2 (67.1 / 64.8) | 92.0 / 75.9 | $190 / $200 |
| MFFU fix1 x8 (current) | 11.2 / 11.8 | 39.5 / 44.0 | 41.0 / 48.8 (30.3 / 31.7) | 100 / 92.6 | $174 / $203 |
| MFFU fix3 | 39.4 / 46.2 | 36.9 / 47.8 | 69.1 / 72.0 (52.9 / 52.5) | 82.0 / 76.8 | $297 / $287 |
| Bulenox Opt1 fix4 | 76.6 / 72.3 | 45.5 / 41.7 | 87.8 / 78.1 (72.1 / 68.4) | 88.7 / 77.6 | $162 / $173 (+$148 activation) |
| FundedNext RP fix4 | same as Lucid Pro | | 88.2 / 83.5 | | $269 / $278 |
| MFFU Builder fix3 | | | 85.5 / 80.2 (63.7 T2) | 81.2 T2 | $191 T2 |

### Funded, 1c unless stated (T1 / T2)

| Firm / policy | P(pay <= 41 td) | **P(pay <= 62 td)** | P(pay <= 124 td) | Survive 252 td | Cash in 12 months |
|---|---|---|---|---|---|
| Lucid Pro current (G1000, payout at 4,100) | 49.0 / 43.0 | **72.4 / 59.0** | 86.8 / 62.9 | 83.8 / 44.9 | $8,946 / $5,385 |
| Lucid Pro G500, payout ASAP | 69.1 / 56.8 | 83.3 / 62.7 | 91.1 / 67.4 | 76.7 / 54.4 | $5,166 / $3,553 |
| Lucid Flex current 2c, X4000 | 55.5 / 53.8 | 55.5 / 55.0 | 57.0 / 55.3 | 47.3 / 32.1 | $4,660 / $3,782 |
| Lucid Flex 1c c1500, X2500 | 74.3 / 64.9 | 83.3 / 69.1 | 89.4 / 73.3 | 66.7 / 48.3 | $5,686 / $3,993 |
| MFFU current (keep 4,100) | 37.9 / 36.4 | 65.8 / 58.6 | 86.5 / 70.8 | 85.2 / 47.3 | $18,862 / $15,543 |
| MFFU keep 2,600, no cap | 68.0 / 59.1 | 79.2 / 65.2 | 87.8 / 65.6 | 70.0 / 3.3 | $20,474 / $7,183 |
| FundedNext RP ASAP | 74.3 / 67.5 | 84.8 / 69.9 | 88.4 / 70.7 | 70.4 / 37.2 | $4,105 / $2,442 |
| FundedNext RP c1000 G500 ASAP | 86.1 / 75.4 | 92.8 / 77.6 | 95.3 / 78.6 | 39.8 / 29.7 | $3,392 / $2,602 |
| Bulenox Opt1 ASAP | 59.6 / 54.8 | 79.0 / 68.4 | 92.5 / 68.7 | 92.4 / 51.7 | $10,366 / $7,617 |

### 12-month seat, bootstrap median $/month per seat (T1 / T2)

Seat = eval policy + funded policy + re-buys; current setups.

| Firm | Full edge | -35% | Zero edge | Funded busts per year (full edge) |
|---|---|---|---|---|
| Lucid Pro | 1,209 / 1,131 | 795 / 732 | -62 / -81 | 0.33 / 1.61 |
| Lucid Flex | 1,580 / 1,439 | 905 / 799 | 90 / -11 | 2.6 / 3.6 |
| MFFU Rapid EOD | 1,415 / 1,216 | 761 / 489 | -137 / -131 | 0.15 / 0.55 |
| Bulenox Opt1 | 855 / 810 | 480 / 444 | -49 / -49 | |
| FundedNext Rapid Pro | 612 / 645 | 344 / 331 | | |
| MFFU Builder | 958 / 835 | 539 / 452 | | |

### Haircut on the primary eval metric (T2, bootstrap medians, chosen / current)

| Firm | Full edge | -35% | Zero edge |
|---|---|---|---|
| Lucid Pro | 84.5 / 83.5 | 73.9 / 73.7 | 48.3 / 49.0 |
| Lucid Flex | 77.2 / 75.9 | 64.2 / 61.8 | 30.6 / 36.7 |
| MFFU | 73.8 / 48.1 | 53.9 / 33.4 | 27.5 / 14.9 |

Zero-edge pass rates are the gambler's-ruin baseline: size buys speed even with no edge.

## 4. Answers to the three questions

**(1) Best achievable P(funded within 10 / 22 trading days)**
Policy chosen on T1, T2 value, 35% haircut in brackets. The T2 hindsight maximum is in `prop_wf.json` -> Q1.

| Firm | Single eval, <= 10 d | Single eval, <= 22 d | Up to 3 serial evals, <= 10 d | Up to 3 serial evals, <= 22 d |
|---|---|---|---|---|
| Lucid Pro 50K | 43 (31) | 48 (34) | **77 (67)** | **85 (74)** |
| FundedNext Rapid Pro 50K | 43 | 48 | 77 | 85 |
| Lucid Flex 50K | 35 | 52 | 67 (53) | 76 (65) |
| MFFU Rapid EOD 50K | 38 | 51 | 46 (31) | 71 (53) |
| Bulenox Opt1 50K | 41 | 47 | 72 | 79 (67) |
| MFFU Builder 50K | 43 | 48 | 58 | 80 (64) |

- A single 50K eval is capped near 45-52% within a month on this edge. Only serial re-buys reach 75-85%.
- Lucid Pro's current 4c already sits on that plateau: 77 / 83.5.

**(2) Best achievable P(>= 1 payout within ~90 calendar days (62 trading days) of buying the first eval)**
Searched over the top-10 T1 eval policies x the top-10 T1 funded policies, with re-buys inside the window. Chosen on T1; T2 values, 35% haircut in brackets; fees = fees paid until the first payout or the end of the window.

| Firm | Best (T1-chosen) | Fees | Current setup | Fees |
|---|---|---|---|---|
| FundedNext Rapid Pro | **86.0% (73.3)** | $408 | 83.4 (66.2) | $480 |
| Lucid Pro | 76.2 (57.0) | $371 | 58.7 (39.0) | $364 |
| Lucid Flex | 75.4 (55.2) | $346 | 69.1 (47.7) | $331 |
| MFFU Builder | 75.8 (45.3) | | 76.3 (54.8) | |
| Bulenox Opt1 | 68.4 (43.6) | $460 incl. activation | 66.4 (44.8) | |
| MFFU Rapid EOD | 62.5 (39.6) | $439 | 31.7 (16.3) | $278 |

- Lucid Pro best = eval fix4 + funded payout ASAP with stop 700.
- Lucid Flex best = eval cu2/4@2500 + funded 1c X2500.
- MFFU Rapid EOD best = eval cu2/3 + funded keep 2,600.
- Every policy that raises the chance of an early payout does it by withdrawing small amounts early. That lowers cash per account and seat income: Lucid Pro -18%, Flex -32%.

**(3) Do intraday account stops or eval size schedules help?**

- **Intraday account stops: no.** Mean change in P(funded <= 22 d, 3 evals) vs no stop, over all size policies, on T2:

  | Stop | Change on T2 |
  |---|---|
  | $600 | -7 to -17 pts |
  | $900 | -1.4 to -7 pts |
  | $1,200 | 0 to -2.5 pts |

  The stop helps on T2 in at most 26% of policies. Under a 35% haircut, the best fixed size with a stop is 8-15 pts below the same without one.
- **Size schedules: no measurable gain.**
  - The best cushion schedule beats the best fixed size by about 1-1.5 pts on T2 (Lucid Pro +1.4, P(gain) 0.76; Flex +1.0; MFFU -1.1).
  - Days schedules (EvalMode style) do not help either: T2 -0.8 to +3.4 pts versus the best fixed size (Bulenox +3.4 is the only one above 2), and every one of them is below fixed size on T1.
  - The only large effect is plain size: Flex 2c -> 3-4c, MFFU 1c -> 3c. It moves the 22-day pass up and the 120-day eventual pass down.

## 5. Conditional option for Federico (NOT accepted by the protocol)

**MFFU Rapid EOD 50K eval at 3 contracts instead of 1c x8.**

Gains:
- P(funded <= 22 d, 3 evals): 48.8 -> 72.0 on T2; 31.7 -> 52.5 at a 35% haircut; P(gain) 1.00.
- P(funded <= 10 d, 3 evals): 12 -> 46.
- Seat $/month: +10% on T2 (1,216 -> 1,333) and +17% at a 35% haircut.

Costs:
- P(funded within 120 d, 3 evals): 93 -> 77.
- Fees of the 22-day plan: +$84.
- Zero-edge seat: -131 -> -275 $/month.

It was rejected only by the "others not worse than 5%" rule.

If Federico prefers speed, the settings are:
- PropPreset Mffu50K, PropMode Eval;
- Contracts 3;
- EvalHighWrMultiplier 0 (3c x MOM1030 x4 = 12 lots > 8 already);
- EvalProfitStop 800 (preset), MaxOpenContracts 30 (preset), EvalDailyStop 0.

Funded stays as the preset: Contracts 1, RiskCapPerContract 300, FundedRiskCapCushion 2000, FundedPayoutAt 4600. NQMaster.cs needs no change.

## 6. Settings

The current presets are confirmed:

| Firm | Eval | Funded |
|---|---|---|
| Lucid Pro 50K (PropPreset LucidPro50K) | Contracts 4, EvalTarget 3000, EvalProfitStop 0, EvalDailyStop 0, MaxOpenContracts 40, firm DLL OFF | Contracts 1, FundedProfitStop 1000, RiskCapPerContract 300, FundedRiskCapCushion 1000, FundedPayoutAt 4100, DailyLossPerContract 0 |
| Lucid Flex 50K (PropPreset Lucid50K) | Contracts 2, EvalProfitStop 1350 | Contracts 2, cap 300 below 1000, FundedPayoutAt 4000 |
| MFFU Rapid EOD (PropPreset Mffu50K) | 1c x8 or the 3c option in section 5 | Contracts 1, cap 300 below 2000, FundedPayoutAt 4600 |

Other notes:
- Mffu50KLadder was not re-scored here beyond the policy grid: the ladder at 1c, P(payout <= 62 td) 39 / 35%, is slow to pay by design.
- A cushion size schedule (cu*) would need new code (EvalCushionFull / EvalSafeSet switch module sets, not contract counts). It is not needed, because it is not better.

## 7. Caveats

- T1 holds about 34 independent 21-day blocks. Differences under about 3 pts in pass rates are within noise.
- The edge was assembled with 2020-26 in view, so T2 is out of sample for the policy only, not for the strategy.
- Funded starts are unconditional, not conditional on a pass.
- Intraday trailing (Bulenox) is optimistic.
- MFFU news blackout is not modelled (1.5-6.8% of P&L).
- Lucid Flex fee is $105.2 (the survey uses $146).
