# Prop firm research notes (2026-10-08)

## LUCID (official help center support.lucidtrading.com; site lucidtrading.com 403 to fetch)
- Flex eval (art 12945790, 2026-08-31): 25/50/100/150K target 1250/3000/6000/9000; MLL EOD 1000/2000/3000/4500; consistency 50%; max 2/4/6/10 minis (20/40/60/100 micros); no time limit; DLL optional at checkout (Customization art 16226050, 2026-08-06; DLL on = cheaper; off = pricier; amounts per plan card 600/1200/1800/2700).
- Flex funded (12945795, 2026-08-15): EOD trailing, DLL optional (same choice as eval), no consistency, no buffer, 90/10, scaling plan yes.
- Flex payouts (12945796, 2026-07-28): min $500, 5 profitable days per cycle >= 100/150/200/250, net cycle profit >0, max 50% of profit up to 1000/2000/2500/3000 (not increasing), up to 5 payouts then live review; request any day. MLL resets to lock (initial+100) on request (tradetanto).
- Flex scaling (tradetanto 2026-09-10): 50K 0-999 -> 2 minis/20 micros; 1000-1999 -> 30; 2000+ -> 40. 150K: 0-999 40 micros, 1000-1999 50, 2000-2999 60, 3000-4499 80, 4500+ 100.
- Pro eval: same targets/MLL, NO consistency, DLL optional 600/1200/1800/2700 (soft). Pro funded (12890069, 2026-08-26): same MLL, fixed DLL optional or scaling DLL 60% of peak EOD; no scaling plan (full size). Pro payouts (12890092, 2026-08-06): 40% consistency per cycle, buffer = initial MLL+100 (52,100 on 50K), min req 500, max payout 1: 1000/2000/2500/3000, 2+: 1500/2500/3000/3500; min profit per cycle 250/500/750/1000; tradetanto min 3 days.
- NEW LucidDaily (launched July 2026): eval target same, MLL same, 50% consistency, EOD or intraday eval DD (choice), DLL on/off 600/1200/1800/2700 soft carries to funded. FUNDED: ALWAYS INTRADAY trailing (incl unrealized), trails until initial trail bal (52,100 on 50K) then locks at 50,100; NO consistency; payout any day of all profit above buffer (52,100), min $500, 90/10, no cap; max daily sim profit 6k/8k/10k/12k -> moves live; NO trading of US red-folder news (flat +-1 min, HARD breach). Live: $0 start, EOD DD 2000 (50K), no DLL, daily payouts, sim profit above buffer payout capped $15k total. Articles 15996664, 15997244, 15997266, 15998336, 15998425, 16085900, 16033858, 16010520 (dated 2026-07-27..08-19).
- Prices (proea.app re-verified 2026-10-08; list): Pro 123/192/307/410; Flex 89/146/293/407; Daily EOD 118/166/267/375; Daily intraday 104/138/224/313; Direct 329/515/700/836. Coupons change (e.g. VAULT LucidDaily 50K intraday DLL-on $75.60 propkoala 2026-10-02). No activation fee.
- Cross plan: flat by 4:45 PM ET; news allowed except LucidDaily funded; bots & copiers allowed; HFT prohibited; microscalping flag >50% profit from <=5s trades; hedging prohibited; max 5 funded + 10 evals (10 combined) per household; inactivity 30 d.

## APEX (official site 403; tradetanto 2026-04-22, proptradingvibes 2026-08-10, prop-memo 2026-09-21)
- 4.0 since 2026-03-01: EOD or Intraday trailing; target 1500/3000/6000/9000; DD 1000/2000/3000/4000; EOD DLL 500/1000/1500/2000 (intraday none); contracts 4/6/8/12 (minis); 30-day access; no min days; no eval consistency. List prices (ptv 08-10) EOD 390/490/790/1490, intraday 167/249/399/599 (always heavy coupons ~80-90%). PA activation ~ $79-159 (sources conflict). PA: safety net 26,100/52,100/103,100/154,100; min request bal +500; 5 qualifying days >= EOD 100/250/300/350 (intraday 100/200/250/300); 50% consistency; min $500; 6 payouts max; 50K caps EOD 1500/1500/2000/2500/2500/3000, intraday 1500/2000/2500/2500/3000/3000; 100% split; 20 PAs; mandatory brackets; flat 4:59 PM ET; PA scaling 50K 2 contracts until +1500 etc.
- AUTOMATION: official help center Prohibited Activities "No Automation or Algorithm Usage allowed" (prop-memo tier D, all accounts). PA compliance article bans fully automated/hands-off. -> NOT USABLE for NQMaster bot.

