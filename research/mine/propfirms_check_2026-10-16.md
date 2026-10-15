# Prop-firm rules check: automation, news, accounts (checked 2026-10-15/16)

Scope: a fully automated NinjaTrader 8 strategy (NQMaster on MNQ, GoldMaster on MGC) on prop-firm accounts.

Confidence labels:
- **CONFIRMED (primary)**: read directly on the firm's own help center or FAQ page.
- **PRIMARY via search excerpt**: the firm's own page is behind Cloudflare (HTTP 403 to every fetch, including archive and reader proxies), so the text comes from search-engine excerpts of that official page, not a direct read.
- **SECONDARY only**: third-party sites only.
- **NOT FOUND**: no answer found.

The "date shown" is the date printed on the help-center article. Lucid and MFFU articles show "Written by ... <date>", which is the current revision date. Some pages only say "Updated over a week ago".

## Previous notes checked against the sources

| Previous note | Result |
|---|---|
| "Apex bans automation since 2026-03-01 (Apex 4.0)" | **Ban CONFIRMED** (Apex's own pages, through search excerpts). **The date is not confirmed.** The same wording also appears on Apex's *Legacy* PA Compliance page, so the PA/Live ban is older than 4.0. Only secondary sources tie it to "March 2026 / 4.0". One Apex consistency article limits the ban to PA and Live accounts. The Prohibited Activities page, the PA compliance pages and the User Agreement ("manually initiated" orders) cover all account types. Either way, NQMaster cannot be used at Apex. |
| "Topstep TopstepX-only for new accounts" | **CONFIRMED, and stricter than the note.** Topstep's help center says "TopstepX™ is the only available trading platform", with no "new accounts" qualifier. Bots are allowed only through the TopstepX/ProjectX API, from your personal device (no VPS), and not in Live Funded accounts. NinjaTrader 8 strategies cannot run there. |
| "Lucid and MFFU allow bots" | **CONFIRMED** from both firms' help centers. The conditions are listed in the Lucid and MFFU sections below. Several third-party blogs (TradersPost, proptradingvibes) wrongly say "semi-automated only / no bots". The primary pages contradict them. |
| "MFFU funded requires flat ±2 min around Tier-1 news" | **CONFIRMED for Rapid Sim Funded and Pro Sim Funded.** Evaluations and Builder plans are permitted to trade Tier 1 news. Two additions:<br>(a) the window also bans resting orders: "No positions or orders (including limit orders)".<br>(b) Tier 1 = FOMC Meetings, FOMC Minutes, Employment Report, CPI (plus EIA for energy traders and agricultural reports for agricultural traders).<br>The same page has an ambiguous "Standard Trading Protocols" clause covering **all** data releases (details in the MFFU section). |

---

## 1. Lucid Trading (LucidFlex, LucidPro)

The help center is at https://support.lucidtrading.com/en/. lucidtrading.com itself returns 403.

### Automation
- **Rule:** Automated trading and trade copiers are allowed. The page does not distinguish evaluation from funded, so the rule covers every plan.
- **Quotes:**
  - "Automated trading systems and trade copiers are permitted"
  - "All automated activity must comply with Lucid Trading rules"
  - "Traders are fully responsible for any software errors, malfunctions, or unintended outcomes"
- **Source:** https://support.lucidtrading.com/en/articles/11404728-other-trading-activities (date shown Aug 26, 2026)
- **Confidence:** CONFIRMED (primary).
- **Own code:** The page has no "must be your own code" clause.

### Prohibited: high-frequency trading
- **Definition:** HFT "is a type of automated trading strategy", meaning a "high volume of trades within extremely short time frames". The page gives "hundreds of orders being placed within minutes" as an example but sets no numeric threshold. Lucid uses "automated risk detection systems to flag HFT activity".
- **Source:** https://support.lucidtrading.com/en/articles/11404736-prohibited-high-frequency-trading (Aug 26, 2026)
- **Confidence:** CONFIRMED.
- **For NQMaster:** about 4-6 trades per day is far from this definition.

### Prohibited: microscalping
- **Rule:** An account is flagged when "More than 50% of your profits are generated from trades held for 5 seconds or less".
- **Source:** https://support.lucidtrading.com/en/articles/11404742-prohibited-microscalping (Aug 26, 2026)
- **Confidence:** CONFIRMED.
- **For NQMaster:** not relevant.

### Prohibited: hedging
- **Rule:** "Lucid Trading strictly prohibits all forms of hedging". This includes "Hedging across multiple accounts held by the same user", and "you cannot go long / short different contracts in separate accounts with correlated assets".
- **Source:** https://support.lucidtrading.com/en/articles/11404734-prohibited-hedging ("Updated over a week ago")
- **Confidence:** CONFIRMED.
- **Operational risk:** different NQMaster profiles or presets on different Lucid accounts (for example eval Ultra and funded WR70Plus) can hold **opposite MNQ positions at the same time**, which this rule forbids. Keep every Lucid account on the same signal set, or make sure directions cannot diverge.
- **MNQ vs MGC:** the page names no instruments. NQ-gold correlation is low, but the wording ("correlated assets") is not limited to specific pairs.

### News
- **Rule:** News trading is allowed on Flex, Pro and Direct. It is not allowed on LucidDaily.
- **Quotes:**
  - "Allowed on Flex, Pro and Direct"
  - "Traders may enter or exit positions around scheduled or unscheduled news events on these plans without it being a breach"
  - "Trading red folder news on the LucidDaily is a hard breach"
- **Source:** same Other Trading Activities page (Aug 26, 2026).
- **Confidence:** CONFIRMED.

### Maximum accounts
- **Limits:**
  - "Up to 10 active evaluation accounts per household or family"
  - "a maximum of 10 accounts in total across evaluation accounts and funded accounts"
  - "Up to 5 active funded accounts per household or family"
  - Different funded types combined may not exceed 5
  - LucidLive has a separate limit of 5
- **Source:** https://support.lucidtrading.com/en/articles/11404617-maximum-number-of-accounts (Aug 26, 2026)
- **Confidence:** CONFIRMED.
- **Matches the earlier note** (5 funded, 10 total). The "$750K combined" figure from the earlier note is **not found** on this page.

### LucidFlex consistency
- **Rule:** The evaluation requires a 50% consistency percentage: "you must have Consistency Percentage of 50% or less to be eligible to upgrade". The formula is "Largest Single Day Profit / Account Profit".
- **Source:** https://support.lucidtrading.com/en/articles/12945805-lucidflex-consistency-percentage (Aug 26, 2026)
- **Funded:** no consistency rule is stated on this page or on the Flex payouts page.
- **Confidence:** CONFIRMED.

### LucidPro consistency
- **Funded:** "In our LucidPro funded accounts you must meet a Consistency Percentage of 40% to be eligible to request a payout". It "resets and must be met again after each payout".
  - The rule rose from 35% to 40% for accounts bought or reset on or after 11/28/2025 at 3:00 PM EST.
  - No consistency applies once an account is promoted to Live.
- **Evaluation:** the LucidPro evaluation page lists no consistency rule.
- **Sources:**
  - https://support.lucidtrading.com/en/articles/12890109-lucidpro-consistency-percentage (Aug 26, 2026)
  - https://support.lucidtrading.com/en/articles/12890029-lucidpro-evaluation-account (Aug 26, 2026)
- **Confidence:** CONFIRMED.

### Drawdown (Flex and Pro)
- **Type:** "End-of-Day Drawdown (EOD Drawdown)". The MLL trails the highest session closing balance and "locks at the initial balance plus $100" once the account passes the initial trail balance.

| Size | MLL | Initial trail balance | Locked MLL |
|---|---|---|---|
| 25K | $1,000 | 26,100 | 25,100 |
| 50K | $2,000 | 52,100 | 50,100 |
| 100K | $3,000 | — | — |
| 150K | $4,500 | — | — |

- **Payouts:** a payout request moves the MLL to the locked level.
- **Sources:**
  - https://support.lucidtrading.com/en/articles/12945815-lucidflex-drawdown (Aug 26, 2026)
  - https://support.lucidtrading.com/en/articles/12890136-lucidpro-drawdown (Aug 26, 2026)
- **Confidence:** CONFIRMED.

### Other Flex facts
**Evaluation** (https://support.lucidtrading.com/en/articles/12945790-lucidflex-evaluation-account, Aug 31, 2026):
- Targets: 25K $1,250, 50K $3,000, 100K $6,000, 150K $9,000.
- No daily loss limit (optional at checkout).
- Max size: 20 / 40 / 60 / 100 micros.

**Funded scaling** (https://support.lucidtrading.com/en/articles/12945808-lucidflex-scaling-plan, May 6, 2026):

| Funded profit | 25K max | 50K max |
|---|---|---|
| $0-999 | 10 micros | 20 micros |
| $1,000-1,999 | 20 micros | 30 micros |
| $2,000+ | — | 40 micros |

**Payouts** (https://support.lucidtrading.com/en/articles/12945796-lucidflex-payouts, Jul 28, 2026):
- 5 days at or above $100 / $150 / $200 / $250 (25K / 50K / 100K / 150K).
- Net-positive cycle.
- Minimum request $500.
- Maximum request is 50% of profit, capped at $1,000 / $2,000 / $2,500 / $3,000.
- Split 90/10.
- Up to 5 payouts, then the account moves to Live.

### Other Pro facts
**Evaluation** (Aug 26, 2026): targets are the same as Flex. Daily loss limits:
- 25K: none
- 50K: $1,200
- 100K: $1,800
- 150K: $2,700

**Payouts** (https://support.lucidtrading.com/en/articles/12890092-lucidpro-payouts, Aug 6, 2026):
- The buffer is the initial MLL + $100.
- First payout capped at $1,000-3,000 depending on size; later payouts at $1,500-3,500.
- Minimum request $500. There is "no fixed payout window".
- 40% best-day rule per cycle.
- Split 90/10.

### Trading hours
- **Rule:** "All positions must be closed by 4:45 PM EST" (Lucid auto-closes positions; this is not a breach). On holidays with altered closing times, positions must be closed before the market closes.
- **Source:** https://support.lucidtrading.com/en/articles/11404729-allowed-trading-times (Aug 26, 2026)
- **Confidence:** CONFIRMED.

### Products and commissions
- **Rule:** MNQ and MGC are both approved. Commissions:
  - MNQ: $0.50 per side ($1.00 round trip)
  - MGC: $0.80 per side ($1.60 round trip)
- **Source:** https://support.lucidtrading.com/en/articles/11508978-approved-products-and-commissions (Aug 26, 2026)
- **Confidence:** CONFIRMED.
- **For research:** the $1.90 round trip used in research is conservative for Lucid.

### Secondary-source conflict
- proptradingvibes.com lists "No Automation" for Lucid. The primary page contradicts it, so ignore it.

---

## 2. MyFundedFutures (MFFU), Rapid plans

The help center is at https://help.myfundedfutures.com/en/.

### Automation
- **Rule:** Automated strategies are allowed if they are "tailored to their own specific settings" and do not exploit simulated fills. No plan or stage is excluded; only the HFT ban mentions "plans".
- **Quotes:**
  - "High-frequency Trading is not allowed on our plans."
  - "Traders may make use of automated trading strategies tailored to their own specific settings so long as these automated tools do not aim to exploit the favorable fills offered in the Simulated Environment."
  - "Traders trading live accounts with automated trading must abide by CME guidelines."
  - Also prohibited: "Exploiting the absence of slippage and utilizing tight brackets to gain from favorable fills".
  - Also prohibited: "Collaborating with others to execute identical or opposite strategies across unconnected accounts" and copy trading between traders.
- **Source:** https://help.myfundedfutures.com/en/articles/8444599-fair-play-and-prohibited-trading-practices (date shown Aug 24, 2026)
- **Confidence:** CONFIRMED (primary).
- **Secondary-source conflict:** TradersPost blogs (Feb/Mar 2026) say "semi-automated only, fully automated prohibited" and cite a 200 trades/day cap. **The primary page contradicts the automation claim and has no trade-count cap.**

### Hedging
- **Rule:** "MyFunded Futures prohibits hedging of any kind". Hedging means buy and sell "on the same underlying asset, at the same time". E-mini and Micro NQ count as the same underlying. "hedging through different unrelated assets is permitted".
- **Source:** https://help.myfundedfutures.com/en/articles/12011241-hedging-what-you-should-know (Nov 10, 2025)
- **Confidence:** CONFIRMED.
- **For NQMaster:** it is not explicit about the trader's own separate accounts. As at Lucid, avoid opposite MNQ positions across accounts.

### News
- **Source:** https://help.myfundedfutures.com/en/articles/8230009-news-trading-policy (date shown Aug 31, 2026)
- **Confidence:** CONFIRMED.
- **Scope:** T1 news trading is "prohibited" on **Rapid Sim Funded** and **Pro Sim Funded**. It is "permitted" in **all evaluations** and **Builder Plans**. Live is not mentioned.
- **Window:** "No positions or orders (including limit orders) can be open 2 minutes before and after the release." For an 8:30 release, "positions must be closed by 8:28:00 or earlier, and may only be reopened after 8:32:00".
  - **NewsBlackout implication:** besides being flat, NQMaster/GoldMaster must have **no resting entry orders** (stop or limit) in the window.
- **Tier 1 list:** "FOMC Meetings, FOMC Minutes, Employment Report, CPI" for all traders; "EIA" for energy traders; "Agricultural Reports" for agricultural traders. The page never says "NFP"; that is the Employment Report. "FOMC Meetings" = the rate decision days.
- **Ambiguity:**
  - The "Standard Trading Protocols" say "Ensuring no open positions or orders are active in the order book 2 minutes before and after any data release" and "These protocols apply to all news releases".
  - The next section then says "you may trade through other news releases if it aligns with your regular trading strategy".
  - The text is self-contradictory. The strict reading (±2 min around *every* release) was estimated earlier to cost Ultra about 15-18%. **Still worth asking MFFU in writing.**
- **Consequences:** the page states none. Secondary sources say account closure.
- **Confirmed by plan page:** the Rapid EOD 50K page lists "T1 News Trading: No" for Sim Funded and "Yes" for the evaluation.

### Rapid EOD 50K
- **Source:** https://help.myfundedfutures.com/en/articles/16158363-rapid-eod-50k-a-comprehensive-look (Aug 24, 2026)
- **Confidence:** CONFIRMED.
- **Evaluation:**
  - Target $3,000.
  - $2,000 EOD trailing ("does not move intraday – only at the close of each trading session"), locking at +$100.
  - 30% consistency.
  - Minimum 4 days.
  - No daily loss limit.
  - "3 minis / 30 micros".
- **Sim funded:**
  - No consistency.
  - Buffer "$2,100 in realized profits before the first payout"; after that, each payout unlocks when net profit since the last payout reaches $500.
  - Payouts **daily**, no cap per cycle, minimum $500.
  - Split 90/10.
  - Max 30 micros.
  - No activation fee.
  - 7-day inactivity rule.
- **Price:** not shown on the page.

### Rapid EOD 25K
- **Source:** https://help.myfundedfutures.com/en/articles/16727601-rapid-eod-25k-a-comprehensive-look (Sep 2, 2026)
- **Confidence:** CONFIRMED.
- **Evaluation:**
  - Target **$1,500**.
  - **$1,000 EOD** trailing, locking at +$100.
  - 30% consistency.
  - Minimum 4 days.
  - 20 micros.
- **Sim funded:**
  - Buffer $1,100; then a payout unlocks every $250 of net profit.
  - Payouts daily, no cap, minimum $500.
  - Split 90/10.
  - No T1 news.
- **Note:** this replaces the earlier "MFFU 25K rules unknown (assumed scaled)": the target is $1,500, not $1,250.

### Account limits
- **Source:** https://help.myfundedfutures.com/en/articles/16498635-moving-from-evaluation-to-sim-funded-account (Sep 4, 2026)
- **Confidence:** CONFIRMED.
- **Evaluations:** "a maximum of 10 active Evaluation Accounts".
- **Sim funded at 25K/50K:** up to 5 in any mix, with plan caps:
  - Rapid EOD 25K: 3
  - Rapid EOD 50K: 3
  - Builder 25K: 2
  - Builder 50K: 1
- **Any 100K/150K account held:** maximum 3 sim funded accounts in total.
- **Matches the earlier "max 3 accounts"** for Rapid EOD 50K.

### Other rules
- **Cross-instrument size** (https://help.myfundedfutures.com/en/articles/10244682-cross-instrument-policy, Aug 24, 2026): combined orders across instruments must stay within the account's contract limit ("may technically execute ... but this is not permitted!").
  - **For NQMaster:** MNQ and MGC together count toward the 30-micro cap (MaxOpenContracts).
- **2% price-limit rule** (https://help.myfundedfutures.com/en/articles/9698984-2-price-limit-rule, Aug 24, 2026): no trading when a product is within 2% of a CME price limit, on Sim Funded and Live Funded.
- **Hours** (https://help.myfundedfutures.com/en/articles/9558251-permitted-times-to-trade, Aug 24, 2026): positions are auto-closed at 4:10 PM EST on regular days.
  - On holiday half-days "auto-liquidation will not occur at the half-time market close". The trader must flatten, or the account can be breached. SkipShortSessions covers this.

---

## 3. Apex Trader Funding

Every apextraderfunding.com and support.apextraderfunding.com page returns Cloudflare 403, including through the Wayback Machine and reader proxies. The text below comes from search-engine excerpts of Apex's own pages.

### Prohibited Activities page
- **Quote:** "No Automation or Algorithm Usage allowed: Rewards are intended to recognize human traders actively participating in the learning process, not to reward automated systems executing preprogrammed logic."
- **Sources:**
  - https://apextraderfunding.com/help-center/getting-started/prohibited-activities/
  - https://support.apextraderfunding.com/hc/en-us/articles/40463668243099-Prohibited-Activities
- **Confidence:** PRIMARY via search excerpt. The same sentence is quoted by proplens.trading, which says it checked firm pages on Sep 30, 2026.

### PA compliance pages
- **Quote:** "At Apex Trader Funding, the use of automation is strictly prohibited on all account types. This includes any form of AI (Artificial Intelligence), Autobots, algorithms, fully automated trading systems, and high-frequency trading (HFTs)."
- **Penalty:** "immediate closure of your PA or Live account and the forfeiture of all funds and balances".
- **Allowed:** ATM bracket (stop/target) automation is allowed.
- **Sources:**
  - https://support.apextraderfunding.com/hc/en-us/articles/31519788944411-Performance-Account-PA-and-Compliance
  - https://apextraderfunding.com/help-center/performance-accounts-pa/legacy-performance-account-pa-compliance/
- **Confidence:** PRIMARY via search excerpt.

### User Agreement
- **Rule (excerpt as summarized):** orders must be manually initiated. Any tool that "pre-programs, batch-submits, pre-loads, auto-executes ... or otherwise automates orders entry or order modification" is prohibited.
- **Source:** https://dashboard.apextraderfunding.com/legal/user-agreement
- **Confidence:** PRIMARY via search excerpt; the full text could not be read.
- **Live program FAQ:** also says automation and algorithms are not allowed.

### Contradictions and open points
- **Date:** the ban is confirmed, but **"since 2026-03-01" is not confirmed.** The identical "all account types" sentence is on the **Legacy** PA Compliance page, so the PA/Live ban existed before Apex 4.0. Only secondary sources (TradersPost March 2026, prop-memo, pickmytrade) link it to "Apex 4.0 / March 2026". 4.0 may have extended the ban explicitly to evaluations.
- **Scope:** one Apex article ("What are the Consistency Rules for PA and Funded Accounts?") scopes the ban to PA and Live only. A few vendor blogs (QuantVPS, CrossTrade sales page) still say bots are fine in evaluations.
- **Practical conclusion:** do not use NQMaster at Apex. A pass would lead to a PA where automation means forfeiture, and the current pages say "all account types".
- **Secondary, not verified:** Apex halted metals contracts on 2026-03-14 (proptradingvibes). If true, MGC would not be available at Apex anyway.

---

## 4. Other firms (automation, one line each)

### Topstep
- **Rule:** Bots are allowed only through the TopstepX/ProjectX API. NinjaTrader cannot be used.
- **Quotes:**
  - "TopstepX™ is the only available trading platform" (https://help.topstep.com/en/articles/8284199-new-to-topstep-start-here, Jul 20, 2026).
  - "Custom automated strategies and bots are allowed via the TopstepX / ProjectX API, subject to standard platform rules and our prohibition on highfrequency trading (HFT)".
  - "All trading activity must originate from your personal device". Running automation on a VPS "can result in account suspension or removal".
  - API access costs $29/month.
  - "Live funded accounts are not allowed to trade through the ProjectX API" (https://help.topstep.com/en/articles/11187768-topstepx-api-access, "Updated over a month ago").
- **Confidence:** CONFIRMED.

### Bulenox
- **Rule:** Bots are allowed if the trader built them for personal use. News trading has no blackout.
- **Quotes from the official FAQ** (https://bulenox.com/faq, read from the page source, no date shown):
  - "Yes. Bots, algorithms and trade copiers are permitted. If you connect to Rithmic through a third-party API or composite software, an additional $100 per month applies. Only user-built tools intended solely for the account owner's personal use are permitted. Commercial, shared, rented or publicly distributed automation tools are not allowed."
  - News: "No blackout windows, no forced position closing". All positions must be closed by 3:59 pm CT.
- **Confidence:** CONFIRMED.
- **Open questions:**
  - The older Terms of Use (PDF dated July 2021) reportedly require management approval for third-party algorithms. SECONDARY / old.
  - Whether NinjaTrader on Rithmic triggers the $100 "composite software" fee: NOT FOUND, ask Bulenox.

### FundedNext Futures
- **Rule:** EAs and bots are allowed in the Challenge and in funded accounts. No setup support is given; latency abuse and order flooding are banned.
- **Quotes** (https://helpfutures.fundednext.com/en/articles/14298560-is-the-usage-of-automated-trading-systems-eas-and-bots-allowed-in-fundednext-futures, Apr 9, 2026):
  - "FundedNext Futures allows the use of automated trading systems, including Expert Advisors (EAs) and trading bots" in the Challenge and on FundedNext accounts.
  - No setup support is offered.
  - "strategies that aim to exploit system vulnerabilities—such as latency abuse or order flooding—are strictly prohibited."
- **Confidence:** CONFIRMED.
- **Note:** the forex FundedNext rules (an extra EA fee, no identical trades across accounts) are a separate help center and do not apply to Futures.

---

## Action items for NQMaster / GoldMaster

1. **MFFU NewsBlackout:** besides being flat, cancel resting entry orders 2 minutes before to 2 minutes after each T1 release:
   - FOMC decision
   - FOMC minutes
   - Employment Report (NFP)
   - CPI

   This applies to Rapid and Pro sim-funded accounts only; evaluations are exempt. Check that the current code does this.
2. **Hedging (Lucid and MFFU):** do not run settings on different accounts at the same firm that can hold opposite MNQ positions at the same time, such as eval Ultra on one account and funded WR70Plus on another. Lucid's rule names "separate accounts with correlated assets" explicitly.
3. **Combined size limits:** MFFU counts MNQ + MGC together toward 30 micros (50K). Lucid Flex funded 50K starts at 20 micros and 25K at 10 micros. Check MaxOpenContracts per preset.
4. **Ask MFFU in writing:** does the "all news releases ±2 min, no orders" Standard Protocol apply to every data release, or only to T1 releases on sim funded?
5. **Lucid costs:** MNQ $1.00 and MGC $1.60 round trip, below the research assumption of $1.90.
