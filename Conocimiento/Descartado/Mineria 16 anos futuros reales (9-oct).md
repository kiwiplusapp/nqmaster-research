# 16-year real-futures mining (2026-10-09)

Question: are there more Nasdaq strategies with a HIGH win rate AND a HIGH profit factor?
Data: Databento real NQ futures 2010-06 → 2026-10 (`research/data/nqdb.npz`), $ per MNQ with $1.90 + 1 tick per side.
Code: `research/mine/run_mine_db.py`, `families5.py`, `mine_db_select.py`, `mine_db_robust.py`, `orb0820_check.py`, `orfail_ext.py`.

Protocol (fixed before looking): chosen on 2020-23 only (≥ 100 trades, WR ≥ 60%, PF ≥ 1.4), then out of sample
2024-26 (PF ≥ 1.3, WR ≥ 58%), 2015-19 and 2010-14 with costs scaled to the daily range (PF ≥ 1.1 / ≥ 1.0).

| What | Result | Decision |
|---|---|---|
| 29 old families, 45,278 configs | 145 pass 2020-23; **0** pass everything | ❌ |
| 4 new families, 8,208 configs: daily setups (IBS, 2 closes, prior-day return), relative volume (RVOL), 5-min volume climax, failed opening-range breakout | family medians PF 0.91-1.02; DAY_MR 42 pass 2020-23 → median PF 0.75 in 2024-26 | ❌ |
| Looser (2020-26 only): 29 survive | 16 = 08:20 range breakout, 6 = VW13 (already in NQMaster), 3 = 4H engulfing (known), 1 night fade, 3 low-RVOL continuation (isolated cells, neighbours PF 0.6-1.6) | ❌ |
| 08:20-08:30 range breakout (70% WR, PF 1.6) | edge only in the 08:30 news minute; counting the news whipsaw days the sim skipped → PF 1.23-1.28; +4 ticks on news fills → ~1.07 | ❌ (news slippage) |
| 08:20 breakout, TICK-LEVEL backtest (every real NQ print, May 2025 - Oct 2026, `orb0820_ticks.py`) | 1-minute sim same period PF 1.46 / +$3,032; ticks: best case (fill at the triggering print) PF 1.09 / +$621; 50 ms PF 0.98 / -$150; 250 ms PF 0.96 / -$290; CPI/NFP days entry slippage 34 ticks average, p90 168 at 50 ms; MNQ prints (Sep 2025) same as NQ | ❌ confirmed |
| PF ≥ 1.2 in all 4 periods: 10 configs, WR 36-62% | 20:00→05:00 fade = NF05 (confirmed again); 09:30 drive 2R lowers Ultra's Sharpe 2020-23; 01:00 fade isolated | — |
| Failed 15-min OR breakout with the trend (OR_FAIL, breakout ≥ 0.10 ATR, 5-min close back inside) | WR ~70% at 0.5R (PF 1.11/1.32/1.11/1.21) or WR ~50% to the other side (PF 1.23/1.21/1.37/1.26); +0.07-0.10 Sharpe to Ultra in all 4 periods, correlation −0.02 to −0.07, ~$60/month per contract; BUT in 2024-26 only bk 0.10 works (0.15+ → PF 0.86-0.89); 10 of 168 extended variants hold | ⚠️ watch list, not added |

Conclusion: high win rate + high PF that holds across regimes is not in this data. Selecting the best of 2020-23 finds
strategies that still work in 2024-26 15% of the time (10x chance) but 0% that also worked in 2010-19: the Nasdaq intraday edges
are a post-2020 regime. Ultra already combines the best of them (portfolio WR ~65%, PF ~1.5).
