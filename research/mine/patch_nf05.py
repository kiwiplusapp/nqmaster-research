"""NQMaster: overnight fade modules from the gold G_DRIVE family mined on NQ (gnq_check.py, gnq_port.py, gnq_lc.py).
  NF05   : at 05:00 ET, if the move since the 20:00 bar open is >= 0.35 x daily ATR -> FADE it (market), stop 0.2 ATR, target 2R,
           max 240 min, any direction. IS / C24 / REAL PF 1.65 / 1.32 / 1.33, 2015-19 (cost-normalised) 1.61, +4 ticks/side 1.29.
           Ultra Sharpe 3.12/3.37/3.59 -> 3.21/3.38/3.62; Lucid lifecycle 150K 6c/3c $1,984 -> $2,069 / month per account (8 of 9 tests
           better), 50K 2c/2c $1,311 -> $1,362. ON in Ultra.
  LF0315 : at 03:15, move since the 03:00 open >= 0.10 ATR -> fade, stop 0.2 ATR, 2R, max 600 min. Trade-level Sharpe +0.05-0.12 but the
           lifecycle gain is mixed -> OFF by default (switch).
New time-module reference: Lookback -5 = open of the bar at the module's anchor time (first bar within 5 minutes of it)."""
p = r"D:\NinjaTrader Strategy\NQMaster.cs"
s = open(p, encoding="utf-8").read()
def rep(a, b):
    global s
    n = s.count(a); assert n == 1, (n, a[:100]); s = s.replace(a, b)
rep("\t\t\tpublic bool Parked, ParkLimit;", "\t\t\tpublic int Anchor = -1; public double AnchorPx = double.NaN;	// Lookback -5: open of the bar at the anchor time (ET minutes)\n\t\t\tpublic bool Parked, ParkLimit;")
rep("UseLateFh = true; Vw13Wide = true;", "UseLateFh = true; Vw13Wide = true; UseNf05 = true; UseLf0315 = false;")
rep("\t\t\tMod latefh = AddTime(\"LATEFH\", (custom ? UseLateFh : ul && UseLateFh), 1500, -4, false, 0.20, 0.5, 0, false, false); latefh.MinDist = 0.25; latefh.FhCheck = true;\n",
    "\t\t\tMod latefh = AddTime(\"LATEFH\", (custom ? UseLateFh : ul && UseLateFh), 1500, -4, false, 0.20, 0.5, 0, false, false); latefh.MinDist = 0.25; latefh.FhCheck = true;\n"
    "\t\t\tMod nf05 = AddTime(\"NF05\", (custom ? UseNf05 : ul && UseNf05), 500, -5, true, 0.20, 2.0, 240, false, false); nf05.MinDist = 0.35; nf05.Anchor = 20 * 60;\n"
    "\t\t\tMod lf0315 = AddTime(\"LF0315\", (custom ? UseLf0315 : ul && UseLf0315), 315, -5, true, 0.20, 2.0, 600, false, false); lf0315.MinDist = 0.10; lf0315.Anchor = 3 * 60;\n")
rep("\t\t\telse if (m.Lookback == -4) { if (double.IsNaN(full1)) return; reference = rthFirstClose; }\n",
    "\t\t\telse if (m.Lookback == -4) { if (double.IsNaN(full1)) return; reference = rthFirstClose; }\n\t\t\telse if (m.Lookback == -5) reference = m.AnchorPx;\n")
# capture the anchor bar's open (first bar opening within 5 minutes after the anchor), reset each session
rep("\t\t\tif (openMin == 599) close10 = Close[0];\n",
    "\t\t\tif (openMin == 599) close10 = Close[0];\n"
    "\t\t\tforeach (Mod m in timeMods) if (m.Anchor >= 0 && double.IsNaN(m.AnchorPx) && openMin >= m.Anchor && openMin <= m.Anchor + 5) m.AnchorPx = Open[0];\n")
rep("\t\t\tforeach (Mod m in timeMods) { m.Done = false; m.Retry = false; }\n", "\t\t\tforeach (Mod m in timeMods) { m.Done = false; m.Retry = false; m.AnchorPx = double.NaN; }\n")
rep("\t\t[NinjaScriptProperty][Display(Name = \"VW13 wide on Ultra (0.15 ATR, x2 at 0.30)\", Order = 21, GroupName = \"01. Module switches (any profile)\")] public bool Vw13Wide { get; set; }",
    "\t\t[NinjaScriptProperty][Display(Name = \"VW13 wide on Ultra (0.15 ATR, x2 at 0.30)\", Order = 21, GroupName = \"01. Module switches (any profile)\")] public bool Vw13Wide { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"NF05 on (05:00 fade of the move since 20:00; Ultra)\", Order = 22, GroupName = \"01. Module switches (any profile)\")] public bool UseNf05 { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"LF0315 on (03:15 fade of the London first 15 min; Ultra, off by default)\", Order = 23, GroupName = \"01. Module switches (any profile)\")] public bool UseLf0315 { get; set; }")
open(p, "w", encoding="utf-8", newline="\n").write(s); print("patched")
