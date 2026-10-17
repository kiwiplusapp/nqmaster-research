# Code review 2026-10-17: VolbReArm, funded size ladder, DailyLossPerContract

Scope: `diff NQMaster_backup_pre_volbrearm.cs NQMaster.cs` (all three features), checked against `research/mine/reentry_lab.py` (VOLB_RE_E),
`ladder_plan.py`, `ladder_stop.py` and `seats_plan.paths`. Line numbers refer to the current `NQMaster.cs` (2,231 lines).

- `bash tools/nt8_stub/check.sh NQMaster.cs`: clean (exit 0).
- C# 5: no string interpolation, no `=>` members, no `nameof`, no `?.`; all new text uses `string.Format`.
- The UTF-8 BOM on line 1 is already in HEAD, so it is harmless.

No Critical findings. The VolbReArm logic matches the research rule. The ladder is fixed for the whole day in steady state. The main gaps are research-vs-code mismatches that make live results come in below the research numbers, plus one start-up sizing hole.

## Severity-ranked findings

### HIGH

**H1. The research ladder scales GOLD with k, but the code and the recipe do not. The recipe also leaves out SixYearModules.**
- In research, `seats_plan.paths` adds the gold Robust path into the base component `a` (line 50: `a = (a[0] + g[0], ...)`). Then `ladder_plan.gears` builds `FL/FC = k * full` for k = 1..4. So the simulated account trades gold at k MGC (up to 4), not at 2.
  - This corrects the premise that gold "should not exceed 2 per the sim".
- GoldMaster has no ladder. `GoldMaster.Qty()` returns `FundedStepUpContracts` (default 2) only if its own `FundedStepUpCushion` is set. Otherwise it returns `Contracts` (1).
- The ladder recipe in RUNBOOK_OPERACION.md line 21 and NQMASTER_GUIA.md 2b/2c does not mention GoldMaster at all.
- It also does not mention `SixYearModules = true`. The research set is "Ultra+six+gold", and SixYearModules defaults to OFF.
- Effect on income: gold Robust is roughly 14-16% of per-contract P&L. At k = 4 with gold at 2, the code earns about 7% less than the research; with gold left at 1, about 10% less. The research daily stop (ladder_stop) also counted gold P&L.
- Without the six-year modules, the guide's own number is $163-217/day instead of $214-288/day.
- Fix (recipe, one line in the runbook row): `SixYearModules true; GoldMaster Robust, FundedStepUpCushion 3000, FundedStepUpContracts 2 (gold capped at 2: ~7% below the research ladder at 4c)`.
- Alternative: port the ladder to GoldMaster, `GoldMaster.cs:504`: `return Math.Min(FundedLadderMax, FundedStepUpContracts + (int)Math.Floor((stepCushion - FundedStepUpCushion) / Math.Max(1, FundedLadderStep)));`. Note that gold at 4 MGC also counts toward the MFFU 30-micro cap (see M2).

### MEDIUM

**M1. At go-live, working entries keep the size computed from the HISTORICAL cushion** (lines 373-384).
- During history, `PropEquity()` (line 1594) is `StartBalance + netPnl` of the loaded backtest. 45+ loaded days of Ultra often make more than $3k, so the historical ladder already sits at 2-3 contracts per module.
- At `State.Realtime`, entries still working are carried over with `GetRealtimeOrder` (line 380) at their historical quantity. Only then does `PropGoLive()` (line 384) recompute `propCushion` from the real account.
- Result: a VOLB / ORB stop or a LON / ICT limit placed earlier in the session can go live at 2-4x (MOM1030 x4 → up to 16 lots) on an account whose real cushion says 1 contract with the $300 risk cap.
- This hole already existed for the old step-up (max 2). The ladder makes it up to 4x larger.
- Fix (one line after `PropGoLive();`, with `int hq = Qty();` saved just before it): `if (Qty() != hq) foreach (Mod m in mods) if (Working(m.Entry)) ChangeOrder(m.Entry, Math.Max(1, m.Entry.Quantity * Qty() / Math.Max(1, hq)), m.Entry.LimitPrice, m.Entry.StopPrice);`

