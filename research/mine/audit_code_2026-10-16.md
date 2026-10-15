# NQMaster.cs code review, 2026-10-16 (read-only)

Scope: `NQMaster.cs` (1,901 lines). The focus was on code added since 2026-10-14 (CPI09, the size multipliers, the health report, DisableModules, the edge-alarm fallback and the Mffu50K preset) and on the critical order and account paths.

Method:
- Read the whole file.
- Checked every finding against the surrounding code. Where a finding claims that the code differs from research, also checked the research script (`sniper_life.py`, `sniper_uniform.csv`, `robust2_build.py`, `os_adapt.py`, `month80.py`).
- Type-checked as C# 5 with `mcs -langversion:5` against the NT8 API stub (`scratchpad/stub/s0.cs`): **0 errors**. The file has not been compiled in NinjaTrader.

## Findings

| id | severity | file:line | description | concrete failure scenario | suggested fix |
|---|---|---|---|---|---|
| F1 | **high** | NQMaster.cs:850-853, 1176-1185 | The risk cap measures CPI09 / MOM1030 risk **after** the x4 / x8 multiplier. `TooBig` gets `tq = 4 x Qty()`, so per-base risk = 4 x the 1-lot risk. The research that shipped x4 in funded accounts (`sniper_life.py` l.35-36: `S1 = T[S].assign(w=1.0)`, `S1.risk / S1.w <= cap`) caps the **1-lot** risk and then multiplies the trade by m. The x2 boosts (ICT, ctx) do include the weight in research too (`robust2_build.py` l.28 `risk = |e-sl0| x 2 x w`), so for them the code and research agree. | Mffu50K funded (cap $300 while the cushion is < $2,000, which is most days until the $52,100 lock). CPI09 x4 risk = 0.35 x ATR x $2 x 4 = 2.8 x ATR > $300 for any ATR > 107, so CPI09 **never trades** (MinAtrPoints is 150). MOM1030 x4 = 1.6 x ATR > $300 for ATR > 187.5, so it almost never trades (2024-26 ATR is 300-600). Research had both at x4 in that state. The same happens in a Manual eval (EvalRiskCapCushion 1200) and in a Lucid 25K funded account (cap $150 below $500). This can last weeks, and nothing appears on the dashboard except a higher "skipped" count. | Size the multiplier after the 1-lot check, as in research:<br>`int hw = 1;`<br>`if (!noBoost && m.Sig == "CPI09") hw = HwMult(Cpi09Multiplier);`<br>`if (!noBoost && m.Sig == "MOM1030") hw = HwMult(Mom1030Multiplier);`<br>`if (hw > 1) tq = hw * Qty();`<br>`...`<br>`if (TooBig(m.Sig, st * TickSize, hw > 1 ? Qty() : tq)) return;` |
| F2 | **high** | NQMaster.cs:175, 180, 188, 193-194 (ApplyPreset funded branches); 1437-1451 (AccountGuard) | The eval-target stop is not mode-gated. `AccountGuard` stops trading when `EvalTarget > 0` in **any** PropMode, and no funded preset branch resets `EvalTarget` to 0. In funded mode the target is `max(EvalTarget, bestDay / ConsistencyPct)`, and Mffu50K funded keeps `ConsistencyPct = 30`. `ApplyPreset` writes into the instance's public properties. When a running strategy is edited or re-enabled (NT clones the instance), and in a saved workspace, the eval values (EvalTarget 3000, EvalHighWrMultiplier 8, Contracts 2 for LucidPro25K) come back in the property grid. | User runs the eval with PropPreset Mffu50K (EvalTarget becomes 3000), passes, then edits the same strategy to PropMode Funded. EvalTarget is still 3000. The MFFU plan keeps $4,100 of profit, so once cash ≥ 50,000 + max(3000, bestDay/0.3) the funded account sets `targetHit`, flattens and **stops trading for good**: it un-latches only if the balance falls back below. The same happens if the user typed EvalTarget in Manual mode and later picks a funded preset. The dashboard only says "eval target reached". | In every funded preset branch add `EvalTarget = 0;` (and reset `EvalHighWrMultiplier = 0`).<br>Gate the guard: `if (EvalTarget > 0 && PropMode != NQMasterPropMode.Funded && !targetHit)`, plus the same condition on the un-latch block.<br>In DataLoaded: `if (PropMode == NQMasterPropMode.Funded && EvalTarget > 0) Warn("nqm_cfg", "EvalTarget ignored in Funded mode");` |
| F3 | **high** | NQMaster.cs:1200-1268 (no persistence); guide NQMASTER_GUIA.md:55 ("Days to load ≥ 45") | The edge-monitor CUSUM, the alarm and a running fallback (`edgeS`, `edgeDays`, `edgeAlarm`, `edgeFbLeft`, `edgeFbOff`) exist only in memory. After any restart (NinjaTrader or PC restart, disable/enable, reload after an F5 recompile) they are rebuilt from the loaded history only. Prop state, by contrast, is persisted in `nqmaster_prop_<acct>.txt`. | With Days to load 45 (~31 trading days), S can grow by at most 31 x (k - z̄). Reaching h = 18.57 needs a mean z ≈ -0.52 for 31 straight days, which is about -$416 per day per contract at ATR 400, about -$13k per contract in 6 weeks. The documented case "dead edge detected in ~158 days, negative edge in ~92" **can never fire** if NT is restarted at least every ~6 weeks. A fallback that fired 100 days ago is cancelled by the next restart, and the full profile comes back with no message. | Minimum fix: at go-live, if the first loaded session is after `EdgeMonitorStart`, warn that the monitor only sees N days and that Days to load must be ≥ the calendar days since the start date + 30. Track `firstSessDay` at the first IsFirstBarOfSession.<br>Proper fix: persist `edgeS;edgeDays;edgeAlarm;edgeFbLeft;edgeFbOff;lastCountedDate` per account and instrument in `EdgeDayClose` (realtime only). At go-live, load the file when `lastCountedDate >= EdgeMonitorStart`, and replay only the history days counted after `lastCountedDate`; keep a `List<KeyValuePair<DateTime,double>>` of (date, z) during history for this. |
| F4 | **medium** | NQMaster.cs:553-559, 973, 1615; skip paths 693, 702, 707, 703 | MSEQS only arms after an ORB60 **fill** (`orbFirstDir` is set in OnExecutionUpdate), and the ORB60 range is only built when `orb.On`. Research applies the risk cap and the module subsets after the fact to an engine that always produces the ORB60 event. The cap filter is `X[X.risk <= cap]` (robust2_build.py:63). The fallback and review sets (os_adapt.py) work on per-module streams. | Prop mode with the cap active: ORB60 risk = min(OR range, 0.35 ATR) x $2 x ctx w. At ATR 400 that is up to $280, or $560 with ctx x2, so `TooBig` skips ORB60 and MSEQS is dead that day. Research keeps those MSEQS trades. The same happens with `MaxOpenContracts` cutting ORB60 to 0 (`o.Trades = 2`), 2 rejections (`RejToday`), `DisableModules=ORB60`, `UseOrb=false`, or the built-in 2020 fallback list (ORB60 off, MSEQS on). In all these cases MSEQS never trades and nothing is printed. | Build the ORB60 range whenever `orb.On \|\| mseqs.On`.<br>Record a virtual ORB60 trigger independent of the order: in a small `OrbVirtual()` with ManageOrb's preconditions (pullback day, trend, window, OrbPriorCloseAtr), store `orbVirtDir = trendDir; orbVirtPx = entry;`. Each 1-minute bar: `if (orbFirstDir == 0 && orbVirtDir != 0 && (orbVirtDir == 1 ? High[0] >= orbVirtPx : Low[0] <= orbVirtPx)) { orbFirstDir = orbVirtDir; orbFirstMin = openMin; }`.<br>First confirm in the research engine (wrq_lib MSEQS) which ORB60 event it keys on. |
| F5 | **medium** | NQMaster.cs:179, 192, 800 | The Lucid50K / Mffu50K eval presets force `EvalHighWrMultiplier = 8` whatever `Contracts`, `AdaptiveSize` or `EvalMode` are. The property text and the research say "8 at 1 contract". | Contracts 2: MOM1030 and CPI09 go to 16 lots. CPI09 stop = 0.35 x ATR x $2 x 16 = 11.2 x ATR, which is more than the $2,000 trailing DD for ATR > 179, so one CPI09 stop busts the eval unless the cushion has grown. Research at base 2 (sniper_uniform.csv, Lucid Flex 50K): x8 is worse than x4 on T1 (p20 39.8% vs 45.3%, bust 57.1% vs 47.5%). MFFU base 2 x8 (peak 34 lots) is above the 30 cap and was never tested; CapQty cuts it ad hoc. Note: even at 1 contract, CPI09 x8 risk (5.6 x ATR $) exceeds the whole $2,000 DD for ATR > 357. Research includes this, but it is worth knowing. | Make the preset total-lot based:<br>`private int HwMult(int normal) { if (PropMode != NQMasterPropMode.Eval \|\| EvalHighWrMultiplier <= 0) return normal; return Math.Max(normal, EvalHighWrMultiplier / Math.Max(1, Qty())); }`<br>This gives 8 total lots at 1c and x4 (8 lots) at 2c. Or set the preset to `EvalHighWrMultiplier = (Contracts == 1 && !AdaptiveSize && !EvalMode) ? 8 : 0;`. |
| F6 | low-medium | NQMaster.cs:1205-1222, 1257-1261, 1243-1249 | The fallback does not validate module names, and it puts the monitor to sleep even when it changes nothing. (a) Names in `EdgeFallbackOff` that match no module (typos, e.g. `MOM1O`) are accepted. The alarm message then lists them as "modules off" while nothing changes. (b) When the list is empty or invalid (built-in table 2025-26, or 2027+ after the table goes stale), `edgeFbLeft = 252` still makes the CUSUM rest for 252 counted days. (c) Years after 2027 silently reuse the 2027 list (`else s = "REV06"`). | An alarm in Nov-Dec 2026 (possible after an Aug-2026-type streak: about 7 days at z ≈ -2.5) prints "alert only". The monitor is then blind until about Dec 2027, so a second, real decay cannot alarm. | Keep only valid names (`BySig(x) != null`) and Warn on unknown ones.<br>If the valid list is empty, do not start the rest period: `edgeAlarm = false; edgeS = 0;` (alert only, re-armed).<br>`if (year > 2027) Warn("nqm_fb_year", "fallback table not updated for " + year + ": re-run robust16.py");` |
| F7 | low | NQMaster.cs:395, 841, 851 | `MomAgreement` only applies when `profUltra`, which is false in **Custom**, but the MOM1030 x4 multiplier applies in every profile. In Custom, MOM1030 runs alone at x4. The x4 evidence (size_q.py, wr80_lab.py: ~80% WR) is for MOM1030 *with* the agreement filter. | A user picks Custom to tweak the ORB (Custom has every switch on by default): MOM1030 trades every day at 4 lots, without the filter that made it profitable. | `if (MomAgreement && (profUltra \|\| Profile == NQMasterProfile.Custom) && ...)`, or apply the x4 only when the agreement check ran. |
| F8 | low | NQMaster.cs:384, 474, 1674-1679 | `PrintModuleReport("end of run")` runs in `State.Terminated` and calls `Log()`, which formats `Times[0][0]`. If the bars are no longer accessible in Terminated (not verifiable without NT), the exception is caught after the **first** module line, and the end-of-backtest health report is cut off ("module report skipped: ..."). | A Strategy Analyzer run prints only one module row. The yearly-review tool (its stated purpose) is lost for backtests. | In PrintModuleReport replace `Log("health " + ...)` with `if (State == State.Realtime) LogFile("health " + line.Trim());`. |
| F9 | low | NQMaster.cs:1228-1231, 1237, 1250 | The edge-monitor inputs no longer match the calibration. (a) k / h come from monitor_recal (2026-10-12) and ultraq_build (10-14), before MOM1030 / CPI09 x4 (10-15) and eval x8. z is "per base contract", but days now include 4-8 lot trades, so the mean and variance of z, and with them the documented 1.5%/yr false-alarm rate, have changed. (b) Days blocked for operational reasons are counted with z = 0, i.e. S += k: roll halt, pause file, SkipShortSessions sessions, prop daily stop and target hit (eval), desync. | A paused or halted week adds 5k = 0.38 to S. A roll forgotten for 8 days adds 0.6. Small, but systematic. | Re-run `monitor_recal.py` on the current trade set (x4 weights, CPI09). Set `edgeDayTradable = false` on days where CanTrade was false for operational reasons: track a `dayBlocked` flag set in CanTrade for rollHalt / shortSession / pause / desync / targetHit. |
| F10 | low | NQMaster.cs:614 | Time modules fire only on the bar whose close is **exactly** `Hm(m.Time)`. If MNQ has no trade in that minute, the bar does not exist and the module skips the day with no message. The anchor logic already tolerates gaps (`openMin <= Anchor + 5`); the trigger does not. More likely on MNQ than on the NQ research data, at the night times (04:30, 05:00, 06:00, 07:00). | An MNQ chart with no 04:29 bar means LF0430 is lost that day, silently. | `if (m.On && !m.Done && closeMin >= Hm(m.Time) && closeMin <= Hm(m.Time) + 2) { ... }`. Done already prevents double entry. |

