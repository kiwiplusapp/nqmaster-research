"""Patch NQMaster.cs: 'Ultra ampliado' (research/mine/ultra_plus.py, ampliado_mc.py) - more trades/day at the same WR / PF.
ENG10  : 4H candle 06:00-10:00 closes beyond the 02:00-06:00 candle's extreme in its direction AND with the daily trend ->
         10:00-11:30 stop entry 1 tick beyond it, stop at half its range, target 0.5R, max 400 min (ENGULF_4H 1172).
LATEFH : 15:00, first half hour (10:00 close vs prior RTH close) and the RTH move agree, both >= 0.25 ATR -> continue,
         stop 0.20 ATR, target 0.5R (LATE_MOM 1107). VW13 wide (Ultra): 0.15 ATR from VWAP, x2 at 0.30 (as WR70Plus)."""
p = r"D:\NinjaTrader Strategy\NQMaster.cs"
s = open(p, encoding="utf-8").read()
def rep(a, b, cnt=1):
    global s
    n = s.count(a); assert n == cnt, (n, a[:90]); s = s.replace(a, b)
rep("\t\t\tpublic bool BaseOn;\n", "\t\t\tpublic bool BaseOn; public bool FhCheck;\n")
rep("\t\tprivate Mod orb, orb2, mseq, mseqs, crt, lon, ict, rsi, volb;\n",
    "\t\tprivate Mod orb, orb2, mseq, mseqs, crt, lon, ict, rsi, volb, eng10;\n\t\tprivate double e10aO, e10aH, e10aL, e10aC, e10bO, e10bH, e10bL, e10bC, close10 = double.NaN; private bool e10aHas, e10bHas, eng10Done;\n")
rep("UseVw13 = true; UseVolBreak = true; UseLate15 = true;", "UseVw13 = true; UseVolBreak = true; UseLate15 = true; UseEng10 = true; UseLateFh = true; Vw13Wide = true;")
rep("vw13.MinDist = w7 ? 0.15 : 0.30; vw13.DoubleDist = w7 ? 0.30 : 0;", "bool vwWide = w7 || (ul && Vw13Wide); vw13.MinDist = vwWide ? 0.15 : 0.30; vw13.DoubleDist = vwWide ? 0.30 : 0;")
rep("late15.MinDist = 0.5;\n", "late15.MinDist = 0.5;\n\t\t\tMod latefh = AddTime(\"LATEFH\", (custom ? UseLateFh : ul && UseLateFh), 1500, -2, false, 0.20, 0.5, 0, false, false); latefh.MinDist = 0.25; latefh.FhCheck = true;\n\t\t\teng10 = NewMod(\"ENG10\", (custom ? UseEng10 : ul && UseEng10), 0.5); eng10.PriceTarget = true; eng10.MaxHold = 400;\n")
# candle tracking (every 1-minute bar) right after the session high / low update
rep("\t\t\tsessHi = Math.Max(sessHi, High[0]); sessLo = Math.Min(sessLo, Low[0]);\n",
    "\t\t\tsessHi = Math.Max(sessHi, High[0]); sessLo = Math.Min(sessLo, Low[0]);\n"
    "\t\t\tif (openMin >= 120 && openMin < 360) { if (!e10aHas) { e10aO = Open[0]; e10aH = High[0]; e10aL = Low[0]; e10aHas = true; } e10aH = Math.Max(e10aH, High[0]); e10aL = Math.Min(e10aL, Low[0]); e10aC = Close[0]; }\n"
    "\t\t\telse if (openMin >= 360 && openMin < 600) { if (!e10bHas) { e10bO = Open[0]; e10bH = High[0]; e10bL = Low[0]; e10bHas = true; } e10bH = Math.Max(e10bH, High[0]); e10bL = Math.Min(e10bL, Low[0]); e10bC = Close[0]; }\n"
    "\t\t\tif (openMin == 599) close10 = Close[0];\n")
rep("\t\t\tvolbDone = false; volbUp = double.NaN; volbDn = double.NaN;\n", "\t\t\tvolbDone = false; volbUp = double.NaN; volbDn = double.NaN;\n\t\t\te10aHas = false; e10bHas = false; eng10Done = false; close10 = double.NaN;\n")
rep("\t\t\tif (volb.InTrade && CurrentBars[0] - volb.EntryBar >= volb.MaxHold) ExitModule(volb, \"time exit\");\n",
    "\t\t\tif (volb.InTrade && CurrentBars[0] - volb.EntryBar >= volb.MaxHold) ExitModule(volb, \"time exit\");\n\t\t\tif (eng10.InTrade && CurrentBars[0] - eng10.EntryBar >= eng10.MaxHold) ExitModule(eng10, \"time exit\");\n")
