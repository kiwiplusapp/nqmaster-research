# NQMaster: every profile version on the same real futures data

Data nqdb.npz (Databento NQ 1m, back-adjusted). Real view 20200101..20261008: $1.90 RT + 1 tick per side, $ per 1 MNQ base contract; size multipliers as each profile had them (ICT x2, confluence/context x2, cap 2x); FOMC days skipped; MinAtrPoints 150 (no trading on days with daily ATR < 150: ~15% of 2020 and ~7% of 2021 days); day set = all session dates in the window minus FOMC; ATR<150 days = 0 P&L. Funded risk: EOD trailing $2,000, lock at start+100, breach EOD balance <= threshold; target +$3,000 EOD; one account started on every trading day. Norm view: 0.345% of daily ATR, P&L in % of ATR. Skipped: MaxTrades (MOM1130 / RSI2 entries not available on nqdb). Script: research/mine/hist_profiles.py; data: hist_profiles.json, hist_profiles_trades.pkl.

<!-- analysis -->
## Analysis

**Sanity check.** The rebuild of Ultra, UltraLean and WR70Plus reproduces db_long.json exactly: every block, both views, and the same trades as db_long_trades.pkl.

**Did earlier systems backtest better? No.** Each version improved Sharpe over the one before it on the same real futures: MaxSharpe 2.60, MaxPlus 2.77, MaxPlus2 2.90, Ultra_v1 2.94, Ultra_ampliado 3.00, Ultra_night 3.16, Ultra 3.43. The same order holds in each sub-period: 2.56 -> 3.42 in 2020-23 and 2.68 -> 3.51 in 2024-26. PF rose from 1.29 to 1.47. The 2026-10-08 rules (ORB prior-close, VOLB break-even, MOM agreement) gave the largest single step. Ultra_night -> Ultra: Sharpe +0.27, PF 1.39 -> 1.47, losing months 15 -> 11, P(bust 63d) 23 -> 20%, with the same $/month (2,044 vs 2,040) on 9% fewer trades. The ORB prior-close rule also improves every old profile as coded today ("_now" rows): Sharpe +0.10 to +0.26 and a lower max DD.

Caveat: the later versions were selected while looking at more data (CFD 2020-23 and 2024-26, real MNQ 2024-26), so part of their 2024-26 lead is in-sample. The only fully unseen test is the cost-normalised 2010-19 view. There, later versions are also better: Ultra PF 1.01 / 1.12, MaxSharpe 0.96 / 0.97, MaxPlus2 0.97 / 1.00. Still, nothing except Durable6 (1.18 / 1.23) and Core (1.05-1.07 / 1.18-1.23) has a clear edge before 2020.

**Best per metric (2020-26, 1 base contract).**
- PF: Durable6 1.63 (only 1.4 trades/day, 51% of its trades from VOLB). Among full systems, WR70Plus 1.52.
- Win rate: WR70Plus 70.5%.
- Sharpe: Ultra 3.43 (UltraLean 3.36, WR70Plus 3.35).
- $/month: Ultra and Ultra_night, about $2,040.
- Lowest max DD: WinRate70 as coded ($2,334) and MaxSharpe as coded ($2,454).
- Lowest bust odds: WinRate70 as coded, 0% within 63 days, then MaxSharpe about 3.7% and Estable 4.2%.

The low-DD, low-bust profiles earn only $600-750 a month. Their safety comes from small size, not a better edge. WR70Plus reaches +$3k first about as often as MaxSharpe and WinRate70 (87% vs 87-90%), and it gets there in about half the time (36 vs 66-80 days).

**Dominance.** Over the full period:
- MaxPlus2 (the historical design) is worse than WR70Plus on every metric.
- MaxPlus (on every metric) and Core (on the risk-adjusted set) are dominated by today's MaxPlus.
- In 2020-23, WR70Plus dominates MaxPlus, MaxPlus2 and Core as coded today. Ultra dominates Ultra_night.
- In 2024-26, MaxSharpe and WinRate70 dominate Estable (PF 1.27, Sharpe 1.93). This makes the eval safe set worth a second look.
- No profile as coded today is strictly dominated over the full period. MaxPlus2 as coded today is within a hair of WR70Plus: worse PF, WR, Sharpe, $/month and P(+3k), and better only on max DD ($3,991 vs $4,059).

**NinjaTrader profiles.**
- Obsolete: MaxPlus, MaxPlus2 and Core.
  - MaxPlus and MaxPlus2 are earlier steps of Ultra, beaten by Ultra on Sharpe and by WR70Plus on PF and WR.
  - Core has the lowest Sharpe of the coded profiles (2.46) and a 58% WR. Its "defensive / pre-2020-robust" role is better filled by Durable6 (PF 1.63, Sharpe 2.78, $1,148/month, norm 1.18 / 1.23). Durable6 is not an NT profile; it could be a Custom preset.
