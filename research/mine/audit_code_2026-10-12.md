# NQMaster / GoldMaster: operational and logic code audit (2026-10-12)

**What was audited**
- `NQMaster.cs` as committed at HEAD `ac18a01` (1,536 lines; "configurable warm-up days").
- `GoldMaster.cs` (756 lines, unchanged in the working tree).
- Line numbers below refer to these versions.

**Concurrent edit.** During the audit, an uncommitted overhaul of `NQMaster.cs` appeared in the working tree (`NQMaster_backup_pre_overhaul.cs`). It reduces the profiles to Ultra / WR70Plus / Durable / Custom and adds `MinStopAtr` and `RiskCapPerContract`. I checked its diff. It does not touch the areas of the findings below: session end and holidays, account-position reconciliation, maximum open contracts, the stale-order watchdog, `InTrade` bookkeeping, the news list, rollover and logging. So every finding still applies; only the line numbers move.

**Evidence used**
- Full read of both strategies.
- The guides `NQMASTER_GUIA.md` / `GOLDMASTER_GUIA.md` and `research/mine/propfirms_2026.md`.
- The NinjaTrader validation exports in `research/nt_exports/2026-10-09/`:
  - Ultra MNQ: 2,221 trades.
  - GoldMaster Robust MGC: 332 trades.
  - Times are in Argentina time, converted to ET for the analysis below.
- Diffs against `*_backup_pre_warmup.cs`.
- Official calendars: BLS schedules 2026/2027, the Fed FOMC calendar, and the MyFundedFutures help centre (sources at the end).

**Nothing was edited, compiled or committed.**

---

## Summary table

