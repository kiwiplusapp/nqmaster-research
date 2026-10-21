# Bot-friendly 50K prop plans: scored with the house race engine (2026-10-21)

Rules: `propfirms_2026-10-21.md` / `.json`. Engine: `prop_survey_sim.py` -> `prop_survey_sim.json` (runtime ~4 min).

## How the plans were scored
- Paths: NQ-only 2027 default (Ultra as coded + SO04/RV11/ORFAIL/CAM3, no GoldMaster), real NQ 2020-02..2026-10, +1 tick per side, minute resolution (`lucidpro_week.load()` with `nogold`).
- Size: k = 1..4 base MNQ per module, MOM1030/CPI09 at x4. Mean P&L is $90 per base contract per day in T1 and $120 in T2.
- Edge levels: full edge, and a 35% haircut (0.35 x mean daily P&L x k removed every day).
- Periods: T1 = starts 2020-03..2023-10, T2 = starts 2024-01.. (only starts with enough room for the window). The eval size k is chosen on T1, by serial pass within 22 trading days per dollar of fees; T2 is reported unchanged.
- Eval race: target T with NQMaster EvalTarget flatten.
  - Drawdown types: EOD, intraday (peak taken from minute closes), or static; lock at +100.
  - DLL: soft (day stopped) or hard (bust).
  - Consistency c: pass only when best day <= c x profit.
  - Min days: if the target is reached early, the account is parked until the minimum is met.
  - Time limit: 21 days for Trading Pit.
- Serial: a new eval the day after each bust, inside the window. Fees are the price per eval; subscriptions charge one month per started 21 trading days. Activation fees are added where the metric says so.
- Funded (generic minute model, 1 base contract): firm buffer, cap, % of profit, cycle consistency, qualifying days, min days, payout count limit, DLL.
  - Payout policy (house research): Lucid Flex / Tradeify Select / FTMO Growth request at $4,000 profit, Lucid Pro at $4,100, uncapped daily-payout firms (MFFU Rapid, LucidDaily) keep $4,100.
  - Every payout keeps >= $1,000 above the post-payout threshold. Payout = 90/10 or the firm's split.
- "12-month net per slot": serial evals at the chosen k until funded (<= 120 trading days), then that one funded account at 1c until month 12 (no re-buy after a funded bust). Net = payouts after split - eval fees - activation.

## Ranking 1: P(funded within 22 trading days per $), serial re-buys
Shown as T1/T2. Cost = eval fees + activation, paid only on pass. "per $100" = pass-% per $100 of cost.

| Plan | k | Funded <= 22 d | Cost | per $100 | k = 4: funded <= 22 d / cost | -35% edge, k = 4 | Single eval <= 22 d (chosen k) | Single <= 120 d, k = 1 |
|---|---|---|---|---|---|---|---|---|
| **Lucid Pro 50K, DLL off** | 2 | 72/84% | $177/182 | 41/46 | **96/99%**, $239/230 | 88/96% | 53/58% | 79/79% |
| **MFFU Builder 50K** (1 per user) | 2 | 69/79 | $158/170 | 44/47 | 92/89, $212/237 | 80/79 | 53/57 | 78/76 |
| FundedNext Flex 50K (rules S) | 1 | 40/52 | $87/94 | 46/55 | 66/74 | 49/59 | 38/45 | 69/74 |
| TradeDay Fast Pass 50K (rules S) | 2 | 59/72 | $162/172 | 37/42 | 74/81 | 59/70 | 44/49 | 79/78 |
| Tradeify Growth 50K (excluded: bot clause) | 3 | 85/93 | $214/227 | 40/41 | 94/93 | 85/85 | 50/52 | 79/77 |
| Lucid Pro 50K, DLL 1,200 | 3 | 86/90 | $213/239 | 40/38 | 93/91 | 84/85 | 49/51 | 79/76 |
| **FundedNext Rapid Pro 50K** | 2 | 72/84 | $230/237 | 31/36 | **96/99**, $311/299 | 88/96 | 53/58 | 79/79 |
| **Bulenox Opt1 50K** (intraday 2,500) | 2 | 72/83 | $241/264 | 30/32 | **95/100**, $341/356 | 88/96 | 52/59 | 81/83 |
| Bulenox Opt2 50K (EOD 2,500 + DLL 1,100) | 3 | 84/85 | $263/288 | 32/30 | 90/95 | 80/83 | 61/56 | 85/81 |
| FundedNext Rapid Daily 50K | 2 | 69/79 | $222/238 | 31/33 | 92/89 | 80/79 | 53/57 | 78/76 |
| Lucid Flex 50K | 2 | 65/78 | $228/247 | 28/32 | 81/89 | 67/75 | 48/52 | 79/79 |
| MFFU Rapid 50K (intraday funded) | 2 | 65/78 | $246/265 | 26/29 | 81/89 | 67/75 | 48/52 | 79/79 |
| FTMO Futures Growth 50K ($119/mo) | 2 | 54/67 | $208/220 | 26/31 | 66/72 | 49/59 | 40/46 | 79/78 |
| LucidDaily 50K (EOD eval) | 2 | 65/78 | $260/281 | 25/28 | 81/89 | 67/75 | 48/52 | 79/79 |
| Trading Pit Prime 50K (30-day window) | 2 | 47/55 | $228/259 | 21/21 | 49/36 | 26/16 | 39/40 | 30/33 |
| FTMO Futures Pro 50K (hard DLL, $139/mo) | 2 | 59/68 | $338/427 | 17/16 | 62/52 | 42/24 | 25/29 | 85/65 |
| MFFU Rapid EOD 50K (30% consistency) | 2 | 36/45 | $248/277 | 14/16 | 38/48 | 29/32 | 28/33 | 78/78 |

