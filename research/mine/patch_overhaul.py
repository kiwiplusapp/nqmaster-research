"""2026-10-12 overhaul of NQMaster.cs (Federico: robustness, PF / WR, remove unneeded profiles). Research: robust2_*.py,
cand16.py, cand16_life.py, rules16_*.py, monitor_recal.py, hist_profiles.md.
 - profiles: Ultra / WR70Plus / Durable (new, 16-year durable modules) / Custom; MaxSharpe, WinRate70, Gold, MaxTrades, MaxPlus,
   MaxPlus2 and Core removed (dominated or superseded; GoldMaster replaces Gold)
 - Ultra defaults: ENG10 and LATEFH off (UseEng10 / UseLateFh false)
 - context boosts ORB60 'ATR ratio' and ORB90 'near VWAP' removed (did not hold on 2010-19 nor 2024-26)
 - MinStopAtr 0.10: structure modules skip trades whose stop is < 0.10 x daily ATR (WR +0.4-0.8 in all 4 periods)
 - risk cap by cushion: in PropMode Eval / Funded, while the day-start cushion is below EvalRiskCapCushion (1,200) /
   FundedRiskCapCushion (2,000), trades risking more than RiskCapPerContract ($300) per base contract are skipped
 - edge monitor recalibrated (Ultra 0.0758 / 18.57, WR70Plus 0.0577 / 12.18, Durable 0.0458 / 10.71)
 - FundedCushionSafe default 0 (the risk cap replaces the SAFE set in the funded account)"""
import sys
P = sys.argv[1] if len(sys.argv) > 1 else "NQMaster.cs"
s = open(P, encoding="utf-8").read()


def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n: sys.exit(f"expected {n} x, found {c}: {a[:100]!r}")
    s = s.replace(a, b)


# ---------------- header
i0 = s.index("// Profiles (Profile parameter;"); i1 = s.index("// Account layer: FOMC days skipped")
s = s[:i0] + """// Profiles (Profile parameter; every module can still be switched on/off below):
//   Ultra     : default. ORB60 0.6R + ORB90 (pullback days), MSEQ, MSEQS, CRT11 2R, ICT x2, MOM11, MOM1030 / MOM13 (only with
//               another module open the same way), ON07, REV06, LON, VW13 wide, VOLB 2R, LATE15, night fades NF05 / LF06 / LF0430;
//               ENG10 / LATEFH off since 2026-10-12. Real NQ futures 2020-23 / 2024-26: WR 66.9 / 65.7%, PF 1.47 / 1.50,
//               Sharpe 3.38 / 3.65, ~4.7 trades/day, $1,700-2,300 per month per contract.
//   WR70Plus  : >= 70% win rate build: ORB60 0.75R, ORB90, MSEQ, MSEQS, CRT11, ICT x2, MOM11, REV06, VW13 wide, VOLB with the
//               trend at 0.5R, LATE15 (+ night fades with NightOnWr70). WR 72.2 / 69.4%, PF 1.57 / 1.48, ~3.3 trades/day.
//   Durable   : the 6 modules that held up on 16 years of real futures (2010-2026): ORB60, ORB90, MSEQS, CRT11, VOLB 2R, NF05.
//               PF 1.63, WR 62%, ~1.4 trades/day, cost-normalised PF 1.18 / 1.23 in 2010-14 / 2015-19. Fallback if the edge
//               monitor alarms or the post-2020 regime fades.
//   Custom    : every module switch and the ORB range / target / pullback settings apply.
// Risk layer (2026-10-12): structure stops >= 0.10 ATR; in prop accounts trades risking > $300 per contract are skipped while
// the cushion is small (fewer lost accounts: MyFundedFutures 2024-26 resampled 1.65 -> 0.70 per year per slot).
""" + s[i1:]

# ---------------- enum + defaults
rep("public enum NQMasterProfile { MaxSharpe, WinRate70, Gold, Custom, MaxTrades, MaxPlus, MaxPlus2, Ultra, WR70Plus, Core }",
    "public enum NQMasterProfile { Ultra, WR70Plus, Durable, Custom }")
