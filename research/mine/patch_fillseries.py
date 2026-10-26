"""2026-10-26 experiment 01 (docs/PLAN_2026-10-26.md, 5A): FillSeries for NQMaster.cs.
Adds an optional intrabar fill series (1 tick / 1 second) and routes every managed order to it, following NinjaTrader's
SampleIntrabarBacktest pattern, so the Strategy Analyzer fills stop-market / limit entries and the stop / target exits
on ticks instead of the 1-minute OHLC (OrderFillResolution.High is not offered for multi-series strategies).
FillSeries = Off (default) keeps the strategy byte-for-byte equivalent in behaviour: fillBip = 0 everywhere.
Also: run-time print (DataLoaded -> Terminated) to report the Off / Tick1 ratio, and a TraceOrders switch.
Run from the repo root: python3 research/mine/patch_fillseries.py   (idempotent: refuses to patch twice).
Backup: archive/backups/NQMaster_backup_pre_fillseries.cs"""
import os, re, sys
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
    "\t\tprivate int fillBip;\t\t\t\t// BarsInProgress every order is submitted to: 0 (1-minute bars, as always) or 2 (FillSeries Tick1 / Second1)\n"
    "\t\tprivate DateTime runStart;\t\t\t// wall clock at DataLoaded -> run-time line at Terminated (Off vs Tick1 ratio)\n")
# 3. defaults
rep("\t\t\t\tUseOrderFlowBoost = false; OrderFlowCvdMin = 0.015; OrderFlowBoost = 2; OrderFlowStack = false;\n",
    "\t\t\t\tUseOrderFlowBoost = false; OrderFlowCvdMin = 0.015; OrderFlowBoost = 2; OrderFlowStack = false;\n"
    "\t\t\t\tFillSeries = NQMasterFillSeries.Off; TraceOrdersLog = false;\n")
# 4. configure
rep("\t\t\telse if (State == State.Configure)\n\t\t\t{\n\t\t\t\tAddDataSeries(BarsPeriodType.Minute, 5);\n\t\t\t}\n",
    "\t\t\telse if (State == State.Configure)\n\t\t\t{\n\t\t\t\tAddDataSeries(BarsPeriodType.Minute, 5);\n"
    "\t\t\t\t// experiment 01 (docs/PLAN_2026-10-26.md): optional intrabar series (index 2) that receives every order, as in NinjaTrader's\n"
    "\t\t\t\t// SampleIntrabarBacktest. Backtest realism only: the 1-minute logic is untouched, fills happen on ticks / seconds.\n"
    "\t\t\t\tif (FillSeries == NQMasterFillSeries.Tick1) AddDataSeries(BarsPeriodType.Tick, 1);\n"
    "\t\t\t\telse if (FillSeries == NQMasterFillSeries.Second1) AddDataSeries(BarsPeriodType.Second, 1);\n"
    "\t\t\t\tfillBip = FillSeries == NQMasterFillSeries.Off ? 0 : 2;\n"
    "\t\t\t\tTraceOrders = TraceOrdersLog;\n\t\t\t}\n")
# 5. DataLoaded: start clock
rep("\t\t\telse if (State == State.DataLoaded)\n\t\t\t{\n\t\t\t\trthCloses = new List<double>(); atrHist = new List<double>();\n",
    "\t\t\telse if (State == State.DataLoaded)\n\t\t\t{\n"
    "\t\t\t\trunStart = DateTime.Now; Print(string.Format(\"NQMaster | fill series {0} (orders on BarsInProgress {1}), trace orders {2}, run started {3:HH:mm:ss}\", FillSeries, fillBip, TraceOrders ? \"on\" : \"off\", runStart));\n"
    "\t\t\t\trthCloses = new List<double>(); atrHist = new List<double>();\n")
# 6. Terminated: run time
rep("\t\t\t\tif (mods != null && !wentLive) PrintModuleReport(\"end of run\");\n",
    "\t\t\t\tif (mods != null && !wentLive) PrintModuleReport(\"end of run\");\n"
    "\t\t\t\tif (mods != null && runStart.Year > 2000 && BarsArray != null && BarsArray.Length > fillBip && BarsArray[0] != null)\n"
    "\t\t\t\t\tPrint(string.Format(\"NQMaster | RUN TIME fill series {0}: {1:0.0} s wall clock, {2:N0} 1-minute bars{3}\", FillSeries, (DateTime.Now - runStart).TotalSeconds, BarsArray[0].Count,\n"
    "\t\t\t\t\t\tfillBip > 0 && BarsArray[fillBip] != null ? string.Format(\", {0:N0} fill-series bars\", BarsArray[fillBip].Count) : \"\"));\n")
# 7. OnBarUpdate guard (first line) + fill series must have bars before an order can go to it
rep("\t\tprotected override void OnBarUpdate()\n\t\t{\n\t\t\tif (badTimeframe || CurrentBars[0] < 3) return;\n",
    "\t\tprotected override void OnBarUpdate()\n\t\t{\n"
    "\t\t\tif (BarsInProgress == 2) return;\t\t\t\t// fill series (FillSeries Tick1 / Second1): orders only, no logic\n"
    "\t\t\tif (badTimeframe || CurrentBars[0] < 3 || (fillBip > 0 && CurrentBars[fillBip] < 1)) return;\n")
