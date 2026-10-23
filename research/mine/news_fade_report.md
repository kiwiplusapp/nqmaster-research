# Macro-release fade at the open (CPI09 on other releases) — 2026-10-19

Question: CPI09 (fade the 08:30→09:29 move at the 09:30 open on CPI days, x ≥ 0.05 ATR, stop 0.35 ATR fixed, 0.5R, hold 60) is one of the best
modules per trade. Does the same rule, or a close variant, work on the OTHER scheduled macro releases?

Files: `research/mine/news_fade.py` (run, ~1 min, 2 processes) → `news_fade.json`, `news_fade_cells.csv`; date lists `research/news_dates_<type>.csv`
built by `research/mine/news_dates_build.py` (sources in its docstring; fetched 2026-10-19). Data: real Databento NQ 1-minute 2010-06..2026-10 (`nqdb.npz`).

## Protocol (fixed before looking)

- Periods: A 2010-14 and B 2015-19 cost-normalised (0.345% ATR per round trip), T1 2020-23 and T2 2024-26 real $ per MNQ ($1.90 + 1 tick per side;
  stress = 4 ticks per side).
- Each release type is a separate hypothesis. One pre-registered pool: the exact CPI09 cell on all 08:30 monthly BLS/BEA/Census releases together
  (PPI + Retail + Durables + GDP + PCE, CPI days excluded).
- Grid per type (288 cells, `families_gold.gen_drive` on release days only): anchor = release minute, entry at the next "open" (09:30 for 08:30
  releases, 10:30 for 10:00, 14:30 for 14:00) when |move since the release| ≥ x ATR, x ∈ {0.03, 0.05, 0.1, 0.2}, fade or follow, fixed stop
  0.25/0.35/0.5 ATR, target 0.5/1/2R, hold 30/60/120 min (216 cells) + the early fade 1/5/15 min after the release (72 cells).
- Selection on T1: n ≥ 30, PF ≥ 1.3, WR ≥ 60. Survival: T2 PF ≥ 1.2, T2 stress ≥ 1.1, A ≥ 1.0, B ≥ 1.0, plateau (≥ half of the one-parameter
  neighbours with T1 PF ≥ 1.2 and T2 PF ≥ 1.0). The same cells on non-release days are the control (must NOT work there).
- Transplant: the exact CPI09 cell on each type = one test per type, the least-mined check.
- Portfolio: survivors added to the 2027 default (`nt_compare.research_set("ultra_d4")`, first-come conflict filter), Sharpe / maxDD / worst month
  T1 and T2, 21-day block bootstrap (1,000 draws) of the Sharpe gain.

## 1. Date lists and spike validation

Spike = range of the release-minute bar / day ATR, divided by the median of the same minute on non-release days of the same year; hit = ratio ≥ 2.
CPI and NFP (known-good lists) are the references. Lists with a hit rate < 50% were dropped.

| List | Time ET | Source | Dates in data | Hit rate (pre-2020 / 2020+) | Median ratio | Status |
|---|---|---|---|---|---|---|
| CPI (reference) | 08:30 | BLS archive (news_hist.py) | 193 | 0.87 (0.82 / 0.94) | 5.2 | ok |
| NFP (reference) | 08:30 | news.py | 193 | 0.90 (0.88 / 0.94) | 10.0 | ok |
| PPI | 08:30 | BLS news-release archive | 194 | 0.76 (0.66 / 0.90) | 3.4 | usable |
| RETAIL (advance retail sales) | 08:30 | Census MARTS PDFs 2009-19 + Census calendars 2020-26 | 188 | 0.84 (0.84 / 0.83) | 4.2 | usable |
| DURABLES (advance) | 08:30 | Census M3 PDFs 2009-19 + calendars 2020-26 | 180 | 0.63 (0.67 / 0.56) | 2.5 | usable |
| GDP (advance/second/third) | 08:30 | BEA archive 2009-17 + bea.gov/news/archive 2018-26 | 187 | 0.81 (0.81 / 0.80) | 3.7 | usable |
| PCE / Personal Income | 08:30 | BEA archive (same) | 187 | 0.56 (0.41 / 0.78) | 2.4 | usable (weak pre-2020; shares the day with GDP 3rd estimate since 2018) |
| CLAIMS (weekly) | 08:30 | rule: Thursday, Wednesday on holidays | 850 | 0.63 (0.59 / 0.68) | 2.6 | usable |
| FOMC minutes | 14:00 | FOMC decision + 21 days | 126 | 0.64 (0.69 / 0.57) | 2.6 | usable (already in the NewsBlackout list) |
| JOLTS | 10:00 | BLS archive | 196 | 0.20 | 1.2 | dropped: no 10:00 spike |
| ISM manufacturing | 10:00 | rule: 1st business day | 196 | 0.46 (0.42 / 0.52) | 1.9 | dropped (just below 0.5; a weak 10:00 reaction, not a wrong list) |
| ISM services | 10:00 | rule: 3rd business day | 193 | 0.31 | 1.7 | dropped |
| Conference Board confidence | 10:00 | rule: last Tuesday | 193 | 0.23 | 1.4 | dropped |
| Michigan prelim / final | 10:00 | rule: 2nd / 4th Friday | 195 / 192 | 0.15 / 0.18 | 1.2 | dropped (10:00 ET since 2013 only; before that 09:55 for subscribers) |
| Treasury auctions | 13:00 | — | — | — | — | not built: TreasuryDirect search API returns 400/500 and the `auctioned` endpoint caps at 250 records |

