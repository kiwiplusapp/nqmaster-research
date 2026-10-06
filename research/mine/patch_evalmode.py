"""'Pass easy' eval mode (research/mine/eval_pol50.py, final_verify2.py): 1 contract, from the 9th eval session (index 8) 2 contracts while
the eval profit is below $2,100 and the cushion over the EOD-trailing threshold is >= $1,000. Lucid 50K: pass 62% (vs 48% fixed 2),
median 15 days (vs 9), P(pass <= 22 d) 46% (same), lifecycle -10% $.
NQMaster: new EvalLateMinCushion (0 = off) in Qty(). GoldMaster: same EvalMode block (EvalMode, EvalStartDate, EvalLateDay, EvalLateGoal,
EvalLateContracts, EvalLateMinCushion); cushion from NQMaster's prop file (whole-account EOD peak) in realtime, own EOD peak otherwise."""
p = r"D:\NinjaTrader Strategy\NQMaster.cs"
s = open(p, encoding="utf-8").read()
def rep(a, b, cnt=1):
    global s
    n = s.count(a); assert n == cnt, (n, a[:120]); s = s.replace(a, b)
rep("\t\t\tif (EvalMode) return (evalDayIndex >= EvalLateDay && evalEqDayStart < EvalLateGoal) ? EvalLateContracts : Contracts;",
    "\t\t\tif (EvalMode) return (evalDayIndex >= EvalLateDay && evalEqDayStart < EvalLateGoal\n"
    "\t\t\t\t&& (EvalLateMinCushion <= 0 || double.IsNaN(propCushion) || propCushion >= EvalLateMinCushion)) ? EvalLateContracts : Contracts;")
rep("EvalLateGoal = 2000; EvalLateContracts = 3;", "EvalLateGoal = 2000; EvalLateContracts = 3; EvalLateMinCushion = 0;")
rep("\t\t[NinjaScriptProperty][Range(1, 50)][Display(Name = \"Late contracts\", Order = 5, GroupName = \"05. Evaluation mode\")] public int EvalLateContracts { get; set; }",
    "\t\t[NinjaScriptProperty][Range(1, 50)][Display(Name = \"Late contracts\", Order = 5, GroupName = \"05. Evaluation mode\")] public int EvalLateContracts { get; set; }\n"
    "\t\t[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = \"Late size only if cushion >= $ (0 = off; 'pass easy' 1000, needs PropMode Eval)\", Order = 6, GroupName = \"05. Evaluation mode\")] public double EvalLateMinCushion { get; set; }")
open(p, "w", encoding="utf-8", newline="\n").write(s); print("nq ok")

p = r"D:\NinjaTrader Strategy\GoldMaster.cs"
s = open(p, encoding="utf-8").read()
rep("\t\t\tpublic bool Def; public double DPx;", "\t\t\tpublic bool Def; public double DPx; public int Q = 1;")
rep("EdgeMonitor = true; EdgeMonitorPause = false;", "EvalMode = false; EvalStartDate = \"2026-10-05\"; EvalLateDay = 8; EvalLateGoal = 2100; EvalLateContracts = 2; EvalLateMinCushion = 1000;\n\t\t\t\tEdgeMonitor = true; EdgeMonitorPause = false;")
rep("\t\t\tfomcToday = SkipFomc && fomc.Contains(sessionDate);\n", "\t\t\tfomcToday = SkipFomc && fomc.Contains(sessionDate);\n\t\t\tEvalSessionStart();\n")
rep("\t\t#region Modules\n",
    "\t\t// ---- evaluation mode ('pass easy', research/mine/eval_pol50.py): Contracts (1) per module; from the EvalLateDay-th session (0-based,\n"
    "\t\t// from EvalStartDate) EvalLateContracts while the eval profit is below EvalLateGoal and the cushion over the EOD-trailing threshold\n"
    "\t\t// is >= EvalLateMinCushion. Realtime: account equity and NQMaster's prop file (whole-account EOD peak); historical: this strategy.\n"
    "\t\tprivate int evalDayIndex = -1; private double evalEqDayStart, evalPnlBase = double.NaN, evalPeak = double.NaN, evalCushion = double.NaN;\n"
    "\t\tprivate void EvalSessionStart()\n\t\t{\n\t\t\tif (!EvalMode) return;\n\t\t\tDateTime st;\n"
    "\t\t\tif (!DateTime.TryParseExact(EvalStartDate ?? \"\", \"yyyy-MM-dd\", CultureInfo.InvariantCulture, DateTimeStyles.None, out st) || sessionDate < st.Year * 10000 + st.Month * 100 + st.Day) return;\n"
    "\t\t\tif (double.IsNaN(evalPnlBase)) evalPnlBase = netPnl;\n"
    "\t\t\tevalDayIndex++; evalEqDayStart = State == State.Realtime ? Account.Get(AccountItem.CashValue, Currency.UsDollar) - StartBalance : netPnl - evalPnlBase;\n"
    "\t\t\tdouble pk = double.NaN;\n"
    "\t\t\tif (State == State.Realtime)\n\t\t\t\ttry\n\t\t\t\t{\n"
    "\t\t\t\t\tstring f = Path.Combine(Core.Globals.UserDataDir, \"nqmaster_prop_\" + Account.Name + \".txt\"); double v;\n"
    "\t\t\t\t\tif (File.Exists(f) && double.TryParse(File.ReadAllText(f).Trim().Split(';')[0], NumberStyles.Any, CultureInfo.InvariantCulture, out v)) pk = v - StartBalance;\n"
    "\t\t\t\t}\n\t\t\t\tcatch { }\n"
    "\t\t\tevalPeak = double.IsNaN(evalPeak) ? Math.Max(0, evalEqDayStart) : Math.Max(evalPeak, evalEqDayStart);\n"
    "\t\t\tif (double.IsNaN(pk)) pk = evalPeak; else pk = Math.Max(pk, evalEqDayStart);\n"
    "\t\t\tdouble thr = pk >= 2100 ? 100 : pk - 2000; evalCushion = evalEqDayStart - thr;\n"
    "\t\t\tif (PrintLog) Print(string.Format(\"{0} | GOLD | EVAL day {1}: profit {2:0}, cushion {3:0} -> {4} contracts\", sessionDate, evalDayIndex, evalEqDayStart, evalCushion, Qty()));\n"
    "\t\t}\n"
    "\t\tprivate int Qty()\n\t\t{\n"
    "\t\t\tif (EvalMode && evalDayIndex >= EvalLateDay && evalEqDayStart < EvalLateGoal && (EvalLateMinCushion <= 0 || double.IsNaN(evalCushion) || evalCushion >= EvalLateMinCushion)) return EvalLateContracts;\n"
    "\t\t\treturn Contracts;\n\t\t}\n\n\t\t#region Modules\n")