- MaxTrades: could not be rebuilt (no MOM1130 / RSI2 entries). Earlier research found the same money at a lower PF.
- MaxSharpe and WinRate70 fill the same "small and safe" role. Keep at most one, WinRate70: higher WR, PF and Sharpe, lower DD, 0% 63-day bust.
- Keep: Ultra, WR70Plus, Gold, Custom.
- Removing enum values breaks saved NT templates that use them, so deprecating or hiding them is safer than deleting.
<!-- /analysis -->

## Full period 2020-01 .. 2026-10 (real view; funded starts 2020-26)

| Profile | Date | Tr/day | WR % | PF | Avg $ | $/mo | Sharpe | Max DD $ | Ret/DD | Longest DD (d) | Worst month $ | Losing mo | Worst 20d $ | Top module (% trades) | P(bust 21d) | P(bust 63d) | P(+3k first) | Days to +3k |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MaxSharpe | 2026-09-28 | 3.72 | 66.0 | 1.29 | 9.6 | 748 | 2.60 | 2 965 | 3.0 | 271 | -1 561 | 16/82 | -2 348 | MOM11 20% | 0.7% | 3.8% | 87.2% | 66 |
| WinRate70 | 2026-09-28 | 2.93 | 69.8 | 1.32 | 9.8 | 604 | 2.58 | 3 190 | 2.3 | 186 | -1 843 | 19/82 | -1 934 | MOM11 26% | 1.4% | 5.1% | 79.4% | 69 |
| MaxPlus | 2026-09-29 | 3.82 | 65.6 | 1.35 | 13.1 | 1 054 | 2.77 | 3 146 | 4.0 | 168 | -2 248 | 14/82 | -2 866 | MOM11 20% | 5.5% | 13.7% | 75.6% | 45 |
| MaxPlus2 | 2026-10-02 | 3.83 | 66.3 | 1.40 | 16.9 | 1 363 | 2.90 | 4 160 | 3.9 | 165 | -3 129 | 16/82 | -3 931 | MOM11 20% | 8.6% | 20.4% | 77.1% | 36 |
| Core | 2026-10-03 | 1.93 | 54.5 | 1.38 | 21.6 | 878 | 2.34 | 3 483 | 3.0 | 120 | -2 895 | 24/82 | -3 472 | VOLB 37% | 4.9% | 15.4% | 80.0% | 65 |
| Ultra_v1 | 2026-10-03 | 4.61 | 64.0 | 1.40 | 18.3 | 1 767 | 2.94 | 4 876 | 4.3 | 133 | -3 274 | 18/82 | -4 660 | MOM11 16% | 12.9% | 26.5% | 68.2% | 26 |
| Ultra_ampliado | 2026-10-06 | 5.28 | 64.6 | 1.39 | 17.1 | 1 898 | 3.00 | 5 497 | 4.1 | 130 | -3 522 | 16/82 | -5 282 | MOM11 14% | 12.1% | 23.0% | 71.4% | 24 |
| Ultra_night | 2026-10-07 | 5.62 | 64.3 | 1.39 | 17.3 | 2 044 | 3.16 | 5 708 | 4.3 | 133 | -3 445 | 15/82 | -5 140 | MOM11 13% | 12.5% | 23.2% | 73.0% | 23 |
| Ultra | 2026-10-08 | 5.10 | 65.9 | 1.47 | 19.1 | 2 040 | 3.43 | 5 871 | 4.2 | 127 | -3 635 | 11/82 | -5 484 | MOM11 15% | 7.5% | 19.9% | 78.5% | 25 |
| UltraLean | 2026-10-08 | 4.24 | 66.6 | 1.49 | 21.1 | 1 875 | 3.36 | 5 199 | 4.3 | 129 | -3 357 | 13/82 | -4 750 | MOM11 18% | 7.8% | 19.0% | 79.5% | 27 |
| WR70Plus | 2026-10-08 | 3.22 | 70.5 | 1.52 | 21.4 | 1 448 | 3.35 | 4 059 | 4.3 | 83 | -2 950 | 13/82 | -3 723 | MOM11 24% | 3.9% | 9.1% | 87.4% | 36 |
| Estable | 2026-10-08 | 2.45 | 67.2 | 1.37 | 11.7 | 600 | 2.47 | 3 073 | 2.3 | 78 | -2 028 | 18/82 | -2 482 | REV06 18% | 1.0% | 4.2% | 91.7% | 85 |
| Core_now | 2026-10-08 | 1.86 | 58.0 | 1.43 | 21.9 | 855 | 2.46 | 3 699 | 2.8 | 118 | -3 266 | 20/82 | -3 688 | VOLB 39% | 2.4% | 8.5% | 89.8% | 70 |
| Durable6 | 2026-10-09 | 1.43 | 61.7 | 1.63 | 38.1 | 1 148 | 2.78 | 3 845 | 3.6 | 74 | -2 504 | 16/82 | -3 638 | VOLB 51% | 4.7% | 12.4% | 84.5% | 48 |