The 10:00 releases do not move NQ at the minute level the way 08:30 releases do (ratio 1.2-1.9 vs 2.4-5 for the 08:30 group), so the whole 10:00
family is out before any trading test. CSVs for the dropped lists are kept for the record.

## 2. Grid per release type (release days only; medians over the 288 cells)

| Type | T1 pass | of which fades | pass all | median PF A / B / T1 / T2 | control T1 / T2 | best T1 cell (n) → T2 PF |
|---|---|---|---|---|---|---|
| PPI | 18 | 14 | **2** | 1.23 / 0.93 / 0.96 / 0.88 | 0.91 / 0.98 | x0.2 fade 0.5R (13 trades) PF 6.6 → T2 n 8 |
| RETAIL | 1 | 0 | 0 | 1.07 / 0.92 / 0.92 / 0.80 | 0.91 / 0.98 | early fade 08:31 (17) 3.1 → 1.16 |
| DURABLES | 1 | 0 | 0 | 1.12 / 0.98 / 0.95 / 0.93 | 0.91 / 0.98 | follow 09:30 (16) 2.3 → 1.40, A 0.58 |
| GDP | 5 | 0 | 0 | 0.85 / 0.94 / 0.95 / 0.91 | 0.91 / 0.98 | fade 09:30 2R (23) 1.8 → 0.94 |
| PCE | 3 | 0 | 0 | 0.93 / 1.41 / 0.91 / 0.98 | 0.91 / 0.98 | follow x0.2 (10) 2.9 → n 9 |
| CLAIMS | 0 | 0 | 0 | 1.08 / 0.97 / 0.87 / 0.92 | 0.91 / 0.98 | fade 2R (44) 1.5 → 0.48 |
| FOMC minutes (14:30) | 0 | 0 | 0 | 0.97 / 0.82 / 1.09 / 1.16 | 0.94 / 0.92 | early fade 14:01 (12) 13.7 → n 4 |

Across all 7 usable types: 28 cells pass T1, and P(T2 PF ≥ 1.2 | T1 pass) = 10.7% vs a base rate of 20.9% — the T1 selection is anti-predictive,
i.e. the T1 winners are noise. Family medians by direction (release days): the 09:30 fade has T1/T2 median PF 1.44/1.01 on PPI, 0.86/1.49 on Retail,
0.75/0.68 Durables, 0.99/0.94 GDP, 0.83/0.99 PCE, 1.15/0.82 Claims; the early fade (08:31-08:45) is below 1 in T1 and T2 for every type; the
"follow" direction is below 1 almost everywhere. For comparison the same cells on non-release days: 09:30 fade 0.82/1.09.

### The two PPI "survivors"

`{x 0.03, fade at 09:30, stop 0.5 ATR, target 1R or 2R, hold 120}`: A 1.39/1.23, B 1.00/1.04, T1 n 40 WR 60.0 PF 1.93/1.88, T2 n 29 WR 58.6
PF 1.38/1.27 (stress 1.35/1.23). They pass the letter of the protocol but not its spirit:

- WR is exactly the 60.0 threshold and B is 1.00/1.04 (borderline on two of the five gates).
- The same cells on non-release days: T1 PF 0.90/0.93, **T2 PF 1.20/1.21** — in 2024-26 the generic 09:30 fade with a 0.5 ATR stop makes money on
  every day, so the T2 result on PPI days is not distinguishable from the plain 09:30 effect. In the x 0.03 neighbourhood the release-vs-control
  T2 gap is small (1.38 vs 1.20, 1.27 vs 1.21) while in T1 it is large (1.93 vs 0.90): the PPI-specific edge lives in 2020-23 only.
- By year (1R cell, real $ per MNQ, ~10 trades/yr): 2010-19 six of ten years negative, +$523 / +41 / +810 / +303 in 2020-23, −$543 / +781 / +790 in
  2024-26 — about $35-45/month at best.