rep("				Profile = NQMasterProfile.MaxSharpe;", "				Profile = NQMasterProfile.Ultra;")
rep("UseEng10 = true; UseLateFh = true;", "UseEng10 = false; UseLateFh = false;")
rep("FundedCushionSafe = 750;", "FundedCushionSafe = 0;")
rep("NewsBlackout = false; NewsTimes = \"\";\n",
    "NewsBlackout = false; NewsTimes = \"\";\n\t\t\t\tMinStopAtr = 0.10; RiskCapPerContract = 300; EvalRiskCapCushion = 1200; FundedRiskCapCushion = 2000;\n")

# ---------------- BuildModules
a = s.index("			bool w7 = Profile == NQMasterProfile.WR70Plus, mt ="); b = s.index("			rsi = NewMod(\"RSI2\"")
b = s.index("\n", b) + 1
s = s[:a] + """			bool w7 = Profile == NQMasterProfile.WR70Plus, ul = Profile == NQMasterProfile.Ultra, du = Profile == NQMasterProfile.Durable, custom = Profile == NQMasterProfile.Custom;
			profUltra = ul;
			mods = new List<Mod>(); timeMods = new List<Mod>();
			orb = new Mod(); orb.Sig = "ORB60"; orb.Kind = 0;
			orb.On = UseOrb;
			orb.Range = custom ? OrbRangeMin : 60;
			orb.R = custom ? OrbTargetR : (w7 ? 0.75 : 0.6);
			orb.UsePullback = custom ? OrbPullbackFilter : true;
			mods.Add(orb);
			orb2 = new Mod(); orb2.Sig = "ORB90"; orb2.Kind = 0; orb2.On = (custom ? UseOrb90 : (ul || w7 || du) && UseOrb90); orb2.Range = 90; orb2.R = 0.6; orb2.UsePullback = true;
			mods.Add(orb2);
			mseq = NewMod("MSEQ", (custom ? UseMseq : (ul || w7) && UseMseq), 0.5); mseq.PriceTarget = true;
			mseqs = NewMod("MSEQS", (custom ? UseMseqShort : (ul || w7 || du) && UseMseqShort), 0.75); mseqs.PriceTarget = true;
			crt = NewMod("CRT11", UseCrt, 2.0); crt.PriceTarget = true;
			lon = NewMod("LON", (custom ? UseLon : ul && UseLon), 2.0); lon.PriceTarget = true;
			ict = NewMod("ICT", (custom ? UseIct : (ul || w7) && UseIct), 1.0); ict.PriceTarget = true;
			AddTime("MOM11", (custom ? UseMom11 : (ul || w7) && UseMom11), 1100, -2, false, 0.25, 0.3, 0, false, true);
			AddTime("MOM13", (custom ? UseMom13 : ul && UseMom13), 1300, -2, false, 0.20, 1.0, 240, true, false);
			AddTime("MOM1030", (custom ? UseMom1030 : ul && UseMom1030), 1030, -2, false, 0.20, 0.3, 60, true, false);
			AddTime("ON07", (custom ? UseOn07 : ul && UseOn07), 700, 30, false, 0.20, 1.0, 60, true, false);
			AddTime("REV06", (custom ? UseRev06 : (ul || w7) && UseRev06), 600, 30, true, 0.20, 0.3, 240, true, false);
			AddTime("MOM1130", custom && UseMom1130, 1130, -2, false, 0.25, 0.3, 0, false, true);
			Mod vw13 = AddTime("VW13", (custom ? UseVw13 : (ul || w7) && UseVw13), 1301, -3, false, 0.15, 0.5, 120, true, false); bool vwWide = w7 || ((ul || custom) && Vw13Wide); vw13.MinDist = vwWide ? 0.15 : 0.30; vw13.DoubleDist = vwWide ? 0.30 : 0;
			Mod late15 = AddTime("LATE15", (custom ? UseLate15 : (ul || w7) && UseLate15), 1500, -4, false, 0.30, 0.5, 0, true, false); late15.MinDist = 0.5;
			Mod latefh = AddTime("LATEFH", (custom ? UseLateFh : ul && UseLateFh), 1500, -4, false, 0.20, 0.5, 0, false, false); latefh.MinDist = 0.25; latefh.FhCheck = true;
			Mod nf05 = AddTime("NF05", (custom ? UseNf05 : (ul || du || (w7 && NightOnWr70)) && UseNf05), 500, -5, true, 0.20, 2.0, 240, false, false); nf05.MinDist = 0.35; nf05.Anchor = 20 * 60;
			Mod lf0315 = AddTime("LF0315", (custom ? UseLf0315 : ul && UseLf0315), 315, -5, true, 0.20, 2.0, 600, false, false); lf0315.MinDist = 0.10; lf0315.Anchor = 3 * 60;
			Mod lf06 = AddTime("LF06", (custom ? UseLf06 : (ul || (w7 && NightOnWr70)) && UseLf06), 600, -5, true, 0.20, 0.5, 240, false, false); lf06.MinDist = 0.20; lf06.Anchor = 4 * 60;
			Mod lf0430 = AddTime("LF0430", (custom ? UseLf0430 : (ul || (w7 && NightOnWr70)) && UseLf0430), 430, -5, true, 0.35, 0.5, 240, true, false); lf0430.MinDist = 0.10; lf0430.Anchor = 4 * 60;
			eng10 = NewMod("ENG10", (custom ? UseEng10 : ul && UseEng10), 0.5); eng10.PriceTarget = true; eng10.MaxHold = 400;
			volb = NewMod("VOLB", (custom ? UseVolBreak : (ul || w7 || du) && UseVolBreak), w7 ? 0.5 : 2.0); volb.PriceTarget = true; volb.MaxHold = 400; volbTrendOnly = w7; volbTrendBase = volbTrendOnly; volbRBase = volb.R;
			rsi = NewMod("RSI2", custom && UseRsi2, 0.3); rsi.StopAtr = 0.15; rsi.MaxHold = 120;
""" + s[b:]

