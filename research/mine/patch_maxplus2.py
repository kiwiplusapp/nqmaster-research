p = r"D:\NinjaTrader Strategy\NQMaster.cs"; s = open(p, encoding="utf-8").read()
def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (a[:100], s.count(a)); s = s.replace(a, b)
rep("Custom, MaxTrades, MaxPlus }", "Custom, MaxTrades, MaxPlus, MaxPlus2 }")
rep("//   MaxPlus   : MaxSharpe (NQ)", "//   MaxPlus2  : MaxPlus + context-sized rules (x2 / skip, research/mine/filt_holdout.py) + VW13 (13:01 VWAP-distance momentum, 0.5R)\n//   MaxPlus   : MaxSharpe (NQ)")
rep("public bool Trend; public bool Vwap; public bool Done;", "public bool Trend; public bool Vwap; public bool Done; public double MinDist;")
rep("bool mt = Profile == NQMasterProfile.MaxTrades, mp = Profile == NQMasterProfile.MaxPlus, ms =",
    "bool mt = Profile == NQMasterProfile.MaxTrades, mp2 = Profile == NQMasterProfile.MaxPlus2, mp = Profile == NQMasterProfile.MaxPlus || mp2, ms =")
rep('''			AddTime("MOM1130", (custom ? UseMom1130 : (mt) && UseMom1130), 1130, -2, false, 0.25, 0.3, 0, false, true);
''', '''			AddTime("MOM1130", (custom ? UseMom1130 : (mt) && UseMom1130), 1130, -2, false, 0.25, 0.3, 0, false, true);
			AddTime("VW13", (custom ? UseVw13 : (mp2) && UseVw13), 1301, -3, false, 0.15, 0.5, 120, true, false).MinDist = 0.30;
''')
rep("private void AddTime(string sig, bool on, int t, int lb, bool rev, double sa, double r, int hold, bool trend, bool vwap)",
    "private Mod AddTime(string sig, bool on, int t, int lb, bool rev, double sa, double r, int hold, bool trend, bool vwap)")
rep("			mods.Add(m); timeMods.Add(m);\n		}", "			mods.Add(m); timeMods.Add(m); return m;\n		}")
rep("				NewSession();\n			}\n			bool inRth", "				NewSession();\n				sessHi = High[0]; sessLo = Low[0];\n			}\n			sessHi = Math.Max(sessHi, High[0]); sessLo = Math.Min(sessLo, Low[0]);\n			bool inRth")
rep("			todayAtr = atrDaily;\n			prevRet =", "			todayAtr = atrDaily;\n			atrRatio = double.NaN;\n			if (atrHist.Count >= 20 && todayAtr > 0) { List<double> srt = new List<double>(atrHist); srt.Sort(); int nn = srt.Count; double med = nn % 2 == 1 ? srt[nn / 2] : 0.5 * (srt[nn / 2 - 1] + srt[nn / 2]); atrRatio = med > 0 ? todayAtr / med : double.NaN; }\n			if (!double.IsNaN(todayAtr)) { atrHist.Add(todayAtr); while (atrHist.Count > 100) atrHist.RemoveAt(0); }\n			prevRet =")
rep("				rthCloses = new List<double>();", "				rthCloses = new List<double>(); atrHist = new List<double>();")
rep("			else if (m.Lookback == -2) reference = rthOpenPx;\n", "			else if (m.Lookback == -2) reference = rthOpenPx;\n			else if (m.Lookback == -3) reference = vwV > 0 ? vwPv / vwV : double.NaN;\n")
rep("			if (m.Trend && d != trendDir) return;\n", "			if (m.Trend && d != trendDir) return;\n			if (m.MinDist > 0 && Math.Abs(Close[0] - reference) < m.MinDist * atrDaily) return;\n			if (CtxOn && m.Sig == \"ON07\" && FeatPdRet(d) < -0.3619) { Log(\"ON07 skipped: prior day moved against (context rule)\"); return; }\n")
rep("if (d == 1) EnterLong(0, LateQty(1, 720), crt.Sig); else EnterShort(0, LateQty(-1, 720), crt.Sig);",
    "int cq = CtxBoost(LateQty(d, 720), FeatTrend(d) >= 1.7456 || FeatGap(d) >= 0.1048 || FeatPdRet(d) >= 0.6155, \"CRT11\");\n\t\t\tif (d == 1) EnterLong(0, cq, crt.Sig); else EnterShort(0, cq, crt.Sig);")
rep("EnterLong(0, LateQty(1, closeMin), mseq.Sig);", "EnterLong(0, CtxBoost(LateQty(1, closeMin), FeatPos(1, Closes[0][0]) >= 0.9686 || FeatM30(1) >= 0.1728 || FeatRet5(1) >= 2.0674, \"MSEQ\"), mseq.Sig);")
rep("			bool through = d == 1 ? Close[0] >= entry : Close[0] <= entry;\n			o.Dir = d;\n",
    "			bool through = d == 1 ? Close[0] >= entry : Close[0] <= entry;\n			o.Dir = d;\n			bool oc = o == orb ? (FeatGap(d) >= 0.3311 || FeatRet5(d) >= 1.8118 || atrRatio >= 1.2615) : (FeatVw(d, entry) < 0.1231 || FeatOpen(d, entry) >= 0.5458);\n			int oq = CtxBoost(Qty(), oc, o.Sig);\n")