- Portfolio (2027 default + PPI09 1R, conflict filter, 57 trades kept): T1 Sharpe 3.49 → 3.49, T2 4.07 → 4.04, T2 maxDD $3,586 → $4,402 (+23%),
  worst month −$2,182 → −$2,438; bootstrap ΔSharpe T1 p50 +0.01 [−0.10, +0.09] P(gain) 0.53, T2 −0.04 [−0.18, +0.12] P(gain) 0.37. The 2R cell is
  the same (T2 4.07 → 4.03). It fails the audit criterion (DD / worst month ≤ +5%) and adds no Sharpe.

## 3. Transplanted CPI09 cell (one test per type)

| Type | n A / B / T1 / T2 | PF A / B / T1 / T2 (T2 stress) | WR T1 / T2 | pass |
|---|---|---|---|---|
| CPI (reference) | 42 / 45 / 41 / 27 | 1.58 / 1.13 / 1.94 / 2.62 (2.55) | 78.0 / 81.5 | yes (known) |
| PPI | 39 / 38 / 36 / 29 | 1.68 / 0.80 / 1.51 / 0.74 (0.72) | 66.7 / 58.6 | no (T2) |
| RETAIL | 41 / 44 / 28 / 25 | 1.59 / 1.40 / 0.76 / 1.49 (1.44) | 53.6 / 68.0 | no (T1) |
| DURABLES | 41 / 36 / 26 / 24 | 1.01 / 0.85 / 0.51 / 0.48 | 50.0 / 50.0 | no |
| GDP | 39 / 41 / 34 / 22 | 1.16 / 0.61 / 0.63 / 0.76 | 55.9 / 59.1 | no |
| PCE | 31 / 37 / 34 / 22 | 0.99 / 1.77 / 0.77 / 0.78 | 58.8 / 63.6 | no |
| CLAIMS | 182 / 165 / 142 / 105 | 1.41 / 0.84 / 1.00 / 0.83 (0.81) | 62.0 / 61.9 | no |
| FOMC minutes (14:30) | 29 / 31 / 25 / 16 | 0.57 / 1.77 / 1.36 / 1.88 (1.81) | 68.0 / 75.0 | no (n < 30, A 0.57) |
| POOL 08:30 monthly (PPI+Retail+Durables+GDP+PCE, 414 dates) | 165 / 166 / 141 / 98 | 1.21 / 0.92 / 0.79 / 0.78 | 58.2 / 59.2 | no |
| control: all non-release days 08:30 anchor | 252 / 279 / 233 / 171 | 1.28 / 0.81 / 0.82 / 0.91 | 58.4 / 62.0 | — |
| control: non-release days 10:00 anchor (10:30 entry) | 328 / 342 / 301 / 207 | 0.85 / 0.88 / 0.77 / 0.81 | 51.2 / 53.6 | — |

The CPI09 rule does not transfer: on every other 08:30 release, and on the pre-registered pool, it behaves like the non-release control
(PF ~0.8, WR ~58-62%). CPI itself stays the only release where the 09:30 fade has PF ≥ 1.1 in all four periods and WR ~80%. Retail (T2 1.49) and
FOMC minutes (T1/T2 1.36/1.88) each win one or two periods and lose the others — the usual single-period noise for 20-40 trades.

## 4. Verdict

- **Nothing survives.** No release type other than CPI gives a 09:30 (or 10:30 / 14:30) fade or follow rule that holds 2010-14, 2015-19, 2020-23
  and 2024-26; the two PPI cells that pass the mechanical gates are borderline (WR 60.0, B 1.00), indistinguishable from the generic 09:30 fade in
  2024-26, and lower the 2027 default's T2 Sharpe while raising its drawdown by 23%. The pooled 08:30 test fails, the early fade fails everywhere,
  and the 10:00 releases do not even move NQ at the minute level.
- The CPI reaction is special (median spike ratio 5.2 vs 2.4-4.2 for the other 08:30 releases, and only CPI has a post-release trend that reverses
  at the open with WR ~80%). Keep CPI09 as the single news module; do not add Ppi09 / Ret09 / Gdp09 / Pce09 / Clm09 modules.
- No NQMaster change. If one wanted to watch something, it would be the PPI 09:30 fade with a 0.5 ATR stop (worth ~$40/month, no Sharpe gain) and the
  FOMC-minutes 14:30 fade (16 T2 trades, inside the news blackout anyway) — neither justifies code.
- Lists for future use: `news_dates_ppi/retail/durables/gdp/pce/claims/fomc_min.csv` are validated by the spike check (hit rates 0.56-0.84);
  `jolts/ism_mfg/ism_serv/cb_conf/umich_p/umich_f.csv` are rule-based or do not spike and should not be used for trading without a better source.