rep("\t\t\tif (m.Dir == 1) EnterLong(Contracts, m.Sig); else EnterShort(Contracts, m.Sig);\n", "\t\t\tm.Q = Qty();\n\t\t\tif (m.Dir == 1) EnterLong(m.Q, m.Sig); else EnterShort(m.Q, m.Sig);\n")
rep("\t\t\tif (d == 1) EnterLongStopMarket(0, true, Contracts, px, m.Sig); else EnterShortStopMarket(0, true, Contracts, px, m.Sig);",
    "\t\t\tm.Q = Qty();\n\t\t\tif (d == 1) EnterLongStopMarket(0, true, m.Q, px, m.Sig); else EnterShortStopMarket(0, true, m.Q, px, m.Sig);")
rep("\t\t\tif (m.Dir == 1) ExitLong(0, Contracts, m.Sig + \"X\", m.Sig); else if (m.Dir == -1) ExitShort(0, Contracts, m.Sig + \"X\", m.Sig);",
    "\t\t\tif (m.Dir == 1) ExitLong(0, Math.Max(1, m.Q), m.Sig + \"X\", m.Sig); else if (m.Dir == -1) ExitShort(0, Math.Max(1, m.Q), m.Sig + \"X\", m.Sig);")
rep("\t\t[Display(Name = \"Print log\", Order = 2, GroupName = \"03. Display\")] public bool PrintLog { get; set; }",
    "\t\t[Display(Name = \"Print log\", Order = 2, GroupName = \"03. Display\")] public bool PrintLog { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"Eval mode (late size-up, 'pass easy')\", Order = 1, GroupName = \"05. Evaluation mode\")] public bool EvalMode { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"Eval start date (yyyy-MM-dd)\", Order = 2, GroupName = \"05. Evaluation mode\")] public string EvalStartDate { get; set; }\n"
    "\t\t[NinjaScriptProperty][Range(1, 30)][Display(Name = \"Late day (sessions since start, 0-based)\", Order = 3, GroupName = \"05. Evaluation mode\")] public int EvalLateDay { get; set; }\n"
    "\t\t[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = \"Late goal $ (size up if profit below)\", Order = 4, GroupName = \"05. Evaluation mode\")] public double EvalLateGoal { get; set; }\n"
    "\t\t[NinjaScriptProperty][Range(1, 50)][Display(Name = \"Late contracts\", Order = 5, GroupName = \"05. Evaluation mode\")] public int EvalLateContracts { get; set; }\n"
    "\t\t[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = \"Late size only if cushion >= $ (0 = off)\", Order = 6, GroupName = \"05. Evaluation mode\")] public double EvalLateMinCushion { get; set; }")
open(p, "w", encoding="utf-8", newline="\n").write(s); print("gold ok")
