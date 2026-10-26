"""2026-10-26 experiment 01 (docs/PLAN_2026-10-26.md, 5A): FillSeries for NQMaster.cs (v3, after the adversarial review).
Adds an optional intrabar fill series (1 tick / 1 second) and routes every managed order to it, following NinjaTrader's
SampleIntrabarBacktest pattern, so the Strategy Analyzer fills stop-market / limit entries and the stop / target exits
on ticks instead of the 1-minute OHLC (OrderFillResolution.High is not offered for multi-series strategies).
FillSeries = Off (default) keeps the strategy equivalent in behaviour: fillBip = 0 everywhere, every new branch is inert.
v2: the fill series takes the orders only once it has bars (Continuum tick history starts 2026-08-25, minutes go back years).
v3 (review 2026-10-26): back to the 1-minute series at State.Realtime (backtest-only feature), tick-gap counter in the RUN TIME
line, FillBar()/FillBarTime() also keyed on the fill time (not only on BarsInProgress), flip after BarsRequiredToTrade bars of
the fill series, series count printed at DataLoaded.
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

# 1. enum
rep("\tpublic enum NQMasterSafeSet { Classic, Estable }\n",
    "\tpublic enum NQMasterSafeSet { Classic, Estable }\n"
    "\tpublic enum NQMasterFillSeries { Off, Tick1, Second1 }\t// experiment 01 (2026-10-26): intrabar fill series for the Strategy Analyzer\n")
# 2. fields
rep("\t\tprivate bool badTimeframe;\n",
    "\t\tprivate bool badTimeframe;\n"
    "\t\tprivate int fillCfg, fillBip;\t\t// fillCfg = series configured for the orders (0 = 1-minute bars as always, 2 = FillSeries Tick1 / Second1);\n"
    "\t\t\t\t\t\t\t\t\t\t\t\t\t// fillBip = the one in use on this bar: 2 once the fill series has bars (tick history can start years after the minutes), else 0\n"
    "\t\tprivate int tickGapBars;\t\t\t// 1-minute bars with volume whose minute has no fill-series bar (provider tick gap): a run with gaps is not valid for H1\n"
    "\t\tprivate DateTime runStart;\t\t\t// wall clock at DataLoaded -> run-time line at Terminated (Off vs Tick1 ratio)\n")
# 3. defaults
rep("\t\t\t\tUseOrderFlowBoost = false; OrderFlowCvdMin = 0.015; OrderFlowBoost = 2; OrderFlowStack = false;\n",
    "\t\t\t\tUseOrderFlowBoost = false; OrderFlowCvdMin = 0.015; OrderFlowBoost = 2; OrderFlowStack = false;\n"
    "\t\t\t\tFillSeries = NQMasterFillSeries.Off; TraceOrdersLog = false;\n")
# 4. configure
rep("\t\t\telse if (State == State.Configure)\n\t\t\t{\n\t\t\t\tAddDataSeries(BarsPeriodType.Minute, 5);\n\t\t\t}\n",
    "\t\t\telse if (State == State.Configure)\n\t\t\t{\n\t\t\t\tAddDataSeries(BarsPeriodType.Minute, 5);\n"
    "\t\t\t\t// experiment 01 (docs/PLAN_2026-10-26.md): optional intrabar series (index 2) that receives every order, as in NinjaTrader's\n"
    "\t\t\t\t// SampleIntrabarBacktest. Backtest realism only: the 1-minute logic is untouched, fills happen on ticks / seconds. Never put\n"
    "\t\t\t\t// FillSeries in an optimizer range (the number of series would change between iterations); live charts switch back at Realtime.\n"
    "\t\t\t\tif (FillSeries == NQMasterFillSeries.Tick1) AddDataSeries(BarsPeriodType.Tick, 1);\n"
    "\t\t\t\telse if (FillSeries == NQMasterFillSeries.Second1) AddDataSeries(BarsPeriodType.Second, 1);\n"
    "\t\t\t\tfillCfg = FillSeries == NQMasterFillSeries.Off ? 0 : 2; fillBip = 0;\n"
    "\t\t\t\tTraceOrders = TraceOrdersLog;\n\t\t\t}\n")
# 5. DataLoaded: start clock, series count
rep("\t\t\telse if (State == State.DataLoaded)\n\t\t\t{\n\t\t\t\trthCloses = new List<double>(); atrHist = new List<double>();\n",
    "\t\t\telse if (State == State.DataLoaded)\n\t\t\t{\n"
    "\t\t\t\trunStart = DateTime.Now; Print(string.Format(\"NQMaster | fill series {0} (orders on BarsInProgress {1}; {2} series loaded), trace orders {3}, run started {4:HH:mm:ss}\", FillSeries, fillCfg, BarsArray != null ? BarsArray.Length : 0, TraceOrders ? \"on\" : \"off\", runStart));\n"
    "\t\t\t\trthCloses = new List<double>(); atrHist = new List<double>();\n")
# 6. Realtime: backtest-only feature -> orders back to the 1-minute series, with a warning
rep("\t\t\telse if (State == State.Realtime)\n\t\t\t{\n\t\t\t\t// an entry still Initialized at the switch was never processed on history (NinjaTrader would send it live now): drop it\n",
    "\t\t\telse if (State == State.Realtime)\n\t\t\t{\n"
    "\t\t\t\tif (fillCfg > 0) { fillCfg = 0; fillBip = 0; Warn(\"nqm_fill\", \"NQMaster | FillSeries \" + FillSeries + \" is for the Strategy Analyzer only: live orders go back to the 1-minute series. Set it to Off in the live template.\"); }\n"
    "\t\t\t\t// an entry still Initialized at the switch was never processed on history (NinjaTrader would send it live now): drop it\n")
# 7. Terminated: run time + tick gaps
rep("\t\t\t\tif (mods != null && !wentLive) PrintModuleReport(\"end of run\");\n",
    "\t\t\t\tif (mods != null && !wentLive) PrintModuleReport(\"end of run\");\n"
    "\t\t\t\tif (mods != null && runStart.Year > 2000 && BarsArray != null && BarsArray.Length > fillCfg && BarsArray[0] != null)\n"
    "\t\t\t\t\tPrint(string.Format(\"NQMaster | RUN TIME fill series {0}: {1:0.0} s wall clock, {2:N0} 1-minute bars{3}{4}\", FillSeries, (DateTime.Now - runStart).TotalSeconds, BarsArray[0].Count,\n"
    "\t\t\t\t\t\tfillCfg > 0 && BarsArray[fillCfg] != null ? string.Format(\", {0:N0} fill-series bars\", BarsArray[fillCfg].Count) : \"\",\n"
    "\t\t\t\t\t\tfillCfg > 0 ? string.Format(\", {0} tick-gap minutes (must be 0 for H1)\", tickGapBars) : \"\"));\n")
# 8. OnBarUpdate: guard first; the fill series takes the orders once it has BarsRequiredToTrade bars; tick-gap watch
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
    "\t\t\t}\n")
# 9. every order call: BarsInProgress 0 -> fillBip
for a, b, c in [("EnterLong(0, ", "EnterLong(fillBip, ", 9), ("EnterShort(0, ", "EnterShort(fillBip, ", 9),
                ("EnterLongStopMarket(0, true, ", "EnterLongStopMarket(fillBip, true, ", 4), ("EnterShortStopMarket(0, true, ", "EnterShortStopMarket(fillBip, true, ", 4),
                ("EnterLongLimit(0, true, ", "EnterLongLimit(fillBip, true, ", 3), ("EnterShortLimit(0, true, ", "EnterShortLimit(fillBip, true, ", 3),
                ("ExitLong(0, ", "ExitLong(fillBip, ", 2), ("ExitShort(0, ", "ExitShort(fillBip, ", 2)]:
    rep(a, b, c)
# 10. FlattenAll: Off keeps the parameterless exit; a fill series gets the same whole-position market exit on it
rep("\t\t\tif (Position.MarketPosition == MarketPosition.Long) ExitLong(); else ExitShort();\n\t\t\tLog(\"FLATTEN: \" + why);\n",
    "\t\t\t// FillSeries Off: the parameterless exit, as always. Tick1 / Second1: the same whole-position market exit (default names 'Sell' /\n"
    "\t\t\t// 'Buy to cover', fromEntrySignal empty = every entry) submitted to the fill series, so the exit fills on the next tick.\n"
    "\t\t\tif (fillBip == 0) { if (Position.MarketPosition == MarketPosition.Long) ExitLong(); else ExitShort(); }\n"
    "\t\t\telse if (Position.MarketPosition == MarketPosition.Long) ExitLong(fillBip, Position.Quantity, \"Sell\", \"\");\n"
    "\t\t\telse ExitShort(fillBip, Position.Quantity, \"Buy to cover\", \"\");\n"
    "\t\t\tLog(\"FLATTEN: \" + why);\n")
# 11. OnExecutionUpdate: the bar index / bar time of a fill must not depend on which series triggered the callback. With a fill series the
#     callback runs while the 1-minute bar of the fill is still forming (CurrentBars[0] = the bar before it, fill time later than the last
#     closed 1-minute bar); with Off NinjaTrader fills on the closed bar (CurrentBars[0] = the fill bar, fill time = its close). With Off the
#     helpers return exactly CurrentBars[0] / Times[0][0] (fillCfg == 0), so live behaviour does not change either.
rep("\t\tprivate static int Hm(int hhmm) { return (hhmm / 100) * 60 + hhmm % 100; }\n",
    "\t\tprivate static int Hm(int hhmm) { return (hhmm / 100) * 60 + hhmm % 100; }\n"
    "\t\t// fill callbacks: index / close time of the 1-minute bar the fill belongs to (fill series: that bar is still forming, so +1 bar / +1 min)\n"
    "\t\tprivate bool FillAhead(DateTime t) { return fillCfg > 0 && fillBip > 0 && (BarsInProgress == fillBip || t > Times[0][0]); }\n"
    "\t\tprivate int FillBar(DateTime t) { return CurrentBars[0] + (FillAhead(t) ? 1 : 0); }\n"
    "\t\tprivate DateTime FillBarTime(DateTime t) { return FillAhead(t) ? Times[0][0].AddMinutes(1) : Times[0][0]; }\n")
rep("\t\t\t\tif (m == orb) { orb.Trades++; if (orbFirstDir == 0) { orbFirstDir = orb.Dir; DateTime eo = ToEt(Times[0][0]).AddMinutes(-1); orbFirstMin = eo.Hour * 60 + eo.Minute; } }\n",
    "\t\t\t\tif (m == orb) { orb.Trades++; if (orbFirstDir == 0) { orbFirstDir = orb.Dir; DateTime eo = ToEt(FillBarTime(time)).AddMinutes(-1); orbFirstMin = eo.Hour * 60 + eo.Minute; } }\n")
rep("\t\t\t\tif (m == volb) { volbDone = true; volb.EntryBar = CurrentBars[0]; volbBeSet = false; volbTrades++; }\n\t\t\t\tif (m == eng10) eng10.EntryBar = CurrentBars[0];\n",
    "\t\t\t\tif (m == volb) { volbDone = true; volb.EntryBar = FillBar(time); volbBeSet = false; volbTrades++; }\n\t\t\t\tif (m == eng10) eng10.EntryBar = FillBar(time);\n")
rep("\t\t\t\tif (m.Kind == 1 || m == rsi || m.Six) m.EntryBar = CurrentBars[0];\n",
    "\t\t\t\tif (m.Kind == 1 || m == rsi || m.Six) m.EntryBar = FillBar(time);\n")
# 12. properties
rep("\t\t[Browsable(false)] public bool OrderFlowStack { get; set; }\n\t\t#endregion\n",
    "\t\t[Browsable(false)] public bool OrderFlowStack { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"Serie de llenado (solo backtest: Off = barras de 1 min como siempre; Tick1 / Second1 = agrega una serie intrabar y manda todas las órdenes ahí; en vivo vuelve a Off)\", Order = 1, GroupName = \"09. Backtest: realismo de ejecución\")] public NQMasterFillSeries FillSeries { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"TraceOrders en Output (muestra la serie y el precio de cada orden)\", Order = 2, GroupName = \"09. Backtest: realismo de ejecución\")] public bool TraceOrdersLog { get; set; }\n"
    "\t\t#endregion\n")
# 13. header
rep("// Managed orders: one signal per module. An entry is skipped if the strategy holds (or is working) the opposite direction.\n",
    "// Managed orders: one signal per module. An entry is skipped if the strategy holds (or is working) the opposite direction.\n"
    "// FillSeries (2026-10-26, experiment 01): Off = orders on the 1-minute bars (default, unchanged); Tick1 / Second1 = a 1-tick / 1-second\n"
    "//   series is added and every order is submitted to it (SampleIntrabarBacktest), so Strategy Analyzer fills are intrabar. Backtest only:\n"
    "//   at State.Realtime the orders go back to the 1-minute series.\n")
for k in ("EnterLong(0,", "EnterShort(0,", "ExitLong(0,", "ExitShort(0,"):
    assert k not in s, k
open(P, "w", encoding="utf-8-sig").write(s)
print("patched", P, n0, "->", len(s.splitlines()), "lines")