**M2. MaxOpenContracts 30 truncates entries at k = 4, but the research ladder is uncapped.**
- Research open positions only (six_ultra6_trades, 2020-26, with MOM1030 / CPI09 / x2 weights), max simultaneous lots per day:

  | k | p50 | p99 | max | days > 30 | days > 26 |
  |---|---|---|---|---|---|
  | 1 | 3 | 8 | 11 | 0% | 0% |
  | 3 | 9 | 24 | 33 | 0.14% | 0.74% |
  | 4 | 12 | 32 | 44 | 1.4% | 4.0% |

- `OpenAndWorking` (line 229) also counts the unfilled quantity of working entry orders and, in realtime, the MGC position. So `CapQty` cuts entries on more days than the table shows.
- Those days are the high-concurrency, mostly big-trend days, which are the best ones. `ladder_plan`'s "K <= 4 because of the 30-micro cap" is therefore not neutral at K = 4.
- Fix: no code change needed. After the NT run, check the dashboard line "Max open contracts 30: N entries cut". If cuts exceed about 2% of days, compare against `FundedLadderMax 3` (research: $165/205 per day in years 2-3, 0.16/0.45 busts per year).

**M3. DailyLossPerContract measures the strategy only, at bar close, while the research measured the whole account at the minute extreme** (lines 1227-1238).
- Research (`ladder_stop.gears_stop`):
  - The stop is on the account path (NQ + gold).
  - It triggers on the minute LOW path (`lo <= -L`).
  - The day ends at exactly -L x k.
- Code:
  - `netPnl - dayStartPnl` plus `Position.GetUnrealizedProfitLoss(.., Close[0])` covers this strategy's MNQ only.
  - The check runs once per closed 1-minute bar (Calculate.OnBarClose, BIP 0) and exits at the next bar's open.
  - Gold keeps trading after the stop.
  - After a mid-session restart, `netPnl - dayStartPnl` includes today's virtual historical trades and not the real ones. `dayStartPnl` is set on the historical first bar and is not re-aligned in `PropGoLive`.
- `PropDailyCheck` (lines 1673-1682) already does the right thing in realtime: account `CashValue + UnrealizedProfitLoss - propDayStart`, restored across restarts. Funded mode there is hard-wired to no loss stop.
- Fix (line 1677): `double lossStop = evalMode ? EvalDailyStop : (PropMode == NQMasterPropMode.Funded && DailyLossPerContract > 0 ? DailyLossPerContract * edgeDayQty : 0);` Then drop the per-contract term from `DailyLossCheck`.
- Optional (line 1236), to mirror the research trigger: `open = Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Position.MarketPosition == MarketPosition.Long ? Low[0] : High[0]);`
- GoldMaster still would not stop. Either set GoldMaster `AccountDailyStop` to about 1500 x expected k, or accept the gap.

**M4. Silent change of an existing setting: `DailyLossLimit` now includes open losses in every mode** (line 1236).
- Before today the check was realized-only, as the comment at lines 1224-1225 still says ("session's realized P&L").
- The property text "eval: 800, funded: 500" (line 2173) comes from research that used that semantics.
- Anyone running `DailyLossLimit > 0` without the new feature now gets earlier stops. That breaks the "all three features opt-in" claim.
- Fix (line 1236), so open P&L only counts with the new feature: `if (Position.MarketPosition != MarketPosition.Flat && DailyLossPerContract > 0 && PropMode == NQMasterPropMode.Funded) { ... }`

**M5. The Strategy Analyzer cannot reproduce the research ladder** (no withdrawals or busts in history, line 1594).
- In history, `PropEquity = StartBalance + netPnl` never pays out.
- Once the cushion passes $9k, the backtest stays at 4 contracts through drawdowns where the research account, kept at $11.1k, drops to 3. The backtest also never "busts".
- NT P&L and DD at 4c will therefore look better than research. The runbook's "Strategy Analyzer before use" checks the mechanics only, not the numbers.
- Fix (optional): add a `histPaid` field, have `PropEquity` return `StartBalance + netPnl - histPaid` in history, and in `PropSessionStart` add `if (State != State.Realtime && PropMode == NQMasterPropMode.Funded && FundedPayoutAt > 0 && eq - StartBalance >= FundedPayoutAt) { histPaid += eq - StartBalance - (FundedPayoutAt - 500); eq = PropEquity(); }`.

