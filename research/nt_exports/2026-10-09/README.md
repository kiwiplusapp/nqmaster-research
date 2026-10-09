# NinjaTrader Strategy Analyzer check, 2026-10-09

Federico's NT8 backtests with default settings (current code with the 2026-10-08 rules; news blackout and step-up off), 1 contract,
real MNQ / MGC DEC26 1-minute, data from 2025-01-04, first trades 2025-01-27, last 2026-10-08.
Compared with `research/mine/nt_compare.py --set ultra_final` / `--set gold_robust` (research REAL ends 2026-09-25/28).

| | NT trades | NT WR / PF | NT net (comm + 1 tick) | Matched with research | $ on matched trades (research / NT) |
|---|---|---|---|---|---|
| NQMaster Ultra (MNQ) | 2,221 (842 shorts, $37.0k) | 65.8% / 1.56 | $63,656, max DD $4,605 | 1,936 of 2,023 (95.7%) | $51,504 / $51,497 |
| GoldMaster Robust (MGC) | 332 | 61.5% / 1.42 | $11,782, max DD $1,753 | 320 of 321 (99.7%) | $12,195 / $12,116 |

Unmatched NQ trades, explained:
- 29 of 87 research-only are the VW13 second lot (NT books one trade with Qty 2, research two trades).
- 182 of 234 NT-only trades fall in the ~20 trading days after holidays (Jul 4 2025, Labor Day 2025, MLK / Presidents' Day 2026,
  Good Friday 2026) where the research data turns the trend filter off; NT keeps trading (+$1,149). Research artifact, not NT.
- VOLB 30 research-only (+$390) vs 12 NT-only (+$592); MSEQS 12 vs 8 trades. Small, no blocked direction.
Verdict: the NinjaTrader port matches the research. Implementation risk removed for these settings.