## 2020-2023 (real futures; this is where most modules were chosen, on CFD data)

| Profile | Date | Tr/day | WR % | PF | Avg $ | $/mo | Sharpe | Max DD $ | Ret/DD | Longest DD (d) | Worst month $ | Losing mo | Worst 20d $ | Top module (% trades) | P(bust 21d) | P(bust 63d) | P(+3k first) | Days to +3k |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MaxSharpe | 2026-09-28 | 3.67 | 66.4 | 1.29 | 8.7 | 666 | 2.56 | 2 373 | 3.4 | 138 | -1 035 | 9/48 | -1 414 | MOM11 20% | 0.0% | 2.7% | 82.8% | 69 |
| WinRate70 | 2026-09-28 | 2.86 | 70.3 | 1.35 | 9.3 | 558 | 2.74 | 2 203 | 3.0 | 142 | -1 143 | 9/48 | -1 456 | MOM11 25% | 0.0% | 2.6% | 74.5% | 72 |
| MaxPlus | 2026-09-29 | 3.77 | 66.1 | 1.36 | 11.8 | 938 | 2.69 | 3 067 | 3.7 | 113 | -1 795 | 8/48 | -2 354 | MOM11 19% | 2.6% | 10.0% | 74.3% | 47 |
| MaxPlus2 | 2026-10-02 | 3.78 | 66.9 | 1.42 | 15.5 | 1 230 | 2.85 | 3 575 | 4.1 | 113 | -2 129 | 9/48 | -2 521 | MOM11 19% | 6.7% | 18.9% | 77.9% | 37 |
| Core | 2026-10-03 | 1.90 | 55.3 | 1.33 | 16.9 | 674 | 2.09 | 3 483 | 2.3 | 120 | -2 895 | 10/48 | -3 472 | VOLB 37% | 3.4% | 9.8% | 90.2% | 86 |
| Ultra_v1 | 2026-10-03 | 4.55 | 64.7 | 1.39 | 15.9 | 1 517 | 2.76 | 2 765 | 6.6 | 81 | -1 413 | 9/48 | -1 917 | MOM11 16% | 7.8% | 24.4% | 67.8% | 30 |
| Ultra_ampliado | 2026-10-06 | 5.23 | 65.4 | 1.39 | 15.1 | 1 662 | 2.87 | 2 792 | 7.1 | 81 | -1 635 | 7/48 | -1 905 | MOM11 14% | 8.5% | 21.6% | 69.9% | 28 |
| Ultra_night | 2026-10-07 | 5.55 | 65.2 | 1.40 | 15.3 | 1 787 | 3.05 | 3 384 | 6.3 | 79 | -1 848 | 7/48 | -1 840 | MOM11 13% | 7.9% | 20.9% | 72.9% | 28 |
| Ultra | 2026-10-08 | 5.04 | 66.6 | 1.48 | 17.0 | 1 801 | 3.42 | 3 122 | 6.9 | 76 | -1 975 | 5/48 | -2 308 | MOM11 15% | 2.9% | 17.8% | 78.8% | 29 |
| UltraLean | 2026-10-08 | 4.19 | 67.4 | 1.48 | 18.5 | 1 628 | 3.28 | 3 296 | 5.9 | 75 | -1 993 | 7/48 | -2 443 | MOM11 18% | 3.4% | 17.1% | 79.9% | 32 |
| WR70Plus | 2026-10-08 | 3.15 | 71.8 | 1.59 | 20.5 | 1 359 | 3.58 | 2 315 | 7.0 | 83 | -1 160 | 6/48 | -1 733 | MOM11 23% | 0.0% | 1.5% | 93.6% | 39 |
| Estable | 2026-10-08 | 2.43 | 68.7 | 1.47 | 12.5 | 640 | 3.01 | 1 855 | 4.1 | 77 | -1 404 | 10/48 | -1 844 | REV06 18% | 0.0% | 0.0% | 100.0% | 95 |
| Core_now | 2026-10-08 | 1.82 | 58.3 | 1.37 | 17.4 | 665 | 2.26 | 3 699 | 2.2 | 118 | -3 266 | 10/48 | -3 688 | VOLB 38% | 2.1% | 6.9% | 93.1% | 81 |
| Durable6 | 2026-10-09 | 1.39 | 62.9 | 1.60 | 32.7 | 953 | 2.73 | 3 004 | 3.8 | 62 | -1 905 | 8/48 | -2 393 | VOLB 50% | 2.8% | 8.9% | 87.4% | 61 |