# ---------------- profile lists / Gold references
rep("int iq = Qty() * ((Profile == NQMasterProfile.MaxPlus || Profile == NQMasterProfile.MaxPlus2 || Profile == NQMasterProfile.Ultra || Profile == NQMasterProfile.WR70Plus || Profile == NQMasterProfile.Core || Profile == NQMasterProfile.Custom) ? (noBoost ? 1 : IctMultiplier) : 1);",
    "int iq = Qty() * (noBoost ? 1 : IctMultiplier);")
rep("private bool RulesOn { get { return UseConfluence && (Profile == NQMasterProfile.MaxPlus || Profile == NQMasterProfile.MaxPlus2 || Profile == NQMasterProfile.Ultra || Profile == NQMasterProfile.WR70Plus || Profile == NQMasterProfile.Custom); } }",
    "private bool RulesOn { get { return UseConfluence; } }")
rep("private bool CtxOn { get { return UseContextRules && (Profile == NQMasterProfile.MaxPlus2 || Profile == NQMasterProfile.Ultra || Profile == NQMasterProfile.WR70Plus || Profile == NQMasterProfile.Custom); } }",
    "private bool CtxOn { get { return UseContextRules; } }")
rep("""				case NQMasterProfile.WR70Plus: case NQMasterProfile.WinRate70: k = 0.0559; h = 15.05; break;
				case NQMasterProfile.Core: k = 0.0397; h = 9.98; break;
				default: k = 0.0755; h = 16.21; break;			// Ultra (MaxSharpe / MaxPlus / MaxPlus2 / MaxTrades / Custom use the Ultra calibration)""",
    """				case NQMasterProfile.WR70Plus: k = 0.0577; h = 12.18; break;		// research/mine/monitor_recal.py (2026-10-12, real NQ 2020-26)
				case NQMasterProfile.Durable: k = 0.0458; h = 10.71; break;
				default: k = 0.0758; h = 18.57; break;			// Ultra (Custom uses the Ultra calibration)""")
rep("bool counted = EdgeMonitor && Profile != NQMasterProfile.Gold && edgeDayRth", "bool counted = EdgeMonitor && edgeDayRth")
rep("if (MinAtrPoints > 0 && Profile != NQMasterProfile.Gold && !double.IsNaN(todayAtr)", "if (MinAtrPoints > 0 && !double.IsNaN(todayAtr)")
rep("OrderFlowBoost <= 1 || Profile == NQMasterProfile.Gold || !OfAgrees(d)) return q;", "OrderFlowBoost <= 1 || !OfAgrees(d)) return q;")