## TOPSTEP (help.topstep.com)
- Combine: 50K/100K/150K target 3000/6000/9000, MLL EOD trailing 2000/3000/4500 (locks at start bal), consistency target best day < 55%? of target (Combine params art 8284197: 'best day below 55% of profit target' -- actually 50% older), max 5/10/15 minis; min 2 days; TopstepX ONLY for new Combines since 2025-07-07 (NinjaTrader legacy only). Automation only via TopstepX/ProjectX API; VPS/VPN banned; not on Live.
- XFA (art 8284215, 2026-08-05): $0 start, MLL trailing EOD; payout paths Standard (5 winning days >=150; 50% of balance up to cap) / Consistency (3 days, best day <=40%); caps 50K 2000/3000, 100K 3000/4000, 150K 5000/6000 (with DLL added at Combine purchase since 2026-06-02 caps double: 4000/6000, 6000/8000, 10000/12000); 90/10 (post 2026-01-12); after payout MLL resets to $0; max 5 XFAs; Back2Funded 2 reactivations; DLL optional. Fees $30 ACH/wire. Price 50K ~$49/mo (monthly subscription) + activation $149 or No-Activation-Fee combine.

## TRADEIFY (help.tradeify.co 403; tradetanto 2026-09-30; ptv 2026-09-07; official pricing art 14369021)
- Select eval: target 1500/3000/6000/9000; EOD DD 1000/2000/3000/4500; no DLL; 40% consistency (50% add-on); min 3 days (2 w add-on); 1/4/8/12 minis. Price 25K 109, 50K 165, 100K 265, 150K 369 one-time (coupons ~40%).
- Select Flex funded: EOD DD same, lock at start+100 when EOD bal > start+DD+100 or on payout; no DLL; no consistency; 5 winning days >= 100/150/200/250; 50% of profit up to cap 1250/2500/3500/4500 (post 2026-09-01; before 1250/3000/4000/5000); min 250; scaling 50K starts 2 minis/20 micros.
- Select Daily funded: DD 1000/2000/2500/3500; DLL 500/1000/1250/1750; buffer 1100/2100/2600/3600; daily; up to 2x profit since last payout; cap 600/1250/1750/2500 (post 09-01).
- Growth eval: DD 1000/2000/3500/5000 EOD, soft DLL 600/1250/2500/3750, no consistency, 1 day. Funded 35% consistency, min bal 26.5/53/104.5/156.5K, 5 days, caps 50K 1500/2000/2500/3000.
- 90/10 sim; Elite Live 80/20 after 3 payouts on one acct or 10 total; 5 funded per household; flat 4:45 PM ET.
- AUTOMATION (official 'Guidelines for traders' art 10468318): bots allowed if SOLE OWNER, not shared, 'using it across multiple firms is against policy', not HFT; may require live video; funded >50% trades & profit from trades >10s.

## MFFU (help.myfundedfutures.com)
- Rapid EOD 50K (art 16158363, 2026-08-24; launched Aug 2026, $157 one-time): target 3000, EOD MLL 2000, no DLL, 30% eval consistency, min 4 days, 3 minis/30 micros. Funded: $0 start, EOD trailing 2000 locks at $100, no DLL, no consistency, payouts daily after $2,100 realized buffer, later each $500 net, min 500, NO CAP, 90/10; max 3 funded; T1 news (FOMC, minutes, NFP, CPI) prohibited +-2 min in funded. Also 25K version.
- Rapid (intraday funded) 50K (art 13134709): eval EOD 2000, 50% consistency, 2 days, 5 minis; funded INTRADAY trailing 2000 locks at 100, no consistency, daily, buffer 2100, min 500, 90/10. Live auto at $10k single-day profit (excess forfeited). Max sim funded 5 (25/50K only) or 3 if any 100/150K.
- Builder 50K (art 14290805): $153 list ($107/$92 w coupons), target 3000, EOD 2000 (or 1500 add-on), DLL 1000 soft, NO eval consistency, 1 day, 4 minis/40 micros; funded EOD 2000, DLL 1000, 50% cycle consistency, buffer 2100, cap 2000/cycle, 5 payouts then live, 2 days/cycle, 80/20; only 1 Builder funded per user.
- Pro: 80/20, every 14 days, 50% eval consistency.
- Automation (Fair Play art 8444599, 2026-08-24): automated strategies tailored to own settings allowed; no exploiting sim fills; HFT banned; no copy between traders. Flat 4:10 PM ET. Inactivity 7 days. One-time eval pricing since 2026-08-25.