What decides the eval:
- **No eval consistency** is the dominant lever. With the same T 3,000 / D 2,000 EOD, serial 22-day pass at k = 4 is:

  | Eval consistency | Plans | Funded <= 22 d (k = 4) |
  |---|---|---|
  | none | Lucid Pro, FundedNext Rapid Pro | 96-99% |
  | 50% | Lucid Flex, MFFU Rapid | 81-89% |
  | 40% | Tradeify Select, FTMO Growth | 66-72% |
  | 30% | MFFU Rapid EOD | 38-48% |

- **A DLL costs a little:** Lucid Pro with DLL 1,200 drops from 96-99 to 91-93% at k = 4. A **hard** DLL costs a lot: FTMO Pro falls to 52-62% even with D = T.
- **Bulenox's 2,500 intraday drawdown is as good as 2,000 EOD:** stress D-150 gives the same results, so the minute-close peak approximation does not drive it. Its $148 activation makes it the most expensive per pass.
- **A single eval stays at ~50-60% within 22 days at any firm**, the same edge cap as before. 80-100% comes only from serial re-buys (1.5-1.8 evals on average at the chosen k, ~2 at k = 4).

## Ranking 2: P(>= 1 payout within 90 calendar days of funding), 1 contract
Shown as T1/T2; full edge, then the -35% edge in brackets.

| Plan | P(payout <= 90 cd) | Busted within 12 mo |
|---|---|---|
| Trading Pit Prime | 90/89 (81/82) | 100% (rules S) |
| FTMO Pro | 89/73 (82/70) | 100% (hard DLL 1,000) |
| TradeDay Fast Pass | 80/78 (65/70) | 65% (S) |
| FundedNext Rapid Pro | 78/77 (62/68) | 48%, but the account ends after 5 x $1,200 |
| FundedNext Rapid Daily | 77/75 (62/62) | 42% |
| MFFU Builder | 74/74 (60/60) | 35% |
| Bulenox Opt1 | 68/80 (52/55) | 27% |
| Bulenox Opt2 | 71/75 (53/51) | 28% |
| Tradeify Growth | 70/74 (51/53) | 27% |
| Lucid Pro DLL off | 64/74 (46/54), with the $4,100 request policy | 32% |
| Lucid Flex | 65/74 (47/54) | 42% |
| MFFU Rapid EOD | 61/71 (41/51) | 25% |
| MFFU Rapid intraday / LucidDaily | 60/69 (38/48) | 26%, keeping $4,100 |

Fast first payouts come from small caps or low buffers, and those same plans also bust or close the account quickly. The 90-day payout probability is therefore a poor proxy for income.

## Ranking 3: expected net cash per account slot (12 months, one funded account)
Shown as T1/T2; full edge, then -35% edge. "P(neg)" = P(net < 0) in T2 at -35%.