## 2024-2026 (real futures; funded starts 2024-26)

| Profile | Date | Tr/day | WR % | PF | Avg $ | $/mo | Sharpe | Max DD $ | Ret/DD | Longest DD (d) | Worst month $ | Losing mo | Worst 20d $ | Top module (% trades) | P(bust 21d) | P(bust 63d) | P(+3k first) | Days to +3k |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MaxSharpe | 2026-09-28 | 3.81 | 65.5 | 1.28 | 10.8 | 865 | 2.68 | 2 505 | 4.1 | 97 | -1 561 | 7/34 | -2 348 | MOM11 21% | 1.6% | 5.5% | 94.3% | 63 |
| WinRate70 | 2026-09-28 | 3.02 | 69.1 | 1.29 | 10.6 | 671 | 2.46 | 2 343 | 3.4 | 114 | -1 843 | 10/34 | -1 934 | MOM11 26% | 3.4% | 9.2% | 87.2% | 67 |
| MaxPlus | 2026-09-29 | 3.89 | 64.9 | 1.34 | 14.9 | 1 221 | 2.89 | 3 047 | 4.8 | 77 | -2 248 | 6/34 | -2 866 | MOM11 20% | 9.8% | 19.6% | 77.7% | 40 |
| MaxPlus2 | 2026-10-02 | 3.91 | 65.5 | 1.39 | 19.0 | 1 555 | 2.98 | 4 160 | 4.5 | 78 | -3 129 | 7/34 | -3 931 | MOM11 20% | 11.6% | 22.9% | 75.7% | 32 |
| Core | 2026-10-03 | 1.98 | 53.3 | 1.43 | 28.2 | 1 173 | 2.66 | 3 050 | 4.6 | 79 | -1 266 | 14/34 | -2 677 | VOLB 38% | 7.3% | 24.2% | 64.5% | 34 |
| Ultra_v1 | 2026-10-03 | 4.69 | 63.0 | 1.40 | 21.6 | 2 128 | 3.18 | 4 876 | 5.2 | 71 | -3 274 | 9/34 | -4 660 | MOM11 17% | 20.6% | 29.9% | 68.8% | 19 |
| Ultra_ampliado | 2026-10-06 | 5.36 | 63.5 | 1.38 | 19.9 | 2 238 | 3.18 | 5 497 | 4.9 | 75 | -3 522 | 9/34 | -5 282 | MOM11 15% | 17.5% | 25.3% | 73.7% | 19 |
| Ultra_night | 2026-10-07 | 5.73 | 63.2 | 1.39 | 20.1 | 2 416 | 3.34 | 5 708 | 5.1 | 75 | -3 445 | 8/34 | -5 140 | MOM11 14% | 19.3% | 26.9% | 73.1% | 18 |
| Ultra | 2026-10-08 | 5.18 | 64.9 | 1.46 | 21.9 | 2 385 | 3.51 | 5 871 | 4.9 | 70 | -3 635 | 6/34 | -5 484 | MOM11 15% | 14.4% | 23.4% | 78.0% | 19 |
| UltraLean | 2026-10-08 | 4.30 | 65.6 | 1.49 | 24.7 | 2 230 | 3.50 | 5 199 | 5.1 | 67 | -3 357 | 6/34 | -4 750 | MOM11 18% | 14.4% | 22.0% | 78.7% | 21 |
| WR70Plus | 2026-10-08 | 3.31 | 68.8 | 1.46 | 22.7 | 1 577 | 3.17 | 4 059 | 4.7 | 63 | -2 950 | 7/34 | -3 723 | MOM11 24% | 9.8% | 21.2% | 78.1% | 31 |
| Estable | 2026-10-08 | 2.47 | 65.0 | 1.27 | 10.4 | 542 | 1.93 | 3 073 | 2.1 | 78 | -2 028 | 8/34 | -2 482 | REV06 19% | 2.4% | 10.9% | 79.1% | 73 |
| Core_now | 2026-10-08 | 1.92 | 57.6 | 1.49 | 28.0 | 1 128 | 2.73 | 3 135 | 4.3 | 50 | -1 122 | 10/34 | -3 011 | VOLB 40% | 3.0% | 11.1% | 84.7% | 47 |
| Durable6 | 2026-10-09 | 1.50 | 60.2 | 1.66 | 45.2 | 1 429 | 2.91 | 3 845 | 4.5 | 74 | -2 504 | 8/34 | -3 638 | VOLB 51% | 7.6% | 17.9% | 80.0% | 38 |

## Regime robustness: cost-normalised view (cost 0.345% of ATR, P&L in % of ATR, no ATR guard)