rep("			if (d == 1) { if (through) EnterLong(0, Qty(), o.Sig); else EnterLongStopMarket(0, true, Qty(), entry, o.Sig); }\n			else { if (through) EnterShort(0, Qty(), o.Sig); else EnterShortStopMarket(0, true, Qty(), entry, o.Sig); }",
    "			if (d == 1) { if (through) EnterLong(0, oq, o.Sig); else EnterLongStopMarket(0, true, oq, entry, o.Sig); }\n			else { if (through) EnterShort(0, oq, o.Sig); else EnterShortStopMarket(0, true, oq, entry, o.Sig); }")
rep("private bool RulesOn { get { return UseConfluence && (Profile == NQMasterProfile.MaxPlus || Profile == NQMasterProfile.Custom); } }",
    """private bool RulesOn { get { return UseConfluence && (Profile == NQMasterProfile.MaxPlus || Profile == NQMasterProfile.MaxPlus2 || Profile == NQMasterProfile.Custom); } }

		// ---- context rules (MaxPlus2; research/mine/filt_mine.py + filt_holdout.py): thresholds chosen on CFD 2020-23 (tertiles/quintiles),
		// kept only if they also held in 2024-25 on CFD AND real MNQ; 2026 was a clean holdout (PF 1.50 -> 1.58 real, 1.42 -> 1.49 CFD).
		// Boosts double the size (never above 2x the base size), the ON07 rule skips the trade. Features are in daily-ATR units,
		// oriented with the trade direction d.
		private double sessHi, sessLo, atrRatio = double.NaN;
		private List<double> atrHist;
		private bool CtxOn { get { return UseContextRules && (Profile == NQMasterProfile.MaxPlus2 || Profile == NQMasterProfile.Custom); } }
		private int CtxBoost(int q, bool cond, string who)
		{
			if (!CtxOn || !cond) return q;
			int cap = 2 * Qty();
			if (q >= cap) return q;
			Log(who + " context x2"); return cap;
		}
		private double LastClose(int back) { int n = rthCloses.Count; return n > back ? rthCloses[n - 1 - back] : double.NaN; }
		private double FeatTrend(int d)
		{
			if (rthCloses.Count < 15 || double.IsNaN(todayAtr) || todayAtr <= 0) return double.NaN;
			double sm = 0; foreach (double x in rthCloses) sm += x; sm /= rthCloses.Count;
			return (LastClose(0) - sm) * d / todayAtr;
		}
		private double FeatGap(int d) { return (double.IsNaN(rthOpenPx) || todayAtr <= 0) ? double.NaN : (rthOpenPx - LastClose(0)) * d / todayAtr; }
		private double FeatPdRet(int d) { return (double.IsNaN(full1) || double.IsNaN(full2) || todayAtr <= 0) ? double.NaN : (full1 - full2) * d / todayAtr; }
		private double FeatRet5(int d) { return todayAtr > 0 ? (LastClose(0) - LastClose(5)) * d / todayAtr : double.NaN; }
		private double FeatPos(int d, double px) { return sessHi > sessLo ? (d == 1 ? (px - sessLo) : (sessHi - px)) / (sessHi - sessLo) : double.NaN; }
		private double FeatM30(int d) { return (CurrentBars[0] > 31 && todayAtr > 0) ? (Closes[0][0] - Closes[0][30]) * d / todayAtr : double.NaN; }
		private double FeatVw(int d, double px) { return (vwV > 0 && todayAtr > 0) ? (px - vwPv / vwV) * d / todayAtr : double.NaN; }
		private double FeatOpen(int d, double px) { return (double.IsNaN(rthOpenPx) || todayAtr <= 0) ? double.NaN : (px - rthOpenPx) * d / todayAtr; }""")
rep("IctMultiplier = 2; UseConfluence = true;", "IctMultiplier = 2; UseConfluence = true; UseContextRules = true; UseVw13 = true;")
rep('''		[NinjaScriptProperty][Display(Name = "Confluence rules (MaxPlus/Custom)''', '''		[NinjaScriptProperty][Display(Name = "Context rules (MaxPlus2/Custom): x2 ORB60/ORB90/CRT11/MSEQ in favourable context, skip ON07 after a counter day", Order = 45, GroupName = "03. Risk / account")] public bool UseContextRules { get; set; }
		[NinjaScriptProperty][Display(Name = "VW13 on ", Order = 18, GroupName = "01. Module switches (any profile)")] public bool UseVw13 { get; set; }
		[NinjaScriptProperty][Display(Name = "Confluence rules (MaxPlus/Custom)''')
open(p, "w", encoding="utf-8", newline="").write(s); print("patched")
