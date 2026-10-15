# NinjaTrader validation of NQMaster after the 2026-10-12 overhaul (2026-10-14)

Federico's Strategy Analyzer run: Profile Ultra, PropMode Off, Contracts 1, MNQ 1-minute, 2024-01-01 .. 2026-10-12, commission $1.90 per contract, slippage 1 tick. Files: `ultra_settings.csv`, `ultra_summary.csv`, `ultra_trades.csv`.

**NinjaTrader:**
- 3,072 trades (first trade 2024-01-22, after the warm-up), 4.5 per day, WR 65.5%, PF 1.52.
- Net $77,808 (longs $35.4k, shorts $42.4k), max drawdown $4,896, $2,385 per month.
- 28 of 34 months positive. Worst month 2024-09 -$2,459; Aug 2026 -$1,733.

| Year | Trades | Net | PF | WR |
|---|---|---|---|---|
| 2024 | 1,075 | $16,222 | 1.35 | 63.5% |
| 2025 | 1,127 | $27,932 | 1.52 | 67.3% |
| 2026 (to Oct 12) | 870 | $33,654 | 1.67 | 65.5% |

**Comparison with the research** (`research/mine/nt_compare.py ... --set ultra_r` = `cand16.py` UltraR on real Databento NQ, 2024-01-22 .. 2026-10-08): `compare_ultra_r.md`, `compare_ultra_r_mismatch.csv`.
- **Trades:** 2,882 of 3,109 research trades matched (92.7%).
- **$ per contract:** research $61,017, NinjaTrader $61,154. Daily correlation 0.967. With sizes: research $75.0k vs NT $77.8k (NT has 405 trades at 2 lots vs 326 in research).
- **Unmatched trades:**
  - VW13: 62 research-only, which are the 2nd lot that NT books as one trade with Qty 2.
  - VOLB: 43 / 23.
  - MSEQS: 12 research-only, mostly 13:50-15:15 ET, net about +$780. This is a small, known port difference that was also seen on 2026-10-09.
  - ICT / REV06 / ON07 / MOM13: about 20 each way, mostly holiday-window trades.
- **Verdict:** the overhauled code reproduces the research. Implementation risk is removed for the current Ultra.