## New code: checked and found OK

- **CPI09:**
  - `cpiToday` is set at the session start from the trade date (18:00 rollover).
  - The 08:30 anchor tolerates a missing bar (+5 min).
  - The anchor is recorded before the news-blackout early return at l.568, so Mffu50K funded still gets AnchorPx.
  - The entry is the bar closing 09:30 (market at the 09:30 open), with MaxHold 60.
  - FOMC + CPI days are skipped by `fomcToday`.
  - The BuiltinCpi dates include the 2025 shutdown changes (2025-10-24, 2025-12-18, no Nov 2025).
  - An overnight module (LF06 holds until 10:00) open in the opposite direction makes CPI09 skip. This matches "first trade wins".
- **Multipliers:**
  - `noBoost` (SAFE / NoBoost gear) disables them. `HwMult` only acts in Eval.
  - Every entry path goes through `OfApply` → `CapQty`: ORB, VOLB (both paths), ENG10 (both), time modules, CRT11, LON, MSEQ, MSEQS, RSI2, ICT, the pend5 retry and the parked re-placement. A 16-lot MOM1030 is therefore cut to `MaxOpenContracts`.
  - `OpenAndWorking` counts the position plus the unfilled part of every working entry, excluding zombies. In realtime it also counts the other instruments of the account (MGC).
  - No integer overflow is possible (max 50 x 8 x 2).