# ---------------- context rules: drop ORB60 ATR-ratio and ORB90 near-VWAP boosts
rep("bool oc = o == orb ? (FeatGap(d) >= 0.3311 || FeatRet5(d) >= 1.8118 || atrRatio >= 1.2615) : (FeatVw(d, entry) < 0.1231 || FeatOpen(d, entry) >= 0.5458);",
    "// 2026-10-12 (research/mine/rules16_check.py): the ORB60 'ATR ratio' and ORB90 'near VWAP' boosts did not hold on 2010-19 nor 2024-26 -> removed\n"
    "\t\t\tbool oc = o == orb ? (FeatGap(d) >= 0.3311 || FeatRet5(d) >= 1.8118) : (FeatOpen(d, entry) >= 0.5458);")

# ---------------- entry sites: minimum stop + risk cap (before DirectionAllowed: a skipped trade must not cancel other orders)
rep("			int oq = CtxBoost(Qty(), oc, o.Sig);\n",
    "			int oq = CtxBoost(Qty(), oc, o.Sig);\n"
    "\t\t\tif (TooTight(o.Sig, st * TickSize, todayAtr) || TooBig(o.Sig, st * TickSize, oq)) { o.Trades = 2; return; }\n")
rep("			double lvl = d == 1 ? Instrument.MasterInstrument.RoundToTickSize(volbUp) : Instrument.MasterInstrument.RoundToTickSize(volbDn);\n",
    "			double lvl = d == 1 ? Instrument.MasterInstrument.RoundToTickSize(volbUp) : Instrument.MasterInstrument.RoundToTickSize(volbDn);\n"
    "\t\t\tif (TooTight(volb.Sig, Math.Abs(lvl - rthOpenPx), todayAtr) || TooBig(volb.Sig, Math.Abs(lvl - rthOpenPx), Qty())) { volbDone = true; return; }\n")
rep("			if (risk <= 0.02 * todayAtr || risk > 0.6 * todayAtr) return;\n",
    "			if (risk <= 0.02 * todayAtr || risk > 0.6 * todayAtr) return;\n"
    "\t\t\tif (TooTight(eng10.Sig, risk, todayAtr) || TooBig(eng10.Sig, risk, Qty())) return;\n")
rep("""			if (!DirectionAllowed(d)) return;
			int st = Math.Max(4, (int)Math.Round(m.StopAtr * atrDaily / TickSize));
			SetStopLoss(m.Sig, CalculationMode.Ticks, st, false);
			SetProfitTarget(m.Sig, CalculationMode.Ticks, Math.Max(1, (int)Math.Round(m.R * st)));
			m.Dir = d; m.EntryBar = CurrentBars[0] + 1;
			int tq = m.Sig == "MOM13" ? LateQty(d, Hm(m.Time)) : Qty();
			if (m.DoubleDist > 0 && !noBoost && Math.Abs(Close[0] - reference) >= m.DoubleDist * atrDaily) tq = 2 * Qty();
""", """			int st = Math.Max(4, (int)Math.Round(m.StopAtr * atrDaily / TickSize));
			int tq = m.Sig == "MOM13" ? LateQty(d, Hm(m.Time)) : Qty();
			if (m.DoubleDist > 0 && !noBoost && Math.Abs(Close[0] - reference) >= m.DoubleDist * atrDaily) tq = 2 * Qty();
			if (TooBig(m.Sig, st * TickSize, tq)) return;
			if (!DirectionAllowed(d)) return;
			SetStopLoss(m.Sig, CalculationMode.Ticks, st, false);
			SetProfitTarget(m.Sig, CalculationMode.Ticks, Math.Max(1, (int)Math.Round(m.R * st)));
			m.Dir = d; m.EntryBar = CurrentBars[0] + 1;
""")
rep("""			if (risk <= 0 || risk > 0.5 * todayAtr || !DirectionAllowed(d)) return;
			ArmPriceBracket(crt, d, stop);
			int cq = CtxBoost(LateQty(d, 720), FeatTrend(d) >= 1.7456 || FeatGap(d) >= 0.1048 || FeatPdRet(d) >= 0.6155, "CRT11");
""", """			if (risk <= 0 || risk > 0.5 * todayAtr) return;
			int cq = CtxBoost(LateQty(d, 720), FeatTrend(d) >= 1.7456 || FeatGap(d) >= 0.1048 || FeatPdRet(d) >= 0.6155, "CRT11");
			if (TooTight(crt.Sig, risk, todayAtr) || TooBig(crt.Sig, risk, cq) || !DirectionAllowed(d)) return;
			ArmPriceBracket(crt, d, stop);
""")
rep("				if (risk <= 0 || risk > 0.25 * atrDaily) { lonStage = 3; return; }\n",
    "				if (risk <= 0 || risk > 0.25 * atrDaily) { lonStage = 3; return; }\n"
    "\t\t\t\tif (TooTight(lon.Sig, risk, atrDaily) || TooBig(lon.Sig, risk, Qty())) { lonStage = 3; return; }\n")
