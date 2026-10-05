p = r"D:\NinjaTrader Strategy\NQMaster.cs"; s = open(p, encoding="utf-8").read()
def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (a[:100], s.count(a)); s = s.replace(a, b)
rep("Custom, MaxTrades, MaxPlus, MaxPlus2 }", "Custom, MaxTrades, MaxPlus, MaxPlus2, Ultra }")
rep("//   MaxPlus2  : MaxPlus", "//   Ultra     : MaxPlus2 + VOLB (L. Williams volatility breakout: stop entries at RTH open +/- 0.45 x prior RTH range, stop at the\n//               RTH open, 2R, both directions; robust 2015-2026 cost-normalised; big stop -> NOT for 25K accounts)\n//   MaxPlus2  : MaxPlus")
rep("private Mod orb, orb2, mseq, mseqs, crt, lon, ict, rsi;", "private Mod orb, orb2, mseq, mseqs, crt, lon, ict, rsi, volb;\n\t\tprivate double volbUp = double.NaN, volbDn = double.NaN; private bool volbDone;")
rep("bool mt = Profile == NQMasterProfile.MaxTrades, mp2 = Profile == NQMasterProfile.MaxPlus2, mp =",
    "bool mt = Profile == NQMasterProfile.MaxTrades, ul = Profile == NQMasterProfile.Ultra, mp2 = Profile == NQMasterProfile.MaxPlus2 || ul, mp =")
rep('''			rsi = NewMod("RSI2",''', '''			volb = NewMod("VOLB", (custom ? UseVolBreak : (ul) && UseVolBreak), 2.0); volb.PriceTarget = true; volb.MaxHold = 400;
			rsi = NewMod("RSI2",''')
# levels at the first RTH bar
rep("if (!dayHasBars) { dayHigh = High[0]; dayLow = Low[0]; dayHasBars = true; rthOpenPx = Open[0]; SetupIctLevels(); }",
    "if (!dayHasBars) { dayHigh = High[0]; dayLow = Low[0]; dayHasBars = true; rthOpenPx = Open[0]; SetupIctLevels();\n\t\t\t\t\tdouble prng = prevRthHigh - prevRthLow; volbUp = double.IsNaN(prng) ? double.NaN : rthOpenPx + 0.45 * prng; volbDn = double.IsNaN(prng) ? double.NaN : rthOpenPx - 0.45 * prng; }")
rep("			rsiTrades = 0;\n", "			rsiTrades = 0;\n			volbDone = false; volbUp = double.NaN; volbDn = double.NaN;\n")
# time exit for VOLB
rep("			if (rsi.InTrade && CurrentBars[0] - rsi.EntryBar >= rsi.MaxHold) ExitModule(rsi, \"time exit\");\n",
    "			if (rsi.InTrade && CurrentBars[0] - rsi.EntryBar >= rsi.MaxHold) ExitModule(rsi, \"time exit\");\n			if (volb.InTrade && CurrentBars[0] - volb.EntryBar >= volb.MaxHold) ExitModule(volb, \"time exit\");\n")
# manage VOLB each 1m bar
rep("			if (lon.On && overnight && openMin < RthOpen) LondonStep(openMin);\n",
    "			if (lon.On && overnight && openMin < RthOpen) LondonStep(openMin);\n			if (volb.On && inRth && etDate == rthDay) ManageVolb(openMin);\n")
rep("		private void TimeEntry(Mod m)\n", """		// ---- VOLB: one stop entry per day at RTH open +/- 0.45 x prior RTH range (the side nearer to price is kept working),
		// stop at the RTH open price, target 2R, max 400 min, 09:30-15:00 entries (research/mine/families2.py, VOL_BREAK).
		private void ManageVolb(int openMin)
		{
			if (volbDone || volb.InTrade || double.IsNaN(volbUp) || double.IsNaN(rthOpenPx) || atrCount < 14) return;
			if (openMin >= 900) { if (Working(volb.Entry)) CancelOrder(volb.Entry); volbDone = true; return; }
			int d = (volbUp - Close[0]) <= (Close[0] - volbDn) ? 1 : -1;
			if (Working(volb.Entry))
			{
				if (volb.Dir == d) return;
				CancelOrder(volb.Entry); return;                    // switch side on the next bar
			}
			double lvl = d == 1 ? Instrument.MasterInstrument.RoundToTickSize(volbUp) : Instrument.MasterInstrument.RoundToTickSize(volbDn);
			if ((d == 1 && Close[0] >= lvl) || (d == -1 && Close[0] <= lvl)) { volbDone = true; return; }   // already through: no chase
			if (!DirectionAllowed(d)) return;
			ArmPriceBracket(volb, d, Instrument.MasterInstrument.RoundToTickSize(rthOpenPx));
			if (d == 1) EnterLongStopMarket(0, true, Qty(), lvl, volb.Sig); else EnterShortStopMarket(0, true, Qty(), lvl, volb.Sig);
		}

		private void TimeEntry(Mod m)
""")
rep("				if (m == orb2) orb2.Trades++;\n", "				if (m == orb2) orb2.Trades++;\n				if (m == volb) { volbDone = true; volb.EntryBar = CurrentBars[0]; }\n")
rep("IctMultiplier = 2; UseConfluence = true; UseContextRules = true; UseVw13 = true;", "IctMultiplier = 2; UseConfluence = true; UseContextRules = true; UseVw13 = true; UseVolBreak = true;")
rep('''		[NinjaScriptProperty][Display(Name = "VW13 on ", Order = 18,''', '''		[NinjaScriptProperty][Display(Name = "VOLB on ", Order = 19, GroupName = "01. Module switches (any profile)")] public bool UseVolBreak { get; set; }
		[NinjaScriptProperty][Display(Name = "VW13 on ", Order = 18,''')
rep("(Profile == NQMasterProfile.MaxPlus || Profile == NQMasterProfile.MaxPlus2 || Profile == NQMasterProfile.Custom)",
    "(Profile == NQMasterProfile.MaxPlus || Profile == NQMasterProfile.MaxPlus2 || Profile == NQMasterProfile.Ultra || Profile == NQMasterProfile.Custom)")
rep("UseContextRules && (Profile == NQMasterProfile.MaxPlus2 || Profile == NQMasterProfile.Custom)", "UseContextRules && (Profile == NQMasterProfile.MaxPlus2 || Profile == NQMasterProfile.Ultra || Profile == NQMasterProfile.Custom)")
rep("int iq = Qty() * ((Profile == NQMasterProfile.MaxPlus || Profile == NQMasterProfile.Custom) ? IctMultiplier : 1);",
    "int iq = Qty() * ((Profile == NQMasterProfile.MaxPlus || Profile == NQMasterProfile.MaxPlus2 || Profile == NQMasterProfile.Ultra || Profile == NQMasterProfile.Custom) ? IctMultiplier : 1);")
open(p, "w", encoding="utf-8", newline="").write(s); print("patched")