- **ApplyPreset:** it runs in DataLoaded after the FOMC / CPI parsing and before the news parsing, BuildModules and EdgeParams. No preset-controlled value is read or cached before it. The `FundedPayoutAt` dependency on `FundedStepUpCushion` is correct; it is only shown on the dashboard. The `NewsBlackout = true` funded switch works. The 5-minute entries are blocked through `newsBlock5` + `BarsInProgress == 1`.
- **DisableModules / ApplyDisableList:**
  - It runs after BuildModules and before `BaseOn = On`.
  - PropSessionStart rebuilds `On` from `BaseOn`, so disabled modules stay off in every gear.
  - Unknown names are reported.
  - The only side effect is F4 (ORB60 → MSEQS).
- **Fallback vs gating:**
  - `m.On = BaseOn && !FallbackOff && (estable ? EstableSig : SAFE rule)` is recomputed in PropSessionStart.
  - PropSessionStart is called at **every** session start, including PropMode Off. In the session-start block, EdgeDayClose (l.510) runs before PropSessionStart (l.522), so a new alarm takes effect in the same session.
  - At go-live, PropGoLive → PropSessionStart reapplies the gear.
  - CancelAllEntries runs before the On flags change, so no orphan entries are left.
- **Health report:**
  - Guarded by `mods != null`: Terminated without DataLoaded is safe.
  - `SystemPerformance` is null-checked.
  - The whole report is in try/catch (F8 aside).
  - It runs once at go-live (`wentLive`) and once at the end of a backtest.
