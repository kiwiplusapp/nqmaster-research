# Futures prop firms for an automated NinjaTrader 8 bot (survey 2026-10-21)

Scope: NQMaster (fully automated NT8 strategy, MNQ 1-minute, ~5 trades/day, entries 04:00-15:30 ET, flat by 15:55 ET, no overnight or weekend holds).
Requirements: (a) automation allowed in BOTH evaluation and funded, (b) NinjaTrader 8 via Rithmic / Tradovate / NT brokerage, (c) a ~50K plan.
Machine-readable rules: `propfirms_2026-10-21.json`. Scores: `prop_survey_sim.json` (`prop_survey_sim.py`), ranking in `prop_survey_report.md`.

Sources and confidence:
- **P** = read on the firm's own help center / FAQ page (date = date printed on the page).
- **Px** = firm's own page known only through a quote (search excerpt or the prop-memo.com survey of official pages, 2026-09-21/22; page returns 403 to fetch).
- **S** = third-party only (tradetanto, proptradingvibes, proea.app, propfirmmap, damnpropfirms, traderspost...). **UNVERIFIED** where stated.
- Earlier primary reads: `propfirms_2026.md` (2026-10-08) and `propfirms_check_2026-10-16.md` (2026-10-16). Nothing below was re-purchased or tested with a live account.

## 1. Automation verdict per firm