| # | Severity | Finding | Where |
|---|---|---|---|
| C1 | **Critical** | GoldMaster flattens at 16:51 ET, after MFFU's 16:10 ET auto-close and Lucid's 16:45 ET cutoff. The firm's close is invisible to the strategy, so GoldMaster's later exit order opens a **reverse, unprotected, after-hours position**. MFFU says such an order "will sometimes … go through and disqualify your trading account". 25 of 332 validated gold trades were still open after 16:10 (19 after 16:45). | GoldMaster.cs:111, 239-244, 529-535, 727 |
| H1 | High | No reconciliation of the strategy position against the account position (`PositionAccount` is never read). After a restart with a real position open, an external or manual flatten, or an OCO/overfill failure, exits can open reverse unprotected positions, and orphan brackets stay live. | NQMaster.cs:138, 1130-1144, 1270-1308; GoldMaster.cs:101, 524-536, 602-622 |
| H2 | High | Holiday, half-day and special-closure sessions are not modelled:<br>- No early flatten. On MFFU holidays nobody auto-liquidates and not being flat is a breach.<br>- Entries continue until the close.<br>- Working GTC entries are never cancelled at the next session start (VOLB keeps yesterday's level).<br>- 61 validated holiday-session trades lost $2,029 at 1 contract.<br>- The research skipped these sessions for MOM11; the code does not. | NQMaster.cs:276-292, 338, 391-407, 491-495, 564-614; GoldMaster.cs:239, 276-310 |
| H3 | High | No cap on total open contracts. Validated peak: 11 MNQ at 1 contract (2025-08-08 15:01), i.e. **22 micros at 2 contracts**. That is above Lucid 50K funded tier-1 (20 micros). The guide's "fits in 20" (line 187) is out of date. | NQMaster.cs:860-867 and all entry paths (`OfApply` 1409) |
| M1 | Medium | News list:<br>- The **2026-10-02 NFP is missing**.<br>- No 2027 CPI/NFP, although BLS published them (list below).<br>- No warning when the list runs out; unparsable tokens are dropped silently. | NQMaster.cs:92, 178-183; GoldMaster.cs:68, 128-133; research/mine/patch_wrq_news.py:19, research/news.py:25 |
| M2 | Medium | In realtime, the stale-order watchdog drops orders that may still be live at the broker after 2 minutes ("cancel never confirmed" / "never accepted"). The opposite direction is then allowed again. | NQMaster.cs:1221-1249; GoldMaster.cs:556-583 |
| M3 | Medium | The module's `InTrade` flag is cleared by the first protective fill of a multi-lot entry (`PerEntryExecution`). The remaining lots lose their time exits (LON 09:30, NF05 / REV06 / LF* / ON07 holds). | NQMaster.cs:1305-1306; GoldMaster.cs:609, 619-620 |
| M4 | Medium | Prop state is stored per PC; Federico runs a second PC.<br>- A stale or missing file gives a too-low peak, so the cushion is **overstated** and the strategy runs FULL / step-up on a thinner real cushion.<br>- A mid-session restart writes intraday cash into the "EOD peak" and gates on intraday cash.<br>- The best day is lost if NT was off for a whole session. | NQMaster.cs:968-1048 (1005, 1019-1026) |
| M5 | Medium | Contract rollover has no guard and no documented procedure. The strategy can keep trading the expiring month, and night positions can be open at the 09:30 ET final settlement. | NQMaster.cs / GoldMaster.cs (absent) |
| M6 | Medium | Logging and alerting:<br>- Output window only, lost when NT closes.<br>- Exits and P&L are not logged; VOLB placement is not logged.<br>- No `Alert()`.<br>- No warm-up warning in NQMaster. | NQMaster.cs:1338, 478-513, 188-200 |
| M7 | Medium | A restart rebuilds the edge-monitor CUSUM and the `DailyLossLimit` baseline from *virtual* history. The CUSUM forgets every day older than "Days to load". | NQMaster.cs:933-952, 279, 832-836 |
| M8 | Medium | No intraday "liquidation guard" relative to the computed EOD threshold. The `MaxDrawdown` guard trails intraday cash instead. Worst validated day at 1 contract (NQ + gold): -$2,191, which exceeds a $2,000 drawdown. | NQMaster.cs:1107-1128 |
| L1-L8 | Low | See the Low section: rejection loops, gate change without cancelling orders, exact-minute triggers, silent time-zone / template fallbacks, hard-coded $2,000 DD in GoldMaster, `Range` attributes, `ChangeOrder` in managed mode, log noise. | various |

---

## Critical

### C1. GoldMaster is flat at 16:51 ET, but both firms close earlier, so a reverse after-hours position can be opened

**Code**
- `GoldMaster.cs:111` sets `FlattenTime = 1651`.
- `:239` flattens at the bar closing at 16:51.
- Time exits (`:240-244`, `MaxHold` 400 bars for OD1030 / ENG0408 / ENG0206) can fire any time before that.
- `GOLDMASTER_GUIA.md:9` tells the user "Cierra todo a las 16:51 ET".

**Firm rules**
- The project's own survey (`research/mine/propfirms_2026.md:11, 34, 60`) records "Lucid: flat by 4:45 PM ET" and "MFFU: flat 4:10 PM ET".
- The MFFU help centre (article 9558251) says:
  - "any open positions will be automatically closed at 4:10 PM EST on regular (non-holiday) trading days".
  - Do not "force a trade multiple times on the market after 4:10 PM EST", since this "will sometimes cause the order to go through and disqualify your trading account".

**Scenario** (MFFU)
1. ENG0408 is long 1 MGC at 16:09.
2. MFFU's risk system sells it at 16:10. NinjaTrader books that fill as a non-strategy order, so the **strategy position stays "long 1"**.
3. At 16:25-16:51, GoldMaster's time exit (`ExitModule`) or `FlattenAll` (`ExitLong()`) sends a market SELL.
4. If it goes through, the account is now **short 1 MGC after the cutoff**, with no stop, because the strategy thinks it just went flat and NT cancels the bracket.
5. That is a rule violation plus an unprotected overnight position.

On Lucid the same happens between 16:45 and 16:51. If the firm does not cancel GoldMaster's resting stop and target at its auto-close, those can also fill later and open a position.

**Frequency** (validated MGC export, 18.3 months, 1 contract)
- 25 of 332 trades (7.5%, about 1.4 per month) were still open after 16:10 ET: OD1030 9, ENG0206 8, ENG0408 8. They netted -$2,080.
- 19 were still open after 16:45.
- NQMaster is not affected: `FlattenTime` is 1556, and none of 2,221 trades exited after 16:00.

**Fix**
1. **Settings (immediate):** set GoldMaster `FlattenTime = 1600` on both firms, and fix `GOLDMASTER_GUIA.md:9`.
2. **Code:**
   - Change the default to 1600.
   - Never send an exit for a position the account no longer holds (H1 check).
   - Optionally add a `FirmCutoff` property (1610 MFFU / 1645 Lucid). After it, refuse every order and only alert.
3. **Research:** the gold research assumed flat at 16:50 (`MINE_FLAT 1010`). Re-run `gold_curated` with flat at 16:00 to re-price these ~7.5% of trades. The effect is small and probably positive: those trades were net losers.

---

## High

### H1. Strategy position vs account position is never reconciled

**Code**
- `PositionAccount` / `Account.Positions` are not read anywhere.
- Startup is `StartBehavior.WaitUntilFlat` (`NQMaster.cs:138`, `GoldMaster.cs:101`). This syncs only to the *virtual* historical position.
- Exits use the strategy position (`ExitModule` 1130-1135, `FlattenAll` 1137-1144; GoldMaster 524-536).
- `RealtimeErrorHandling.IgnoreAllErrors` (`:140`) disables NinjaTrader's own overfill handling.

**Scenarios**
1. **Restart with a real position open.** For example, NT or the PC crashes at 05:30 while NF05 / LF0430 / REV06 are open (night modules hold 04:30-10:00). On restart the virtual history may be flat, so the strategy trades on top of a real position it does not know about. The old stop and target may still be working at the broker. When they fill they open new positions.
2. **External flatten.** This covers C1 (firm cutoff), a firm liquidation, and Federico pressing "Flatten" or "Close" on the chart or Positions tab. The strategy still believes it is in the trade, so its next time exit / 15:56 flatten / protective-rejection exit **opens a reverse position**.
3. **OCO or overfill failure** (stop and target both fill in a fast market). The account ends opposite and unprotected. Nothing detects it until 15:56, which for night modules is up to 11 hours later.

**Fix**
1. Add a per-bar realtime check. Only act on a mismatch that persists for 2 consecutive bars, so in-flight fills are not misread. Code below (C# 5).
2. On a persistent mismatch: cancel the strategy's orders, stop new entries for the session, `Print` and `Alert`. Optionally (a property) call `Account.Flatten(new[] { Instrument })` when the account holds something the strategy does not.
3. Never send `ExitModule` / `FlattenAll` orders while the mismatch flag is set.

```csharp
private int desyncBars; private bool desyncHalt;
private int SignedQty(Position p) { return p.MarketPosition == MarketPosition.Flat ? 0 : (p.MarketPosition == MarketPosition.Long ? p.Quantity : -p.Quantity); }
private void CheckAccountSync()   // call at the top of OnBarUpdate (BIP 0) in realtime
{
    if (State != State.Realtime) return;
    if (SignedQty(PositionAccount) == SignedQty(Position)) { desyncBars = 0; return; }
    if (++desyncBars < 2 || desyncHalt) return;
    desyncHalt = true; CancelAllEntries();
    Print(string.Format("NQMaster | ACCOUNT/STRATEGY POSITION MISMATCH: account {0}, strategy {1} - new entries and exits stopped. Fix the position by hand, then restart the strategy.", SignedQty(PositionAccount), SignedQty(Position)));
    Alert("nqm_desync", Priority.High, "NQMaster position mismatch - check the account", "", 60, Brushes.Red, Brushes.White);
}
```

Add `if (desyncHalt) return false;` to `CanTrade()`, and guard `ExitModule` / `FlattenAll` with `if (desyncHalt) return;`.

**Operating rule for the guide**
- Never flatten by hand while a strategy is enabled.
- In an emergency: (1) create the pause file, or disable the strategy; (2) flatten the instrument in the Positions tab; (3) confirm no working orders remain; (4) only then re-enable.
- After any crash or restart, check the Positions and Orders tabs for MNQ and MGC before enabling.
- Connection-loss setting: test on Sim with a forced disconnect while in a position. "Keep running" preserves the broker-held brackets; "Recalculate" re-runs history and can leave the account and the strategy out of sync. Choose deliberately.

### H2. Holiday, half-day and special-closure sessions

**Facts from the validation export**

NinjaTrader's template does close positions on CME half days. There are 22 "Exit on session close" trades, all at 13:00 or 13:15 ET:

| Day | Dates |
|---|---|
| Presidents' Day | 2025-02-17, 2026-02-16 |
| Memorial Day | 2025-05-26, 2026-05-25 |
| Juneteenth | 2025-06-19, 2026-06-19 |
| July 3 / 4 | 2025-07-03, 2025-07-04, 2026-07-03 |
| Labor Day | 2025-09-01, 2026-09-07 |
| Thanksgiving and the day after | 2025-11-27, 2025-11-28 |
| Christmas Eve | 2025-12-24 |

That NT exit at T-30 s is the **only** flatten on those days:
- `FlattenTime` 15:56 never arrives (`NQMaster.cs:338`).
- The code has no notion of the session's actual end.

**Problems**

1. **Rule exposure.**
   - MFFU: "During holiday trading hours, auto-liquidation will not occur … Failure to close the positions before the market closes will result in breaching of the account." Lucid: "on market holidays with altered hours you must be flat before the market close."
   - The protection is a market order 30 s before a thin close, which works only if NT's template has the right early-close time.
   - Ad-hoc closures are a real risk. The 2025-01-09 national day of mourning (equity futures halted early) is already in the research memory. If the template lacks such a closure, NT never exits, and night modules can be open into the halt.
2. **Entries right up to the close.**
   - MOM13 entered at 13:01 ET with 14 min left (2025-07-03, 2025-12-24); VW13 at 13:02 ET (2025-11-28).
   - On a 13:00 close, the final bar (closing at 13:00) still runs ManageVolb (`openMin 779 < 899`), MOM13 (`closeMin == 780`) and the 5-minute MSEQ / MSEQS block.
   - **Verify on Market Replay** (e.g. 2025-11-28 and 2025-12-24): with `Calculate.OnBarClose`, NinjaTrader raises a bar's close on the first tick of the next bar. At a session break that is the next session's first tick at 18:00. Entries from the stale 13:00 bar could then be sent in the evening session.
3. **Working entries are never cancelled at a session change.**
   - `NewSession()` (`:391-407`) clears `Parked` / `pend5` but does not cancel working orders.
   - Entries are GTC (`:139`). Normally they are all cancelled at 15:56, but on a half day nothing cancels an order placed after NT's exit-on-close.
   - ManageVolb then **keeps an old same-direction order at yesterday's level** (`:491-495`: `if (Working(volb.Entry)) { if (volb.Dir == d) return; …}`).
4. **Money** (1 contract, validation window ~20 months):

| Strategy | Holiday / half-day trades | Net | Per trade | All-days average per trade |
|---|---|---|---|---|
| NQMaster | 51 | -$1,367 | -$27 | about +$29 |
| GoldMaster | 10 | -$662 | | |

   Every module except ON07 / REV06 / LF06 lost on these sessions. The research **explicitly skipped early-close / holiday sessions for MOM11**: `research/mine/wrq_build.py`, `b_tmom`, "full session (timefill.py skipped early-close / holiday sessions)". The code traded MOM11 on 12 such days.

**Fix** (C# 5, `SessionIterator` is NT8 API)

```csharp
private SessionIterator sessIt; private int sessEndMin = 17 * 60; private bool shortSession;
// State.DataLoaded:            sessIt = new SessionIterator(Bars);
// inside if (Bars.IsFirstBarOfSession) (BIP 0), before NewSession():
CancelAllEntries(); pend5 = null; foreach (Mod m in mods) m.Retry = false;   // nothing from the last session survives
sessIt.GetNextSession(Time[0], true);
DateTime endEt = ToEt(sessIt.ActualSessionEnd);
sessEndMin = endEt.Hour * 60 + endEt.Minute;            // 17:00 normally; 13:00 / 13:15 on CME half days
shortSession = sessEndMin < 16 * 60;
// flatten: int flatMin = Math.Min(Hm(FlattenTime), sessEndMin - 5);  if (closeMin >= flatMin && closeMin < 18 * 60) { FlattenAll(...); return; }
// CanTrade(): if (SkipShortSessions && shortSession) { status = "holiday / half-day session"; return false; }   // default true
// realtime stale-bar guard (new entries only): if (State == State.Realtime && (Core.Globals.Now - Time[0]).TotalSeconds > 90) skip entries this bar
```

- Do the same in GoldMaster (`NewSession`, `:239`).
- Add a `SpecialCloseDates` list, or document that the pause file must be created before any announced ad-hoc closure.

### H3. No cap on total open contracts (MNQ + MGC)

**Code.** `Qty()` (`:860-867`) is multiplied independently in each module:
- context x2 (`CtxBoost`), confluence x2 (`LateQty`), ICT x `IctMultiplier`, VW13 `DoubleDist`;
- `EvalLateContracts`, `FundedStepUpContracts`.

Nothing limits the sum.

**Evidence.**
- Validated Ultra at 1 contract peaked at **11 MNQ open** on 2025-08-08 15:01 ET: VOLB 1, ORB60 1, ORB90 2, MOM13 1, LATE15 1, LATEFH 1, MSEQ 2, CRT11 2.
- At the recommended 2 contracts that is **22 micros**, plus MGC when gold is open.
- Daily maxima at 1 contract (NQ + gold): ≥8 on 3 of 427 days and ≥10 on 1 day. So at 2 contracts, ≥20 micros on about 1 day in 427.
- At 3 contracts (`EvalLateContracts`, or step-up with x2 boosts) it is far worse.

**Firm limits.** Lucid 50K funded starts at 20 micros (project memory). `NQMASTER_GUIA.md:187` says the worst day is "~20 micros … fits". That predates the night modules, LATE15 / LATEFH / ENG10 and VW13 x2. Depending on the firm, the excess is either rejected (a missed trade, harmless) or a rule violation.

**Fix.** Add a `MaxOpenContracts` property (0 = off; Lucid 50K funded: 20). Every entry already goes through `OfApply()` (`:1409`), so cap there and skip the entry when the result is 0. Each caller needs an `if (q <= 0) return;` before `Enter…`.

```csharp
private int OpenAndWorking()
{
    int n = Position.MarketPosition == MarketPosition.Flat ? 0 : Position.Quantity;
    foreach (Mod m in mods) if (Working(m.Entry)) n += Math.Max(0, m.Entry.Quantity - m.Entry.Filled);
    if (State == State.Realtime) foreach (Position p in Account.Positions) if (p.Instrument != Instrument) n += p.Quantity;   // MGC from GoldMaster
    return n;
}
private int CapQty(int q) { return MaxOpenContracts <= 0 ? q : Math.Max(0, Math.Min(q, MaxOpenContracts - OpenAndWorking())); }
```

GoldMaster needs the same cap: its `SendMarket` and `StopEntry` set `m.Q = Qty()`.

---

## Medium

### M1. News list: one past gap, 2027 missing, no warning

**What is wrong**
- **The 2026-10-02 08:30 Employment Situation is missing** from `BuiltinNews` (`NQMaster.cs:92`, `GoldMaster.cs:68`):
  - `research/news.py:25` skips the first-Friday fill for 2026 months > 9.
  - The manual additions in `research/mine/patch_wrq_news.py:19` list only 10-14, 11-06, 11-10, 12-04 and 12-10.
  - BLS confirms 2026-10-02 08:30.
  - The date has passed, but any October-2026 backtest or comparison with `NewsBlackout` on is off by one event, and it shows the list was assembled by hand.
- The built-in CPI/NFP list ends **2026-12-10**. FOMC minutes run to 2027-12-29. FOMC days run to 2028-01-26; the Fed calendar matches, and the next date after that is not published.
- Nothing warns when the list runs out. Unparsable `NewsTimes` / `FomcDates` tokens are dropped silently (`:178-183`), e.g. "2027-01-08 8:30" fails the `HH:mm` format.

**BLS 2027 schedule**
- Published; last modified 2026-10-09.
- Verified directly on the January, May, June, November and December pages. The other months come from the 2027 summary page and the search snippet; check them once against bls.gov.
- Paste into `NewsTimes` on both strategies:

```
2027-01-08 08:30,2027-01-13 08:30,2027-02-05 08:30,2027-02-11 08:30,2027-03-05 08:30,2027-03-10 08:30,2027-04-02 08:30,2027-04-13 08:30,2027-05-07 08:30,2027-05-12 08:30,2027-06-04 08:30,2027-06-10 08:30,2027-07-02 08:30,2027-07-14 08:30,2027-08-06 08:30,2027-08-11 08:30,2027-09-03 08:30,2027-09-14 08:30,2027-10-08 08:30,2027-10-14 08:30,2027-11-05 08:30,2027-11-10 08:30,2027-12-03 08:30,2027-12-10 08:30
```

**Fix**
- Add these dates to `BuiltinNews`.
- Add a start-up check in `State.Realtime`. If `NewsBlackout` is on and the last 08:30 event is less than 35 days ahead, `Print` a warning and show it on the dashboard. Also print every unparsed token.

### M2. The stale-order watchdog can drop orders that are still live (realtime)

**Code.** `PurgeStaleEntries` (`NQMaster.cs:1221-1238`, `GoldMaster.cs:556-571`) drops an order 2 bars after an unconfirmed cancel or a non-acceptance. `DropStale` clears `m.Entry` and the order is no longer counted by `DirectionAllowed` / `OppBusy` / `ManageVolb`.

**Why it matters.**
- In a backtest this is correct; it fixed the 14-month "no shorts" bug.
- In realtime, an order stuck in `CancelPending` / `Submitted` for 2 minutes usually means a broker or connection delay. The order may still rest at the exchange and fill later.
- Meanwhile an opposite entry has been allowed. A managed entry in the opposite direction then nets against or reverses the position. The brackets of both entries are live, and the result can be an unprotected position.

**Fix.** In realtime, do not release the block.
- Keep zombies in the opposite-direction checks while `Working(z)`, e.g. in `DirectionAllowed` / `OppBusy`:
  `foreach (Order z in zombies) if (State == State.Realtime && Working(z) && ((z.OrderAction == OrderAction.Buy) ? 1 : -1) == -d) return false;`
- Raise an `Alert`.
- Optionally stop new entries until the zombie reaches a terminal state.

### M3. `InTrade` is cleared by the first protective fill of a multi-lot entry

**Code.** `NQMaster.cs:1305-1306`: `if (from != null && execution.Order.OrderState == OrderState.Filled) from.InTrade = false;`. GoldMaster has the same at `:619-620` and treats further entry fills as "already in trade" at `:609`.

**Scenario.**
- `StopTargetHandling.PerEntryExecution` creates one stop and one target per entry execution.
- With 2-contract settings, or any x2 boost, a 2-lot market or limit entry filled as 1 + 1 gets two separate stop/target pairs.
- When the first target fills, the module is marked flat while one lot is still open. Its time exit (`:339-342`, LON 09:30 exit `:356`, VOLB / ENG10 hold) no longer fires.
- The lot is then held to its stop/target or 15:56: longer than researched, and through the 08:30 releases on Lucid.
- A later fill of the same entry order counts as a "first fill" again: `orb.Trades++`, `onSum`, `ictTrades`.

**Fix.** Track open quantity per module: add `public int OpenQty;` to `Mod`. In `OnExecutionUpdate`:
- entry branch: `m.OpenQty += quantity`;
- exit branch: `from.OpenQty = Math.Max(0, from.OpenQty - quantity); if (from.OpenQty == 0) from.InTrade = false;`;
- set `first = m.OpenQty == quantity`;
- reset `OpenQty` wherever `InTrade` is reset on flat.

### M4. Prop-state robustness (cushion can be overstated)

1. **The state file is per PC.** `nqmaster_prop_<account>.txt` lives in `Documents\NinjaTrader 8` (`PropFile`, `:973`), and Federico has a second PC.
   - If the strategy runs on PC2 for a while and then on PC1, PC1's file is stale.
   - If the file's date is still ≥ `EvalStartDate`, its lower peak is accepted (`:991-993`), so `propThr` is too low and **the cushion is too high**.
   - The gate can then pick FULL, and `StepUpOn` (`:859`) 2 contracts, while the real cushion is thin. This is the non-conservative direction.
   - Fix (operational): after switching PCs, set `PropThresholdOverride` (or `PropPeakOverride`) from the firm dashboard for the first session.
   - Fix (code): a `PropFolder` property, so the file can sit in a synced folder (OneDrive), plus a start-up `Print` of the computed threshold so it can be compared with the dashboard.
2. **Mid-session restart.**
   - `PropGoLive` → `PropSessionStart` uses `eq = Account CashValue` *now*, including today's realized P&L. It does `if (eq > propPeak) propPeak = eq;` (`:1022`), persists that (`:1023`), and gates on `propCushion = eq - propThr` (`:1026`).
   - So intraday cash becomes the "end-of-day peak". That is conservative for the threshold, but the cushion is non-conservative for step-up: a +$1,000 morning can switch to 2 contracts mid-day.
   - Fix: when `propRestoredDay == tday`, use `propDayStart` instead of `eq` for both the peak update and the cushion.
3. **`RealizedProfitLoss`.** `propDayStart = Cash - Account.Get(RealizedProfitLoss)` (`:1005`; GoldMaster `:151`) assumes that item is *today's* realized P&L and that it resets at the session boundary. Verify once on the live connection (Tradovate / Rithmic). If it is cumulative, a mid-day start hits `EvalProfitStop` at once.
4. **Best day lost.** If NinjaTrader was off for a whole session, the best day is only recovered from the immediately previous session (`:995`). An under-counted best day under-states the consistency target, so `targetHit` can latch "eval target reached" and stop trading before the firm considers the eval passed.
   - Document: set `EvalBestDaySoFar` after any gap.
   - Print `need` on the dashboard.

### M5. Contract rollover: no guard, no procedure

**Situation.** The strategy runs on a fixed contract (MNQ 12-26, MGC 12-26). Nothing detects NinjaTrader's roll date, and neither guide mentions rolling. A search for "roll" / "vencim" finds nothing.

**Risks**
- Trading a thinning expiring month for about 8 days after the roll date.
- The MNQ 12-26 final settlement is 09:30 ET on 2026-12-18. NF05 / LF06 / REV06 positions can be open then.
- If the merge policy is not "Merge back adjusted", the history before the roll is on another price basis. ICT levels (prior-day high/low), the ORB prior-close filter (`OrbPriorCloseAtr`) and the gap features then break on the roll day; the true range is inflated by the roll spread (~1% for NQ).

**State that carries over.** The prop file (keyed by account), so the roll itself is safe. The edge-monitor and history state are rebuilt from the loaded bars.

**Procedure for the guide.** On the NinjaTrader roll date (MNQ / MGC Dec-26 → Mar-27: around 2026-12-10), after 16:00 ET and before 18:00 ET while flat:
1. Disable both strategies.
2. Re-enable them on the new month, same account and settings, Days to load ≥ 45 / 120.
3. Check "Merge back adjusted" under Tools > Options > Data.

**Code guard.**
- At `DataLoaded`, and at each realtime session start: if a rollover entry in `Instrument.MasterInstrument.RollOverCollection` has `ContractMonth > Instrument.Expiry` and `Date <= Core.Globals.Now`, the contract has rolled.
- Then: `CanTrade()` returns false, the dashboard shows "contract rolled, move to <next>", and `Alert()` fires.
- Check the member names compile; they are NT8 `Rollover.ContractMonth` / `.Date`.

### M6. Logging and alerting are not enough for a bad-day post-mortem

**What is logged now**
- Everything goes through `Print` (`Log`, `:1338`), which lands in the Output window and is gone after an NT restart.
- No line is written when a stop or target fills: no exit price, P&L, or account cash / unrealized at that moment.
- VOLB, the largest-risk module, never logs its stop placement, side switches or cancels (`:478-513`). Only fills are logged.
- No `Alert()` anywhere: STALE ORDER, REJECTED, edge alarm, prop stops, target reached.
- NQMaster gives no warm-up warning in realtime and shows "trading" while `atrCount < AtrMin` (GoldMaster does warn, `:159`, `:671`).
- On every enable, `PrintLog` replays all of history into Output, so live lines get buried.

**Fix**
1. Append each `Log` line in realtime to `Documents\NinjaTrader 8\nqmaster_logs\<account>_<yyyyMMdd>.txt` (`File.AppendAllText` in `try`). Prefix history lines with `[H]`, or do not print them.
2. Log exits in `OnExecutionUpdate` (exit branch): module, order name, price, qty, plus `Account` cash / unrealized.
3. Add a VOLB placement log.
4. Raise `Alert(...)` for: rejections, stale orders, the H1 mismatch, prop stops, the edge alarm, target reached.
5. Add an NQMaster realtime warm-up warning, mirroring GoldMaster's.
6. Print the version (and a parameter hash) at start-up.

### M7. Restart state comes from virtual history

**What happens**
- `edgeS` / `edgeDays` (`:920-952`) are recomputed from virtual history trades on every enable. Only days inside "Days to load" count.
- With Days to load 45, after about 2 months the live CUSUM silently "forgets" its early days. It may never alarm, or alarm on simulated rather than real fills.
- `dayStartPnl` (`:279`) and `DailyLossLimit` (`:832-836`) mix virtual pre-restart P&L with live P&L on a restart day. `DailyLossLimit` is 0 by default.

**Fix.** Persist `edgeS`, `edgeDays` and the last counted date to a file in realtime, and restore them at go-live, the same way the prop file is handled.

### M8. No intraday liquidation guard relative to the EOD threshold

**Situation**
- The computed threshold `propThr` (`:1024`) is used only for gating at the session start.
- The optional `MaxDrawdown` guard (`:1127`) trails intraday cash from strategy start. That is the wrong model for EOD-trailing firms.
- Worst validated day at 1 contract (NQ + gold): **-$2,191 on 2026-08-28**. NQ alone -$1,749.
- At 2 contracts, one bad day can take a fresh account through its $2,000 threshold, and at these firms any intraday touch of the threshold is a bust.

**Suggestion.** An optional `PropLiquidationBuffer` (e.g. $150): in realtime, if `Cash + Unrealized <= propThr + buffer`, `FlattenAll` and stop the day. That turns some busts into near-misses and backstops software failures such as H3. Quantify it first with the existing minute-path account simulations; the research found daily *loss stops* neutral, but this is a different, edge-only trigger.

---

## Low

- **L1 – Rejection loops.**
  - After a rejection, VOLB re-submits a stop every bar until 15:00 (`ManageVolb`, `Working(volb.Entry)` is false after the rejection, `volbDone` stays false).
  - If the account is liquidation-only or disabled after a breach, every module and `FlattenAll` keep sending rejected orders.
  - Fix: count rejections per module per day and disable the module after 2. A rejection reason containing "liquidat" / "disabled" / "margin" stops all new entries.
- **L2 – Gate change without cancelling orders.**
  - At a mid-session restart, `PropGoLive` → `PropSessionStart` (`:1036-1039`) can switch modules off while their live order is still working.
  - `ManageVolb`, `ManageEng10` and the ICT invalidation only run when the module is `On`, so the order is unmanaged until 15:56. `ManageParked` also re-places parked orders of modules that are off.
  - Fix: when `On` turns false, `CancelEntry(m); m.Parked = false;`.
- **L3 – Exact-minute triggers.**
  - These need a bar at an exact minute: `closeMin == Hm(m.Time)` (`:380`), ORB `OrReady` at `openMin == RthOpen + Range - 1` (`:325`), CRT `openMin == 719` (`:383`), ENG10 `openMin != 599` (`:525`).
  - A missing 1-minute bar (data gap, reconnect) silently skips the trade or the whole ORB day.
  - Fix: use `>=` with a Done flag, and log the skip.
- **L4 – Silent time-zone / template fallbacks.**
  - `ToEt` falls back to chart time if the conversion fails (`:1330-1335`). For a user in Argentina that would shift every module by 1-2 h.
  - Nothing checks that the chart uses the ETH trading-hours template; a 24/7 or RTH template breaks the session logic silently.
  - Fix: print and refuse to trade if `etZone == null`, or if `Bars.TradingHours.Name` does not contain "ETH".
- **L5 – GoldMaster hard-coded drawdown.**
  - GoldMaster hard-codes a $2,000 trailing drawdown and a $2,100 lock in its eval and step-up cushions (`GoldMaster.cs:354, 374`). For 100K/150K accounts the values are wrong, though in the conservative direction.
  - Fix: add a `PropTrailingDD` property as in NQMaster. `StartBalance` must also be set per account size.
- **L6 – Parameter validation.**
  - `Range` attributes accept invalid HHmm values (`FlattenTime` 1075, `VolbTrendLastEntry` 1090).
  - GoldMaster has duplicate display `Order = 15` (`:735`, `:741`).
  - NQMaster `EvalTarget` with `PropMode = Off` ignores consistency, because `propDayStart` stays NaN (`:1116`).
- **L7 – `ChangeOrder` in managed mode.** The order-flow re-sizing calls `ChangeOrder` on managed entry orders (`:1428`); NT documents it for the unmanaged approach. The boost is default off and failed out of sample, so keep it off. If ever revived, re-size by re-calling the `Enter…` method with the same signal.
- **L8 – Cosmetic.** The dashboard total mixes virtual history with live trades (`:1345`). The `LF0430` time exit lands at about 08:31 on CPI / NFP days when `NewsBlackout` is off (Lucid), as in the research.

---

## Checked and fine

- **Time conversion and DST.**
  - `ToEt` converts from NinjaTrader's general time zone (Argentina) to ET with `TimeZoneInfo`. The export times confirm the setting.
  - US DST changes happen on Sundays at 02:00 ET while CME is closed, so no session has ambiguous ET times.
  - The Europe/US DST-mismatch weeks do not matter, because modules and research both use ET clock times.
- **Session dating.** Sunday 18:00 sessions map to Monday (`tradeDay`, `:283`). FOMC skip covers the evening before (session-based). The CME maintenance hour is covered: the bar closing at 17:00 falls inside the 15:56-17:59 flatten branch, and GoldMaster returns during 17:00-18:00.
- **Normal-day flatten.** 15:56 / 16:51 plus NT's `IsExitOnSessionCloseStrategy` backstop at T-30 s. In the export, no NQ trade exits after 16:00 and none crosses a session.
- **Sessions without a complete RTH day.**
  - `full1` = NaN chain (`:281-282`, `:430`).
  - Partial days still feed ATR / trend. That differs from the research artifact, and NT validation gave +$1,149 in those windows.
- **`ExitModule` + `Position.Quantity` + `fromEntrySignal` closes only that module.** In the export, all 261 "<Sig>X" exits belong to their own entry; 0 cross-module.
- **Stop/target re-arming and opposite-direction guards.**
  - Every entry path re-arms its stop/target (`SetStopLoss` / `ArmPriceBracket`) immediately before entering, including parked and deferred re-placements. Stale per-signal stop prices cannot carry across days.
  - `DirectionAllowed` / `OppBusy` / the ManageVolb checks keep opposite entries from coexisting, so a managed `Enter` can never reverse a position.
- **Rejected orders.** A rejected protective order exits its module; any other rejected exit flattens, guarded once per bar; a rejected entry is skipped. A fill beyond the stop exits at once (`:1298`).
- **No exception paths found.**
  - Series indices are bounded (`CurrentBars[1] >= 8`, `CurrentBars[0] > Lookback`, ICT `j + 1 <= CurrentBars[1]`).
  - `Account` is touched only in realtime or inside `try`.
  - File I/O is in `try`.
- **Numeric safety.**
  - NaN and divide-by-zero are guarded (ATR, VWAP, RSI, CUSUM, consistency `need`).
  - Prices are tick-rounded (`RoundToTickSize` / `RoundDownToTickSize`, OR / candle extremes are traded prices). Tick stops have minimums of 8 / 4 ticks.
- **Research parity.** `Close[Lookback-1]` (ON07 / REV06) matches the research `c[ei-L]` (`tmom.py`). The MOM11 VWAP agreement matches `wrq_build.py`. Time exits match `tmom.sim`.
- **FOMC list.** The built-in list matches federalreserve.gov through 2028-01-26. FOMC minutes 2026-27 = decision + 21 days are correct. The Nov / Dec 2026 CPI and NFP dates match BLS.
- **News window.** Flat on the bar closing at T-3 (before T-2:00); entries resume with the bar closing at T+2. The 5-minute series is blocked for entries that would straddle the release. FOMC days are fully skipped.
- **Prop file I/O.** Uses `InvariantCulture` (safe under the Spanish locale). GoldMaster ignores files older than `EvalStartDate`. The NQ/Gold read-write race at 18:00 fails safely: catch, then fall back to own data.
- **Watchdog in backtests.** It never touches healthy orders: `Accepted`, `Working` and `TriggerPending` are not dropped, and a market order is checked only after ≥2 bars.
- **`WarmupDays` is behaviour-neutral at defaults** (diff against `*_backup_pre_warmup.cs`):
  - NQMaster: `AtrMin = min(14, 15) = 14` and `TrendMin = min(15, 15) = 15` replace the literal 14 / 15 in every check (ORB, VOLB, ENG10, time modules, CRT, LON, MSEQ, RSI2, ICT, `FeatTrend`). The ATR ramp (`k = min(atrCount, 14)`) is unchanged. Only the end-of-run message text changed.
  - GoldMaster at 60: the ATR divisor stays 14, trend needs `min(20, 60) = 20` closes, and `AtrOk` needs `closes >= min(15, 60) = 15` and `rthDays >= 60`. Identical to before.
- **The order-flow code is behaviour-neutral at its default (off)** (`UseOrderFlowBoost = false`):
  - `OnMarketData` returns on its first statement.
  - `OfApply` returns `q` unchanged (`OfQty` early return).
  - `OfRefresh` / `ChangeOrder` are never called (`:372`).
  - `ParkOrder` uses `e.Quantity`.
  - The watchdog's size-change branch needs `OfChangeOrd == e`, which stays null.
  - The fill counters, dashboard line and end-of-run print are all gated.
- **NinjaTrader validation.** It already reproduced the research at 95.7% of trades and identical matched dollars. The findings above are operational and edge cases that a backtest does not exercise: firm cutoffs, restarts, manual actions, rollover, half days, live broker latency.

## Suggested order of work

1. **Today (settings only):**
   - GoldMaster `FlattenTime 1600` on every MFFU / Lucid account (C1).
   - Paste the 2027 `NewsTimes` (M1).
   - Write the manual-flatten / restart / roll procedure into the guides (H1, M5).
   - On the PC that runs live, keep the prop file current, or set `PropThresholdOverride` after switching PCs (M4).
2. **Next code release:**
   - Account sync check + halt (H1).
   - Session-end awareness: cancel entries at session start, skip and flatten short sessions, stale-bar guard (H2).
   - `MaxOpenContracts` (H3).
   - Per-module open quantity (M3).
   - Realtime watchdog hold (M2).
   - File log + `Alert` (M6).
   - Then compile, re-run the Strategy Analyzer regression with `nt_compare.py`, and test on Market Replay over 2025-11-28 / 2025-12-24 and a roll date.
3. **Later:** persist the edge monitor (M7); research the liquidation-buffer guard (M8); the Low items.

## Sources (accessed 2026-10-12)
- BLS release calendar 2027: https://www.bls.gov/schedule/2027/home.htm (month pages /2027/01_sched_list.htm … /12_sched_list.htm)
- BLS October / November / December 2026: https://www.bls.gov/schedule/2026/10_sched_list.htm, https://www.bls.gov/schedule/2026/11_sched_list.htm, https://www.bls.gov/schedule/2026/12_sched_list.htm
- Federal Reserve FOMC calendars: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
- MyFundedFutures, "Permitted times to trade": https://help.myfundedfutures.com/en/articles/9558251-permitted-times-to-trade
- Lucid 4:45 PM ET cutoff: project survey `research/mine/propfirms_2026.md:11, 26`; third-party: https://proptradingvibes.com/blog/lucid-trading-allowed-trading-times