## LUCID extra
- Pro eval (12890029, 2026-08-26): DLL 0/1200/1800/2700 (DLL optional per customization 16226068 2026-08-06; DLL-off costs more), no consistency.
- Flex drawdown (12945815, 2026-08-26): EOD both phases; trails to initial trail bal (52,100) then locks 50,100; on payout request MLL -> locked balance (50,100).
- Flex scaling (12945808, 2026-05-06): 50K: profit 0-999 20 micros, 1000-1999 30, 2000+ 40; payouts lower profit -> lower tier.
- Other trading activities (11404728, 2026-08-26): automated systems and copiers permitted; news allowed except LucidDaily (hard breach).
- New Live Structure (16558826): when moved live ALL sim accounts close; funded accts with 0 payouts refunded eval cost; live $0 start, EOD DD 2000 (50K), lock $100 when live profit = DD or on payout; bonus after live target 4000 (50K) + 20 days; daily payouts; no consistency, no DLL; 2-week cooldown after blowing.

## FUNDEDNEXT FUTURES (helpfutures.fundednext.com, articles modified 2026-09-30)
- Bolt + old Rapid discontinued 2026-07-10; new Rapid Pro / Rapid Daily.
- Rapid Pro eval (17229677): 25/50/100K price 79.99/149.99/249.99 (50% off of 159.98/299.98/499.98); target 1500/3000/5000; MLL EOD 1000/2000/2500, locks 25,100/50,100/100,100; DLL none (add-on 500/1000/1250); NO consistency; no min days; no time limit; 2/4/6 minis (20/40/60 micros); microscalping hold at 40%.
- Rapid Pro funded (17229713): EOD MLL same, lock same; 40% consistency; min cycle profit 500; min withdrawal 250; max per cycle 800/1200/2500; every 3 days; no buffer; 90/10; account concludes after 5th reward.
- Rapid Daily eval (17229762): same prices/targets, DLL 500/1000/1250, no consistency. Funded (17229779): EOD MLL, DLL, NO consistency, buffer 26,100/52,100/102,600, daily payouts, min cycle profit 500, max 800/1200/2500 per cycle, 90/10, concludes after 5 rewards.
- Flex (fundednext.com/futures): 50K target 2500, DD 1500 EOD, 40% eval consistency, funded none, 5 benchmark days >=200, 50% up to 1500, 80% (90 add-on)... price 50K $69.99 promo.
- Automation (14298560, 2026-04-09): EAs/bots allowed in challenge and funded; no latency abuse/order flooding; HFT banned; copy only own accounts. News unrestricted. Flat by 3:10 PM CT. Max 5 FundedNext accounts / $700k. Live at $100k total profits.

## BULENOX (tradetanto 2026-09-25, ptv 2026-08-25; official 403)
- Qualification (legacy) one-time since 2026-08-17 (no subscription): 50K list $175 (promos to $43), activation $143/148/248/498 (25/50/100/150K); target 1500/3000/6000/9000; Option 1 intraday trailing DD 1500/2500/3000/4500 no DLL; Option 2 EOD same DD + DLL 500/1100/2200/3300 + scaling (50K 2->7 minis); no eval consistency.
- Master: DD same, lock at start+100 when bal hits 26.6/52.6/103.1/154.6K; DLL removed at lock (Opt 2); 40% consistency (best day/total over account life) at payout; >=10 trading days per payout; min $1,000; caps payout 1-3: 1000/1500/1750/2000 then none; weekly (Wed); 100% first $10k then 90/10; reserve must remain; max 5 masters; after 3 payouts discretionary consolidation into 1 funded (cap $30k).
- Fast Track (no eval, $488 50K) and Momentum ($143 50K; DD 2250, 35% consistency, caps 1500/2000/2500/3000, DLL for life).
- Automation: allowed only if built by you, own accounts; no shared/commercial tools; third-party API $100/mo. News allowed. Flat 3:59 PM CT.

## FTMO FUTURES (tradetanto 2026-09-17; beta since late Aug 2026; no payout history)
- Pro: target 3000/6000/9000; EOD trailing DD 3000/4500/6000 lock at start; HARD DLL 1000/1500/2000 eval and funded; eval consistency 50%; funded none; 5 qualifying days >= 200/300/500; cap 5000/6000/8000; 100% of profit withdrawable; 90/10; $139/mo (50K).
- Growth: DD 2000/3500/5000; no eval DLL, soft funded DLL 1000/2000/3000; 40% eval consistency; 4 days >= 150/250/300; 50% of profit up to 2500/3000/4000; $119/mo.
- Funded contracts start 2 minis (50K). Max 3 sim-funded. Automation allowed (no HFT/latency arb). Flat 4:10 PM ET.