| Firm | Verdict for NQMaster | Clause (exact wording) | URL | Page date / conf. |
|---|---|---|---|---|
| Lucid Trading | **ALLOWED** (no own-code clause; HFT banned; microscalping flag >50% of profit from trades <=5 s; hedging across own accounts banned) | "Automated trading systems and trade copiers are permitted" / "Traders are fully responsible for any software errors, malfunctions, or unintended outcomes" | https://support.lucidtrading.com/en/articles/11404728-other-trading-activities | 2026-08-26, P |
| MyFundedFutures (MFFU) | **ALLOWED** (own settings; no sim-fill exploitation; HFT banned; no copy between traders) | "Traders may make use of automated trading strategies tailored to their own specific settings so long as these automated tools do not aim to exploit the favorable fills offered in the Simulated Environment." | https://help.myfundedfutures.com/en/articles/8444599-fair-play-and-prohibited-trading-practices | 2026-08-24, P |
| Bulenox | **ALLOWED, own-built only** (NQMaster is own code) ; Rithmic only; "$100 per month" for third-party API/composite software (ask whether NT8 triggers it) | "Bots, algorithms and trade copiers are permitted. ... Only user-built tools intended solely for the account owner's personal use are permitted. Commercial, shared, rented or publicly distributed automation tools are not allowed." | https://bulenox.com/faq | no date (read 2026-10-16), P |
| FundedNext Futures | **ALLOWED** (no latency abuse / order flooding; may ask to disclose the system) | "FundedNext Futures allows the use of automated trading systems, including Expert Advisors (EAs) and trading bots" | https://helpfutures.fundednext.com/en/articles/14298560 | 2026-04-09, P |
| FTMO Futures | **ALLOWED** (own strategy; third-party EA risks refusal; API order-rate limit; VPS/VPN allowed) | "we have no reasons for limiting or restricting your trading strategy, whether it's discretionary trading, algorithmic trading or EAs" | https://ftmo.com/en/futures/faq/ftr-which-instruments-can-i-trade-and-what-strategies-am-i-allowed-to-use/ | modified 2026-09-12, P (read today) |
| Tradeify | **ALLOWED with conditions -> NOT usable in parallel**: sole owner, may require live video, and the same bot may not be used at another firm | "You must be able to prove that you are the sole owner of the bot or strategy" ; "using it across multiple firms is against policy" | https://help.tradeify.co/en/articles/10468318-guidelines-for-traders | Px (403) |
| TradeDay | **ALLOWED for self-built (implicit)**; VPS banned; >200 trades/day = HFT; identical trades across users = all closed | "Algos and Bots purchased from a third party and employed by the trader are forbidden." | https://tradeday.freshdesk.com/en/support/solutions/articles/103000085101 | 2025-11-28, P (read today) |
| The Trading Pit (Futures Prime) | **ALLOWED (own EA)**; NinjaTrader support UNVERIFIED (Quantower/Rithmic primary) | "Yes, we allow you to trade using your own Expert Advisor (EA)" | https://support.thetradingpit.com/can-i-use-an-expert-advisor-0-0 | Px (prop-memo 2026-09-21) |
| Funded Futures Network | discretionary; 2022 Terms of Use ban bots; Onyx platform -> **excluded** | "Automated trading is allowed but at the discretion of FFN." | https://fundedfuturesnetwork.zendesk.com/hc/en-us/articles/47493608444059 | Px (403) |
| BluSky | **unclear** -> excluded until confirmed in writing (page only bans automation "to unfairly influence outcomes"; vendor blogs say bots OK) | "using automated software (AI, ultra-high speed, bulk data entry) to unfairly influence outcomes" | https://help.blusky.pro/en/articles/12069208 | 2026-02-23, P (read today) |
| Apex Trader Funding | **BANNED** (all account types; 'since 4.0 / 2026-03-01' only secondary) | "No Automation or Algorithm Usage allowed" ; "the use of automation is strictly prohibited on all account types" | https://apextraderfunding.com/help-center/getting-started/prohibited-activities/ | Px |
| Topstep | **No NinjaTrader**: TopstepX only; bots only via ProjectX API, personal device, not on Live | "TopstepX(TM) is the only available trading platform" | https://help.topstep.com/en/articles/8284199-new-to-topstep-start-here | 2026-07-20, P |
| Take Profit Trader | BANNED | "Automated trading systems, bots, or algorithmic execution tools are not permitted." | https://support.takeprofittrader.com/hc/en-us/articles/34431153546397 | Px |
| Alpha Futures | BANNED (+ NinjaTrader partnership ended 2026-07-12) | "The use of AI, bots, and other automated trading mechanisms is strictly prohibited across all account types." | https://help.alpha-futures.com/en/articles/9508585 | Px |
| Phidias | semi-auto only (damnpropfirms Oct-2026 says fully automated OK: conflict, trust the rules page) | "Only semi-automated software is permitted, provided the trader actively monitors and manually adjusts all trades." | https://phidiaspropfirm.com/rules | Px |
| Elite Trader Funding | BANNED unless written approval; VPS/VPN banned; 10 s min hold | "expressly authorized in writing by ETF" | https://elitetraderfunding.app/terms-of-service | Px |
| Top One Futures | BANNED (NT ATM brackets only) | "we do not allow the use of Expert Advisors (EAs) or Bots on our accounts." | https://help.toponefutures.com/en/articles/10907920 | Px |
| Leeloo Trading | BANNED | "If a system is trading for you, it's not allowed." | https://support.leelootrading.com/kb/a205/is-dca-or-algo-trading-allowed-at-leeloo.aspx | Px |
| Earn2Trade | no written bot policy; copiers banned; "software/AI/ultra-high-speed input to gain an unfair advantage" prohibited -> excluded | (see left) | https://help.earn2trade.com/en/articles/9286647 | Px |
| DayTraders.com | manual trading required; NinjaTrader not supported | heading "Manual Trading Required" | (not linked) | Px |
| UProfit | unclear; TradingView/Tradoverse only; VPS/VPN = closure | "automated software intended to manipulate outcomes" | https://uprofit.com/help/trading-best-practices-important-information-38280308499604 | Px |
| The5ers Futures / E8 Futures | BANNED | "No. These practices are strictly forbidden." / "Semi-Automated or Fully-Automated Trading" (prohibited) | https://www.the5ers.com/futures/ , https://helpfutures.e8markets.com/en/articles/10209270 | Px |
| YRM Prop | approval required; stopped selling new accounts mid-Sep 2026 | "Automated trading is restricted unless explicitly approved." | https://intercom.help/yrmprop/en/articles/11100376 | Px |
| New 2026 entrants seen | IQ Capital (listed as algo-friendly by damnpropfirms Oct 2026, no rules found), Aqua Futures (semi-auto only), TickTick Trader (banned per third parties) | - | - | S |

Conclusion: usable today with NT8 automation = **Lucid, MFFU, Bulenox, FundedNext, FTMO Futures**, plus **TradeDay** (no VPS) and **The Trading Pit** (NT8 unverified). **Tradeify** is allowed but its cross-firm clause forbids running the same bot elsewhere.

## 2. 50K plans (one row per plan)

Columns: price = typical price per eval (list in brackets), DD = drawdown amount/type (lock), DLL, eval consistency, min days, max micros; funded = buffer / consistency / min days / cap per payout / frequency / split / payouts before live or closure. All drawdowns lock at start + $100 (or start) once the peak reaches DD + $100 unless noted.

