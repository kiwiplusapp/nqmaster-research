"""2026-10-16 six-year round: adds the 7 new modules (CA04V, SO04, GD03, RV11, ENG26, ORFAIL, CAM3) and lets the same switch turn LATEFH on in Ultra (default OFF until the NinjaTrader parity run).
Research: research/mine/six_reselect.py, six_combo2.py, six_life.py. Reproduces NQMaster.cs from NQMaster_backup_pre_six.cs."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src = open(os.path.join(ROOT, "NQMaster_backup_pre_six.cs"), encoding="utf-8").read()


def rep(old, new, count=1):
    global src
    n = src.count(old)
    if n != count: sys.exit(f"anchor found {n} times (expected {count}): {old[:90]!r}")
    src = src.replace(old, new)


# ---- header
rep("//   Custom    : every module switch and the ORB range / target / pullback settings apply.\n",
    "//   Custom    : every module switch and the ORB range / target / pullback settings apply.\n"
    "// Six-year modules (2026-10-16, Ultra, group 11, default OFF): CA04V, SO04, GD03, RV11, ENG26, ORFAIL, CAM3 + LATEFH. Chosen on real NQ\n"
    "//   2020-10..2023, checked on 2024-26 (research/mine/six_reselect.py, six_combo2.py, six_life.py), with opposite-position blocking:\n"
    "//   Ultra Sharpe 3.45 / 3.96 -> 3.76 / 4.09, +$13.8k over 6 years per contract (+9%), max drawdown $4,694 -> $4,406, WR -1.5 pts.\n"
    "//   MFFU 50K per seat 2024-26: +$67/month (full edge), +$8 (35% less edge, worse worst year). Weak in 2010-19 (post-2020 edge).\n")
# ---- Mod fields
rep("public int OpenQty, RejToday;", "public int OpenQty, RejToday;\n\t\t\tpublic double FixTgt = double.NaN; public bool StructStop, WinHas, Six; public double WinH, WinL, RvolMax;	// six-year modules (2026-10-16)")
rep("private List<Mod> timeMods;",
    "private List<Mod> timeMods;\n"
    "\t\t// six-year modules (2026-10-16): ENG26 (22-02 vs 02-06 4H engulf at 09:30), ORFAIL (failed 15-min ORB), CAM3 (Camarilla L3/H3 fade)\n"
    "\t\tprivate Mod eng26, orf, cam3; private List<Mod> sixMods = new List<Mod>();\n"
    "\t\tprivate double e26aO, e26aH, e26aL, e26aC; private bool e26aHas;\n"
    "\t\tprivate double sVwPv, sVwV;	// session VWAP since 18:00 (CA04V)\n"
    "\t\tprivate double rvAcc; private bool rvDone; private List<double> rvHist = new List<double>();	// RTH volume 09:30-10:59 (RV11)\n"
    "\t\tprivate double orfH, orfL, orfExt, orfSl, orfTp; private int orfBrk, orfBi, orfSig; private bool orfHas, orfReady, orfDone;\n"
    "\t\tprivate double camLev, camExt, camSl, camTp; private int camSide, camBr = -1, camSig; private bool camDone = true;")
# ---- defaults
rep("EvalHighWrMultiplier = 0;", "EvalHighWrMultiplier = 0;\n\t\t\t\tSixYearModules = false; UseCa04v = true; UseSo04 = true; UseGd03 = true; UseRv11 = true; UseEng26 = true; UseOrFail = true; UseCam3 = true;")
# ---- module setup
rep("\t\t\tMod latefh = AddTime(\"LATEFH\", (custom ? UseLateFh : ul && UseLateFh),",
    "\t\t\tbool six = Profile == NQMasterProfile.Ultra && SixYearModules;	// six-year modules (group 11, 2026-10-16); also switches LATEFH on\n"
    "\t\t\tMod latefh = AddTime(\"LATEFH\", (custom ? UseLateFh : ul && (UseLateFh || six)),")
rep("mods = new List<Mod>(); timeMods = new List<Mod>();", "mods = new List<Mod>(); timeMods = new List<Mod>(); sixMods = new List<Mod>();")
rep("cpi09.Anchor = 8 * 60 + 30; cpi09.CpiOnly = true;\n",
    "cpi09.Anchor = 8 * 60 + 30; cpi09.CpiOnly = true;\n"
    "\t\t\t// six-year modules (research/mine/six_combo2.py; real NQ 2020-10..2026, chosen on 2020-23, checked on 2024-26). Ultra only (not UltraQ).\n"
    "\t\t\tMod ca04v = AddTime(\"CA04V\", ((custom ? SixYearModules : six) && UseCa04v), 401, -6, false, 0.15, 1.0, 120, false, false); ca04v.MinDist = 0.20;	// 04:00 momentum vs the session VWAP\n"
    "\t\t\tMod so04 = AddTime(\"SO04\", ((custom ? SixYearModules : six) && UseSo04), 401, -1, false, 0.15, 1.0, 330, true, false); so04.MinDist = 0.35;	// 04:00 momentum vs the 18:00 open, with the trend\n"
    "\t\t\tMod gd03 = AddTime(\"GD03\", ((custom ? SixYearModules : six) && UseGd03), 500, -5, true, 0.20, 2.0, 240, true, false); gd03.MinDist = 0.20; gd03.Anchor = 3 * 60; gd03.StructStop = true;	// 05:00 fade of the move since 03:00, with the trend\n"
    "\t\t\tMod rv11 = AddTime(\"RV11\", ((custom ? SixYearModules : six) && UseRv11), 1100, -7, false, 0.15, 1.0, 400, false, false); rv11.MinDist = 0.25; rv11.RvolMax = 0.8;	// 11:00 low-volume continuation vs the prior close\n"
    "\t\t\teng26 = NewMod(\"ENG26\", ((custom ? SixYearModules : six) && UseEng26), 0.5); eng26.PriceTarget = true; eng26.MaxHold = 400; eng26.Six = true; sixMods.Add(eng26);\n"
    "\t\t\torf = NewMod(\"ORFAIL\", ((custom ? SixYearModules : six) && UseOrFail), 1.0); orf.PriceTarget = true; orf.MaxHold = 240; orf.Six = true; sixMods.Add(orf);\n"
    "\t\t\tcam3 = NewMod(\"CAM3\", ((custom ? SixYearModules : six) && UseCam3), 1.0); cam3.PriceTarget = true; cam3.MaxHold = 240; cam3.Six = true; sixMods.Add(cam3);\n")
rep("LATEFH NF05 LF06 LF0430 CPI09 ENG10 VOLB ...)", "LATEFH NF05 LF06 LF0430 CPI09 ENG10 VOLB CA04V SO04 GD03 RV11 ENG26 ORFAIL CAM3 ...)")
# ---- per-bar state (before any early return of the entry section)
rep("foreach (Mod m in timeMods) if (m.Anchor >= 0 && double.IsNaN(m.AnchorPx) && openMin >= m.Anchor && openMin <= m.Anchor + 5) m.AnchorPx = Open[0];\n",
    "foreach (Mod m in timeMods) if (m.Anchor >= 0 && double.IsNaN(m.AnchorPx) && openMin >= m.Anchor && openMin <= m.Anchor + 5) m.AnchorPx = Open[0];\n"
    "\t\t\tforeach (Mod m in timeMods) if (m.StructStop && !double.IsNaN(m.AnchorPx)) { if (!m.WinHas) { m.WinH = High[0]; m.WinL = Low[0]; m.WinHas = true; } else { m.WinH = Math.Max(m.WinH, High[0]); m.WinL = Math.Min(m.WinL, Low[0]); } }\n"
    "\t\t\t{ double sv = Volume[0] > 0 ? Volume[0] : 1.0; sVwPv += (High[0] + Low[0] + Close[0]) / 3.0 * sv; sVwV += sv; }\n"
    "\t\t\tif (openMin >= 1320 || openMin < 120) { if (!e26aHas) { e26aO = Open[0]; e26aH = High[0]; e26aL = Low[0]; e26aHas = true; } e26aH = Math.Max(e26aH, High[0]); e26aL = Math.Min(e26aL, Low[0]); e26aC = Close[0]; }\n"
    "\t\t\torfSig = 0; camSig = 0;\n")
rep("c2H = Math.Max(c2H, High[0]); c2L = Math.Min(c2L, Low[0]); } c2C = Close[0]; }\n",
    "c2H = Math.Max(c2H, High[0]); c2L = Math.Min(c2L, Low[0]); } c2C = Close[0]; }\n"
    "\t\t\t\tif (openMin < 660) { rvAcc += Volume[0]; if (openMin == 659) rvDone = true; }\n"
    "\t\t\t\tif (orf.On) OrfTrack(openMin);\n")
rep("\t\t\tAccountGuard();\n\t\t\tDailyLossCheck();\n", "\t\t\tif (cam3.On) Cam3Track(openMin);\n\t\t\tAccountGuard();\n\t\t\tDailyLossCheck();\n")
# ---- exits
rep("if (eng10.InTrade && CurrentBars[0] - eng10.EntryBar >= eng10.MaxHold) ExitModule(eng10, \"time exit\");\n",
    "if (eng10.InTrade && CurrentBars[0] - eng10.EntryBar >= eng10.MaxHold) ExitModule(eng10, \"time exit\");\n"
    "\t\t\tforeach (Mod m in sixMods) if (m.InTrade && m.MaxHold > 0 && CurrentBars[0] - m.EntryBar >= m.MaxHold) ExitModule(m, \"time exit\");\n")
# ---- entries
rep("\t\t\tif (eng10.On) ManageEng10(openMin);\n",
    "\t\t\tif (eng10.On) ManageEng10(openMin);\n"
    "\t\t\tif (eng26.On && openMin == 929) Eng26Entry();\n"
    "\t\t\tif (orfSig != 0) { int os = orfSig; orfSig = 0; SixEnter(orf, os, orfSl, orfTp); }\n"
    "\t\t\tif (camSig != 0) { int cs = camSig; camSig = 0; SixEnter(cam3, cs, camSl, camTp); }\n")
# ---- session / RTH-day resets
rep("e10aHas = false; e10bHas = false; eng10Done = false;",
    "e26aHas = false; sVwPv = 0; sVwV = 0; foreach (Mod m in timeMods) m.WinHas = false;\n"
    "\t\t\torfHas = orfReady = orfDone = false; orfBrk = 0; orfSig = 0;\n"
    "\t\t\t// CAM3 levels: prior complete RTH close +- 1.1/4 of the prior RTH range, the side of the daily trend (research PIVOT_FADE CAM3)\n"
    "\t\t\tcamSig = 0; camBr = -1; camSide = trendDir; camDone = !(cam3 != null && cam3.On) || camSide == 0 || double.IsNaN(full1) || double.IsNaN(prevRthHigh) || double.IsNaN(todayAtr);\n"
    "\t\t\tcamLev = camDone ? double.NaN : full1 - camSide * (prevRthHigh - prevRthLow) * 1.1 / 4.0;\n"
    "\t\t\te10aHas = false; e10bHas = false; eng10Done = false;")
rep("rthDay = etDate; dayHasBars = false;",
    "rthDay = etDate; dayHasBars = false;\n"
    "\t\t\tif (rvDone) { rvHist.Add(rvAcc); while (rvHist.Count > 20) rvHist.RemoveAt(0); }	// RV11: prior days' 09:30-10:59 volume\n"
    "\t\t\trvAcc = 0; rvDone = false;")
# ---- TimeEntry: new references, RVOL filter, structure stop
rep("\t\t\telse if (m.Lookback == -3) reference = vwV > 0 ? vwPv / vwV : double.NaN;\n",
    "\t\t\telse if (m.Lookback == -3) reference = vwV > 0 ? vwPv / vwV : double.NaN;\n"
    "\t\t\telse if (m.Lookback == -6) reference = sVwV > 0 ? sVwPv / sVwV : double.NaN;	// session VWAP since 18:00\n"
    "\t\t\telse if (m.Lookback == -7) reference = full1;	// prior complete RTH close\n")
rep("\t\t\tif (m.MinDist > 0 && Math.Abs(Close[0] - reference) < m.MinDist * atrDaily) return;\n",
    "\t\t\tif (m.MinDist > 0 && Math.Abs(Close[0] - reference) < m.MinDist * atrDaily) return;\n"
    "\t\t\tif (m.RvolMax > 0)\n\t\t\t{\n"
    "\t\t\t\tif (!rvDone || rvHist.Count < 10) return;\n"
    "\t\t\t\tdouble rs = 0; foreach (double x in rvHist) rs += x;\n"
    "\t\t\t\tif (rs <= 0 || rvAcc / (rs / rvHist.Count) > m.RvolMax) { Log(m.Sig + \" skipped: relative volume above \" + m.RvolMax.ToString(\"0.00\")); return; }\n"
    "\t\t\t}\n")
rep("\t\t\tint st = Math.Max(4, (int)Math.Round(m.StopAtr * atrDaily / TickSize));\n",
    "\t\t\tint st = Math.Max(4, (int)Math.Round(m.StopAtr * atrDaily / TickSize));\n"
    "\t\t\tif (m.StructStop)\n\t\t\t{\n"
    "\t\t\t\t// GD03: stop beyond the window's extreme (anchor -> signal bar) + 1 tick, capped at StopAtr x ATR (research G_DRIVE stop=1)\n"
    "\t\t\t\tif (!m.WinHas) return;\n"
    "\t\t\t\tdouble rk = Math.Min((d == 1 ? Close[0] - m.WinL : m.WinH - Close[0]) + TickSize, m.StopAtr * atrDaily);\n"
    "\t\t\t\tif (rk <= 2 * TickSize) return;\n"
    "\t\t\t\tst = Math.Max(1, (int)Math.Round(rk / TickSize));\n"
    "\t\t\t}\n")
# ---- fills
rep("if (m.Kind == 1 || m == rsi) m.EntryBar = CurrentBars[0];", "if (m.Kind == 1 || m == rsi || m.Six) m.EntryBar = CurrentBars[0];")
rep("\t\t\t\t\tdouble tgt = Instrument.MasterInstrument.RoundToTickSize(fill + m.Dir * m.R * risk);\n",
    "\t\t\t\t\tdouble tgt = Instrument.MasterInstrument.RoundToTickSize(double.IsNaN(m.FixTgt) ? fill + m.Dir * m.R * risk : m.FixTgt);\n"
    "\t\t\t\t\tif ((tgt - fill) * m.Dir <= 0) { ExitModule(m, \"filled beyond the target\"); return; }\n")
# ---- inactivity thresholds (1.5 x the longest 2020-26 gap in tradable days; research/mine/six_inactivity.json)
rep("\t\t\t\tcase \"MSEQS\": return 233;\n",
    "\t\t\t\tcase \"MSEQS\": return 233;\n"
    "\t\t\t\tcase \"LATEFH\": return 26; case \"ORFAIL\": return 60; case \"ENG26\": return 69; case \"GD03\": return 72; case \"SO04\": return 93;\n"
    "\t\t\t\tcase \"CA04V\": return 105; case \"RV11\": return 107; case \"CAM3\": return 117;\n")
# ---- new methods (before TimeEntry)
rep("\t\tprivate void TimeEntry(Mod m)\n",
    "\t\t// ---- six-year modules (2026-10-16) -----------------------------------------------------------------------------\n"
    "\t\tprivate void SixEnter(Mod m, int d, double sl, double tgt)\n\t\t{\n"
    "\t\t\tlastDeferred = false;\n"
    "\t\t\tif (m.InTrade || Working(m.Entry) || atrCount < AtrMin) return;\n"
    "\t\t\tint q = Qty();\n"
    "\t\t\tif (TooBig(m.Sig, Math.Abs(Close[0] - sl), q) || !DirectionAllowed(d)) return;\n"
    "\t\t\tArmPriceBracket(m, d, sl); m.FixTgt = tgt;\n"
    "\t\t\tq = OfApply(m, q, d);\n"
    "\t\t\tif (q <= 0) return;\n"
    "\t\t\tOrder o = d == 1 ? EnterLong(0, q, m.Sig) : EnterShort(0, q, m.Sig);\n"
    "\t\t\tif (o != null) m.Entry = o;\n"
    "\t\t\tLog(string.Format(\"{0} {1} | SL {2}{3}\", m.Sig, d == 1 ? \"BUY\" : \"SELL\", Fmt(sl), double.IsNaN(tgt) ? \"\" : \" | TP \" + Fmt(tgt)));\n"
    "\t\t}\n"
    "\t\t// ENG26: 4H candle 02:00-06:00 body-engulfs 22:00-02:00 with opposite colours -> trade its way at 09:30 (market), stop beyond the\n"
    "\t\t// 02-06 candle, 0.5R, 400 min (research ENGULF_4H #25: T1 PF 1.57, T2 1.33)\n"
    "\t\tprivate void Eng26Entry()\n\t\t{\n"
    "\t\t\tif (eng26.InTrade || !e26aHas || !e10aHas || double.IsNaN(todayAtr) || todayAtr <= 0) return;\n"
    "\t\t\tint s = 0;\n"
    "\t\t\tif (e10aC > e10aO && e26aC < e26aO && e10aC >= e26aO && e10aO <= e26aC) s = 1;\n"
    "\t\t\telse if (e10aC < e10aO && e26aC > e26aO && e10aC <= e26aO && e10aO >= e26aC) s = -1;\n"
    "\t\t\tif (s == 0) return;\n"
    "\t\t\tdouble sl = s == 1 ? e10aL - TickSize : e10aH + TickSize;\n"
    "\t\t\tdouble risk = (Close[0] - sl) * s;\n"
    "\t\t\tif (risk <= 0.02 * todayAtr || risk > 0.6 * todayAtr) return;\n"
    "\t\t\tSixEnter(eng26, s, sl, double.NaN);\n"
    "\t\t}\n"
    "\t\t// ORFAIL: 15-min opening range; a break of >= 0.1 ATR that closes back inside on a 5-minute close within 30 min (before 14:00)\n"
    "\t\t// -> trade back the other way with the trend, stop beyond the break extreme, target the opposite range side (research OR_FAIL #142)\n"
    "\t\tprivate void OrfTrack(int openMin)\n\t\t{\n"
    "\t\t\tif (orfDone) return;\n"
    "\t\t\tif (openMin >= 570 && openMin < 585) { if (!orfHas) { orfH = High[0]; orfL = Low[0]; orfHas = true; } else { orfH = Math.Max(orfH, High[0]); orfL = Math.Min(orfL, Low[0]); } if (openMin == 584) orfReady = true; return; }\n"
    "\t\t\tif (!orfReady || openMin < 585) return;\n"
    "\t\t\tif (openMin >= 840 || double.IsNaN(todayAtr) || todayAtr <= 0) { orfDone = true; return; }\n"
    "\t\t\tdouble A = todayAtr;\n"
    "\t\t\tif (orfBrk == 0)\n\t\t\t{\n"
    "\t\t\t\tif (High[0] > orfH + 0.1 * A) { orfBrk = 1; orfExt = High[0]; orfBi = CurrentBars[0]; }\n"
    "\t\t\t\telse if (Low[0] < orfL - 0.1 * A) { orfBrk = -1; orfExt = Low[0]; orfBi = CurrentBars[0]; }\n"
    "\t\t\t\tif (orfBrk == 0) return;\n"
    "\t\t\t}\n"
    "\t\t\telse orfExt = orfBrk == 1 ? Math.Max(orfExt, High[0]) : Math.Min(orfExt, Low[0]);\n"
    "\t\t\tif (CurrentBars[0] - orfBi > 30) { orfDone = true; return; }\n"
    "\t\t\tif ((openMin - 570) % 5 != 4) return;\n"
    "\t\t\tif (orfBrk == 1 ? Close[0] >= orfH : Close[0] <= orfL) return;\n"
    "\t\t\torfDone = true;\n"
    "\t\t\tint s = -orfBrk;\n"
    "\t\t\tif (s != trendDir) return;\n"
    "\t\t\tdouble sl = orfBrk == 1 ? orfExt + TickSize : orfExt - TickSize;\n"
    "\t\t\tdouble risk = (Close[0] - sl) * s, tp = s == -1 ? orfL : orfH;\n"
    "\t\t\tif (risk < 0.03 * A || risk > 0.4 * A || (tp - Close[0]) * s <= TickSize) return;\n"
    "\t\t\torfSig = s; orfSl = sl; orfTp = tp;\n"
    "\t\t}\n"
    "\t\t// CAM3: Camarilla L3 (uptrend) / H3 (downtrend) untouched from 18:00 to 10:00; between 10:00 and 15:30 a break of the level\n"
    "\t\t// that closes back within 10 bars -> fade it, stop 0.02 ATR beyond the break extreme, target the RTH VWAP (research PIVOT_FADE #365)\n"
    "\t\tprivate void Cam3Track(int openMin)\n\t\t{\n"
    "\t\t\tif (camDone || double.IsNaN(camLev)) return;\n"
    "\t\t\tif (openMin >= 1080 || openMin < 600) { if (camSide == 1 ? Low[0] < camLev : High[0] > camLev) camDone = true; return; }\n"
    "\t\t\tif (openMin >= 930) { camDone = true; return; }\n"
    "\t\t\tif (camBr < 0) { if (camSide == 1 ? Low[0] < camLev : High[0] > camLev) { camBr = CurrentBars[0]; camExt = camSide == 1 ? Low[0] : High[0]; } else return; }\n"
    "\t\t\tcamExt = camSide == 1 ? Math.Min(camExt, Low[0]) : Math.Max(camExt, High[0]);\n"
    "\t\t\tif (camSide == 1 ? Close[0] > camLev : Close[0] < camLev)\n\t\t\t{\n"
    "\t\t\t\tcamDone = true;\n"
    "\t\t\t\tdouble A = todayAtr, sl = camExt - camSide * 0.02 * A, risk = (Close[0] - sl) * camSide, vw = vwV > 0 ? vwPv / vwV : double.NaN;\n"
    "\t\t\t\tif (risk > 0 && !double.IsNaN(vw) && (vw - Close[0]) * camSide > 0.25 * risk) { camSig = camSide; camSl = sl; camTp = vw; }\n"
    "\t\t\t\treturn;\n"
    "\t\t\t}\n"
    "\t\t\tif (CurrentBars[0] - camBr >= 10) camDone = true;\n"
    "\t\t}\n\n"
    "\t\tprivate void TimeEntry(Mod m)\n")
# ---- properties (group 11)
rep("\t\t[NinjaScriptProperty][Display(Name = \"LATEFH on (15:00, first half hour + RTH move agree; Ultra)\"",
    "\t\t[NinjaScriptProperty][Display(Name = \"Six-year modules on (Ultra: CA04V SO04 GD03 RV11 ENG26 ORFAIL CAM3 + LATEFH; test first, 2026-10-16)\", Order = 1, GroupName = \"11. Six-year modules (2020-26)\")] public bool SixYearModules { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"CA04V on (04:00 momentum vs session VWAP, >= 0.20 ATR, stop 0.15 ATR, 1R)\", Order = 2, GroupName = \"11. Six-year modules (2020-26)\")] public bool UseCa04v { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"SO04 on (04:00 momentum vs 18:00 open, >= 0.35 ATR, with trend, 1R)\", Order = 3, GroupName = \"11. Six-year modules (2020-26)\")] public bool UseSo04 { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"GD03 on (05:00 fade of the move since 03:00, with trend, 2R)\", Order = 4, GroupName = \"11. Six-year modules (2020-26)\")] public bool UseGd03 { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"RV11 on (11:00 low relative volume continuation vs prior close, 1R)\", Order = 5, GroupName = \"11. Six-year modules (2020-26)\")] public bool UseRv11 { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"ENG26 on (4H 02-06 engulfs 22-02, entry 09:30, 0.5R)\", Order = 6, GroupName = \"11. Six-year modules (2020-26)\")] public bool UseEng26 { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"ORFAIL on (failed 15-min opening-range break, with trend)\", Order = 7, GroupName = \"11. Six-year modules (2020-26)\")] public bool UseOrFail { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"CAM3 on (Camarilla L3/H3 fade to VWAP, with trend)\", Order = 8, GroupName = \"11. Six-year modules (2020-26)\")] public bool UseCam3 { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"LATEFH on (15:00, first half hour + RTH move agree; Ultra)\"")
open(os.path.join(ROOT, "NQMaster.cs"), "w", encoding="utf-8").write(src)
print("NQMaster.cs patched")