## EXCLUDED / restricted for bots
- Apex: 'No Automation or Algorithm Usage allowed' (help center), tier D.
- Take Profit Trader: 'No Trading Bots or Algos' all stages.
- Alpha Futures: semi-auto only + NinjaTrader partnership ended 2026-07-12.
- Phidias: bots/fully automated banned (semi-auto supervised only).
- Elite Trader Funding: banned without written approval; 10 s min hold.
- Earn2Trade: no written policy; copiers banned; 30% eval consistency; 50K Gauntlet Mini target 3000 DD 2000 DLL 1100.
- TradeDay: self-built OK but VPS banned; Quick Pay funded intraday DD, 50/50 split < $4k; Fast Pass 45% consistency eval & funded, cap 1500/cycle (50K), 80/20; 50K EOD $70/mo (QP) / $95/mo (FP).
- Topstep: TopstepX ONLY for new Combines (NinjaTrader closed to new users 2025-07-07); automation only via ProjectX API; no VPS. Combine 55% best-day consistency; XFA caps 50K 2000/3000 (or 4000/6000 w DLL), 90/10, MLL resets to $0 after payout; call-up to Live closes all XFAs; LFA 20% tradable/80% reserve.
- Tradeify: same bot cannot be used across multiple firms (official guidelines art 10468318).

## Reputation (propfirmmap payout ranking ~2026-10): Topstep #4 (93, TP 3.6), ETF #11, MFFU #18 (85.5, TP 4.9/22k), Lucid #24 (85, TP 4.4/6.4k), TradeDay #30, Tradeify #36, TPT #35, Alpha #50, Bulenox #54 (80.5), Earn2Trade #57, FTMO #83, FundedNext #122 (69.5), Apex #129 (68).

## MFFU payout policy (art 13745661, 2026-08-25): Rapid (intraday & EOD) buffer 2100/3100/4600 (50/100/150K), min 500 after clearing buffer, no max stated, daily, 90/10; live: auto at $10k single-day net profit or risk-team discretion after consistent payouts. Pro: 14 days, 80/20, min 1000. Builder: cap 2000 (50K), 80/20, live after 5 payouts.
## Bulenox live: 3 payouts -> discretionary review; consolidation, $30k total transition cap (ptv 2026-08-25); declining offer can forfeit balance (reviews).
## Lucid live: moving live closes ALL sim accounts (art 16558826). Topstep call-up closes all XFAs. MFFU: live+sim can't be traded simultaneously, Rapid accounts merged into one live.

## TOY MODEL (iid t5 daily, mu 125 sd 500 per contract, bridge intraday extremes; NOT the real sim)
Eval pass 1c (<=22d / <=30d / <=44d / ever / median d):
 LucidFlex50 53/65/73/75/17; LucidPro50 DLLoff 53/64/72/73/16; LucidDaily intraday-eval 48/59/64/65; MFFU RapidEOD50 37/51/64/73/23; MFFU Builder50 55/68/75/77; FN RapidPro50 53/65/72/74; Bulenox Opt2 50 56/70/81/85/18; Tradeify Select50 47/60/70/73; FTMO Pro50 (hard DLL) 45/53/58/59; FTMO Growth50 46/60/69/73; Topstep50 52/64/71/73; Apex EOD50 53/67/75/76; Apex intraday50 50/61/66/67; LucidFlex100 9/22/48/85/41; LucidPro150 0/3/17/93/65.
Eval pass 2c: Flex50 52/53 (med 8); Pro50 54; MFFU RapidEOD 33/40/45/48 (16 d); Bulenox Opt2 62/63 (7 d); FTMO Pro 20; Apex intraday 35; LucidDaily intraday eval 32.
Lifecycle $/mo per 50K slot (12 mo, list fees, best payout policy), 1c: LucidFlex 1174 (busts 1.45/y); LucidPro 1135; LucidDaily (withdraw above 54,100) 1665; MFFU Rapid EOD (keep +2000 extra cushion) 1603 (busts 0.72/y); Bulenox uncapped-after-3 1792 / if account ends after 3 payouts 650-780; FundedNext RapidPro 639; Tradeify Select Flex 1651.
 2c: Flex 1641 (4.7 busts/y); Pro 1410; LucidDaily 2529 (6.3 busts/y); MFFU RapidEOD 2408 (3.5); Bulenox 3595 / 718-938 if ends after 3; FN 699; Tradeify 2883.