| Plan | Price (list) / reset / activation | Target | DD (type) | DLL | Eval consistency | Min days | Max micros | Funded rules | News / hours | Accounts | Conf. |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Lucid Flex 50K | ~$146 list (coupons vary) / reset ~= price / $0 | 3,000 | 2,000 EOD | optional (off) | 50% | none | 40 (funded 20->30->40 by profit) | no buffer; no consistency; 5 days >= $150 per cycle; 50% of profit up to $2,000; min $500; MLL locks at payout; 90/10; 5 payouts then live review | news OK; flat 16:45 ET | 5 funded / 10 total | P (help center Aug 2026); price S |
| Lucid Pro 50K | $115.40 coupon (Federico screenshot 2026-10-20), $192 list / reset $115 / $0 | 3,000 | 2,000 EOD | optional 1,200 soft (OFF costs more) | **none** | none | 40 | buffer 2,100; 40% consistency per cycle; min cycle profit 500; min 3 days (S); caps 2,000 first then 2,500; min $500; 90/10; 5 payouts | news OK; 16:45 ET | 5/10 | P |
| LucidDaily 50K | $166 EOD-eval / $138 intraday-eval list | 3,000 | 2,000 EOD or intraday (eval) | optional soft | 50% | none | 40 | **intraday trailing** (incl. unrealized) to 52,100 then lock 50,100; no consistency; payout any day above 52,100, min 500, no cap; max daily sim profit 6k -> live | **red-folder news = hard breach (funded)**; 16:45 | 5/10 | P (Jul-Aug 2026) |
| LucidDirect 50K | ~$515 list (no eval) | - | 2,000 | - | 20% per cycle (house note 2026-10-07) | - | - | not scored (no eval) | - | - | S |
| MFFU Rapid EOD 50K | $157 one-time / $0 | 3,000 | 2,000 EOD | none | 30% | 4 | 30 (MNQ+MGC combined) | $0 start, EOD 2,000 lock +100; buffer 2,100 realized, then every $500 net; daily; **no cap**; min 500; 90/10; live at $10k single day or discretion | T1 news (FOMC, minutes, NFP, CPI) no positions OR orders +-2 min in funded; auto-flat 16:10 ET | 10 evals, 3 Rapid EOD 50K funded | P (art 16158363, 2026-08-24) |
| MFFU Rapid 50K (intraday funded) | ~$157 (UNVERIFIED) | 3,000 | 2,000 EOD (eval) | none | 50% | 2 | 50 | funded **intraday** trailing 2,000 lock +100; buffer 2,100; daily; no cap; 90/10 | as above | 5 funded | P (art 13134709) |
| MFFU Builder 50K | $107 coupon ($153 list) / $0 | 3,000 | 2,000 EOD (1,500 add-on) | 1,000 soft | **none** | 1 | 40 | EOD 2,000, DLL 1,000; 50% cycle consistency; buffer 2,100; cap 2,000/cycle; 2 days/cycle; 80/20; 5 payouts then live | news allowed (Builder) | **1 Builder 50K per user** | P (art 14290805) |
| Bulenox Opt1 50K | ~$90 typical promo ($175 list) + **$148 activation** | 3,000 | **2,500 intraday** trailing | none | **none** | none (S) | 50 (S) | Master: lock at 52,600; 40% consistency (best day / total, account life); >= 10 trading days per payout; min $1,000; caps ~1,500 for payouts 1-3 then uncapped (S, size mapping unclear); weekly (Wed); 100% of first $10k then 90/10; after 3 payouts discretionary consolidation to live ($30k transition cap, S) | no news blackout; flat 15:59 CT | 5 masters | automation P; plan rules S (tradetanto 2026-09-25) |
| Bulenox Opt2 50K | same as Opt1 | 3,000 | 2,500 EOD | 1,100 (soft assumed, UNVERIFIED) + scaling | none | none | 20->70 scaling (S) | as Opt1; DLL removed at lock | same | 5 | S |
| FundedNext Rapid Pro 50K | $149.99 (50% off $299.98) / $0 | 3,000 | 2,000 EOD lock 50,100 | none (add-on) | **none** | none | 40 | no buffer; 40% consistency; min cycle profit 500; min withdrawal 250; **cap $1,200 per reward**; every 3 days; 90/10; **account concluded after 5 rewards** | news unrestricted; flat 15:10 CT | 5 accounts / $700k | P (arts 17229677/17229713, 2026-09-30) |
| FundedNext Rapid Daily 50K | $149.99 | 3,000 | 2,000 EOD | 1,000 (soft assumed) | none | none | 40 | buffer 52,100; no consistency; daily; min cycle 500; cap 1,200; 5 rewards then concluded | same | same | P |
| FundedNext Flex 50K | ~$71 promo ($134 list) | 2,500 | 1,500 EOD | none | 40% | none | ? | no consistency; 5 days >= 200; 50% up to 1,500; 80/20 | same | same | S (fundednext.com notes 2026-10-08, damnpropfirms) |
| Tradeify Select 50K | ~$116 coupon ($165 list) | 3,000 | 2,000 EOD | none | 40% | 3 | 40 | Select Flex: no DLL, no consistency, 5 days >= 150, 50% up to 2,500, lock at payout, 90/10 | news OK; flat 16:45 ET | 5 funded | S; **bot clause excludes it if NQMaster runs at another firm** |
| Tradeify Growth 50K | price UNVERIFIED (~$116 assumed) | 3,000 | 2,000 EOD | 1,250 soft | none | 1 | 40 | 35% consistency; min balance 53,000; 5 days; caps 1,500/2,000/2,500/3,000 | same | 5 | S |
| FTMO Futures Growth 50K | **$119 / month** | 3,000 | 2,000 EOD (locks at start) | none (funded 1,000 soft) | 40% | ? | 50 (funded 20->50) | no consistency; 4-5 days >= $150-200 (mapping unclear); 50% of profit, cap 2,500; every 4 days; 90/10 | news OK; close by 16:10 ET (S) | 3 sim-funded | P (objectives page 2026-09; program mapping partly inferred) |
| FTMO Futures Pro 50K | **$139 / month** | 3,000 | **3,000 EOD** | **1,000 HARD** (eval + funded) | 50% | ? | 50 | 100% of profit withdrawable, cap 5,000; 5 days >= 200 (?); 90/10 | same | 3 | P (same caveat) |
| TradeDay Fast Pass 50K | $95 / month (S) | 3,000 | 2,000 EOD | none | 45% | 3 (S) | ? | 45% consistency; cap 1,500/cycle; 80/20 (80% of first $50k) | VPS banned | ? | S (TradeDay 2.0, May 2026) |
| Trading Pit Prime 50K | ~$150 (UNVERIFIED) | 3,000 | 2,000 EOD | 1,000 daily pause (S) | 40% best day | 3 | 50 | split 70-80% (conflicting); payouts Fridays (S) | **30-day challenge window**; no weekend (some say no overnight) holds | copy up to 5 own accounts | S |