### LOW

**L1. A missing FundedPayoutAt silently caps the ladder at 2.**
- With the ladder on, the Mffu50K preset (line 206) no longer sets FundedPayoutAt. The property default is 5000 (line 324).
- If Federico forgets the 11600, the dashboard (line 2007) tells him to withdraw down to $4,500. The cushion then never exceeds about $4.4k, so the ladder stays at 2.
- Fix (line 206): `if (FundedLadderStep > 0) FundedPayoutAt = Math.Max(FundedPayoutAt, FundedStepUpCushion + (FundedLadderMax - FundedStepUpContracts) * FundedLadderStep + 2600);` This gives 11,600 for the 3000/2/3000/4 recipe (2,000 DD + 100 lock + 500 minimum payout above B).

**L2. The ladder is silently off in two cases** (lines 1261, 1276):
- `FundedStepUpCushion = 0`. The LucidPro25K / FundedNext25K presets force it to 0 (line 201).
- `EvalMode = true`, because `Qty()` returns the eval branch before `StepUpOn`.
- Fix (end of `ApplyPreset`): `if (FundedLadderStep > 0 && (FundedStepUpCushion <= 0 || EvalMode || PropMode != NQMasterPropMode.Funded)) Print("NQMaster | WARNING: FundedLadderStep is set but the ladder is off (needs PropMode Funded, FundedStepUpCushion > 0, EvalMode false)");`

**L3. `FundedLadderMax` below `FundedStepUpContracts` is ignored** (line 1272). `Math.Max(FundedStepUpContracts, Math.Min(FundedLadderMax, k))` returns FundedStepUpContracts, which is above the "max".
- Fix: `return Math.Min(Math.Max(FundedLadderMax, 1), Math.Max(FundedStepUpContracts, k));`

**L4. The DailyLossCheck limit uses `Qty()`, which can change during the day** when `AdaptiveSize` is on in Funded without step-up: SizeHigh → SizeLow after closed losses. The limit then shrinks right after losses and can trip at once.
- With the ladder, `Qty()` is fixed for the day, so the recipe is not affected.
- Fix (line 1233): `lim = Math.Max(lim, DailyLossPerContract * edgeDayQty);` (`edgeDayQty` is set after `PropSessionStart`, line 550).

**L5. `Math.Min(0, open)` ignores open profit** (line 1237). The research stop used total day equity. With -$1,600 realized and +$300 open, the code stops at day equity -$1,300 against a $1,500 limit.
- Conservative, but it differs from ladder_stop.
- Fix: `if (netPnl - dayStartPnl + open <= -lim)`

**L6. VolbReArm is not limited to the 2R VOLB the research tested** (line 1947). It checks `!volbTrendOnly` but not `volb.R`. A Custom profile with a non-2R, non-trend-only VOLB would re-arm without research behind it. The break-even rule at line 612 guards with `volb.R >= 1.5`.
- Fix: add `&& volb.R >= 1.5` to the condition at line 1947.

**L7. VolbReArm after a partially filled entry.**
- If the VOLB entry is PartFilled and the "Stop loss" closes the filled part, `OpenQty` reaches 0 and VOLB re-arms while `volb.Entry` (the remainder) is still working.
- `ManageVolb` then keeps or cancels that remainder (line 774). If it fills later, it counts as the second trade (`volbTrades` = 2) at the old size.
- Rare in practice: stop-market MNQ entries almost never part-fill at these sizes.
- Fix (line 1947): add `&& !Working(volb.Entry)` to the condition.

**L8. A payout requested intraday leaves that day's size on the pre-withdrawal cushion.** The research withdraws at day end.
- Fix: add " after the 16:00 close" to the PAYOUT dashboard text (line 2007).

**L9. Duplicate property `Order` values make the property-grid order ambiguous:**
- `FundedLadderStep` / `FundedLadderMax` (Order 18/19, group 07) collide with `RiskCapPerContract` / `EvalRiskCapCushion` (lines 2114-2115, 2222-2223).
- `DailyLossPerContract` (Order 47, group 03) collides with `MinAtrPoints` (lines 2174-2175).
- Fix: renumber to 26/27 in group 07 and 48 in group 03.