# 8. every order call: BarsInProgress 0 -> fillBip
for a, b, c in [("EnterLong(0, ", "EnterLong(fillBip, ", 9), ("EnterShort(0, ", "EnterShort(fillBip, ", 9),
                ("EnterLongStopMarket(0, true, ", "EnterLongStopMarket(fillBip, true, ", 4), ("EnterShortStopMarket(0, true, ", "EnterShortStopMarket(fillBip, true, ", 4),
                ("EnterLongLimit(0, true, ", "EnterLongLimit(fillBip, true, ", 3), ("EnterShortLimit(0, true, ", "EnterShortLimit(fillBip, true, ", 3),
                ("ExitLong(0, ", "ExitLong(fillBip, ", 2), ("ExitShort(0, ", "ExitShort(fillBip, ", 2)]:
    rep(a, b, c)
# 9. FlattenAll: the parameterless exit stays on the primary series (unchanged behaviour with Off); with a fill series, exit each module on it
rep("\t\t\tif (Position.MarketPosition == MarketPosition.Long) ExitLong(); else ExitShort();\n\t\t\tLog(\"FLATTEN: \" + why);\n",
    "\t\t\t// FillSeries Off: the parameterless exit, as always. Tick1 / Second1: the same whole-position market exit (default names 'Sell' /\n"
    "\t\t\t// 'Buy to cover', fromEntrySignal empty = every entry) submitted to the fill series, so the exit fills on the next tick.\n"
    "\t\t\tif (fillBip == 0) { if (Position.MarketPosition == MarketPosition.Long) ExitLong(); else ExitShort(); }\n"
    "\t\t\telse if (Position.MarketPosition == MarketPosition.Long) ExitLong(fillBip, Position.Quantity, \"Sell\", \"\");\n"
    "\t\t\telse ExitShort(fillBip, Position.Quantity, \"Buy to cover\", \"\");\n"
    "\t\t\tLog(\"FLATTEN: \" + why);\n")
# 10. properties
rep("\t\t[Browsable(false)] public bool OrderFlowStack { get; set; }\n\t\t#endregion\n",
    "\t\t[Browsable(false)] public bool OrderFlowStack { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"Serie de llenado (solo backtest: Off = barras de 1 min como siempre; Tick1 / Second1 = agrega una serie intrabar y manda todas las órdenes ahí)\", Order = 1, GroupName = \"09. Backtest: realismo de ejecución\")] public NQMasterFillSeries FillSeries { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"TraceOrders en Output (muestra la serie y el precio de cada orden)\", Order = 2, GroupName = \"09. Backtest: realismo de ejecución\")] public bool TraceOrdersLog { get; set; }\n"
    "\t\t#endregion\n")
# 11. header
rep("// Managed orders: one signal per module. An entry is skipped if the strategy holds (or is working) the opposite direction.\n",
    "// Managed orders: one signal per module. An entry is skipped if the strategy holds (or is working) the opposite direction.\n"
    "// FillSeries (2026-10-26, experiment 01): Off = orders on the 1-minute bars (default, unchanged); Tick1 / Second1 = a 1-tick / 1-second\n"
    "//   series is added and every order is submitted to it (SampleIntrabarBacktest), so Strategy Analyzer fills are intrabar. Backtest only.\n")
# 12. OnExecutionUpdate: with a fill series the callback runs while the 1-minute bar of the fill is still forming (CurrentBars[0] = the bar
#     before it); with Off / realtime-less history NinjaTrader fills on the closed bar (CurrentBars[0] = the fill bar). FillBar() / FillBarTime()
#     give the same bar index and bar time in both modes, so MaxHold exits and the ORB first-fill minute are identical and only the fills differ.
rep("\t\tprivate static int Hm(int hhmm) { return (hhmm / 100) * 60 + hhmm % 100; }\n",
    "\t\tprivate static int Hm(int hhmm) { return (hhmm / 100) * 60 + hhmm % 100; }\n"
    "\t\t// fill callbacks: index / close time of the 1-minute bar the fill belongs to (fill series: that bar is still forming, so +1 bar / +1 min)\n"
    "\t\tprivate int FillBar() { return CurrentBars[0] + (fillBip > 0 && BarsInProgress == fillBip ? 1 : 0); }\n"
    "\t\tprivate DateTime FillBarTime() { return fillBip > 0 && BarsInProgress == fillBip ? Times[0][0].AddMinutes(1) : Times[0][0]; }\n")
rep("\t\t\t\tif (m == orb) { orb.Trades++; if (orbFirstDir == 0) { orbFirstDir = orb.Dir; DateTime eo = ToEt(Times[0][0]).AddMinutes(-1); orbFirstMin = eo.Hour * 60 + eo.Minute; } }\n",
    "\t\t\t\tif (m == orb) { orb.Trades++; if (orbFirstDir == 0) { orbFirstDir = orb.Dir; DateTime eo = ToEt(FillBarTime()).AddMinutes(-1); orbFirstMin = eo.Hour * 60 + eo.Minute; } }\n")
rep("\t\t\t\tif (m == volb) { volbDone = true; volb.EntryBar = CurrentBars[0]; volbBeSet = false; volbTrades++; }\n\t\t\t\tif (m == eng10) eng10.EntryBar = CurrentBars[0];\n",
    "\t\t\t\tif (m == volb) { volbDone = true; volb.EntryBar = FillBar(); volbBeSet = false; volbTrades++; }\n\t\t\t\tif (m == eng10) eng10.EntryBar = FillBar();\n")
rep("\t\t\t\tif (m.Kind == 1 || m == rsi || m.Six) m.EntryBar = CurrentBars[0];\n",
    "\t\t\t\tif (m.Kind == 1 || m == rsi || m.Six) m.EntryBar = FillBar();\n")
assert s.count("(0, ") == 0 or all(k not in l for l in s.splitlines() for k in ("EnterLong(0,", "EnterShort(0,", "ExitLong(0,", "ExitShort(0,"))
open(P, "w", encoding="utf-8-sig").write(s)
print("patched", P, n0, "->", len(s.splitlines()), "lines")