rep("""					int mq = CtxBoost(LateQty(1, closeMin), FeatPos(1, Closes[0][0]) >= 0.9686 || FeatM30(1) >= 0.1728 || FeatRet5(1) >= 2.0674, "MSEQ");
					if (!DirectionAllowed(1, 2))""", """					int mq = CtxBoost(LateQty(1, closeMin), FeatPos(1, Closes[0][0]) >= 0.9686 || FeatM30(1) >= 0.1728 || FeatRet5(1) >= 2.0674, "MSEQ");
					if (TooTight(mseq.Sig, c0m - stopm, todayAtr) || TooBig(mseq.Sig, c0m - stopm, mq)) { }
					else if (!DirectionAllowed(1, 2))""")
rep("""					int sq = LateQty(-1, closeMin);
					if (!DirectionAllowed(-1, 2))""", """					int sq = LateQty(-1, closeMin);
					if (TooTight(mseqs.Sig, stops - c0s, todayAtr) || TooBig(mseqs.Sig, stops - c0s, sq)) { }
					else if (!DirectionAllowed(-1, 2))""")
rep("""				if (d != 0 && DirectionAllowed(d))
				{
					int st = Math.Max(4, (int)Math.Round(rsi.StopAtr * todayAtr / TickSize));""", """				int rst = Math.Max(4, (int)Math.Round(rsi.StopAtr * todayAtr / TickSize));
				if (d != 0 && !TooBig(rsi.Sig, rst * TickSize, Qty()) && DirectionAllowed(d))
				{
					int st = rst;""")
rep("""				int iq = Qty() * (noBoost ? 1 : IctMultiplier);
				if (!DirectionAllowed(d))""", """				int iq = Qty() * (noBoost ? 1 : IctMultiplier);
				if (TooTight(ict.Sig, risk, todayAtr) || TooBig(ict.Sig, risk, iq)) continue;
				if (!DirectionAllowed(d))""")

# ---------------- helpers (after LateQty)
rep("""		private int LateQty(int d, int entryMin)
		{""", """		// ---- trade-level risk rules (2026-10-12; research/mine/robust2_*.py, cand16*.py, real Databento NQ futures 2010-2026)
		// MinStopAtr: structure modules (ORB, VOLB, MSEQ, MSEQS, CRT11, ICT, LON, ENG10) skip a trade whose stop is closer than this many
		// daily ATRs: inside the day's noise (WR +0.4 to +0.8 points in 2010-14, 2015-19, 2020-23 and 2024-26, PF +0.01, $ unchanged).
		// Risk cap: in PropMode Eval / Funded, while the cushion over the liquidation threshold at the session start is below
		// EvalRiskCapCushion / FundedRiskCapCushion, a trade whose stop risks more than RiskCapPerContract $ per base contract is skipped.
		// The big-risk trades are the best ones on average, but a few of them can wipe a small cushion. MyFundedFutures 50K, 1 contract,
		// 1,000 resampled years per period: accounts lost per year per slot 0.56 -> 0.45 (2020-23), 1.65 -> 0.89 (2024-26), income -6%.
		private int riskSkips;
		private bool TooTight(string who, double stopPts, double atr)
		{
			if (MinStopAtr <= 0 || double.IsNaN(atr) || atr <= 0 || stopPts >= MinStopAtr * atr) return false;
			Log(string.Format("{0} skipped: stop {1:0.00} pts is inside the day's noise (< {2:0.00} x ATR {3:0.0})", who, stopPts, MinStopAtr, atr)); return true;
		}
		private bool RiskCapActive { get { return PropMode != NQMasterPropMode.Off && RiskCapPerContract > 0 && !double.IsNaN(propCushion)
			&& propCushion < (PropMode == NQMasterPropMode.Eval ? EvalRiskCapCushion : FundedRiskCapCushion); } }
		private bool TooBig(string who, double stopPts, int qty)
		{
			if (!RiskCapActive || qty <= 0) return false;
			double perBase = stopPts * Instrument.MasterInstrument.PointValue * qty / Math.Max(1, Qty());
			if (perBase <= RiskCapPerContract) return false;
			riskSkips++;
			Log(string.Format("{0} skipped by the risk cap: ${1:0} per base contract > ${2:0} while the cushion is ${3:0}", who, perBase, RiskCapPerContract, propCushion)); return true;
		}
		private int LateQty(int d, int entryMin)
		{""")