### INFO / verified OK

- **(a) Ladder size is fixed for the day.**
  - `propCushion` is assigned in one place only, line 1645 in `PropSessionStart`. That runs on `Bars.IsFirstBarOfSession` (line 549) and in `PropGoLive` (line 1626).
  - When state is restored, `eqRef` is the saved day start, so the ladder uses the day-start cushion as in `fu_ladder_m`.
  - Every `Qty()` call site works within the session and sees the same value: CtxBoost, LateQty, HwQty, TooBig, TimeEntry, ORB, VOLB, ENG10, LON, RSI2, ICT, OfApply, SIZE log, dashboard, DailyLossCheck, edgeDayQty.
  - `StepUpOn` ignores AdaptiveSize.
  - The only intraday change is the go-live switch (M1).
- **Formula equivalence.** The code's `FundedStepUpContracts + floor((c - FundedStepUpCushion) / Step)`, capped at Max, equals research `1 + floor(c / S)` capped at K only when all of these hold: Contracts = 1, FundedStepUpContracts = 2, FundedStepUpCushion = FundedLadderStep = S. The recipe meets this.
  - The research low gear (1c with the $300 cap below a $2,000 cushion) equals the Mffu50K risk cap; the cap is never active while the ladder is.
  - Funded x4 MOM1030/CPI09 = `4 * Qty()`, the same as research `k * (a + 4b)`.
- **EvalHighWrMultiplier / HwQty** only applies in Eval; the ladder only in Funded.
- **TooBig** divides by `Qty()`, so the $300 cap stays per base contract at any rung.
- **Daily loss stop blocking (d).**
  - `DailyLossCheck` runs only on BIP 0 (line 515 routes BIP 1 to `OnFiveMinute`), so `Close[0]` is the 1-minute primary series.
  - `FlattenAll` cancels every working entry and clears parked setups (`CancelAllEntries`, line 1765), then exits the position.
  - `dayStopped` makes `CanTrade()` false (line 1723). The 1-minute path then cancels entries and returns before pend5, parked orders, retries and every module (lines 627-628). `OnFiveMinute` also checks `CanTrade()` (line 1086).
  - The reset happens only at the next session's first bar (line 538).
- **Presets** are applied in `State.DataLoaded` (line 360) after the user's property values. Defaults (lines 320-326) keep all three features off. The preset `Print` (line 210) does not list FundedLadderStep / Max, DailyLossPerContract or FundedPayoutAt; adding them would make the Output self-documenting.
- **(e) VolbReArm matches VOLB_RE_E** (`reentry_lab._volb_re` + `wrq_lib.xsim`):
  - Research re-arms only on exit reason 0 (original stop). Reason 3 (BE / moved stop) is excluded, matching `!volbBeSet`. The code sets `volbBeSet` at the bar close and the stop modification takes effect from the next bar, the same order as xsim (stop checked before the BE move).
  - The new stop order is placed at the close of the exit bar, so it is active from bar xi+1 as in research.
  - Same levels (RTH open ± 0.45 x prior range), stop at the RTH open, either side.
  - The 15:00 cut-off matches (`openMin >= 899` cancels; research `sm >= 1500`).
  - The second trade gets fresh `EntryBar` / `volbBeSet` / ArmPriceBracket.
  - `volbTrades < 2` plus the increment on first fill (line 1918) and the reset in NewSession (line 674) allow at most one re-arm per day. The BE stop, the time exit ("VOLBX"), FlattenAll ("Exit"), the daily-loss flatten and a rejected-stop ExitModule never re-arm.
  - `"Stop loss"` is NT8's managed name for `SetStopLoss` orders. The existing rejection handler at line 1895 uses the same string.
  - TooTight / TooBig cannot newly fail on the second attempt (same level, same day-fixed cushion). PastLevel and its market path set `volbDone = true` with no loop.
  - VOLB is never parked (`ParkOrder`, line 1777); an opposite fill just cancels it and ManageVolb re-places it, as on the first attempt. `deferUntil` and the zombie watchdog treat the second order like the first.
  - Parity sets (`ultra_r`, `ultra6`) do not contain re-armed trades, so keep VolbReArm OFF in the parity run.