| Profile | 2010-14 PF | 2010-14 WR | 2015-19 PF | 2015-19 WR | 2020-23 PF | 2024-26 PF |
|---|---|---|---|---|---|---|
| MaxSharpe | 0.96 | 60.0 | 0.97 | 60.7 | 1.30 | 1.28 |
| WinRate70 | 0.99 | 64.3 | 0.98 | 64.5 | 1.33 | 1.29 |
| MaxPlus | 0.98 | 59.3 | 0.99 | 60.1 | 1.36 | 1.34 |
| MaxPlus2 | 0.97 | 59.7 | 1.00 | 60.2 | 1.40 | 1.39 |
| Core | 1.05 | 47.9 | 1.18 | 50.4 | 1.36 | 1.45 |
| Ultra_v1 | 1.01 | 57.3 | 1.06 | 58.5 | 1.39 | 1.40 |
| Ultra_ampliado | 0.99 | 57.6 | 1.06 | 59.3 | 1.39 | 1.38 |
| Ultra_night | 0.99 | 57.7 | 1.08 | 59.5 | 1.38 | 1.38 |
| Ultra | 1.01 | 59.2 | 1.12 | 61.3 | 1.44 | 1.46 |
| UltraLean | 1.02 | 60.1 | 1.12 | 61.9 | 1.45 | 1.49 |
| WR70Plus | 0.98 | 64.2 | 1.07 | 64.6 | 1.52 | 1.46 |
| Estable | 0.97 | 60.0 | 1.00 | 60.6 | 1.45 | 1.29 |
| Core_now | 1.07 | 52.5 | 1.23 | 55.2 | 1.39 | 1.51 |
| Durable6 | 1.18 | 56.9 | 1.23 | 57.8 | 1.57 | 1.66 |

## The old NT profiles as they run in today's NQMaster.cs (ORB prior-close rule applies to every profile)

| Profile | Date | Tr/day | WR % | PF | Avg $ | $/mo | Sharpe | Max DD $ | Ret/DD | Longest DD (d) | Worst month $ | Losing mo | Worst 20d $ | Top module (% trades) | P(bust 21d) | P(bust 63d) | P(+3k first) | Days to +3k |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MaxSharpe | 2026-09-28 | 3.72 | 66.0 | 1.29 | 9.6 | 748 | 2.60 | 2 965 | 3.0 | 271 | -1 561 | 16/82 | -2 348 | MOM11 20% | 0.7% | 3.8% | 87.2% | 66 |
| MaxSharpe_now | code | 3.63 | 66.2 | 1.30 | 9.8 | 744 | 2.70 | 2 454 | 3.6 | 183 | -1 454 | 17/82 | -2 241 | MOM11 21% | 0.6% | 3.6% | 88.9% | 69 |
| WinRate70 | 2026-09-28 | 2.93 | 69.8 | 1.32 | 9.8 | 604 | 2.58 | 3 190 | 2.3 | 186 | -1 843 | 19/82 | -1 934 | MOM11 26% | 1.4% | 5.1% | 79.4% | 69 |
| WinRate70_now | code | 2.84 | 70.2 | 1.34 | 10.0 | 599 | 2.72 | 2 334 | 3.1 | 183 | -1 551 | 18/82 | -1 740 | MOM11 26% | 0.0% | 0.0% | 89.6% | 80 |
| MaxPlus | 2026-09-29 | 3.82 | 65.6 | 1.35 | 13.1 | 1 054 | 2.77 | 3 146 | 4.0 | 168 | -2 248 | 14/82 | -2 866 | MOM11 20% | 5.5% | 13.7% | 75.6% | 45 |
| MaxPlus_now | code | 3.67 | 65.9 | 1.38 | 13.8 | 1 065 | 3.00 | 2 883 | 4.4 | 136 | -2 035 | 16/82 | -2 653 | MOM11 20% | 3.3% | 8.1% | 84.4% | 51 |
| MaxPlus2 | 2026-10-02 | 3.83 | 66.3 | 1.40 | 16.9 | 1 363 | 2.90 | 4 160 | 3.9 | 165 | -3 129 | 16/82 | -3 931 | MOM11 20% | 8.6% | 20.4% | 77.1% | 36 |
| MaxPlus2_now | code | 3.68 | 66.7 | 1.44 | 17.6 | 1 357 | 3.16 | 3 991 | 4.1 | 136 | -2 961 | 16/82 | -3 763 | MOM11 20% | 4.5% | 9.8% | 86.1% | 40 |

| Profile | 2010-14 PF | 2010-14 WR | 2015-19 PF | 2015-19 WR | 2020-23 PF | 2024-26 PF |
|---|---|---|---|---|---|---|
| MaxSharpe_now | 0.95 | 59.9 | 0.96 | 60.6 | 1.31 | 1.30 |
| WinRate70_now | 0.97 | 64.4 | 0.99 | 64.9 | 1.35 | 1.33 |
| MaxPlus_now | 0.96 | 59.2 | 0.99 | 60.0 | 1.39 | 1.38 |
| MaxPlus2_now | 0.96 | 59.6 | 1.00 | 60.1 | 1.45 | 1.42 |

