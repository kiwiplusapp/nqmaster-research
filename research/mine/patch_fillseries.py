"""2026-10-26 experiment 01 (docs/PLAN_2026-10-26.md, 5A): FillSeries for NQMaster.cs (v4).
Adds an optional intrabar fill series (1 tick / 1 second) and routes every managed order to it, following NinjaTrader's
SampleIntrabarBacktest pattern, so the Strategy Analyzer fills stop-market / limit entries and the stop / target exits
on ticks instead of the 1-minute OHLC (OrderFillResolution.High is not offered for multi-series strategies).
FillSeries = Off (default) keeps the strategy equivalent in behaviour: fillBip = 0 everywhere, every new branch is inert
(proved 2026-10-26: Off export identical byte for byte to the pre-patch export, 3,295 trades).
v2: the fill series takes the orders only once it has bars (tick history starts later than the minutes).
v3 (review 2026-10-26): back to the 1-minute series at State.Realtime, tick-gap counter, FillBar() keyed on the fill time too,
flip after BarsRequiredToTrade bars of the fill series, series count printed at DataLoaded.
v4 (P2c 2026-10-26): NinjaTrader keeps the SetStopLoss / SetProfitTarget orders on the PRIMARY series (0 of 283 protective fills
carried tick times), so with a fill series the brackets become explicit ExitLongStopMarket / ExitLongLimit orders on that series,
placed on the entry fill with the levels the Set* calls would have used; market exits cancel the brackets first; orphan guard and
counters (RUN TIME line); Playback keeps the fill series (bracket test), any other live connection switches back to the 1-minute series.
Run from anywhere: python3 research/mine/patch_fillseries.py   (idempotent: refuses to patch twice).
Backup: archive/backups/NQMaster_backup_pre_fillseries.cs"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, "NQMaster.cs")
s = open(P, encoding="utf-8-sig").read()
if "NQMasterFillSeries" in s: sys.exit("already patched")
n0 = len(s.splitlines())

def rep(old, new, count=1):
    global s
    c = s.count(old)
    assert c == count, (c, count, old[:80])
    s = s.replace(old, new)

# ---------------------------------------------------------------- v1-v3
rep("\tpublic enum NQMasterSafeSet { Classic, Estable }\n",
    "\tpublic enum NQMasterSafeSet { Classic, Estable }\n"
    "\tpublic enum NQMasterFillSeries { Off, Tick1, Second1 }\t// experiment 01 (2026-10-26): intrabar fill series for the Strategy Analyzer\n")
rep("\t\t\tpublic double FixTgt = double.NaN; public bool StructStop, WinHas, Six; public double WinH, WinL, RvolMax;\t// six-year modules (2026-10-16)\t// lots still open (multi-lot entries close in parts), rejected orders this session\n",
    "\t\t\tpublic double FixTgt = double.NaN; public bool StructStop, WinHas, Six; public double WinH, WinL, RvolMax;\t// six-year modules (2026-10-16)\t// lots still open (multi-lot entries close in parts), rejected orders this session\n"
    "\t\t\t// explicit brackets (FillSeries Tick1 / Second1, v4): the levels the Set* calls would have used, the working orders, a market exit waiting for their cancel\n"
    "\t\t\tpublic bool XStopPrice, XTgtPrice, XExitPending; public double XStopV = double.NaN, XTgtV = double.NaN; public Order XStop, XTgt; public int XExitQty, XExitBar = -1; public string XExitSig;\n")
rep("\t\tprivate bool badTimeframe;\n",
    "\t\tprivate bool badTimeframe;\n"
    "\t\tprivate int fillCfg, fillBip;\t\t// fillCfg = series configured for the orders (0 = 1-minute bars as always, 2 = FillSeries Tick1 / Second1);\n"
    "\t\t\t\t\t\t\t\t\t\t\t\t\t// fillBip = the one in use on this bar: 2 once the fill series has bars (tick history can start years after the minutes), else 0\n"
    "\t\tprivate int tickGapBars;\t\t\t// 1-minute bars with volume whose minute has no fill-series bar (provider tick gap): a run with gaps is not valid for H1\n"
    "\t\tprivate int orphanCount, xExitForced;\t// explicit brackets: protective orders still working with the module flat (cancelled here), market exits sent without a confirmed cancel\n"
    "\t\tprivate DateTime runStart;\t\t\t// wall clock at DataLoaded -> run-time line at Terminated (Off vs Tick1 ratio)\n")
rep("\t\t\t\tUseOrderFlowBoost = false; OrderFlowCvdMin = 0.015; OrderFlowBoost = 2; OrderFlowStack = false;\n",
    "\t\t\t\tUseOrderFlowBoost = false; OrderFlowCvdMin = 0.015; OrderFlowBoost = 2; OrderFlowStack = false;\n"
    "\t\t\t\tFillSeries = NQMasterFillSeries.Off; TraceOrdersLog = false;\n")
rep("\t\t\telse if (State == State.Configure)\n\t\t\t{\n\t\t\t\tAddDataSeries(BarsPeriodType.Minute, 5);\n\t\t\t}\n",
    "\t\t\telse if (State == State.Configure)\n\t\t\t{\n\t\t\t\tAddDataSeries(BarsPeriodType.Minute, 5);\n"
    "\t\t\t\t// experiment 01 (docs/PLAN_2026-10-26.md): optional intrabar series (index 2) that receives every order, as in NinjaTrader's\n"
    "\t\t\t\t// SampleIntrabarBacktest. Backtest realism only: the 1-minute logic is untouched, fills happen on ticks / seconds. Never put\n"
    "\t\t\t\t// FillSeries in an optimizer range (the number of series would change between iterations); live charts switch back at Realtime.\n"
    "\t\t\t\tif (FillSeries == NQMasterFillSeries.Tick1) AddDataSeries(BarsPeriodType.Tick, 1);\n"
    "\t\t\t\telse if (FillSeries == NQMasterFillSeries.Second1) AddDataSeries(BarsPeriodType.Second, 1);\n"
    "\t\t\t\tfillCfg = FillSeries == NQMasterFillSeries.Off ? 0 : 2; fillBip = 0;\n"
    "\t\t\t\tTraceOrders = TraceOrdersLog;\n\t\t\t}\n")
rep("\t\t\telse if (State == State.DataLoaded)\n\t\t\t{\n\t\t\t\trthCloses = new List<double>(); atrHist = new List<double>();\n",
    "\t\t\telse if (State == State.DataLoaded)\n\t\t\t{\n"
    "\t\t\t\trunStart = DateTime.Now; Print(string.Format(\"NQMaster | fill series {0} (orders on BarsInProgress {1}; {2} series loaded), trace orders {3}, run started {4:HH:mm:ss}\", FillSeries, fillCfg, BarsArray != null ? BarsArray.Length : 0, TraceOrders ? \"on\" : \"off\", runStart));\n"
    "\t\t\t\trthCloses = new List<double>(); atrHist = new List<double>();\n")
# Realtime: backtest-only feature. Playback (Market Replay) keeps the fill series so the explicit brackets can be tested; any other connection switches back.
rep("\t\t\telse if (State == State.Realtime)\n\t\t\t{\n\t\t\t\t// an entry still Initialized at the switch was never processed on history (NinjaTrader would send it live now): drop it\n",
    "\t\t\telse if (State == State.Realtime)\n\t\t\t{\n"
    "\t\t\t\tif (fillCfg > 0)\n"
    "\t\t\t\t{\n"
    "\t\t\t\t\tbool playback = false; try { playback = Connection.PlaybackConnection != null; } catch { }\n"
    "\t\t\t\t\tif (playback) Warn(\"nqm_fill\", \"NQMaster | FillSeries \" + FillSeries + \" kept on the Playback connection (bracket test): orders stay on BarsInProgress \" + fillCfg + \". Never use it on a live account.\");\n"
    "\t\t\t\t\telse { fillCfg = 0; fillBip = 0; Warn(\"nqm_fill\", \"NQMaster | FillSeries \" + FillSeries + \" is for the Strategy Analyzer only: live orders go back to the 1-minute series. Set it to Off in the live template.\"); }\n"
    "\t\t\t\t\tforeach (Mod m in mods) { try { if (m.XStop != null) m.XStop = GetRealtimeOrder(m.XStop); if (m.XTgt != null) m.XTgt = GetRealtimeOrder(m.XTgt); } catch { } }\n"
    "\t\t\t\t}\n"
    "\t\t\t\t// an entry still Initialized at the switch was never processed on history (NinjaTrader would send it live now): drop it\n")
rep("\t\t\t\tif (mods != null && !wentLive) PrintModuleReport(\"end of run\");\n",
    "\t\t\t\tif (mods != null && !wentLive) PrintModuleReport(\"end of run\");\n"
    "\t\t\t\tif (mods != null && runStart.Year > 2000 && BarsArray != null && BarsArray.Length > fillCfg && BarsArray[0] != null)\n"
    "\t\t\t\t\tPrint(string.Format(\"NQMaster | RUN TIME fill series {0}: {1:0.0} s wall clock, {2:N0} 1-minute bars{3}{4}\", FillSeries, (DateTime.Now - runStart).TotalSeconds, BarsArray[0].Count,\n"
    "\t\t\t\t\t\tfillCfg > 0 && BarsArray[fillCfg] != null ? string.Format(\", {0:N0} fill-series bars\", BarsArray[fillCfg].Count) : \"\",\n"
    "\t\t\t\t\t\tfillCfg > 0 ? string.Format(\", {0} tick-gap minutes (must be 0 for H1), {1} orphan protective orders cancelled, {2} market exits forced without a confirmed cancel (both must be 0)\", tickGapBars, orphanCount, xExitForced) : \"\"));\n")
rep("\t\tprotected override void OnBarUpdate()\n\t\t{\n\t\t\tif (badTimeframe || CurrentBars[0] < 3) return;\n",
    "\t\tprotected override void OnBarUpdate()\n\t\t{\n"
    "\t\t\tif (BarsInProgress == 2) return;\t\t\t\t// fill series (FillSeries Tick1 / Second1): orders only, no logic\n"
    "\t\t\tif (badTimeframe || CurrentBars[0] < 3) return;\n"
    "\t\t\tif (fillCfg > 0)\t\t\t\t\t\t\t// orders go to the fill series only once it has bars; before that (no tick history yet) they go to the 1-minute series as with Off\n"
    "\t\t\t{\n"
    "\t\t\t\tint fb = CurrentBars.Length > fillCfg && CurrentBars[fillCfg] >= BarsRequiredToTrade ? fillCfg : 0;\n"
    "\t\t\t\tif (fb != fillBip) { fillBip = fb; Log(string.Format(\"FILL SERIES {0}: orders on BarsInProgress {1} from this bar\", FillSeries, fillBip)); }\n"
    "\t\t\t\tif (fillBip > 0 && BarsInProgress == 0 && Volume[0] > 0 && (Time[0] - Times[fillBip][0]).TotalMinutes > 1.5)\n"
    "\t\t\t\t{ tickGapBars++; if (tickGapBars <= 20) Log(string.Format(\"TICK GAP: this 1-minute bar has volume but the last fill-series bar is {0:HH:mm:ss}\", Times[fillBip][0])); }\n"
    "\t\t\t\tif (BarsInProgress == 0) foreach (Mod m in mods)\n"
    "\t\t\t\t{\n"
    "\t\t\t\t\t// a market exit whose bracket cancel was not confirmed within one bar goes out anyway (counted: must stay 0)\n"
    "\t\t\t\t\tif (m.XExitPending && CurrentBars[0] > m.XExitBar) { m.XExitPending = false; xExitForced++; Log(m.Sig + \" market exit forced: bracket cancel not confirmed within one bar\"); SubmitModuleExit(m, m.XExitQty, m.XExitSig); }\n"
    "\t\t\t\t\t// orphan guard: a protective order still working with the module flat is cancelled and counted (Playback test: must stay 0)\n"
    "\t\t\t\t\tif (!m.InTrade && (Working(m.XStop) || Working(m.XTgt))) { orphanCount++; Print(string.Format(\"{0} | NQMaster | ORPHAN protective order of {1} cancelled (module flat)\", Times[0][0].ToString(\"yyyy-MM-dd HH:mm\", CultureInfo.InvariantCulture), m.Sig)); CancelBrackets(m); }\n"
    "\t\t\t\t}\n"
    "\t\t\t}\n")
for a, b, c in [("EnterLong(0, ", "EnterLong(fillBip, ", 9), ("EnterShort(0, ", "EnterShort(fillBip, ", 9),
                ("EnterLongStopMarket(0, true, ", "EnterLongStopMarket(fillBip, true, ", 4), ("EnterShortStopMarket(0, true, ", "EnterShortStopMarket(fillBip, true, ", 4),
                ("EnterLongLimit(0, true, ", "EnterLongLimit(fillBip, true, ", 3), ("EnterShortLimit(0, true, ", "EnterShortLimit(fillBip, true, ", 3),
                ("ExitLong(0, ", "ExitLong(fillBip, ", 2), ("ExitShort(0, ", "ExitShort(fillBip, ", 2)]:
    rep(a, b, c)
# ExitModule: Off path unchanged; with a fill series the module's brackets are cancelled first and the exit goes out on that series
rep("\t\t\tif (desyncHalt) return;\n\t\t\tif (Position.MarketPosition == MarketPosition.Long) ExitLong(fillBip, Math.Max(1, Position.Quantity), m.Sig + \"X\", m.Sig);\n",
    "\t\t\tif (desyncHalt) return;\n"
    "\t\t\tif (fillBip > 0) { ModuleMarketExit(m, Math.Max(1, m.OpenQty > 0 ? m.OpenQty : Position.Quantity), m.Sig + \"X\"); Log(m.Sig + \" exit: \" + why); return; }\n"
    "\t\t\tif (Position.MarketPosition == MarketPosition.Long) ExitLong(fillBip, Math.Max(1, Position.Quantity), m.Sig + \"X\", m.Sig);\n")
# hedge guard exit (realtime only) through the same path
rep("\t\t\t\tif (m.Dir == 1) ExitLong(fillBip, q, m.Sig + \"X\", m.Sig); else ExitShort(fillBip, q, m.Sig + \"X\", m.Sig);\n",
    "\t\t\t\tModuleMarketExit(m, q, m.Sig + \"X\");\n")
# FlattenAll: Off keeps the parameterless exit; with a fill series every module in trade exits through its own cancel-then-exit path
rep("\t\t\tif (Position.MarketPosition == MarketPosition.Long) ExitLong(); else ExitShort();\n\t\t\tLog(\"FLATTEN: \" + why);\n",
    "\t\t\t// FillSeries Off: the parameterless exit, as always. Tick1 / Second1: each module in trade cancels its brackets and exits on the fill series;\n"
    "\t\t\t// lots no module tracks (none expected) get the whole-position market exit ('Sell' / 'Buy to cover', fromEntrySignal empty = every entry).\n"
    "\t\t\tif (fillBip == 0) { if (Position.MarketPosition == MarketPosition.Long) ExitLong(); else ExitShort(); }\n"
    "\t\t\telse\n\t\t\t{\n"
    "\t\t\t\tint sum = 0; foreach (Mod m in mods) if (m.InTrade && m.OpenQty > 0) { sum += m.OpenQty; ModuleMarketExit(m, m.OpenQty, m.Sig + \"X\"); }\n"
    "\t\t\t\tif (sum == 0) { foreach (Mod m in mods) CancelBrackets(m); if (Position.MarketPosition == MarketPosition.Long) ExitLong(fillBip, Position.Quantity, \"Sell\", \"\"); else ExitShort(fillBip, Position.Quantity, \"Buy to cover\", \"\"); }\n"
    "\t\t\t\telse if (sum < Position.Quantity) Log(string.Format(\"FLATTEN: {0} lot(s) not tracked by any module stay for the session-close exit\", Position.Quantity - sum));\n"
    "\t\t\t}\n"
    "\t\t\tLog(\"FLATTEN: \" + why);\n")
# fill callbacks: bar index / bar time of the fill (+1 bar / +1 min while the 1-minute bar of the fill is still forming); Off: exactly as before
rep("\t\tprivate static int Hm(int hhmm) { return (hhmm / 100) * 60 + hhmm % 100; }\n",
    "\t\tprivate static int Hm(int hhmm) { return (hhmm / 100) * 60 + hhmm % 100; }\n"
    "\t\t// fill callbacks: index / close time of the 1-minute bar the fill belongs to (fill series: that bar is still forming, so +1 bar / +1 min)\n"
    "\t\tprivate bool FillAhead(DateTime t) { return fillCfg > 0 && fillBip > 0 && (BarsInProgress == fillBip || t > Times[0][0]); }\n"
    "\t\tprivate int FillBar(DateTime t) { return CurrentBars[0] + (FillAhead(t) ? 1 : 0); }\n"
    "\t\tprivate DateTime FillBarTime(DateTime t) { return FillAhead(t) ? Times[0][0].AddMinutes(1) : Times[0][0]; }\n"
    "\t\t// ---- explicit brackets (FillSeries Tick1 / Second1, v4). NinjaTrader keeps the orders of SetStopLoss / SetProfitTarget on the primary series\n"
    "\t\t// (measured 2026-10-26: 0 of 283 protective fills carried tick times), so with a fill series the bracket is a pair of explicit exit orders on\n"
    "\t\t// that series, placed on every entry execution with the levels the Set* call would have used (ticks from the average fill price, or a price),\n"
    "\t\t// named 'StopX' / 'TargetX' and tied to the entry signal. A market exit cancels them first (NinjaTrader ignores a market exit while a stop /\n"
    "\t\t// limit exit of the same entry is working) and goes out when the cancels are confirmed, at the latest on the next 1-minute bar.\n"
    "\t\t// With FillSeries Off every call below falls through to the Set* method it replaces: nothing changes.\n"
    "\t\tprivate void BracketStop(Mod m, CalculationMode mode, double v)\n"
    "\t\t{\n"
    "\t\t\tif (fillBip == 0) { SetStopLoss(m.Sig, mode, v, false); return; }\n"
    "\t\t\tm.XStopPrice = mode == CalculationMode.Price; m.XStopV = v;\n"
    "\t\t\tif (m.InTrade && Working(m.XStop)) { try { ChangeOrder(m.XStop, m.XStop.Quantity, 0, BracketPx(m, true)); } catch (Exception ex) { Log(m.Sig + \" stop change failed: \" + ex.Message); } }\n"
    "\t\t}\n"
    "\t\tprivate void BracketTarget(Mod m, CalculationMode mode, double v)\n"
    "\t\t{\n"
    "\t\t\tif (fillBip == 0) { SetProfitTarget(m.Sig, mode, v); return; }\n"
    "\t\t\tm.XTgtPrice = mode == CalculationMode.Price; m.XTgtV = v;\n"
    "\t\t\tif (m.InTrade && Working(m.XTgt)) { try { ChangeOrder(m.XTgt, m.XTgt.Quantity, BracketPx(m, false), 0); } catch (Exception ex) { Log(m.Sig + \" target change failed: \" + ex.Message); } }\n"
    "\t\t}\n"
    "\t\tprivate double BracketPx(Mod m, bool stop)\n"
    "\t\t{\n"
    "\t\t\tint dir = m.Dir != 0 ? m.Dir : (Position.MarketPosition == MarketPosition.Short ? -1 : 1);\n"
    "\t\t\tdouble v = stop ? m.XStopV : m.XTgtV; bool isPx = stop ? m.XStopPrice : m.XTgtPrice;\n"
    "\t\t\treturn Instrument.MasterInstrument.RoundToTickSize(isPx ? v : m.EntryPx + (stop ? -1 : 1) * dir * v * TickSize);\n"
    "\t\t}\n"
    "\t\t// on every entry execution: place or re-size the two bracket orders for the lots open (PriceTarget modules get the target after the fill)\n"
    "\t\tprivate void PlaceBrackets(Mod m)\n"
    "\t\t{\n"
    "\t\t\tif (fillBip == 0 || m.OpenQty <= 0) return;\n"
    "\t\t\tint dir = m.Dir != 0 ? m.Dir : (Position.MarketPosition == MarketPosition.Short ? -1 : 1);\n"
    "\t\t\tif (!double.IsNaN(m.XStopV))\n"
    "\t\t\t{\n"
    "\t\t\t\tdouble sp = BracketPx(m, true);\n"
    "\t\t\t\tif (Working(m.XStop)) { if (m.XStop.Quantity != m.OpenQty) try { ChangeOrder(m.XStop, m.OpenQty, 0, sp); } catch (Exception ex) { Log(m.Sig + \" stop re-size failed: \" + ex.Message); } }\n"
    "\t\t\t\telse m.XStop = dir == 1 ? ExitLongStopMarket(fillBip, true, m.OpenQty, sp, \"StopX\", m.Sig) : ExitShortStopMarket(fillBip, true, m.OpenQty, sp, \"StopX\", m.Sig);\n"
    "\t\t\t}\n"
    "\t\t\tif (!double.IsNaN(m.XTgtV) && !(m.PriceTarget && !m.XTgtPrice))\t// the 4000-tick placeholder of ArmPriceBracket is never placed: the price target replaces it on the fill\n"
    "\t\t\t{\n"
    "\t\t\t\tdouble tp = BracketPx(m, false);\n"
    "\t\t\t\tif (Working(m.XTgt)) { if (m.XTgt.Quantity != m.OpenQty) try { ChangeOrder(m.XTgt, m.OpenQty, tp, 0); } catch (Exception ex) { Log(m.Sig + \" target re-size failed: \" + ex.Message); } }\n"
    "\t\t\t\telse m.XTgt = dir == 1 ? ExitLongLimit(fillBip, true, m.OpenQty, tp, \"TargetX\", m.Sig) : ExitShortLimit(fillBip, true, m.OpenQty, tp, \"TargetX\", m.Sig);\n"
    "\t\t\t}\n"
    "\t\t}\n"
    "\t\tprivate void CancelBrackets(Mod m)\n"
    "\t\t{\n"
    "\t\t\ttry { if (Working(m.XStop)) CancelOrder(m.XStop); } catch { }\n"
    "\t\t\ttry { if (Working(m.XTgt)) CancelOrder(m.XTgt); } catch { }\n"
    "\t\t}\n"
    "\t\tprivate void ModuleMarketExit(Mod m, int qty, string sigX)\n"
    "\t\t{\n"
    "\t\t\tif (fillBip == 0 || (!Working(m.XStop) && !Working(m.XTgt))) { SubmitModuleExit(m, qty, sigX); return; }\n"
    "\t\t\tm.XExitPending = true; m.XExitQty = qty; m.XExitSig = sigX; m.XExitBar = CurrentBars[0];\n"
    "\t\t\tCancelBrackets(m);\n"
    "\t\t}\n"
    "\t\tprivate void SubmitModuleExit(Mod m, int qty, string sigX)\n"
    "\t\t{\n"
    "\t\t\tif (Position.MarketPosition == MarketPosition.Long) ExitLong(fillBip, Math.Max(1, qty), sigX, m.Sig);\n"
    "\t\t\telse if (Position.MarketPosition == MarketPosition.Short) ExitShort(fillBip, Math.Max(1, qty), sigX, m.Sig);\n"
    "\t\t}\n"
    "\t\t// OnOrderUpdate of a bracket order: keep the reference current; once both brackets are no longer working, send the market exit that waited for them\n"
    "\t\tprivate void BracketUpdate(Mod m, Order o)\n"
    "\t\t{\n"
    "\t\t\tif (o.Name == \"StopX\") m.XStop = o; else m.XTgt = o;\n"
    "\t\t\tif (m.XExitPending && !Working(m.XStop) && !Working(m.XTgt))\n"
    "\t\t\t{\n"
    "\t\t\t\tm.XExitPending = false;\n"
    "\t\t\t\tif (m.OpenQty > 0 && Position.MarketPosition != MarketPosition.Flat) SubmitModuleExit(m, m.XExitQty, m.XExitSig);\n"
    "\t\t\t}\n"
    "\t\t}\n")
# OnExecutionUpdate: FillBar / FillBarTime, place the brackets on every entry execution, cancel the sibling when the module is flat, bracket names
rep("\t\t\t\tif (m == orb) { orb.Trades++; if (orbFirstDir == 0) { orbFirstDir = orb.Dir; DateTime eo = ToEt(Times[0][0]).AddMinutes(-1); orbFirstMin = eo.Hour * 60 + eo.Minute; } }\n",
    "\t\t\t\tif (m == orb) { orb.Trades++; if (orbFirstDir == 0) { orbFirstDir = orb.Dir; DateTime eo = ToEt(FillBarTime(time)).AddMinutes(-1); orbFirstMin = eo.Hour * 60 + eo.Minute; } }\n")
rep("\t\t\t\tif (m == volb) { volbDone = true; volb.EntryBar = CurrentBars[0]; volbBeSet = false; volbTrades++; }\n\t\t\t\tif (m == eng10) eng10.EntryBar = CurrentBars[0];\n",
    "\t\t\t\tif (m == volb) { volbDone = true; volb.EntryBar = FillBar(time); volbBeSet = false; volbTrades++; }\n\t\t\t\tif (m == eng10) eng10.EntryBar = FillBar(time);\n")
rep("\t\t\t\tif (m.Kind == 1 || m == rsi || m.Six) m.EntryBar = CurrentBars[0];\n",
    "\t\t\t\tif (m.Kind == 1 || m == rsi || m.Six) m.EntryBar = FillBar(time);\n")
rep("\t\t\t\t\tSetProfitTarget(m.Sig, CalculationMode.Price, tgt);\n\t\t\t\t}\n\t\t\t\tLog(string.Format(\"{0} filled @ {1}\", m.Sig, Fmt(m.EntryPx)));\n",
    "\t\t\t\t\tBracketTarget(m, CalculationMode.Price, tgt);\n\t\t\t\t}\n\t\t\t\tPlaceBrackets(m);\n\t\t\t\tLog(string.Format(\"{0} filled @ {1}\", m.Sig, Fmt(m.EntryPx)));\n")
rep("\t\t\t\texitMod.OpenQty = Math.Max(0, exitMod.OpenQty - quantity); if (exitMod.OpenQty == 0) exitMod.InTrade = false;\n",
    "\t\t\t\texitMod.OpenQty = Math.Max(0, exitMod.OpenQty - quantity); if (exitMod.OpenQty == 0) { exitMod.InTrade = false; CancelBrackets(exitMod); }\t// the sibling bracket, if NinjaTrader did not cancel it\n")
rep("&& !Working(volb.Entry) && execution.Order.Name == \"Stop loss\")\n",
    "&& !Working(volb.Entry) && (execution.Order.Name == \"Stop loss\" || execution.Order.Name == \"StopX\"))\n")
# OnOrderUpdate: bracket orders report here; rejected explicit brackets are handled like rejected Set* orders
rep("\t\t\tMod m = BySig(order.Name);\n\t\t\tif (m != null && !zombies.Contains(order) && (m.Entry == null || m.Entry == order || !Working(m.Entry))) m.Entry = order;\n",
    "\t\t\tMod m = BySig(order.Name);\n"
    "\t\t\tif (m == null && (order.Name == \"StopX\" || order.Name == \"TargetX\")) { Mod bm = BySig(order.FromEntrySignal); if (bm != null) BracketUpdate(bm, order); }\n"
    "\t\t\tif (m != null && !zombies.Contains(order) && (m.Entry == null || m.Entry == order || !Working(m.Entry))) m.Entry = order;\n")
rep("\t\t\t\t\tMod f = (order.Name == \"Stop loss\" || order.Name == \"Profit target\") ? BySig(order.FromEntrySignal) : null;\n",
    "\t\t\t\t\tMod f = (order.Name == \"Stop loss\" || order.Name == \"Profit target\" || order.Name == \"StopX\" || order.Name == \"TargetX\") ? BySig(order.FromEntrySignal) : null;\n")
# every Set* call site goes through the bracket helpers (Off: identical calls)
rep("SetStopLoss(volb.Sig, CalculationMode.Price, be, false);", "BracketStop(volb, CalculationMode.Price, be);")
rep("\t\t\tSetStopLoss(o.Sig, CalculationMode.Ticks, st, false);\n\t\t\tSetProfitTarget(o.Sig, CalculationMode.Ticks, Math.Max(1, (int)Math.Round(st * o.R)));\n",
    "\t\t\tBracketStop(o, CalculationMode.Ticks, st);\n\t\t\tBracketTarget(o, CalculationMode.Ticks, Math.Max(1, (int)Math.Round(st * o.R)));\n")
rep("\t\t\tSetStopLoss(m.Sig, CalculationMode.Ticks, st, false);\n\t\t\tSetProfitTarget(m.Sig, CalculationMode.Ticks, Math.Max(1, (int)Math.Round(m.R * st)));\n",
    "\t\t\tBracketStop(m, CalculationMode.Ticks, st);\n\t\t\tBracketTarget(m, CalculationMode.Ticks, Math.Max(1, (int)Math.Round(m.R * st)));\n")
rep("\t\t\t\t\tSetStopLoss(rsi.Sig, CalculationMode.Ticks, st, false);\n\t\t\t\t\tSetProfitTarget(rsi.Sig, CalculationMode.Ticks, Math.Max(1, (int)Math.Round(rsi.R * st)));\n",
    "\t\t\t\t\tBracketStop(rsi, CalculationMode.Ticks, st);\n\t\t\t\t\tBracketTarget(rsi, CalculationMode.Ticks, Math.Max(1, (int)Math.Round(rsi.R * st)));\n")
rep("\t\t\tSetStopLoss(m.Sig, CalculationMode.Price, stop, false);\n\t\t\tSetProfitTarget(m.Sig, CalculationMode.Ticks, 4000);\t// replaced on fill\n",
    "\t\t\tBracketStop(m, CalculationMode.Price, stop);\n\t\t\tBracketTarget(m, CalculationMode.Ticks, 4000);\t// replaced on fill\n")
assert s.count("SetStopLoss(") == 1 and s.count("SetProfitTarget(") == 1, (s.count("SetStopLoss("), s.count("SetProfitTarget("))
# properties
rep("\t\t[Browsable(false)] public bool OrderFlowStack { get; set; }\n\t\t#endregion\n",
    "\t\t[Browsable(false)] public bool OrderFlowStack { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"Serie de llenado (solo backtest: Off = barras de 1 min como siempre; Tick1 / Second1 = agrega una serie intrabar y manda todas las órdenes ahí; en vivo vuelve a Off)\", Order = 1, GroupName = \"09. Backtest: realismo de ejecución\")] public NQMasterFillSeries FillSeries { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"TraceOrders en Output (muestra la serie y el precio de cada orden)\", Order = 2, GroupName = \"09. Backtest: realismo de ejecución\")] public bool TraceOrdersLog { get; set; }\n"
    "\t\t#endregion\n")
rep("// Managed orders: one signal per module. An entry is skipped if the strategy holds (or is working) the opposite direction.\n",
    "// Managed orders: one signal per module. An entry is skipped if the strategy holds (or is working) the opposite direction.\n"
    "// FillSeries (2026-10-26, experiment 01): Off = orders on the 1-minute bars (default, unchanged); Tick1 / Second1 = a 1-tick / 1-second\n"
    "//   series is added and every order is submitted to it (SampleIntrabarBacktest), with explicit bracket orders 'StopX' / 'TargetX' on that\n"
    "//   series instead of SetStopLoss / SetProfitTarget (those stay on the primary series). Backtest only: at State.Realtime the orders go back\n"
    "//   to the 1-minute series, except on the Playback connection (bracket test).\n")
for k in ("EnterLong(0,", "EnterShort(0,", "ExitLong(0,", "ExitShort(0,"):
    assert k not in s, k
open(P, "w", encoding="utf-8-sig").write(s)
print("patched", P, n0, "->", len(s.splitlines()), "lines")
