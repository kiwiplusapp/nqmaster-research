# Calendar check, 2026-10-19 (NQMaster.cs / GoldMaster.cs)

Built-in lists checked: `BuiltinFomc` (both files; FOMC days skipped), `BuiltinCpi` (NQMaster; CPI09 module), `BuiltinNews` (both files, identical; news blackout +-2 min). Range: 2026-10-19 through the end of 2027, plus the 2028 entry.

Sources:
- FOMC: federalreserve.gov/monetarypolicy/fomccalendars.htm (fetched 2026-10-19). Decision = 2nd meeting day. Minutes = 3 weeks after the decision, 14:00 ET (Fed rule). The page lists release dates only after the minutes are out, so every minutes date from Nov 2026 on is an estimate. fedratecalc.com also lists 2026-11-18.
- CPI: bls.gov/schedule/news_release/cpi.htm and bls.gov/schedule/2027/home.htm (official 2027 schedule, all 08:30 ET).
- NFP (Employment Situation): bls.gov/schedule/news_release/empsit.htm and bls.gov/schedule/2027/home.htm (08:30 ET).

## FOMC decisions (BuiltinFomc: skip day; BuiltinNews: 14:00 blackout, added)

| Date | Event | Source | Status |
|---|---|---|---|
| 2026-10-28 | FOMC decision (Oct 27-28) | Fed calendar | ok in skip list; 14:00 added to news list |
| 2026-12-09 | FOMC decision (Dec 8-9) | Fed calendar | ok; 14:00 added |
| 2027-01-27 | FOMC decision (Jan 26-27) | Fed calendar | ok; 14:00 added |
| 2027-03-17 | FOMC decision (Mar 16-17) | Fed calendar | ok; 14:00 added |
| 2027-04-28 | FOMC decision (Apr 27-28) | Fed calendar | ok; 14:00 added |
| 2027-06-09 | FOMC decision (Jun 8-9) | Fed calendar | ok; 14:00 added |
| 2027-07-28 | FOMC decision (Jul 27-28) | Fed calendar | ok; 14:00 added |
| 2027-09-15 | FOMC decision (Sep 14-15) | Fed calendar | ok; 14:00 added |
| 2027-10-27 | FOMC decision (Oct 26-27) | Fed calendar | ok; 14:00 added |
| 2027-12-08 | FOMC decision (Dec 7-8) | Fed calendar | ok; 14:00 added |
| 2028-01-26 | FOMC decision (Jan 25-26, 2028) | Fed calendar | ok; 14:00 added |

The Fed says every meeting date is tentative until confirmed at the meeting before it.

## FOMC minutes (BuiltinNews, 14:00)

| Date | Event | Source | Status |
|---|---|---|---|
| 2026-11-18 | Minutes of Oct 27-28 | Fed rule (+21 d), fedratecalc | estimate (matches) |
| 2026-12-30 | Minutes of Dec 8-9 | Fed rule (+21 d) | estimate (Dec 2025 minutes came out after 20 days, Dec 30 instead of Dec 31: check in December) |
| 2027-02-17 | Minutes of Jan 26-27 | Fed rule | estimate |
| 2027-04-07 | Minutes of Mar 16-17 | Fed rule | estimate |
| 2027-05-19 | Minutes of Apr 27-28 | Fed rule | estimate |
| 2027-06-30 | Minutes of Jun 8-9 | Fed rule | estimate |
| 2027-08-18 | Minutes of Jul 27-28 | Fed rule | estimate |
| 2027-10-06 | Minutes of Sep 14-15 | Fed rule | estimate |
| 2027-11-17 | Minutes of Oct 26-27 | Fed rule | estimate |
| 2027-12-29 | Minutes of Dec 7-8 | Fed rule | estimate |
| 2024-11-26 | Minutes of Nov 6-7, 2024 (historical) | Fed calendar | fixed (code had 2024-11-28, Thanksgiving) |
| 2025-12-30 | Minutes of Dec 9-10, 2025 (historical) | Fed calendar | fixed (code had 2025-12-31) |