Other sizes (geometry per dollar; see house research 2026-10-13): Lucid Flex/Pro 25K (T 1,250 / D 1,000 EOD, 20 micros) reach the target about twice as fast per contract as 50K and cost ~$80-115; MFFU Rapid EOD 25K T 1,500 / D 1,000; FundedNext Rapid Pro 25K T 1,500 / D 1,000 at $79.99; Bulenox 25K T 1,500 / D 1,500 (D/T = 1.0, best ratio of any plan, S); FTMO Pro 100K T 6,000 / D 4,500 + hard DLL 1,500; Lucid 150K T 9,000 / D 4,500. Lucid 5-funded cap makes income per account the deciding metric there (150K wins on income, 25K on speed).

## 3. Rules that matter for NQMaster (operational)
- Hedging: Lucid and MFFU ban opposite positions across your own accounts -> one profile per firm.
- MFFU funded: no positions AND no resting orders +-2 min around FOMC / minutes / NFP / CPI (NewsBlackout must cancel entries); 30-micro cap counts MNQ + MGC together; auto-flat 16:10 ET.
- LucidDaily funded: red-folder news = hard breach (excluded for NQMaster unless NewsBlackout covers every red-folder release).
- Bulenox: Rithmic only (NT8 on Rithmic OK); the "$100/month third-party API or composite software" fee - ask whether NinjaTrader triggers it; 10 trading days per payout.
- FundedNext Rapid Pro/Daily: account is concluded after 5 rewards of max $1,200 (income ceiling ~$5.4k per account).
- FTMO Futures: monthly subscription; Pro has a HARD $1,000 daily loss (one bad day = account lost).
- TradeDay: no VPS (run on the home PC).
- Tradeify: same bot cannot run at another firm -> skip while NQMaster runs at Lucid/MFFU.