## Dominance (full period)

Risk-adjusted set: higher better pf, sharpe, per_month, p_reach_3k_first; lower better max_dd, p_bust_63d. All-metrics set: higher better pf, wr, sharpe, per_month, worst_20d, worst_month, p_reach_3k_first; lower better max_dd, longest_dd_days, p_bust_63d. A profile is dominated when another is at least as good on every metric of the set and better on at least one. Per-period sets use the funded starts of the same period.

**All versions, risk-adjusted set, 2020-26**

- MaxPlus: dominated by MaxPlus_now
- MaxPlus2: dominated by WR70Plus
- Core: dominated by MaxPlus_now

**All versions, all metrics, 2020-26**

- MaxPlus: dominated by MaxPlus_now
- MaxPlus2: dominated by WR70Plus

**All versions, risk-adjusted set, 2020-23**

- MaxSharpe: dominated by WR70Plus
- WinRate70: dominated by Estable
- MaxPlus: dominated by WR70Plus, Durable6, MaxPlus_now
- MaxPlus2: dominated by Ultra, UltraLean, WR70Plus, MaxPlus2_now
- Core: dominated by WR70Plus
- Ultra_night: dominated by Ultra
- Core_now: dominated by WR70Plus
- MaxPlus_now: dominated by WR70Plus
- MaxPlus2_now: dominated by WR70Plus

**All versions, risk-adjusted set, 2024-26**

- WinRate70: dominated by WinRate70_now
- MaxPlus: dominated by MaxPlus_now
- MaxPlus2: dominated by WR70Plus
- Estable: dominated by MaxSharpe, WinRate70, MaxSharpe_now, WinRate70_now

**Profiles as coded today (MaxSharpe_now, WinRate70_now, MaxPlus_now, MaxPlus2_now, Core_now, Ultra, UltraLean, WR70Plus, Estable), risk-adjusted set, 2020-26**

- none

**Profiles as coded today, all metrics, 2020-26**

- none

**Profiles as coded today, risk-adjusted set, 2020-23**

- MaxPlus_now: dominated by WR70Plus
- MaxPlus2_now: dominated by WR70Plus
- Core_now: dominated by WR70Plus

**Profiles as coded today, risk-adjusted set, 2024-26**

- Estable: dominated by MaxSharpe_now, WinRate70_now

## Per-module contribution, full period ($/month per base contract, PF)