- **Critical paths:**
  - **OnOrderUpdate:**
    - Zombies are never re-attached.
    - A rejected entry is skipped. After 2 rejected entries, the module's `OfApply` returns 0 for the session.
    - A rejected stop or target exits only its module. Any other rejected exit flattens.
    - Account-level rejection texts set `rejectHalt` until the next session.
  - **OnExecutionUpdate:**
    - First-fill bookkeeping runs once. `OpenQty` handles multi-lot partial exits.
    - When `PriceTarget` sees a fill beyond the stop, it exits.
    - Opposite working entries are parked.
  - **Entry protection:**
    - The stop and target are always armed (SetStopLoss / ArmPriceBracket) before the entry call, so no bar runs unprotected under `PerEntryExecution`.
    - VOLB break-even exits at market if the level has already been crossed.
  - **PurgeStaleEntries / DropStale:**
    - Timeouts are 2 bars on history and 5 in realtime.
    - Realtime zombies keep blocking only until the next session start (l.507-508), so a stale order cannot block a direction for weeks.
  - **DirectionAllowed:**
    - An opposite market entry counts as a position.
    - Opposite stop / limit entries are parked and the new entry deferred (`deferUntil` = Max).
    - ORB waits only for an opposite deferred module.
  - **CheckAccountSync:**
    - It arms only after the virtual position is flat.
    - After 2 bars of mismatch it flattens the instrument and terminates.
  - **FlattenAll:** at most once per bar; it always cancels entries first.
  - **Session-start block:**
    - Entries and realtime zombies are cancelled first.
    - Then come the session bounds, the edge day close, the day start, the RTH finalisation, FOMC / CPI flags, the eval session, NewSession, PropSessionStart and edgeDayQty.
    - The order is consistent.
  - **1-minute / 5-minute interaction:**
    - For the same timestamp NT processes BIP 0 before BIP 1, so trend, ATR and the RTH day are current for OnFiveMinute.
    - Entries from both series see each other's working orders, through CapQty and DirectionAllowed.
    - `pend5` is a single slot, but MSEQ (trend up) and MSEQS (ORB60 short) cannot occur on the same day.
- **C# 5:** the file compiles with `mcs -langversion:5` against the NT8 stub: no `$""`, `?.`, `=>` members, `nameof`, `out var` or auto-property initializers. (The grep hits are `$` inside string literals.)

## Not reported (verified as intended or already covered by earlier reviews)
- The realtime-transition drop of Initialized entries adds them to `rtZombies` without a cancel. This is deliberate (NT may send them live) and lasts one session at most.
- `orbFirstMin` uses the previous bar's open time when the fill arrives intrabar in realtime: a 1-minute difference with no practical effect on MSEQS (5-minute bars).
- ExitModule uses `Position.Quantity` together with `fromEntrySignal`; this was validated by the NT runs (95.7% / 92.7% matched trades).