## CPI (BuiltinCpi date + BuiltinNews 08:30)

| Date | Event | Source | Status |
|---|---|---|---|
| 2026-11-10 | CPI Oct 2026 | BLS | ok |
| 2026-12-10 | CPI Nov 2026 | BLS | ok |
| 2027-01-13 | CPI Dec 2026 | BLS | ok |
| 2027-02-11 | CPI Jan 2027 | BLS | ok |
| 2027-03-10 | CPI Feb 2027 | BLS | ok |
| 2027-04-13 | CPI Mar 2027 | BLS | ok |
| 2027-05-12 | CPI Apr 2027 | BLS | ok |
| 2027-06-10 | CPI May 2027 | BLS | ok |
| 2027-07-14 | CPI Jun 2027 | BLS | ok |
| 2027-08-11 | CPI Jul 2027 | BLS | ok |
| 2027-09-14 | CPI Aug 2027 | BLS | ok |
| 2027-10-14 | CPI Sep 2027 | BLS | ok |
| 2027-11-10 | CPI Oct 2027 | BLS | ok |
| 2027-12-10 | CPI Nov 2027 | BLS | ok |

## Employment Situation / NFP (BuiltinNews 08:30)

| Date | Event | Source | Status |
|---|---|---|---|
| 2026-11-06 | NFP Oct 2026 | BLS | ok |
| 2026-12-04 | NFP Nov 2026 | BLS | ok |
| 2027-01-08 | NFP Dec 2026 | BLS | ok |
| 2027-02-05 | NFP Jan 2027 | BLS | ok |
| 2027-03-05 | NFP Feb 2027 | BLS | ok |
| 2027-04-02 | NFP Mar 2027 | BLS | ok |
| 2027-05-07 | NFP Apr 2027 | BLS | ok |
| 2027-06-04 | NFP May 2027 | BLS | ok |
| 2027-07-02 | NFP Jun 2027 | BLS | ok |
| 2027-08-06 | NFP Jul 2027 | BLS | ok |
| 2027-09-03 | NFP Aug 2027 | BLS | ok |
| 2027-10-08 | NFP Sep 2027 | BLS | ok |
| 2027-11-05 | NFP Oct 2027 | BLS | ok |
| 2027-12-03 | NFP Nov 2027 | BLS | ok |

Not built in: CPI / NFP for 2028 (BLS has not published them). The "NEWS LIST ends" alert fires 35 days before the last 08:30 entry (2027-12-10), so in early Nov 2027 they must be added through `CpiDates` / `NewsTimes` or the built-in lists. A US government shutdown can move BLS dates (as in Oct 2025 and early 2026): re-check bls.gov after any shutdown.

## Code changes

- `BuiltinNews` (both files, still identical): FOMC decision times 14:00 added from 2026-10-28 to 2028-01-26. These are a safety net only for when `SkipFomc` is off; with the default (`SkipFomc` true) those days are not traded anyway. `NewsListCheck` only looks at 08:xx entries, so the end-of-list alert is unchanged. Two historical minutes dates were corrected (above).
- Comments updated. No logic changed.
- Contextual-keyword identifiers renamed (behaviour identical):
  - NQMaster `PrintModuleReport`: local `from` -> `fromTime`.
  - NQMaster `NewMod` / `AddTime`: parameter `on` -> `isOn`.
  - NQMaster `OnExecutionUpdate`: local `from` -> `exitMod`.
  - GoldMaster `NewMod`: parameter `on` -> `isOn`.
  - GoldMaster `OnExecutionUpdate`: local `from` -> `exitMod`.
  - No other contextual keyword (when, where, select, let, join, into, orderby, group, by, equals, ascending, descending, var, dynamic, async, await, nameof, yield, value outside setters, global, alias, partial, add, remove) is used as an identifier.
- Backups: `NQMaster_backup_pre_cal17.cs`, `GoldMaster_backup_pre_cal17.cs`. `tools/nt8_stub/check.sh` passes for both files (no output, exit 0). Not compiled in NinjaTrader: press F5 on the PC.