| Plan (eval k) | Net 12 mo | -35% | P(neg) |
|---|---|---|---|
| MFFU Rapid EOD (2) | $12.6k / $19.6k | $5.8k / $7.8k | 32% |
| MFFU Rapid intraday / LucidDaily (2) | 13.3k / 19.6k | 7.0k / 6.1k | 38% |
| Tradeify Select (2) (excluded) | 12.9k / 13.7k | 5.1k / 7.6k | 32% |
| FundedNext Flex (1) (S) | 7.0k / 11.3k | 4.3k / 5.1k | 53% |
| FTMO Growth (2) | 10.6k / 10.3k | 4.4k / 5.1k | 39% |
| Bulenox Opt1 (2) | 7.0k / 10.6k | 3.6k / 4.1k | 35% |
| Bulenox Opt2 (3) | 7.5k / 9.3k | 3.6k / 3.4k | 37% |
| Tradeify Growth (3) | 7.2k / 9.8k | 3.1k / 3.2k | 48% |
| Lucid Pro DLL off (2) | 6.9k / 7.6k | 3.6k / 4.5k | 35% |
| TradeDay Fast Pass (2) | 5.5k / 7.2k | 1.8k / 3.3k | 19% |
| Lucid Flex (2) | 6.0k / 6.1k | 2.9k / 3.7k | 37% |
| MFFU Builder (2) | 4.3k / 4.1k | 2.2k / 2.4k | 36% |
| FundedNext Rapid Pro (2) | 3.4k / 2.9k | 1.7k / 2.2k | 31% |
| Trading Pit | 3.0k / 3.8k | 2.2k / 0.5k | 55% |
| FTMO Pro | 3.2k / 2.2k | 1.6k / 1.1k | 35% |

Income is decided by the funded payout rules, not the eval: uncapped daily payouts (MFFU Rapid) earn the most, while capped and closing plans (FundedNext Rapid Pro: 5 x $1,200; MFFU Builder) earn the least.

## Recommendation (with the edge as validated; halve it for planning)
1. **Pass fastest per dollar: Lucid Pro 50K, DLL OFF, eval 4c serial.**
   - Funded within 22 days 96/99% (-35%: 88/96), cost ~$230-240 per funded account.
   - Funded at 1c: ~$7k a year per account (-35%: $3.6-4.5k).
   - This is already the house LucidPro50K preset.
2. **Earn most per funded account: MFFU Rapid EOD 50K** (keep $4,100, daily uncapped payouts, ~$12.6-19.6k a year at full edge, $5.8-7.8k at -35%).
   - Its 30% eval consistency makes the eval slow: 36-48% funded within 22 days, ~78% within 120 days at 1c.
   - Max 3 funded. Treat it as a slow-but-rich seat.
3. **Diversify the firm: Bulenox Opt1 50K** (no consistency, no DLL, D 2,500).
   - Eval as good as Lucid Pro: k4 95/100%.
   - Income per account $7-10.6k (-35% $3.6-4.1k) because of the 10-day payout cycles, 40% life consistency and caps.
   - Costs: $148 activation; whether NT8 triggers the $100/month composite-software fee is unverified.
4. **Same eval odds as Lucid Pro but capped income:** FundedNext Rapid Pro 50K (96/99%; ~$3k a year, account ends after 5 rewards).
   - Use it only for extra seats once Lucid's 5-funded and MFFU's 3 are full.
5. **Avoid:**
   - FTMO Pro (hard DLL).
   - Trading Pit (30-day window, NT8 unverified).
   - MFFU Rapid EOD as a fast route.
   - LucidDaily funded (red-folder hard breach).
   - Tradeify (cross-firm bot clause).
   - Apex, Topstep, TPT, Alpha, ETF, Top One, Leeloo, Phidias, E8, The5ers (automation not allowed or no NT8).

## Caveats (honest)
- **Fewer independent tests than the starts suggest:** windows overlap, so T1 has ~40 and T2 ~30 effective independent 22-day starts. Pass rates carry +-8-10 points of noise.
- **Selection bias:** the edge was assembled with 2020-26 in view. The -35% columns are the planning level; at zero edge every plan loses its fees.
- **Rules flagged S / UNVERIFIED drive the numbers for some plans:** Bulenox caps and reserve, Tradeify Growth, FundedNext Flex, FTMO payout mapping, TradeDay, Trading Pit. Confirm with each firm in writing before buying.
- **Intraday trailing uses the minute-close peak:** slightly optimistic, though the Bulenox stress test D-150 showed no change. LucidDaily / MFFU Rapid intraday funded busts are likely understated.
- **Contract caps:** k = 4 can briefly exceed 40 micros (house research: max ~44). At MFFU (30 micros, MNQ+MGC combined) k >= 3 does not fit. Set MaxOpenContracts per firm.
- **News rules are not simulated:** MFFU funded T1 and LucidDaily red-folder rules would remove ~2-6% of P&L.
- **The funded model is generic:** it reuses no house lifecycle (one account, no re-buy after a funded bust, a fixed payout policy). Per-seat lifecycles with re-buys (acct1c_lib / mffu_rapid) earn more per month; compare plans with each other, not with those numbers.
- **Prices change weekly** (coupons). The per-$ ranking uses the prices in the JSON.
- **Coordination:** no eval/funded policy was received from the prop_wf optimizer during this run, so fixed sizes were used.