rep("\t\t\tif (volb.On && inRth && etDate == rthDay) ManageVolb(openMin);\n", "\t\t\tif (volb.On && inRth && etDate == rthDay) ManageVolb(openMin);\n\t\t\tif (eng10.On) ManageEng10(openMin);\n")
rep("\t\t\t\tif (m == volb) { volbDone = true; volb.EntryBar = CurrentBars[0]; }\n", "\t\t\t\tif (m == volb) { volbDone = true; volb.EntryBar = CurrentBars[0]; }\n\t\t\t\tif (m == eng10) eng10.EntryBar = CurrentBars[0];\n")
rep("\t\t\tif (m.MinDist > 0 && Math.Abs(Close[0] - reference) < m.MinDist * atrDaily) return;\n",
    "\t\t\tif (m.MinDist > 0 && Math.Abs(Close[0] - reference) < m.MinDist * atrDaily) return;\n"
    "\t\t\tif (m.FhCheck)\n\t\t\t{\n\t\t\t\tif (double.IsNaN(close10) || double.IsNaN(full1)) return;\n\t\t\t\tdouble fh = close10 - full1;\n"
    "\t\t\t\tif ((fh > 0 ? 1 : -1) != (Close[0] > reference ? 1 : -1) || Math.Abs(fh) < m.MinDist * atrDaily) return;\n\t\t\t}\n")
eng = r'''
		// ENG10 (research/mine/ultra_plus.py): 06:00-10:00 4H candle closes beyond the 02:00-06:00 candle in its direction, with the trend.
		private void ManageEng10(int openMin)
		{
			if (eng10Done || eng10.InTrade)
			{
				if (Working(eng10.Entry) && openMin >= 689 && openMin < 18 * 60) { CancelOrder(eng10.Entry); Log("ENG10 entry expired"); }
				return;
			}
			if (openMin != 599) return;
			eng10Done = true;
			if (!e10aHas || !e10bHas || atrCount < 14 || double.IsNaN(todayAtr) || todayAtr <= 0 || trendDir == 0) return;
			int d = 0;
			if (e10bC > e10bO && e10bC > e10aH) d = 1; else if (e10bC < e10bO && e10bC < e10aL) d = -1;
			if (d == 0 || d != trendDir) return;
			double px = Instrument.MasterInstrument.RoundToTickSize(d == 1 ? e10bH + TickSize : e10bL - TickSize);
			if ((d == 1 && Close[0] >= px) || (d == -1 && Close[0] <= px)) return;
			double sl = Instrument.MasterInstrument.RoundToTickSize(px - d * 0.5 * (e10bH - e10bL)), risk = (px - sl) * d;
			if (risk <= 0.02 * todayAtr || risk > 0.6 * todayAtr) return;
			if (!DirectionAllowed(d)) return;
			ArmPriceBracket(eng10, d, sl);
			if (d == 1) EnterLongStopMarket(0, true, Qty(), px, eng10.Sig); else EnterShortStopMarket(0, true, Qty(), px, eng10.Sig);
			Log(string.Format("ENG10 {0} STOP @ {1} | SL {2}", d == 1 ? "BUY" : "SELL", Fmt(px), Fmt(sl)));
		}
'''
rep("\t\tprivate void TimeEntry(Mod m)\n", eng + "\n\t\tprivate void TimeEntry(Mod m)\n")
rep('''		[NinjaScriptProperty][Display(Name = "LATE15 on (15:00 trend-day continuation; Ultra / WR70Plus / Core)", Order = 18, GroupName = "01. Module switches (any profile)")] public bool UseLate15 { get; set; }''',
    '''		[NinjaScriptProperty][Display(Name = "LATE15 on (15:00 trend-day continuation; Ultra / WR70Plus / Core)", Order = 18, GroupName = "01. Module switches (any profile)")] public bool UseLate15 { get; set; }
		[NinjaScriptProperty][Display(Name = "ENG10 on (06-10 4H candle breakout with the trend; Ultra)", Order = 19, GroupName = "01. Module switches (any profile)")] public bool UseEng10 { get; set; }
		[NinjaScriptProperty][Display(Name = "LATEFH on (15:00, first half hour + RTH move agree; Ultra)", Order = 20, GroupName = "01. Module switches (any profile)")] public bool UseLateFh { get; set; }
		[NinjaScriptProperty][Display(Name = "VW13 wide on Ultra (0.15 ATR, x2 at 0.30)", Order = 21, GroupName = "01. Module switches (any profile)")] public bool Vw13Wide { get; set; }''')
open(p, "w", encoding="utf-8", newline="\n").write(s); print("patched")