# ---------------- dashboard line
rep("			if (PropMode == NQMasterPropMode.Funded && FundedStepUpCushion > 0) txt +=",
    "			if (PropMode != NQMasterPropMode.Off && RiskCapPerContract > 0) txt += string.Format(\"\\nRisk cap ${0:0}/contract: {1} (cushion ${2:0} vs ${3:0}) | skipped {4}\", RiskCapPerContract,\n"
    "\t\t\t\tRiskCapActive ? \"ACTIVE\" : \"off\", propCushion, PropMode == NQMasterPropMode.Eval ? EvalRiskCapCushion : FundedRiskCapCushion, riskSkips);\n"
    "\t\t\tif (PropMode == NQMasterPropMode.Funded && FundedStepUpCushion > 0) txt +=")

# ---------------- properties
rep('[NinjaScriptProperty][Display(Name = "Context rules (MaxPlus2/Custom): x2 ORB60/ORB90/CRT11/MSEQ in favourable context, skip ON07 after a counter day", Order = 45, GroupName = "03. Risk / account")]',
    '[NinjaScriptProperty][Display(Name = "Context rules: x2 ORB60/ORB90/CRT11/MSEQ in favourable context, skip ON07 after a counter day", Order = 45, GroupName = "03. Risk / account")]')
rep('[NinjaScriptProperty][Display(Name = "Confluence rules (MaxPlus/Custom): x2 late trades vs MOM11 + with overnight, skip REV06 after same-dir LON", Order = 44, GroupName = "03. Risk / account")]',
    '[NinjaScriptProperty][Display(Name = "Confluence rules: x2 late trades vs MOM11 + with overnight, skip REV06 after same-dir LON", Order = 44, GroupName = "03. Risk / account")]')
rep('[NinjaScriptProperty][Range(1, 5)][Display(Name = "ICT size multiplier (MaxPlus/Custom; equal-risk: ICT stops are the smallest)", Order = 43, GroupName = "03. Risk / account")]',
    '[NinjaScriptProperty][Range(1, 5)][Display(Name = "ICT size multiplier (equal-risk: ICT stops are the smallest)", Order = 43, GroupName = "03. Risk / account")]')
rep("\t\t#region Properties\n",
    "\t\t#region Properties\n"
    "\t\t[NinjaScriptProperty][Range(0.0, 1.0)][Display(Name = \"Min stop for structure modules (x daily ATR; 0.10, 0 = off)\", Order = 26, GroupName = \"02. Edge\")] public double MinStopAtr { get; set; }\n"
    "\t\t[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = \"Risk cap: skip trades risking more than $ per base contract (300; 0 = off)\", Order = 18, GroupName = \"07. Prop account (cushion gating)\")] public double RiskCapPerContract { get; set; }\n"
    "\t\t[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = \"Risk cap active in Eval while cushion < $ (1200)\", Order = 19, GroupName = \"07. Prop account (cushion gating)\")] public double EvalRiskCapCushion { get; set; }\n"
    "\t\t[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = \"Risk cap active in Funded while cushion < $ (2000)\", Order = 20, GroupName = \"07. Prop account (cushion gating)\")] public double FundedRiskCapCushion { get; set; }\n")
open(P, "w", encoding="utf-8").write(s); print("patched", P)