| Module | MaxSharpe | WinRate70 | MaxPlus | MaxPlus2 | Core | Ultra_v1 | Ultra_ampliado | Ultra_night | Ultra | UltraLean | WR70Plus | Estable | Core_now | Durable6 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CRT11 | 98 (1.73) | 98 (1.73) | 170 (1.88) | 200 (1.84) | 70 (1.67) | 159 (1.94) | 159 (1.94) | 159 (1.94) | 178 (2.05) | 176 (2.05) | 205 (1.89) | 87 (1.58) | 80 (1.75) | 166 (1.96) |
| ENG10 |  |  |  |  |  |  | 54 (1.28) | 54 (1.28) | 54 (1.28) |  |  | 55 (1.28) |  |  |
| ICT | 20 (1.22) | 20 (1.22) | 40 (1.22) | 40 (1.22) | 37 (1.24) | 36 (1.23) | 36 (1.23) | 36 (1.23) | 33 (1.20) | 33 (1.20) | 40 (1.22) |  | 34 (1.21) |  |
| LATE15 |  |  |  |  | 41 (1.41) | 41 (1.41) | 41 (1.41) | 41 (1.41) | 41 (1.41) | 41 (1.41) | 41 (1.41) |  | 41 (1.41) |  |
| LATEFH |  |  |  |  |  |  | 44 (1.36) | 44 (1.36) | 46 (1.39) |  |  | 43 (1.36) |  |  |
| LF0430 |  |  |  |  |  |  |  | 41 (1.42) | 41 (1.42) | 41 (1.42) | 41 (1.42) |  |  |  |
| LF06 |  |  |  |  |  |  |  | 25 (1.35) | 25 (1.35) | 25 (1.35) | 24 (1.31) |  |  |  |
| LON | 69 (1.23) |  | 69 (1.23) | 69 (1.23) | 69 (1.23) | 69 (1.23) | 69 (1.23) | 72 (1.24) | 72 (1.24) | 72 (1.24) |  |  | 69 (1.23) |  |
| MOM1030 | 34 (1.15) | 34 (1.15) | 34 (1.15) | 34 (1.15) |  | 34 (1.15) | 34 (1.15) | 34 (1.15) | 39 (1.46) | 32 (1.48) |  |  |  |  |
| MOM11 | 102 (1.23) | 102 (1.23) | 102 (1.23) | 102 (1.23) |  | 103 (1.23) | 103 (1.23) | 103 (1.23) | 107 (1.24) | 104 (1.23) | 103 (1.23) |  |  |  |
| MOM13 | 105 (1.25) |  | 125 (1.27) | 125 (1.27) |  | 125 (1.27) | 125 (1.27) | 125 (1.27) | 135 (1.56) | 123 (1.51) |  |  |  |  |
| MSEQ | 77 (1.36) | 77 (1.36) | 100 (1.39) | 162 (1.45) | 74 (1.41) | 158 (1.53) | 159 (1.54) | 159 (1.54) | 159 (1.50) | 156 (1.49) | 160 (1.46) | 80 (1.37) | 75 (1.39) |  |
| MSEQS |  |  | 59 (2.39) | 59 (2.39) |  | 59 (2.39) | 59 (2.39) | 59 (2.39) | 59 (2.39) | 51 (2.21) | 51 (2.21) |  |  | 51 (2.21) |
| NF05 |  |  |  |  |  |  |  | 80 (1.51) | 80 (1.51) | 80 (1.51) | 73 (1.42) |  |  | 76 (1.43) |
| ON07 | 35 (1.16) | 35 (1.16) | 35 (1.16) | 39 (1.23) |  | 39 (1.23) | 39 (1.23) | 34 (1.21) | 34 (1.21) |  |  | 39 (1.23) |  |  |
| ORB60 | 189 (1.63) | 220 (1.70) | 189 (1.63) | 312 (1.67) | 188 (1.62) | 321 (1.70) | 321 (1.70) | 321 (1.70) | 295 (2.11) | 297 (2.12) | 345 (2.26) |  | 180 (2.06) | 289 (2.06) |
| ORB90 |  |  | 107 (1.43) | 175 (1.59) |  | 180 (1.62) | 180 (1.62) | 180 (1.62) | 184 (2.03) | 185 (2.04) | 185 (2.03) | 120 (1.80) |  | 182 (2.00) |
| REV06 | 18 (1.07) | 18 (1.07) | 24 (1.17) | 24 (1.17) |  | 24 (1.17) | 24 (1.17) | 26 (1.21) | 26 (1.21) | 26 (1.21) | 22 (1.10) | 18 (1.07) |  |  |
| VOLB |  |  |  |  | 398 (1.34) | 399 (1.34) | 399 (1.34) | 399 (1.34) | 379 (1.39) | 379 (1.39) |  |  | 375 (1.39) | 385 (1.39) |
| VOLB_tf1 |  |  |  |  |  |  |  |  |  |  | 103 (1.43) | 103 (1.43) |  |  |
| VW13 |  |  |  | 21 (1.57) |  | 21 (1.56) | 21 (1.56) | 21 (1.56) | 21 (1.57) | 21 (1.57) | 21 (1.57) | 21 (1.57) |  |  |
| VW13b |  |  |  |  |  |  | 31 (1.27) | 31 (1.27) | 33 (1.29) | 33 (1.29) | 34 (1.29) | 35 (1.30) |  |  |

## Profile definitions

| Profile | Date | Modules | Overrides / agreement | Rules | Note |
|---|---|---|---|---|---|
| MaxSharpe | 2026-09-28 | 10: ORB60 MSEQ CRT11 MOM11 MOM13 MOM1030 ON07 REV06 LON ICT | - | conflict only, ICT x1 | v8: 10 modules, ICT x1, no rules |
| WinRate70 | 2026-09-28 | 8: ORB60 MSEQ CRT11 MOM11 MOM1030 ON07 REV06 ICT | - | conflict only, ICT x1 | ORB60 0.75R, no MOM13/LON, ICT x1, no rules |
| MaxPlus | 2026-09-29 | 12: ORB60 MSEQ CRT11 MOM11 MOM13 MOM1030 ON07 REV06 LON ICT ORB90 MSEQS | - | confluence | MaxSharpe + ORB90 + MSEQS, ICT x2, confluence |
| MaxPlus2 | 2026-10-02 | 13: ORB60 MSEQ CRT11 MOM11 MOM13 MOM1030 ON07 REV06 LON ICT ORB90 MSEQS VW13 | - | confluence + 12 context | MaxPlus + 12 context rules + VW13 (0.30 ATR, 1 lot) |
| Core | 2026-10-03 | 7: ORB60 MSEQ CRT11 LON ICT VOLB LATE15 | - | conflict only | ORB60 MSEQ CRT11 LON ICTx2 VOLB2R LATE15, no rules |
| Ultra_v1 | 2026-10-03 | 15: ORB60 MSEQ CRT11 MOM11 MOM13 MOM1030 ON07 REV06 LON ICT ORB90 MSEQS VW13 VOLB LATE15 | - | confluence + 12 context | MaxPlus2 + VOLB + LATE15 |
| Ultra_ampliado | 2026-10-06 | 18: ORB60 MSEQ CRT11 MOM11 MOM13 MOM1030 ON07 REV06 LON ICT ORB90 MSEQS VW13 VOLB LATE15 ENG10 LATEFH VW13b | - | confluence + 12 context | Ultra_v1 + ENG10 + LATEFH + VW13b (VW13 wide) |
| Ultra_night | 2026-10-07 | 21: ORB60 MSEQ CRT11 MOM11 MOM13 MOM1030 ON07 REV06 LON ICT ORB90 MSEQS VW13 VOLB LATE15 ENG10 LATEFH VW13b NF05 LF06 LF0430 | - | confluence + 12 context | Ultra_ampliado + NF05 + LF06 + LF0430 |
| Ultra | 2026-10-08 | 21: ORB60 ORB90 MSEQ MSEQS CRT11 ICT MOM11 MOM1030 MOM13 ON07 REV06 LON VW13b VW13 VOLB LATE15 LATEFH ENG10 NF05 LF06 LF0430 | ORB60, ORB90, VOLB / agr MOM1030, MOM13 | confluence + 12 context | current code: Ultra_night + ORB prior-close, VOLB BE, MOM1030/MOM13 agreement |
| UltraLean | 2026-10-08 | 18: ORB60 ORB90 MSEQ MSEQS CRT11 ICT MOM11 MOM1030 MOM13 REV06 LON VW13b VW13 VOLB LATE15 NF05 LF06 LF0430 | ORB60, ORB90, VOLB / agr MOM1030, MOM13 | confluence + 12 context | Ultra without ON07 / LATEFH / ENG10 |
| WR70Plus | 2026-10-08 | 15: ORB60 ORB90 MSEQ MSEQS CRT11 ICT MOM11 REV06 VW13b VW13 VOLB_tf1 LATE15 NF05 LF06 LF0430 | ORB60, ORB90, VOLB_tf1 | confluence + 12 context | current WR70Plus + NightOnWr70 (ORBt, VOLB_tf1 10:47) |
| Estable | 2026-10-08 | 10: CRT11 ORB90 MSEQ ON07 REV06 VOLB_tf1 VW13b VW13 ENG10 LATEFH | ORB90, VOLB_tf1 | confluence + 12 context, boosts off | eval safe set, boosts off |
| Core_now | 2026-10-08 | 7: ORB60 MSEQ CRT11 LON ICT VOLB LATE15 | ORB60, VOLB | conflict only | Core as coded today (ORBt, VOLB BE) |
| Durable6 | 2026-10-09 | 6: NF05 CRT11 VOLB MSEQS ORB60 ORB90 | ORB60, ORB90, VOLB | confluence + 12 context | 16-year durable modules, Ultra rules/overrides |
| MaxSharpe_now | code | 10: ORB60 MSEQ CRT11 MOM11 MOM13 MOM1030 ON07 REV06 LON ICT | ORB60 | conflict only, ICT x1 | MaxSharpe + ORBt (today's NT MaxSharpe) |
| WinRate70_now | code | 8: ORB60 MSEQ CRT11 MOM11 MOM1030 ON07 REV06 ICT | ORB60 | conflict only, ICT x1 | WinRate70 + ORBt (today's NT WinRate70) |
| MaxPlus_now | code | 12: ORB60 MSEQ CRT11 MOM11 MOM13 MOM1030 ON07 REV06 LON ICT ORB90 MSEQS | ORB60, ORB90 | confluence | MaxPlus + ORBt (today's NT MaxPlus) |
| MaxPlus2_now | code | 13: ORB60 MSEQ CRT11 MOM11 MOM13 MOM1030 ON07 REV06 LON ICT ORB90 MSEQS VW13 | ORB60, ORB90 | confluence + 12 context | MaxPlus2 + ORBt (today's NT MaxPlus2) |

## Sanity check vs db_long.json

- Ultra: trades identical to db_long_trades.pkl = True; db_long.json blocks matched: 2010-2014 yes, 2015-2019 yes, 2020-2023 yes, 2024-2026 yes
- UltraLean: trades identical to db_long_trades.pkl = True; db_long.json blocks matched: 2010-2014 yes, 2015-2019 yes, 2020-2023 yes, 2024-2026 yes
- WR70Plus: trades identical to db_long_trades.pkl = True; db_long.json blocks matched: 2010-2014 yes, 2015-2019 yes, 2020-2023 yes, 2024-2026 yes
