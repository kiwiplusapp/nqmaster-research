//
// NQ MASTER - the whole research portfolio in ONE strategy (NinjaTrader 8, single file)
// ------------------------------------------------------------------------------------------------
// Run on a 1-MINUTE chart (CME US Index Futures ETH): MNQ for the Nasdaq modules, MGC for the gold module.
// A 5-minute series is added internally (MSEQ and ICT modules).
// Profiles (Profile parameter; every module can still be switched on/off below):
//   MaxSharpe : ORB60 0.6R (pullback days) + MSEQ + CRT11 + MOM11 + MOM13 + MOM1030 + ON07 + REV06 + LON + ICT  (use with a Gold chart)
//   WinRate70 : ORB60 0.75R + MSEQ + CRT11 + MOM11 + MOM1030 + ON07 + REV06 + ICT  (NQ only, ~70% win rate)
//   Gold      : ORB30 2R with the daily trend, all days (run on an MGC chart)
//   WR70Plus  : >=70% win rate build (research/mine/wr70_*.py): ORB60 0.75R, ORB90, MSEQ, MSEQS, CRT11, ICT x2, MOM11, REV06, VW13
//               (>=0.15 ATR, 2 lots when >=0.30), VOLB with the trend at 0.5R; LON/ON07/MOM13/MOM1030 off; confluence + context rules.
//               Real MNQ 2024-26: WR 71.5%, PF 1.50, 2.9 trades/day (1 lot base).
//   Ultra     : MaxPlus2 + VOLB (L. Williams volatility breakout: stop entries at RTH open +/- 0.45 x prior RTH range, stop at the
//               RTH open, 2R, both directions; robust 2015-2026 cost-normalised; big stop -> NOT for 25K accounts)
//   MaxPlus2  : MaxPlus + context-sized rules (x2 / skip, research/mine/filt_holdout.py) + VW13 (13:01 VWAP-distance momentum, 0.5R)
//   MaxPlus   : MaxSharpe (NQ) + ORB90 0.6R (pullback days) + MSEQS (short momentum sequence, only after ORB60 entered SHORT)
//   MaxTrades : MaxSharpe (NQ) + MOM1130 (11:30 momentum, VWAP-agree, 0.3R) + RSI2 (5m RSI(2)<10 / >90 pullback with the
//               daily trend AND the intraday trend, 10:30-15:45, stop 0.15 ATRd, 0.3R, max 120 min, up to 3 per day)
// Research results (real MNQ/MGC 2024-26, 1 contract per module, FOMC days skipped, no opposite MNQ positions):
//   MaxSharpe (+Gold chart): WR 64.4%, PF 1.35, Sharpe 3.55, 4.3 trades/day
//   WinRate70            : WR 70.9%, PF 1.42, Sharpe 3.32, 2.9 trades/day
//   MaxPlus (NQ only)    : WR 66.8%, PF 1.40, Sharpe 3.22, 3.9 trades/day, ICT x2 (equal risk) + confluence rules (+9-15% $/month)
//   MaxTrades (NQ only)  : WR 70.1%, PF 1.30, Sharpe 3.08, 5.2 trades/day (MaxSharpe NQ only: WR 67.1%, PF 1.38, 3.7 trades/day)
// Account layer: FOMC days skipped, shared pause file, eval-target stop and drawdown guard (realtime).
// Managed orders: one signal per module. An entry is skipped if the strategy holds (or is working) the opposite direction.
// ------------------------------------------------------------------------------------------------
#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Globalization;
using System.IO;
using System.Text;
using System.Windows.Media;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Tools;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.DrawingTools;
#endregion

namespace NinjaTrader.NinjaScript.Strategies
{
	public enum NQMasterProfile { MaxSharpe, WinRate70, Gold, Custom, MaxTrades, MaxPlus, MaxPlus2, Ultra, WR70Plus, Core }
	public enum NQMasterPropMode { Off, Eval, Funded }

	public class NQMaster : Strategy
	{
		private const int RthOpen = 570, RthClose = 960;
		// FOMC decision days always skipped (merged with the FomcDates parameter). Source: federalreserve.gov (2027 schedule, Sep 2025).
		private const string BuiltinFomc = "2024-01-31,2024-03-20,2024-05-01,2024-06-12,2024-07-31,2024-09-18,2024-11-07,2024-12-18,2025-01-29,2025-03-19,2025-05-07,2025-06-18,2025-07-30,2025-09-17,2025-10-29,2025-12-10,2026-01-28,2026-03-18,2026-04-29,2026-06-17,2026-07-29,2026-09-16,2026-10-28,2026-12-09,2027-01-27,2027-03-17,2027-04-28,2027-06-09,2027-07-28,2027-09-15,2027-10-27,2027-12-08,2028-01-26";

		#region Module state
		private class Mod
		{
			public string Sig; public bool On; public double R; public int Kind;	// Kind: 0 ORB, 1 time, 2 other
			public bool InTrade; public Order Entry; public int Dir; public double StopPx; public double EntryPx; public int EntryBar;
			// ORB
			public int Range; public double OrH, OrL; public bool OrReady, Armed; public int Trades; public bool UsePullback;
			// time module
			public int Time; public int Lookback; public bool Reverse; public double StopAtr; public int MaxHold; public bool Trend; public bool Vwap; public bool Done; public double MinDist; public double DoubleDist;
			// target set on fill (price mode)
			public bool PriceTarget;
			public bool BaseOn; public bool FhCheck;
			public bool Retry;
			public int Anchor = -1; public double AnchorPx = double.NaN;	// Lookback -5: open of the bar at the anchor time (ET minutes)
			public bool Parked, ParkLimit, ParkHit; public double ParkPx; public int ParkQty;	// entry cancelled for an opposite trade, re-placed when free
		}
		private List<Mod> mods;
		private Mod orb, orb2, mseq, mseqs, crt, lon, ict, rsi, volb, eng10;
		private double rthFirstClose = double.NaN;
		private double e10aO, e10aH, e10aL, e10aC, e10bO, e10bH, e10bL, e10bC, close10 = double.NaN; private bool e10aHas, e10bHas, eng10Done;
		private double volbUp = double.NaN, volbDn = double.NaN; private bool volbDone, volbTrendOnly;
		private int orbFirstDir, orbFirstMin = 9999;
		private int m11Dir, onSum, lonDir;	// confluence state (MOM11 direction, overnight modules ON07/REV06/LON)
		private List<Mod> timeMods;
		#endregion

		#region Fields
		private TimeZoneInfo etZone;
		private SimpleFont dashFont;
		private bool badTimeframe;
		private HashSet<int> fomc;

		// completed RTH days
		private int rthDay = -1, rthDaysSeen, atrCount;
		private double dayHigh, dayLow, dayClose, atrDaily = double.NaN, atrPrevClose = double.NaN, prevRthHigh = double.NaN, prevRthLow = double.NaN;
		private double full1 = double.NaN, full2 = double.NaN;
		private bool dayHasBars;
		private int dayLastOpen = -1;
		private List<double> rthCloses;
		private int trendDir;
		private double todayAtr = double.NaN, prevRet = double.NaN;
		private bool pullbackDay, fomcToday;

		// session / intraday
		private double sessOpen = double.NaN, rthOpenPx = double.NaN, vwPv, vwV;
		private double onH, onL, lonH, lonL, postH, postL; private bool onHas, lonHas, postHas;
		private double c1H, c1L, c2H, c2L, c2C; private bool c1Has, c2Has;
		private double rH, rL; private bool rHas; private int lonStage;
		private double[] lvl = new double[6]; private bool[] taken = new bool[6]; private bool levelsReady;
		private bool[] ictAct = new bool[2]; private double[] ictExt = new double[2]; private int[] ictExtBar = new int[2];
		private int ictTrades, ictExpiry; private double ictExtPend;
		private int flattenBar = -1;
		private double rsiUp = double.NaN, rsiDn = double.NaN, rsiVal = 50; private int rsiTrades;
		private string status = "waiting";

		// account layer
		private double highWater = double.NaN; private bool ddTripped, targetHit;
		private int tradesProcessed, totalTrades, totalWins; private double grossWin, grossLoss, netPnl;
		#endregion

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Description = "Whole NQ/Gold research portfolio in one strategy: ORB, MSEQ, CRT11, clock-time modules, London FVG, ICT open, account guard.";
				Name = "NQMaster";
				Calculate = Calculate.OnBarClose;
				EntriesPerDirection = 1;
				EntryHandling = EntryHandling.UniqueEntries;
				IsExitOnSessionCloseStrategy = true;
				ExitOnSessionCloseSeconds = 30;
				IsFillLimitOnTouch = false;
				MaximumBarsLookBack = MaximumBarsLookBack.Infinite;
				OrderFillResolution = OrderFillResolution.Standard;
				Slippage = 1;
				StartBehavior = StartBehavior.WaitUntilFlat;
				TimeInForce = TimeInForce.Gtc;
				RealtimeErrorHandling = RealtimeErrorHandling.IgnoreAllErrors;	// rejections handled in OnOrderUpdate
				StopTargetHandling = StopTargetHandling.PerEntryExecution;
				BarsRequiredToTrade = 20;
				IsInstantiatedOnEachOptimizationIteration = true;

				Profile = NQMasterProfile.MaxSharpe;
				UseOrb = true; OrbRangeMin = 60; OrbTargetR = 0.6; OrbPullbackFilter = true; PullbackMaxRet = 0.44; StopCapAtr = 0.35;
				UseMseq = true; UseCrt = true; UseMom11 = true; UseMom1130 = true; UseRsi2 = true; UseOrb90 = true; UseMseqShort = true; UseMom13 = true; UseMom1030 = true; UseOn07 = true; UseRev06 = true; UseLon = true; UseIct = true;
				Contracts = 1; FlattenTime = 1556; SkipFomc = true;
				AdaptiveSize = false; SizeHigh = 2; SizeLow = 1; SizeDownDrawdown = 600; IctMultiplier = 2; UseConfluence = true; UseContextRules = true; UseVw13 = true; UseVolBreak = true; UseLate15 = true; UseEng10 = true; UseLateFh = true; Vw13Wide = true; UseNf05 = true; UseLf0315 = false; UseLf06 = true; UseLf0430 = true; NightOnWr70 = false;
				FomcDates = "2024-01-31,2024-03-20,2024-05-01,2024-06-12,2024-07-31,2024-09-18,2024-11-07,2024-12-18,2025-01-29,2025-03-19,2025-05-07,2025-06-18,2025-07-30,2025-09-17,2025-10-29,2025-12-10,2026-01-28,2026-03-18,2026-04-29,2026-06-17,2026-07-29,2026-09-16,2026-10-28,2026-12-09";
				StartBalance = 50000; EvalTarget = 0; MaxDrawdown = 0; DrawdownBuffer = 250; DailyLossLimit = 0; MinAtrPoints = 150;
				EvalMode = false; EvalStartDate = "2026-10-05"; EvalLateDay = 12; EvalLateGoal = 2000; EvalLateContracts = 3; EvalLateMinCushion = 0;
				PauseFile = "pause_trading.txt"; ShowDashboard = true; PrintLog = true;
				EdgeMonitor = true; EdgeMonitorPause = false; EdgeMonitorStart = "2026-10-05"; EdgeK = 0; EdgeH = 0;
				PropMode = NQMasterPropMode.Off; PropTrailingDD = 2000; EvalCushionFull = 0; EvalDailyStop = 0; FundedCushionSafe = 750; FundedPayoutAt = 5000; FundedHighFull = true; FundedCushionFull = 0;
				PropPeakOverride = 0; PropThresholdOverride = 0; AtrStartMax = 0; ConsistencyPct = 50; EvalBestDaySoFar = 0; EvalProfitStop = 1400;
			}
			else if (State == State.Configure)
			{
				AddDataSeries(BarsPeriodType.Minute, 5);
			}
			else if (State == State.DataLoaded)
			{
				rthCloses = new List<double>(); atrHist = new List<double>();
				dashFont = new SimpleFont("Consolas", 11);
				try { etZone = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time"); } catch { etZone = null; }
				badTimeframe = !(BarsPeriod.BarsPeriodType == BarsPeriodType.Minute && BarsPeriod.Value == 1);
				if (badTimeframe) Print("NQMaster | Needs a 1-MINUTE chart (CME US Index Futures ETH).");
				fomc = new HashSet<int>();
				foreach (string raw in (BuiltinFomc + "," + (FomcDates ?? "")).Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries))
				{
					DateTime d;
					if (DateTime.TryParseExact(raw.Trim(), "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out d)) fomc.Add(d.Year * 10000 + d.Month * 100 + d.Day);
				}
				BuildModules();
				foreach (Mod m in mods) m.BaseOn = m.On;
				EdgeParams();
			}
			else if (State == State.Realtime)
			{
				foreach (Mod m in mods) if (m.Entry != null) m.Entry = GetRealtimeOrder(m.Entry);
				eqPeak = netPnl;	// adaptive size measures the drawdown from the moment the strategy goes live
				PropGoLive();
			}
			else if (State == State.Terminated)
			{
				if (mods != null && totalTrades == 0 && rthDaysSeen < 25)
					Print(string.Format("NQMaster | 0 trades: only {0} RTH days loaded; needs ~25 days of warm-up. Start the test 2+ months earlier.", rthDaysSeen));
			}
		}

		public override string DisplayName { get { return "NQ MASTER (" + Profile + ")"; } }

		private void BuildModules()
		{
			bool w7 = Profile == NQMasterProfile.WR70Plus, mt = Profile == NQMasterProfile.MaxTrades, ul = Profile == NQMasterProfile.Ultra, mp2 = Profile == NQMasterProfile.MaxPlus2 || ul, mp = Profile == NQMasterProfile.MaxPlus || mp2, ms = Profile == NQMasterProfile.MaxSharpe || mt || mp, wr = Profile == NQMasterProfile.WinRate70, gold = Profile == NQMasterProfile.Gold, custom = Profile == NQMasterProfile.Custom, core = Profile == NQMasterProfile.Core;
			mods = new List<Mod>(); timeMods = new List<Mod>();
			orb = new Mod(); orb.Sig = gold ? "GC_ORB30" : "ORB60"; orb.Kind = 0;
			orb.On = (custom ? UseOrb : (true) && UseOrb);
			orb.Range = custom ? OrbRangeMin : (gold ? 30 : 60);
			orb.R = custom ? OrbTargetR : (gold ? 2.0 : ((wr || w7) ? 0.75 : 0.6));
			orb.UsePullback = custom ? OrbPullbackFilter : !gold;
			mods.Add(orb);
			orb2 = new Mod(); orb2.Sig = "ORB90"; orb2.Kind = 0; orb2.On = (custom ? UseOrb90 : (mp || w7) && UseOrb90); orb2.Range = 90; orb2.R = 0.6; orb2.UsePullback = true;
			mods.Add(orb2);
			mseq = NewMod("MSEQ", (custom ? UseMseq : (!gold) && UseMseq), 0.5); mseq.PriceTarget = true;
			mseqs = NewMod("MSEQS", (custom ? UseMseqShort : (mp || w7) && UseMseqShort), 0.75); mseqs.PriceTarget = true;
			crt = NewMod("CRT11", (custom ? UseCrt : (!gold) && UseCrt), 2.0); crt.PriceTarget = true;
			lon = NewMod("LON", (custom ? UseLon : (ms || core) && UseLon), 2.0); lon.PriceTarget = true;
			ict = NewMod("ICT", (custom ? UseIct : (!gold) && UseIct), 1.0); ict.PriceTarget = true;
			AddTime("MOM11", (custom ? UseMom11 : (!gold && !core) && UseMom11), 1100, -2, false, 0.25, 0.3, 0, false, true);
			AddTime("MOM13", (custom ? UseMom13 : (ms) && UseMom13), 1300, -2, false, 0.20, 1.0, 240, true, false);
			AddTime("MOM1030", (custom ? UseMom1030 : (!gold && !w7 && !core) && UseMom1030), 1030, -2, false, 0.20, 0.3, 60, true, false);
			AddTime("ON07", (custom ? UseOn07 : (!gold && !w7 && !core) && UseOn07), 700, 30, false, 0.20, 1.0, 60, true, false);
			AddTime("REV06", (custom ? UseRev06 : (!gold && !core) && UseRev06), 600, 30, true, 0.20, 0.3, 240, true, false);
			AddTime("MOM1130", (custom ? UseMom1130 : (mt) && UseMom1130), 1130, -2, false, 0.25, 0.3, 0, false, true);
			Mod vw13 = AddTime("VW13", (custom ? UseVw13 : (mp2 || w7) && UseVw13), 1301, -3, false, 0.15, 0.5, 120, true, false); bool vwWide = w7 || (ul && Vw13Wide); vw13.MinDist = vwWide ? 0.15 : 0.30; vw13.DoubleDist = vwWide ? 0.30 : 0;
			Mod late15 = AddTime("LATE15", (custom ? UseLate15 : (ul || w7 || core) && UseLate15), 1500, -4, false, 0.30, 0.5, 0, true, false); late15.MinDist = 0.5;
			Mod latefh = AddTime("LATEFH", (custom ? UseLateFh : ul && UseLateFh), 1500, -4, false, 0.20, 0.5, 0, false, false); latefh.MinDist = 0.25; latefh.FhCheck = true;
			Mod nf05 = AddTime("NF05", (custom ? UseNf05 : (ul || (w7 && NightOnWr70)) && UseNf05), 500, -5, true, 0.20, 2.0, 240, false, false); nf05.MinDist = 0.35; nf05.Anchor = 20 * 60;
			Mod lf0315 = AddTime("LF0315", (custom ? UseLf0315 : ul && UseLf0315), 315, -5, true, 0.20, 2.0, 600, false, false); lf0315.MinDist = 0.10; lf0315.Anchor = 3 * 60;
			Mod lf06 = AddTime("LF06", (custom ? UseLf06 : (ul || (w7 && NightOnWr70)) && UseLf06), 600, -5, true, 0.20, 0.5, 240, false, false); lf06.MinDist = 0.20; lf06.Anchor = 4 * 60;
			Mod lf0430 = AddTime("LF0430", (custom ? UseLf0430 : (ul || (w7 && NightOnWr70)) && UseLf0430), 430, -5, true, 0.35, 0.5, 240, true, false); lf0430.MinDist = 0.10; lf0430.Anchor = 4 * 60;
			eng10 = NewMod("ENG10", (custom ? UseEng10 : ul && UseEng10), 0.5); eng10.PriceTarget = true; eng10.MaxHold = 400;
			volb = NewMod("VOLB", (custom ? UseVolBreak : (ul || w7 || core) && UseVolBreak), w7 ? 0.5 : 2.0); volb.PriceTarget = true; volb.MaxHold = 400; volbTrendOnly = w7;
			rsi = NewMod("RSI2", (custom ? UseRsi2 : (mt) && UseRsi2), 0.3); rsi.StopAtr = 0.15; rsi.MaxHold = 120;
			StringBuilder sb = new StringBuilder();
			foreach (Mod m in mods) if (m.On) sb.Append(m.Sig + " ");
			Print("NQMaster | profile " + Profile + " | modules: " + sb.ToString());
			if (!custom && (OrbRangeMin != 60 || Math.Abs(OrbTargetR - 0.6) > 1e-9 || !OrbPullbackFilter))
				Print("NQMaster | NOTE: ORB range / target R / pullback filter only apply with Profile = Custom. The profile values are being used.");
		}
		private Mod NewMod(string sig, bool on, double r) { Mod m = new Mod(); m.Sig = sig; m.On = on; m.R = r; m.Kind = 2; mods.Add(m); return m; }
		private Mod AddTime(string sig, bool on, int t, int lb, bool rev, double sa, double r, int hold, bool trend, bool vwap)
		{
			Mod m = new Mod(); m.Sig = sig; m.On = on; m.Kind = 1; m.Time = t; m.Lookback = lb; m.Reverse = rev; m.StopAtr = sa; m.R = r; m.MaxHold = hold; m.Trend = trend; m.Vwap = vwap;
			mods.Add(m); timeMods.Add(m); return m;
		}

		protected override void OnBarUpdate()
		{
			if (badTimeframe || CurrentBars[0] < 3) return;
			if (BarsInProgress == 1) { OnFiveMinute(); return; }

			DateTime etClose = ToEt(Time[0]);
			DateTime etOpen = etClose.AddMinutes(-1);
			int openMin = etOpen.Hour * 60 + etOpen.Minute;
			int closeMin = etClose.Hour * 60 + etClose.Minute;
			int etDate = etOpen.Year * 10000 + etOpen.Month * 100 + etOpen.Day;

			ProcessClosedTrades();

			if (Bars.IsFirstBarOfSession)
			{
				EdgeDayClose(etOpen);
				dayStartPnl = netPnl; dayStopped = false;
				// the session that just ended: finalize its RTH day, or mark it as a session without a complete RTH day
				if (dayHasBars) FinalizeRthDay();
				else if (rthDaysSeen > 0) { full2 = full1; full1 = double.NaN; }
				DateTime tradeDay = etOpen.Hour >= 18 ? etOpen.Date.AddDays(1) : etOpen.Date;
				prevSessDay = curSessDay; curSessDay = tradeDay.Year * 10000 + tradeDay.Month * 100 + tradeDay.Day;
				fomcToday = SkipFomc && fomc.Contains(tradeDay.Year * 10000 + tradeDay.Month * 100 + tradeDay.Day);
				EvalSessionStart(tradeDay);
				edgeDayQty = Qty(); edgeDayTradable = !fomcToday; edgeDayDate = tradeDay;
				NewSession();
				PropSessionStart();
				sessHi = High[0]; sessLo = Low[0];
			}
			sessHi = Math.Max(sessHi, High[0]); sessLo = Math.Min(sessLo, Low[0]);
			if (openMin >= 120 && openMin < 360) { if (!e10aHas) { e10aO = Open[0]; e10aH = High[0]; e10aL = Low[0]; e10aHas = true; } e10aH = Math.Max(e10aH, High[0]); e10aL = Math.Min(e10aL, Low[0]); e10aC = Close[0]; }
			else if (openMin >= 360 && openMin < 600) { if (!e10bHas) { e10bO = Open[0]; e10bH = High[0]; e10bL = Low[0]; e10bHas = true; } e10bH = Math.Max(e10bH, High[0]); e10bL = Math.Min(e10bL, Low[0]); e10bC = Close[0]; }
			if (openMin == 599) close10 = Close[0];
			foreach (Mod m in timeMods) if (m.Anchor >= 0 && double.IsNaN(m.AnchorPx) && openMin >= m.Anchor && openMin <= m.Anchor + 5) m.AnchorPx = Open[0];
			bool inRth = openMin >= RthOpen && openMin < RthClose;
			bool overnight = openMin < RthOpen || openMin >= 18 * 60;
			if (overnight && openMin < RthOpen)
			{
				if (!onHas) { onH = High[0]; onL = Low[0]; onHas = true; } else { onH = Math.Max(onH, High[0]); onL = Math.Min(onL, Low[0]); }
				if (openMin >= 120 && openMin < 300) { if (!lonHas) { lonH = High[0]; lonL = Low[0]; lonHas = true; } else { lonH = Math.Max(lonH, High[0]); lonL = Math.Min(lonL, Low[0]); } }
				else if (openMin >= 300) { if (!postHas) { postH = High[0]; postL = Low[0]; postHas = true; } else { postH = Math.Max(postH, High[0]); postL = Math.Min(postL, Low[0]); } }
			}
			else if (overnight)
			{
				if (!onHas) { onH = High[0]; onL = Low[0]; onHas = true; } else { onH = Math.Max(onH, High[0]); onL = Math.Min(onL, Low[0]); }
			}
			if (inRth)
			{
				edgeDayRth = true;
				if (etDate != rthDay) StartRthDay(etDate);
				if (!dayHasBars) { dayHigh = High[0]; dayLow = Low[0]; dayHasBars = true; rthOpenPx = Open[0]; rthFirstClose = Close[0]; SetupIctLevels();
					double prng = prevRthHigh - prevRthLow; volbUp = double.IsNaN(prng) ? double.NaN : rthOpenPx + 0.45 * prng; volbDn = double.IsNaN(prng) ? double.NaN : rthOpenPx - 0.45 * prng; }
				else { dayHigh = Math.Max(dayHigh, High[0]); dayLow = Math.Min(dayLow, Low[0]); }
				dayClose = Close[0]; dayLastOpen = openMin;
				double vol = Volume[0] > 0 ? Volume[0] : 1.0;
				vwPv += (High[0] + Low[0] + Close[0]) / 3.0 * vol; vwV += vol;
				foreach (Mod o in new Mod[] { orb, orb2 })
					if (o.On && openMin < RthOpen + o.Range)
					{
						if (!o.OrReady && o.OrH == 0 && o.OrL == 0) { o.OrH = High[0]; o.OrL = Low[0]; }
						else { o.OrH = Math.Max(o.OrH, High[0]); o.OrL = Math.Min(o.OrL, Low[0]); }
						if (openMin == RthOpen + o.Range - 1) { o.OrReady = true; o.Armed = true; }
					}
				// CRT candles
				if (openMin >= 600 && openMin < 660) { if (!c1Has) { c1H = High[0]; c1L = Low[0]; c1Has = true; } else { c1H = Math.Max(c1H, High[0]); c1L = Math.Min(c1L, Low[0]); } }
				else if (openMin >= 660 && openMin < 720) { if (!c2Has) { c2H = High[0]; c2L = Low[0]; c2Has = true; } else { c2H = Math.Max(c2H, High[0]); c2L = Math.Min(c2L, Low[0]); } c2C = Close[0]; }
			}

			AccountGuard();
			DailyLossCheck();
			PropDailyCheck();

			// exits: module time exits, London exit, flatten
			if (FlattenTime > 0 && closeMin >= Hm(FlattenTime) && closeMin < 18 * 60) { FlattenAll("end of day"); UpdateDashboard(); return; }
			foreach (Mod m in timeMods)
				if (m.InTrade && m.MaxHold > 0 && CurrentBars[0] - m.EntryBar >= m.MaxHold) ExitModule(m, "time exit");
			if (rsi.InTrade && CurrentBars[0] - rsi.EntryBar >= rsi.MaxHold) ExitModule(rsi, "time exit");
			if (volb.InTrade && CurrentBars[0] - volb.EntryBar >= volb.MaxHold) ExitModule(volb, "time exit");
			if (eng10.InTrade && CurrentBars[0] - eng10.EntryBar >= eng10.MaxHold) ExitModule(eng10, "time exit");
			if (lon.InTrade && openMin >= 570 && openMin < 18 * 60) ExitModule(lon, "London exit 09:30");
			if (Working(lon.Entry) && (openMin >= 480 && openMin < 18 * 60)) CancelOrder(lon.Entry);

			bool canTrade = CanTrade();
			if (!canTrade) { CancelAllEntries(); UpdateDashboard(); return; }
			// MSEQ / MSEQS deferred by an opposite stop/limit order: one retry on the next 1-minute bars (research enters them at market)
			if (pend5 != null)
			{
				if (pend5.InTrade || CurrentBars[0] > pend5Bar + 2 || (pend5Dir == 1 ? Close[0] <= pend5Stop : Close[0] >= pend5Stop)) pend5 = null;
				else if (CurrentBars[0] > pend5Bar && DirectionAllowed(pend5Dir))
				{
					ArmPriceBracket(pend5, pend5Dir, pend5Stop); Order po = pend5Dir == 1 ? EnterLong(0, pend5Qty, pend5.Sig) : EnterShort(0, pend5Qty, pend5.Sig);
					if (po != null) pend5.Entry = po; Log(pend5.Sig + " entered after the deferral"); pend5 = null;
				}
			}
			ManageParked(openMin, closeMin);

			// ---- modules on the 1-minute series
			foreach (Mod o in new Mod[] { orb, orb2 })
				if (o.On && inRth && etDate == rthDay && o.OrReady && closeMin >= Math.Max(630, RthOpen + o.Range)) ManageOrb(o, closeMin);
			foreach (Mod m in timeMods)
			{
				if (m.Retry) { m.Retry = false; TimeEntry(m); if (lastDeferred) m.Retry = false; continue; }
				if (m.On && !m.Done && closeMin == Hm(m.Time)) { m.Done = true; TimeEntry(m); if (lastDeferred) m.Retry = true; }
			}
			if (crt.On && inRth && crt.Retry) { crt.Retry = false; crt.Done = false; CrtEntry(); crt.Retry = false; }
			else if (crt.On && inRth && openMin == 719 && c1Has && c2Has) { CrtEntry(); if (lastDeferred) crt.Retry = true; }
			if (lon.On && overnight && openMin < RthOpen) LondonStep(openMin);
			if (volb.On && inRth && etDate == rthDay) ManageVolb(openMin);
			if (eng10.On) ManageEng10(openMin);
			UpdateDashboard();
		}

		#region Session / daily statistics
		private void NewSession()
		{
			sessOpen = Open[0]; rthOpenPx = double.NaN; vwPv = 0; vwV = 0;
			onHas = lonHas = postHas = false; c1Has = c2Has = false; rHas = false; lonStage = 0; levelsReady = false;
			ictAct[0] = ictAct[1] = false; ictTrades = 0;
			orb.OrH = 0; orb.OrL = 0; orb.OrReady = false; orb.Armed = false; orb.Trades = 0;
			orb2.OrH = 0; orb2.OrL = 0; orb2.OrReady = false; orb2.Armed = false; orb2.Trades = 0;
			orbFirstDir = 0; orbFirstMin = 9999;
			foreach (Mod m in timeMods) { m.Done = false; m.Retry = false; m.AnchorPx = double.NaN; }
			crt.Done = false; crt.Retry = false;
			rsiTrades = 0;
			volbDone = false; volbUp = double.NaN; volbDn = double.NaN;
			e10aHas = false; e10bHas = false; eng10Done = false; eng10Retry = false; close10 = double.NaN; rthFirstClose = double.NaN;
			m11Dir = 0; onSum = 0; lonDir = 0;
			foreach (Mod m in mods) m.Parked = false;
			pend5 = null;
		}

		private void StartRthDay(int etDate)
		{
			FinalizeRthDay();
			rthDay = etDate; dayHasBars = false;
			todayAtr = atrDaily;
			atrRatio = double.NaN;
			if (atrHist.Count >= 20 && todayAtr > 0) { List<double> srt = new List<double>(atrHist); srt.Sort(); int nn = srt.Count; double med = nn % 2 == 1 ? srt[nn / 2] : 0.5 * (srt[nn / 2 - 1] + srt[nn / 2]); atrRatio = med > 0 ? todayAtr / med : double.NaN; }
			if (!double.IsNaN(todayAtr)) { atrHist.Add(todayAtr); while (atrHist.Count > 100) atrHist.RemoveAt(0); }
			prevRet = (!double.IsNaN(full1) && !double.IsNaN(full2) && todayAtr > 0 && trendDir != 0) ? (full1 - full2) / todayAtr * trendDir : double.NaN;
			pullbackDay = !double.IsNaN(prevRet) && prevRet < PullbackMaxRet;
			rthDaysSeen++;
		}

		private void FinalizeRthDay()
		{
			if (!dayHasBars) { return; }
			double tr = double.IsNaN(atrPrevClose) ? dayHigh - dayLow : Math.Max(dayHigh - dayLow, Math.Max(Math.Abs(dayHigh - atrPrevClose), Math.Abs(dayLow - atrPrevClose)));
			atrCount++;
			int k = Math.Min(atrCount, 14);
			atrDaily = double.IsNaN(atrDaily) ? tr : ((k - 1) * atrDaily + tr) / k;
			atrPrevClose = dayClose; prevRthHigh = dayHigh; prevRthLow = dayLow;
			full2 = full1; full1 = dayLastOpen >= RthClose - 1 ? dayClose : double.NaN;
			rthCloses.Add(dayClose);
			while (rthCloses.Count > 20) rthCloses.RemoveAt(0);
			trendDir = 0;
			if (rthCloses.Count >= 15)
			{
				double s = 0; foreach (double x in rthCloses) s += x;
				trendDir = dayClose > s / rthCloses.Count ? 1 : (dayClose < s / rthCloses.Count ? -1 : 0);
			}
			todayAtr = atrDaily;
			dayHasBars = false;
		}
		#endregion

		#region Modules
		private void ManageOrb(Mod o, int closeMin)
		{
			if (o.UsePullback && !pullbackDay) return;
			if (trendDir == 0 || atrCount < 14 || double.IsNaN(todayAtr)) return;
			bool window = closeMin < 780;
			if (!window) { if (Working(o.Entry)) CancelOrder(o.Entry); return; }
			if (!o.Parked && !o.Armed && !o.InTrade && !Working(o.Entry) && o.Trades > 0 && o.Trades < 2 && Close[0] < o.OrH && Close[0] > o.OrL) o.Armed = true;
			if (o.Parked || !o.Armed || o.InTrade || Working(o.Entry) || o.Trades >= 2) return;
			if (CurrentBars[0] <= deferUntil) return;			// a deferred module enters first
			int d = trendDir;
			double entry = d == 1 ? o.OrH + TickSize : o.OrL - TickSize;
			double opp = d == 1 ? o.OrL - TickSize : o.OrH + TickSize;
			int st = Math.Max(8, (int)Math.Round(Math.Min(Math.Abs(entry - opp), StopCapAtr * todayAtr) / TickSize));
			o.Armed = false;
			SetStopLoss(o.Sig, CalculationMode.Ticks, st, false);
			SetProfitTarget(o.Sig, CalculationMode.Ticks, Math.Max(1, (int)Math.Round(st * o.R)));
			bool oc = o == orb ? (FeatGap(d) >= 0.3311 || FeatRet5(d) >= 1.8118 || atrRatio >= 1.2615) : (FeatVw(d, entry) < 0.1231 || FeatOpen(d, entry) >= 0.5458);
			int oq = CtxBoost(Qty(), oc, o.Sig);
			if (!DirectionAllowed(d)) { if (lastDeferred) o.Armed = true; else if (!PastLevel(d, entry)) { o.Dir = d; ParkSetup(o, false, Instrument.MasterInstrument.RoundToTickSize(entry), oq); } return; }
			bool through = PastLevel(d, entry);
			o.Dir = d;
			Order r = d == 1 ? (through ? EnterLong(0, oq, o.Sig) : EnterLongStopMarket(0, true, oq, entry, o.Sig)) : (through ? EnterShort(0, oq, o.Sig) : EnterShortStopMarket(0, true, oq, entry, o.Sig));
			if (r != null) o.Entry = r;
			Log(string.Format("{0} {1} @ {2} | SL {3}t | TP {4:0.##}R", o.Sig, d == 1 ? "BUY" : "SELL", Fmt(entry), st, o.R));
		}

		// ---- VOLB: one stop entry per day at RTH open +/- 0.45 x prior RTH range (the side nearer to price is kept working),
		// stop at the RTH open price, target 2R, max 400 min, 09:30-15:00 entries (research/mine/families2.py, VOL_BREAK).
		private void ManageVolb(int openMin)
		{
			if (volbDone || volb.InTrade || double.IsNaN(volbUp) || double.IsNaN(rthOpenPx) || atrCount < 14) return;
			if (openMin >= 899) { if (Working(volb.Entry)) CancelOrder(volb.Entry); volbDone = true; return; }
			int d = (volbUp - Close[0]) <= (Close[0] - volbDn) ? 1 : -1;
			if (volbTrendOnly)
			{
				if (trendDir == 0 || (trendDir == 1 && Low[0] <= volbDn) || (trendDir == -1 && High[0] >= volbUp)) { if (Working(volb.Entry)) CancelOrder(volb.Entry); volbDone = true; return; }
				d = trendDir;
			}
			if (CurrentBars[0] <= deferUntil) return;      // another module is waiting for VOLB's order to be cancelled
			if (Working(volb.Entry))
			{
				if (volb.Dir == d) return;
				CancelOrder(volb.Entry); return;                    // switch side on the next bar
			}
			double lvl = d == 1 ? Instrument.MasterInstrument.RoundToTickSize(volbUp) : Instrument.MasterInstrument.RoundToTickSize(volbDn);
			if (PastLevel(d, lvl))
			{
				// realtime with the ask / bid right at the level (a stop there would be rejected): market entry; further through: no chase
				double mk = double.NaN;
				if (State == State.Realtime) try { mk = d == 1 ? GetCurrentAsk() : GetCurrentBid(); } catch { }
				if (!double.IsNaN(mk) && (mk - lvl) * d <= TickSize && !OppBusy(d, volb))
				{ ArmPriceBracket(volb, d, Instrument.MasterInstrument.RoundToTickSize(rthOpenPx)); Order vm = d == 1 ? EnterLong(0, Qty(), volb.Sig) : EnterShort(0, Qty(), volb.Sig); if (vm != null) volb.Entry = vm; }
				volbDone = true; return;
			}
			// never cancel other modules' working entries for VOLB: wait while the position or a working order points the other way
			if ((d == 1 && Position.MarketPosition == MarketPosition.Short) || (d == -1 && Position.MarketPosition == MarketPosition.Long)) return;
			foreach (Mod o in mods) if (o != volb && Working(o.Entry) && o.Dir == -d) return;
			ArmPriceBracket(volb, d, Instrument.MasterInstrument.RoundToTickSize(rthOpenPx));
			Order vr = d == 1 ? EnterLongStopMarket(0, true, Qty(), lvl, volb.Sig) : EnterShortStopMarket(0, true, Qty(), lvl, volb.Sig);
			if (vr != null) volb.Entry = vr;
		}


		// ENG10 (research/mine/ultra_plus.py): 06:00-10:00 4H candle closes beyond the 02:00-06:00 candle in its direction, with the trend.
		private void ManageEng10(int openMin)
		{
			if (eng10Retry && !eng10.InTrade && !eng10.Parked) { if (openMin >= 600 && openMin < 689) Eng10Place(); else eng10Retry = false; return; }
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
			e10d = d; e10px = px; e10sl = sl; eng10Retry = true; Eng10Place();
		}
		private int e10d; private double e10px, e10sl; private bool eng10Retry;
		private void Eng10Place()
		{
			if (!DirectionAllowed(e10d))
			{
				if (!lastDeferred) { eng10Retry = false; if (!PastLevel(e10d, e10px)) { ArmPriceBracket(eng10, e10d, e10sl); ParkSetup(eng10, false, e10px, Qty()); } }
				return;
			}
			eng10Retry = false;
			ArmPriceBracket(eng10, e10d, e10sl);
			if (PastLevel(e10d, e10px))
			{
				if ((Close[0] - e10px) * e10d > 0.5 * Math.Abs(e10px - e10sl)) { Log("ENG10 skipped (price ran > 0.5R past the level)"); return; }
				Order em = e10d == 1 ? EnterLong(0, Qty(), eng10.Sig) : EnterShort(0, Qty(), eng10.Sig);
				if (em != null) eng10.Entry = em;
			}
			else { Order er = e10d == 1 ? EnterLongStopMarket(0, true, Qty(), e10px, eng10.Sig) : EnterShortStopMarket(0, true, Qty(), e10px, eng10.Sig); if (er != null) eng10.Entry = er; }
			Log(string.Format("ENG10 {0} @ {1} | SL {2}", e10d == 1 ? "BUY" : "SELL", Fmt(e10px), Fmt(e10sl)));
		}
		// price already at/through a stop-entry level? historical: bar close; realtime: current ask / bid (a stop there would be rejected)
		private bool PastLevel(int d, double px)
		{
			if (State == State.Realtime) { try { return d == 1 ? GetCurrentAsk() >= px : GetCurrentBid() <= px; } catch { } }
			return d == 1 ? Close[0] >= px : Close[0] <= px;
		}

		private void TimeEntry(Mod m)
		{
			lastDeferred = false;
			if (atrCount < 14 || double.IsNaN(atrDaily) || m.InTrade) return;
			double reference = double.NaN;
			if (m.Lookback == -1) reference = sessOpen;
			else if (m.Lookback == -2) reference = rthOpenPx;
			else if (m.Lookback == -4) { if (double.IsNaN(full1)) return; reference = rthFirstClose; }
			else if (m.Lookback == -5) reference = m.AnchorPx;
			else if (m.Lookback == -3) reference = vwV > 0 ? vwPv / vwV : double.NaN;
			else if (m.Lookback > 0 && CurrentBars[0] > m.Lookback) reference = Close[m.Lookback - 1];
			if (double.IsNaN(reference) || Close[0] == reference) return;
			int d = Close[0] > reference ? 1 : -1;
			if (m.Reverse) d = -d;
			if (m.Trend && d != trendDir) return;
			if (m.MinDist > 0 && Math.Abs(Close[0] - reference) < m.MinDist * atrDaily) return;
			if (m.FhCheck)
			{
				if (double.IsNaN(close10) || double.IsNaN(full1)) return;
				double fh = close10 - full1;
				if ((fh > 0 ? 1 : -1) != (Close[0] > reference ? 1 : -1) || Math.Abs(fh) < m.MinDist * atrDaily) return;
			}
			if (CtxOn && m.Sig == "ON07" && FeatPdRet(d) < -0.3619) { Log("ON07 skipped: prior day moved against (context rule)"); return; }
			if (RulesOn && m.Sig == "REV06" && lonDir == d) { onSum += d; Log("REV06 skipped: LON already in the same direction"); return; }
			if (m.Vwap)
			{
				if (vwV <= 0) return;
				double vw = vwPv / vwV;
				int vd = Close[0] > vw ? 1 : (Close[0] < vw ? -1 : 0);
				if (vd != (Close[0] > reference ? 1 : -1)) return;
			}
			if (!DirectionAllowed(d)) return;
			int st = Math.Max(4, (int)Math.Round(m.StopAtr * atrDaily / TickSize));
			SetStopLoss(m.Sig, CalculationMode.Ticks, st, false);
			SetProfitTarget(m.Sig, CalculationMode.Ticks, Math.Max(1, (int)Math.Round(m.R * st)));
			m.Dir = d; m.EntryBar = CurrentBars[0] + 1;
			int tq = m.Sig == "MOM13" ? LateQty(d, Hm(m.Time)) : Qty();
			if (m.DoubleDist > 0 && !noBoost && Math.Abs(Close[0] - reference) >= m.DoubleDist * atrDaily) tq = 2 * Qty();
			Order tr = d == 1 ? EnterLong(0, tq, m.Sig) : EnterShort(0, tq, m.Sig);
			if (tr != null) m.Entry = tr;
			Log(string.Format("{0} {1} | ref {2} | SL {3}t", m.Sig, d == 1 ? "BUY" : "SELL", Fmt(reference), st));
		}

		private void CrtEntry()
		{
			lastDeferred = false;
			if (crt.Done || crt.InTrade) return;
			crt.Done = true;
			if (atrCount < 14 || double.IsNaN(todayAtr) || todayAtr <= 0) return;
			int d = 0;
			if (c2H > c1H && c2C < c1H && c2C > c1L && c2L >= c1L) d = -1;
			else if (c2L < c1L && c2C > c1L && c2C < c1H && c2H <= c1H) d = 1;
			if (d == 0 || d != trendDir) return;
			double stop = d == 1 ? c2L - TickSize : c2H + TickSize;
			double risk = (Close[0] + d * TickSize - stop) * d;
			if (risk <= 0 || risk > 0.5 * todayAtr || !DirectionAllowed(d)) return;
			ArmPriceBracket(crt, d, stop);
			int cq = CtxBoost(LateQty(d, 720), FeatTrend(d) >= 1.7456 || FeatGap(d) >= 0.1048 || FeatPdRet(d) >= 0.6155, "CRT11");
			Order cr = d == 1 ? EnterLong(0, cq, crt.Sig) : EnterShort(0, cq, crt.Sig);
			if (cr != null) crt.Entry = cr;
			Log(string.Format("CRT11 {0} | SL {1}", d == 1 ? "BUY" : "SELL", Fmt(stop)));
		}

		private void LondonStep(int openMin)
		{
			if (openMin < 180) { if (!rHas) { rH = High[0]; rL = Low[0]; rHas = true; } else { rH = Math.Max(rH, High[0]); rL = Math.Min(rL, Low[0]); } return; }
			if (!rHas || lonStage >= 3 || lon.InTrade) return;
			if (lonStage == 0)
			{
				if (openMin >= 360) { lonStage = 3; return; }
				if (Close[0] > rH || Close[0] < rL)
				{
					int d = Close[0] > rH ? 1 : -1;
					if (atrCount < 14 || double.IsNaN(atrDaily) || d != trendDir) { lonStage = 3; return; }
					lon.Dir = d; lonStage = 1;
				}
				else return;
			}
			if (lonStage == 1)
			{
				if (openMin >= 480) { lonStage = 3; return; }
				bool gap = lon.Dir == 1 ? Low[0] > High[2] : High[0] < Low[2];
				if (!gap) return;
				double lim = lon.Dir == 1 ? Low[0] : High[0];
				double stop = lon.Dir == 1 ? rL : rH;
				double risk = (lim - stop) * lon.Dir;
				lonStage = 2;
				if (risk <= 0 || risk > 0.25 * atrDaily) { lonStage = 3; return; }
				if (!DirectionAllowed(lon.Dir)) { lonStage = 3; ArmPriceBracket(lon, lon.Dir, stop); ParkSetup(lon, true, lim, Qty()); return; }
				ArmPriceBracket(lon, lon.Dir, stop);
				Order lr = lon.Dir == 1 ? EnterLongLimit(0, true, Qty(), lim, lon.Sig) : EnterShortLimit(0, true, Qty(), lim, lon.Sig);
				if (lr != null) lon.Entry = lr;
				Log(string.Format("LON {0} LIMIT @ {1} | SL {2}", lon.Dir == 1 ? "BUY" : "SELL", Fmt(lim), Fmt(stop)));
			}
		}

		private void SetupIctLevels()
		{
			lvl[0] = prevRthHigh; lvl[1] = onHas ? onH : double.NaN; lvl[2] = lonHas ? lonH : double.NaN;
			lvl[3] = prevRthLow; lvl[4] = onHas ? onL : double.NaN; lvl[5] = lonHas ? lonL : double.NaN;
			for (int q = 0; q < 6; q++) taken[q] = double.IsNaN(lvl[q]);
			if (onHas) { if (!taken[0] && onH > lvl[0]) taken[0] = true; if (!taken[3] && onL < lvl[3]) taken[3] = true; }
			if (postHas) { if (!taken[2] && postH > lvl[2]) taken[2] = true; if (!taken[5] && postL < lvl[5]) taken[5] = true; }
			levelsReady = true;
		}

		private void OnFiveMinute()
		{
			if (CurrentBars[1] < 8) return;
			// RSI(2) on the 5-minute closes (Wilder, alpha 0.5), updated on every 5m bar
			double chg = Closes[1][0] - Closes[1][1];
			if (double.IsNaN(rsiUp)) { rsiUp = Math.Max(chg, 0); rsiDn = Math.Max(-chg, 0); }
			else { rsiUp = 0.5 * rsiUp + 0.5 * Math.Max(chg, 0); rsiDn = 0.5 * rsiDn + 0.5 * Math.Max(-chg, 0); }
			rsiVal = rsiDn > 0 ? 100 - 100 / (1 + rsiUp / rsiDn) : 50;
			DateTime etClose = ToEt(Times[1][0]);
			DateTime etOpen = etClose.AddMinutes(-5);
			int openMin = etOpen.Hour * 60 + etOpen.Minute;
			int closeMin = etClose.Hour * 60 + etClose.Minute;
			int etDate = etOpen.Year * 10000 + etOpen.Month * 100 + etOpen.Day;
			if (etDate != rthDay || !CanTrade()) return;
			if (FlattenTime > 0 && closeMin >= Hm(FlattenTime)) return;

			// ---- MSEQ (uptrend days, signal bar opening 10:30-15:45)
			if (mseq.On && !mseq.InTrade && !Working(mseq.Entry) && trendDir == 1 && openMin >= 630 && openMin < 945 && atrCount >= 14)
			{
				int n = 5; bool ok = Closes[1][n] < Opens[1][n];
				double mainLow = Lows[1][n];
				for (int j = 0; ok && j < n; j++)
				{
					if (Closes[1][j] <= Opens[1][j] || Lows[1][j] <= mainLow) ok = false;
					if (j < n - 1 && Closes[1][j] <= Closes[1][j + 1]) ok = false;
				}
				double c0m = Closes[1][0]; double stopm = Instrument.MasterInstrument.RoundDownToTickSize(c0m - (c0m - mainLow) * 1.75);
				if (ok && stopm < c0m)
				{
					int mq = CtxBoost(LateQty(1, closeMin), FeatPos(1, Closes[0][0]) >= 0.9686 || FeatM30(1) >= 0.1728 || FeatRet5(1) >= 2.0674, "MSEQ");
					if (!DirectionAllowed(1)) { if (lastDeferred) { pend5 = mseq; pend5Dir = 1; pend5Stop = stopm; pend5Qty = mq; pend5Bar = CurrentBars[0]; } }
					else { ArmPriceBracket(mseq, 1, stopm); Order mo = EnterLong(0, mq, mseq.Sig); if (mo != null) mseq.Entry = mo; Log("MSEQ BUY | SL " + Fmt(stopm)); }
				}
			}

			// ---- MSEQS: mirrored momentum sequence (bullish main candle + 5 falling bearish candles below its high), only on days
			// where ORB60 has already entered SHORT (pullback down-trend day), 5m bar opening at/after that entry, 10:30-15:45
			if (mseqs.On && !mseqs.InTrade && !Working(mseqs.Entry) && orbFirstDir == -1 && openMin >= orbFirstMin && openMin >= 630 && openMin < 945)
			{
				int n = 5; bool ok = Closes[1][n] > Opens[1][n];
				double mainHigh = Highs[1][n];
				for (int j = 0; ok && j < n; j++)
				{
					if (Closes[1][j] >= Opens[1][j] || Highs[1][j] >= mainHigh) ok = false;
					if (j < n - 1 && Closes[1][j] >= Closes[1][j + 1]) ok = false;
				}
				double c0s = Closes[1][0]; double stops = Instrument.MasterInstrument.RoundToTickSize(c0s + (mainHigh - c0s) * 1.75);
				if (ok && stops > c0s)
				{
					int sq = LateQty(-1, closeMin);
					if (!DirectionAllowed(-1)) { if (lastDeferred) { pend5 = mseqs; pend5Dir = -1; pend5Stop = stops; pend5Qty = sq; pend5Bar = CurrentBars[0]; } }
					else { ArmPriceBracket(mseqs, -1, stops); Order so = EnterShort(0, sq, mseqs.Sig); if (so != null) mseqs.Entry = so; Log("MSEQS SELL | SL " + Fmt(stops)); }
				}
			}

			// ---- RSI2 pullback: RSI(2) < 10 (> 90) with the daily trend and the intraday trend (price vs RTH open and VWAP agree)
			if (rsi.On && !rsi.InTrade && !Working(rsi.Entry) && rsiTrades < 3 && closeMin >= 630 && closeMin < 945 && atrCount >= 14 && trendDir != 0
				&& !double.IsNaN(rthOpenPx) && vwV > 0 && !double.IsNaN(todayAtr) && todayAtr > 0)
			{
				double c0 = Closes[1][0], vw = vwPv / vwV;
				int it = (c0 > rthOpenPx && c0 > vw) ? 1 : ((c0 < rthOpenPx && c0 < vw) ? -1 : 0);
				int d = 0;
				if (rsiVal < 10 && trendDir == 1 && it == 1) d = 1;
				else if (rsiVal > 90 && trendDir == -1 && it == -1) d = -1;
				if (d != 0 && DirectionAllowed(d))
				{
					int st = Math.Max(4, (int)Math.Round(rsi.StopAtr * todayAtr / TickSize));
					SetStopLoss(rsi.Sig, CalculationMode.Ticks, st, false);
					SetProfitTarget(rsi.Sig, CalculationMode.Ticks, Math.Max(1, (int)Math.Round(rsi.R * st)));
					rsi.Dir = d; rsiTrades++;
					Order rr = d == 1 ? EnterLong(0, Qty(), rsi.Sig) : EnterShort(0, Qty(), rsi.Sig);
					if (rr != null) rsi.Entry = rr;
					Log(string.Format("RSI2 {0} | RSI {1:0.0} | SL {2}t", d == 1 ? "BUY" : "SELL", rsiVal, st));
				}
			}

			// ---- ICT open (09:30-10:30 bar open)
			if (!ict.On || !levelsReady) return;
			if (Working(ict.Entry))
			{
				bool invalid = (ict.Dir == -1 && Highs[1][0] > ictExtPend) || (ict.Dir == 1 && Lows[1][0] < ictExtPend);
				if (CurrentBars[1] >= ictExpiry || invalid) CancelOrder(ict.Entry);
			}
			bool inWin = openMin >= 570 && openMin < 630;
			for (int q = 0; q < 6; q++)
			{
				if (taken[q]) continue;
				bool hit = q < 3 ? Highs[1][0] > lvl[q] : Lows[1][0] < lvl[q];
				if (!hit) continue;
				taken[q] = true;
				if (!inWin) continue;
				int s = q < 3 ? 0 : 1;
				if (s == 0 && (!ictAct[0] || Highs[1][0] > ictExt[0])) { ictAct[0] = true; ictExt[0] = Highs[1][0]; ictExtBar[0] = CurrentBars[1]; }
				if (s == 1 && (!ictAct[1] || Lows[1][0] < ictExt[1])) { ictAct[1] = true; ictExt[1] = Lows[1][0]; ictExtBar[1] = CurrentBars[1]; }
			}
			if (!inWin) { ictAct[0] = ictAct[1] = false; return; }
			for (int s = 0; s < 2; s++)
			{
				if (!ictAct[s]) continue;
				if (s == 0 && Highs[1][0] > ictExt[0]) { ictExt[0] = Highs[1][0]; ictExtBar[0] = CurrentBars[1]; }
				if (s == 1 && Lows[1][0] < ictExt[1]) { ictExt[1] = Lows[1][0]; ictExtBar[1] = CurrentBars[1]; }
				if (CurrentBars[1] - ictExtBar[s] > 4) { ictAct[s] = false; continue; }
				if (CurrentBars[1] == ictExtBar[s]) continue;
				int j = CurrentBars[1] - ictExtBar[s];
				if (s == 0) { if (Closes[1][j] <= Opens[1][j]) j++; while (j + 1 <= CurrentBars[1] && Closes[1][j] > Opens[1][j] && Closes[1][j + 1] > Opens[1][j + 1]) j++; }
				else { if (Closes[1][j] >= Opens[1][j]) j++; while (j + 1 <= CurrentBars[1] && Closes[1][j] < Opens[1][j] && Closes[1][j + 1] < Opens[1][j + 1]) j++; }
				double cisd = Opens[1][j];
				bool trig = s == 0 ? Closes[1][0] < cisd : Closes[1][0] > cisd;
				if (!trig) continue;
				ictAct[s] = false;
				int d = s == 0 ? -1 : 1;
				if (ict.InTrade || Working(ict.Entry) || ict.Parked || ictTrades >= 3 || d != trendDir || atrCount < 14) continue;
				double stop = d == -1 ? ictExt[s] + TickSize : ictExt[s] - TickSize;
				double lim = Instrument.MasterInstrument.RoundToTickSize(cisd);
				if ((d == -1 && lim <= Closes[1][0]) || (d == 1 && lim >= Closes[1][0])) continue;
				double risk = (stop - lim) * (-d);
				if (risk <= 0 || risk > 0.25 * todayAtr) continue;
				int iq = Qty() * ((Profile == NQMasterProfile.MaxPlus || Profile == NQMasterProfile.MaxPlus2 || Profile == NQMasterProfile.Ultra || Profile == NQMasterProfile.WR70Plus || Profile == NQMasterProfile.Core || Profile == NQMasterProfile.Custom) ? (noBoost ? 1 : IctMultiplier) : 1);
				if (!DirectionAllowed(d))
				{
					if (lastDeferred) ictAct[s] = true;
					else { ict.Dir = d; ictExtPend = ictExt[s]; ictExpiry = CurrentBars[1] + 20; ArmPriceBracket(ict, d, stop); ParkSetup(ict, true, lim, iq); }
					continue;
				}
				ict.Dir = d; ictExtPend = ictExt[s]; ictExpiry = CurrentBars[1] + 20;
				ArmPriceBracket(ict, d, stop);
				Order ir = d == 1 ? EnterLongLimit(0, true, iq, lim, ict.Sig) : EnterShortLimit(0, true, iq, lim, ict.Sig);
				if (ir != null) ict.Entry = ir;
				Log(string.Format("ICT {0} LIMIT @ {1} | SL {2}", d == 1 ? "BUY" : "SELL", Fmt(lim), Fmt(stop)));
			}
		}

		private void ArmPriceBracket(Mod m, int d, double stop)
		{
			m.Dir = d; m.StopPx = stop;
			SetStopLoss(m.Sig, CalculationMode.Price, stop, false);
			SetProfitTarget(m.Sig, CalculationMode.Ticks, 4000);	// replaced on fill
		}
		#endregion

		#region Account layer and helpers
		// ---- position size: fixed Contracts, or adaptive (SizeHigh while the strategy's closed-trade drawdown from its
		// peak is below SizeDownDrawdown, SizeLow otherwise). Research (Apex 50K, real MNQ): 2 -> 1 when DD > $800 gives
		// pass-in-30-days 29% with 5% bust vs fixed 2: 33% pass / 21% bust.
		private double eqPeak;
		// ---- daily loss limit (funded-account mode): once the session's realized P&L of this strategy reaches -DailyLossLimit,
		// flatten and stop for the rest of the session (research/mine/apex50_stats.py: Apex 50K PA busts 42/12/33% -> 29/8/20% with $400).
		private double dayStartPnl; private bool dayStopped;
		private void DailyLossCheck()
		{
			if (DailyLossLimit <= 0 || dayStopped) return;
			if (netPnl - dayStartPnl <= -DailyLossLimit) { dayStopped = true; FlattenAll("daily loss limit"); Log("DAILY LOSS LIMIT reached - no more trades this session"); }
		}
		// ---- evaluation mode (research/mine/evalpol.py): Contracts per module (2 recommended); if on the EvalLateDay-th session
		// (0-based, counted from EvalStartDate) the evaluation profit is still below EvalLateGoal, trade EvalLateContracts until the end.
		// Apex 50K, Ultra: pass within 30 days 39% (3 fixed) -> 50% (2 -> 3 at day 12 if < $2,000, daily loss limit $800).
		private int evalDayIndex = -1; private double evalEqDayStart, evalPnlBase = double.NaN;
		private double EvalEquity()
		{
			if (State == State.Realtime) return Account.Get(AccountItem.CashValue, Currency.UsDollar) - StartBalance;
			return double.IsNaN(evalPnlBase) ? 0 : netPnl - evalPnlBase;
		}
		private void EvalSessionStart(DateTime tradeDay)
		{
			if (!EvalMode) return;
			DateTime st;
			if (!DateTime.TryParseExact(EvalStartDate ?? "", "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out st) || tradeDay < st) return;
			if (double.IsNaN(evalPnlBase)) evalPnlBase = netPnl;
			evalDayIndex++; evalEqDayStart = EvalEquity();
			if (evalDayIndex == EvalLateDay && evalEqDayStart < EvalLateGoal) Log(string.Format("EVAL: day {0}, profit {1:0} < {2:0} -> {3} contracts", evalDayIndex, evalEqDayStart, EvalLateGoal, EvalLateContracts));
		}
		private int Qty()
		{
			if (EvalMode) return (evalDayIndex >= EvalLateDay && evalEqDayStart < EvalLateGoal
				&& (EvalLateMinCushion <= 0 || double.IsNaN(propCushion) || propCushion >= EvalLateMinCushion)) ? EvalLateContracts : Contracts;
			if (!AdaptiveSize) return Contracts;
			return (eqPeak - netPnl) > SizeDownDrawdown ? SizeLow : SizeHigh;
		}

		// ---- confluence rules (research/improve2.py, chosen on CFD 2020-23, held every year 2020-26 and on real MNQ):
		// A) late modules (CRT11, MOM13, MSEQ, MSEQS entering after 11:00) trade 2x size when they go AGAINST today's MOM11 trade
		//    and WITH the overnight modules (sign of ON07+REV06+LON directions): PF 2.06 / 1.81 / 1.63 vs 1.38 / 1.16 / 1.22.
		// B) REV06 is skipped when LON already entered the same direction today: PF 0.83 / 0.92 / 1.12 vs 1.37 / 1.29 / 1.20.
		private bool RulesOn { get { return UseConfluence && (Profile == NQMasterProfile.MaxPlus || Profile == NQMasterProfile.MaxPlus2 || Profile == NQMasterProfile.Ultra || Profile == NQMasterProfile.WR70Plus || Profile == NQMasterProfile.Custom); } }

		// ---- context rules (MaxPlus2; research/mine/filt_mine.py + filt_holdout.py): thresholds chosen on CFD 2020-23 (tertiles/quintiles),
		// kept only if they also held in 2024-25 on CFD AND real MNQ; 2026 was a clean holdout (PF 1.50 -> 1.58 real, 1.42 -> 1.49 CFD).
		// Boosts double the size (never above 2x the base size), the ON07 rule skips the trade. Features are in daily-ATR units,
		// oriented with the trade direction d.
		private double sessHi, sessLo, atrRatio = double.NaN;
		private List<double> atrHist;
		private bool CtxOn { get { return UseContextRules && (Profile == NQMasterProfile.MaxPlus2 || Profile == NQMasterProfile.Ultra || Profile == NQMasterProfile.WR70Plus || Profile == NQMasterProfile.Custom); } }
		private int CtxBoost(int q, bool cond, string who)
		{
			if (!CtxOn || !cond || noBoost) return q;
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
		private double FeatOpen(int d, double px) { return (double.IsNaN(rthOpenPx) || todayAtr <= 0) ? double.NaN : (px - rthOpenPx) * d / todayAtr; }
		private int LateQty(int d, int entryMin)
		{
			int q = Qty();
			if (RulesOn && !noBoost && m11Dir == -d && onSum * d > 0 && entryMin > 660) { q *= 2; Log("confluence x2 (against MOM11, with overnight)"); }
			return q;
		}


		// ---- edge monitor (research/mine/robust_monitor.py). Live trading is the final out-of-sample test: this one-sided CUSUM
		// watches the daily P&L per base contract, normalised by the daily ATR (z = day $ / contracts / (2 x ATR points)):
		//   S = max(0, S + k - z); alarm when S > h.  k = half the backtested mean, h calibrated on 2020-26 block bootstrap so that
		// false alarms are rare (Ultra: 1.5%/year, 7% in 3 years) and no alarm fires anywhere in the 2020-26 history.
		// If the edge disappears (mean -> 0) the alarm fires after ~7 months (median), if it turns negative (-50%) after ~4 months.
		// Days that cannot trade (FOMC, low ATR, sessions without RTH) are not counted. Counting starts at EdgeMonitorStart.
		private double edgeS, edgeK = double.NaN, edgeH = double.NaN; private int edgeDays, edgeDayQty = 1; private bool edgeAlarm, edgePaused, edgeDayRth, edgeDayTradable;
		private DateTime edgeDayDate = DateTime.MinValue;
		private void EdgeParams()
		{
			double k, h;
			switch (Profile)
			{
				case NQMasterProfile.WR70Plus: case NQMasterProfile.WinRate70: k = 0.0559; h = 15.05; break;
				case NQMasterProfile.Core: k = 0.0397; h = 9.98; break;
				default: k = 0.0755; h = 16.21; break;			// Ultra (MaxSharpe / MaxPlus / MaxPlus2 / MaxTrades / Custom use the Ultra calibration)
			}
			edgeK = EdgeK > 0 ? EdgeK : k; edgeH = EdgeH > 0 ? EdgeH : h;
		}
		private void EdgeDayClose(DateTime etNow)
		{
			bool counted = EdgeMonitor && Profile != NQMasterProfile.Gold && edgeDayRth && edgeDayTradable && edgeDayDate != DateTime.MinValue && !double.IsNaN(todayAtr) && todayAtr > 0
				&& !(MinAtrPoints > 0 && todayAtr < MinAtrPoints);
			DateTime st;
			if (counted && DateTime.TryParseExact(EdgeMonitorStart ?? "", "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out st) && edgeDayDate >= st)
			{
				if (double.IsNaN(edgeK)) EdgeParams();
				double z = (netPnl - dayStartPnl) / Math.Max(1, edgeDayQty) / (2.0 * todayAtr);
				edgeS = Math.Max(0.0, edgeS + edgeK - z); edgeDays++;
				if (PrintLog) Print(string.Format("{0} | NQM | EDGE day {1}: z {2:0.000} | CUSUM {3:0.00} / {4:0.00} ({5:0}%)", edgeDayDate.ToString("yyyy-MM-dd"), edgeDays, z, edgeS, edgeH, 100 * edgeS / edgeH));
				if (!edgeAlarm && edgeS > edgeH)
				{
					edgeAlarm = true; edgePaused = EdgeMonitorPause;
					Print(string.Format("NQMaster | EDGE MONITOR ALARM {0}: live results are no longer consistent with the backtested edge ({1} days counted). {2}",
						edgeDayDate.ToString("yyyy-MM-dd"), edgeDays, EdgeMonitorPause ? "New entries paused. Review, then set a new 'Edge monitor start date' to resume." : "Alert only (pause is off)."));
				}
			}
			edgeDayRth = false;
		}


		// ---- prop-account cushion gating (research/mine/acct_final.py; Lucid Flex 50K, 1 contract per module, MNQ + MGC 2024-26)
		// Eval  : FULL while the cushion over the liquidation threshold is >= EvalCushionFull ($900), SAFE below; own daily stop $700.
		//         Pass 88.9% vs 78.0% (busts 11% vs 22%) when evals are also started only with ATR < 1.15 x its 60-day median.
		// Funded: SAFE while cushion < FundedCushionSafe ($1,500), NO-BOOST above; request payouts at >= $6,000 profit.
		// EQUILIBRIO defaults (acct_life2.py / acct_mc.py, 12-month lifecycle): eval = full profile (EvalCushionFull 0, no daily stop) with
		// GoldMaster Robust; funded = SAFE below $750 cushion, FULL above (FundedHighFull), payouts at $5,000 with GoldMaster WinRate.
		// vs today: +$20-200/month per account in history, +1 tick cost stress and 2,000 bootstrap years; fewer funded accounts lost.
		//         Accounts lost within 12 months 25% vs 44%; cash per account ~$6.8k vs ~$5.6k.
		private enum GateMode { Full, NoBoost, Safe }
		private GateMode gate = GateMode.Full; private bool noBoost, propStopped;
		private double propPeak = double.NaN, propThr = double.NaN, propCushion = double.NaN, propDayStart = double.NaN, atrStartRatio = double.NaN;
		private bool propLive; private double propBestDay = 0, savedPrevDayStart = double.NaN, storedOverride = double.NaN; private int propRestoredDay = -1, prevSessDay, curSessDay;
		private int EvalStartInt() { DateTime st; return DateTime.TryParseExact(EvalStartDate ?? "", "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out st) ? st.Year * 10000 + st.Month * 100 + st.Day : 0; }
		private void PropSave(int tradeDay)
		{
			if (!propLive) return;
			try { File.WriteAllText(PropFile, string.Format(CultureInfo.InvariantCulture, "{0:0.00};{1};{2:0.00};{3:0.00};{4:0.00}", propPeak, tradeDay, propDayStart, propBestDay, PropPeakOverride)); } catch { }
		}
		private string PropFile { get { try { return Path.Combine(Core.Globals.UserDataDir, "nqmaster_prop_" + (Account != null ? Account.Name : "acct") + ".txt"); } catch { return null; } } }
		private double PropEquity()
		{
			if (State == State.Realtime) return Account.Get(AccountItem.CashValue, Currency.UsDollar);
			return StartBalance + netPnl;
		}
		private void PropGoLive()
		{
			if (PropMode == NQMasterPropMode.Off) return;
			propLive = true; propPeak = StartBalance; propDayStart = double.NaN; propBestDay = EvalBestDaySoFar;
			DateTime et = ToEt(Times[0][0]); DateTime td = et.Hour >= 18 ? et.Date.AddDays(1) : et.Date; int today = td.Year * 10000 + td.Month * 100 + td.Day;
			try
			{
				string f = PropFile;
				if (f != null && File.Exists(f))
				{
					string[] a = File.ReadAllText(f).Trim().Split(';'); double v;
					int fd = 0; double ds, bd, ov;
					bool fresh = a.Length >= 4 && int.TryParse(a[1], out fd) && fd >= EvalStartInt();	// older than EvalStartDate = another eval
					bool stalePeak = PropMode == NQMasterPropMode.Eval && a.Length >= 4 && !fresh;				// a new eval does not inherit an old peak
					if (!stalePeak && a.Length > 0 && double.TryParse(a[0], NumberStyles.Any, CultureInfo.InvariantCulture, out v)) propPeak = Math.Max(propPeak, v);
					if (fresh && double.TryParse(a[2], NumberStyles.Any, CultureInfo.InvariantCulture, out ds))
					{ if (fd == today) propDayStart = ds; else if (fd == prevSessDay) savedPrevDayStart = ds; }
					if (fresh && double.TryParse(a[3], NumberStyles.Any, CultureInfo.InvariantCulture, out bd)) propBestDay = Math.Max(propBestDay, bd);
					if (a.Length >= 5 && double.TryParse(a[4], NumberStyles.Any, CultureInfo.InvariantCulture, out ov)) storedOverride = ov;
				}
			}
			catch { }
			// manual correction (e.g. a stale file after an account reset): applied once; later restarts keep the higher saved peak
			bool newOverride = double.IsNaN(storedOverride) || Math.Abs(PropPeakOverride - storedOverride) > 0.01;
			if (PropPeakOverride > 0) propPeak = newOverride ? PropPeakOverride : Math.Max(propPeak, PropPeakOverride);
			// first start of the day (no saved state): the day started at equity now minus what the account already realized today
			if (double.IsNaN(propDayStart)) { try { propDayStart = PropEquity() - Account.Get(AccountItem.RealizedProfitLoss, Currency.UsDollar); } catch { } }
			// the last session NinjaTrader saw start was not closed by it (shut down before 18:00): its P&L = today's start - its start
			if (!double.IsNaN(savedPrevDayStart) && !double.IsNaN(propDayStart)) { propBestDay = Math.Max(propBestDay, propDayStart - savedPrevDayStart); savedPrevDayStart = double.NaN; }
			if (!double.IsNaN(propDayStart)) { propRestoredDay = today; }
			PropSessionStart();
		}
		private void PropSessionStart()
		{
			gate = GateMode.Full; noBoost = false; propStopped = false;
			if (PropMode != NQMasterPropMode.Off)
			{
				double eq = PropEquity();
				DateTime et0 = ToEt(Times[0][0]); DateTime td0 = et0.Hour >= 18 ? et0.Date.AddDays(1) : et0.Date; int tday = td0.Year * 10000 + td0.Month * 100 + td0.Day;
				if (propRestoredDay == tday && !double.IsNaN(propDayStart)) { }                  // restarted mid-session: keep the saved day start
				else { if (!double.IsNaN(propDayStart)) propBestDay = Math.Max(propBestDay, eq - propDayStart); propDayStart = eq; }
				propRestoredDay = -1;
				if (double.IsNaN(propPeak)) propPeak = Math.Max(StartBalance, PropPeakOverride > 0 ? PropPeakOverride : eq);
				if (eq > propPeak) propPeak = eq;
				PropSave(tday);
				propThr = propPeak >= StartBalance + PropTrailingDD + 100 ? StartBalance + 100 : propPeak - PropTrailingDD;
				if (PropThresholdOverride > 0) propThr = PropThresholdOverride;
				propCushion = eq - propThr;
				if (PropMode == NQMasterPropMode.Eval) gate = propCushion >= EvalCushionFull ? GateMode.Full : GateMode.Safe;
				else if (FundedCushionFull > 0) gate = propCushion < FundedCushionSafe ? GateMode.Safe : (propCushion < FundedCushionFull ? GateMode.NoBoost : GateMode.Full);
				else gate = propCushion >= FundedCushionSafe ? (FundedHighFull ? GateMode.Full : GateMode.NoBoost) : GateMode.Safe;
				noBoost = gate != GateMode.Full;
			}
			foreach (Mod m in mods)
				m.On = m.BaseOn && !(gate == GateMode.Safe && (m.Sig == "VOLB" || m.Sig == "LON" || m.Sig == "MOM1030" || m.Sig == "MOM11"));
			atrStartRatio = double.NaN;
			if (atrHist != null && atrHist.Count >= 20 && !double.IsNaN(todayAtr) && todayAtr > 0)
			{
				List<double> srt = new List<double>(atrHist.Count > 60 ? atrHist.GetRange(atrHist.Count - 60, 60) : atrHist); srt.Sort(); int nn = srt.Count;
				double med = nn % 2 == 1 ? srt[nn / 2] : 0.5 * (srt[nn / 2 - 1] + srt[nn / 2]); atrStartRatio = med > 0 ? todayAtr / med : double.NaN;
			}
			if (PropMode != NQMasterPropMode.Off) Log(string.Format("PROP {0}: equity {1:0} | threshold {2:0} | cushion {3:0} -> {4}", PropMode, PropEquity(), propThr, propCushion, gate));
		}
		private void PropDailyCheck()
		{
			if (PropMode != NQMasterPropMode.Eval || (EvalDailyStop <= 0 && EvalProfitStop <= 0) || propStopped || double.IsNaN(propDayStart)) return;
			double now = State == State.Realtime ? Account.Get(AccountItem.CashValue, Currency.UsDollar) + Account.Get(AccountItem.UnrealizedProfitLoss, Currency.UsDollar)
				: StartBalance + netPnl + (Position.MarketPosition == MarketPosition.Flat ? 0 : Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Closes[0][0]));
			if (EvalDailyStop > 0 && now - propDayStart <= -EvalDailyStop) { propStopped = true; FlattenAll("prop daily stop"); Log(string.Format("PROP DAILY STOP: {0:0} today", now - propDayStart)); }
			else if (EvalProfitStop > 0 && now - propDayStart >= EvalProfitStop) { propStopped = true; FlattenAll("eval daily profit stop"); Log(string.Format("EVAL DAILY PROFIT STOP: +{0:0} today (Lucid consistency)", now - propDayStart)); }
		}

		private bool lastDeferred; private int deferUntil = -1;
		private Mod pend5; private int pend5Dir, pend5Qty, pend5Bar; private double pend5Stop;
		// Opposite open position -> skip. Opposite WORKING entry orders (e.g. an ORB stop order) -> cancel them and defer this entry
		// one bar (NinjaTrader's managed rules ignore an entry while an opposite entry order is working).
		private bool DirectionAllowed(int d)
		{
			lastDeferred = false;
			if ((d == 1 && Position.MarketPosition == MarketPosition.Short) || (d == -1 && Position.MarketPosition == MarketPosition.Long)) return false;
			// an opposite MARKET entry already sent (fills at the next open) counts as an open position: research keeps the first trade
			foreach (Mod m in mods) if (Working(m.Entry) && m.Dir == -d && m.Entry.OrderType == OrderType.Market) return false;
			bool blocked = false;
			foreach (Mod m in mods) if (Working(m.Entry) && m.Dir == -d) { ParkOrder(m); blocked = true; }
			if (blocked) { lastDeferred = true; deferUntil = CurrentBars[0] + (BarsInProgress == 1 ? 5 : 1); return false; }
			return true;
		}

		private bool CanTrade()
		{
			if (fomcToday) { status = "FOMC day: no trading"; return false; }
			if (targetHit) { status = "eval target reached"; return false; }
			if (ddTripped) { status = "drawdown guard"; return false; }
			if (dayStopped) { status = "daily loss limit"; return false; }
			if (propStopped) { status = "prop daily stop"; return false; }
			if (MinAtrPoints > 0 && Profile != NQMasterProfile.Gold && !double.IsNaN(todayAtr) && todayAtr < MinAtrPoints) { status = "low volatility (ATR " + todayAtr.ToString("0") + " < " + MinAtrPoints.ToString("0") + ")"; return false; }
			if (PauseActive()) { status = "MANUAL PAUSE (file)"; return false; }
			if (edgePaused) { status = "EDGE MONITOR ALARM - review before trading"; return false; }
			status = "trading";
			return true;
		}

		private void AccountGuard()
		{
			if (State != State.Realtime) return;
			double bal = Account.Get(AccountItem.CashValue, Currency.UsDollar);
			if (double.IsNaN(highWater) || bal > highWater) highWater = bal;
			if (EvalTarget > 0 && !targetHit)
			{
				// Lucid-style consistency: the best day may be at most ConsistencyPct % of the total profit -> the real target can be higher
				double eqNow = bal + Account.Get(AccountItem.UnrealizedProfitLoss, Currency.UsDollar);
				double today = double.IsNaN(propDayStart) ? 0 : eqNow - propDayStart;
				double need = EvalTarget;
				if (ConsistencyPct > 0) need = Math.Max(need, Math.Max(propBestDay, today) * 100.0 / ConsistencyPct);
				if (eqNow >= StartBalance + need) { targetHit = true; FlattenAll("eval target"); Print(string.Format("NQMaster | EVAL TARGET REACHED (+{0:0}, needed {1:0}) - trading stopped.", bal - StartBalance, need)); }
			}
			if (EvalTarget > 0 && targetHit && Position.MarketPosition == MarketPosition.Flat && Math.Abs(Account.Get(AccountItem.UnrealizedProfitLoss, Currency.UsDollar)) < 0.01)
			{
				double today = double.IsNaN(propDayStart) ? 0 : bal - propDayStart, need = EvalTarget;
				if (ConsistencyPct > 0) need = Math.Max(need, Math.Max(propBestDay, today) * 100.0 / ConsistencyPct);
				if (bal < StartBalance + need) { targetHit = false; Print(string.Format("NQMaster | eval target not met after closing (+{0:0}, needed {1:0}) - trading resumes.", bal - StartBalance, need)); }
			}
			if (MaxDrawdown > 0 && bal <= highWater - MaxDrawdown + DrawdownBuffer && !ddTripped) { ddTripped = true; FlattenAll("drawdown guard"); Print("NQMaster | DRAWDOWN GUARD - trading stopped."); }
		}

		private void ExitModule(Mod m, string why)
		{
			if (Position.MarketPosition == MarketPosition.Long) ExitLong(0, Math.Max(1, Position.Quantity), m.Sig + "X", m.Sig);
			else if (Position.MarketPosition == MarketPosition.Short) ExitShort(0, Math.Max(1, Position.Quantity), m.Sig + "X", m.Sig);
			Log(m.Sig + " exit: " + why);
		}

		private void FlattenAll(string why)
		{
			CancelAllEntries();
			if (Position.MarketPosition == MarketPosition.Flat || flattenBar == CurrentBars[0]) return;
			flattenBar = CurrentBars[0];
			if (Position.MarketPosition == MarketPosition.Long) ExitLong(); else ExitShort();
			Log("FLATTEN: " + why);
		}

		private void CancelAllEntries() { foreach (Mod m in mods) { m.Parked = false; if (Working(m.Entry)) CancelOrder(m.Entry); } }
		// ---- parking (research/mine/patch_review2.py): research keeps every module's order working and only drops a fill against an open
		// opposite position. NinjaTrader's managed rules cannot hold opposite entry orders at once, so the cancelled one is kept here and
		// re-placed as soon as no opposite position / working order remains. Dropped if its level trades while blocked or its window ends.
		private void ParkOrder(Mod o)
		{
			Order e = o.Entry;
			if (e == null || !Working(e)) return;
			if (o != volb && (e.OrderType == OrderType.StopMarket || e.OrderType == OrderType.Limit))
			{ o.Parked = true; o.ParkHit = false; o.ParkLimit = e.OrderType == OrderType.Limit; o.ParkPx = o.ParkLimit ? e.LimitPrice : e.StopPrice; o.ParkQty = Math.Max(1, e.Quantity); Log(o.Sig + " order parked (opposite trade)"); }
			CancelOrder(e);
		}
		// a setup blocked by an opposite POSITION at placement time: kept and placed when free (research drops only a fill against it)
		private void ParkSetup(Mod o, bool limit, double px, int qty)
		{
			o.Parked = true; o.ParkHit = false; o.ParkLimit = limit; o.ParkPx = px; o.ParkQty = Math.Max(1, qty);
			Log(string.Format("{0} setup parked @ {1} (opposite position open)", o.Sig, Fmt(px)));
		}
		private bool OppBusy(int d, Mod self)
		{
			if ((d == 1 && Position.MarketPosition == MarketPosition.Short) || (d == -1 && Position.MarketPosition == MarketPosition.Long)) return true;
			foreach (Mod o in mods) if (o != self && Working(o.Entry) && o.Dir == -d) return true;
			return false;
		}
		private bool ParkExpired(Mod o, int openMin, int closeMin)
		{
			if (o.Kind == 0) return closeMin >= 780;
			if (o == eng10) return openMin >= 689;
			if (o == lon) return openMin >= 480;
			if (o == ict) return CurrentBars[1] >= ictExpiry || (ict.Dir == -1 && High[0] > ictExtPend) || (ict.Dir == 1 && Low[0] < ictExtPend);
			return true;
		}
		private void ManageParked(int openMin, int closeMin)
		{
			foreach (Mod o in mods)
			{
				if (!o.Parked) continue;
				if (o.ParkLimit ? (o.Dir == 1 ? Low[0] <= o.ParkPx : High[0] >= o.ParkPx) : (o.Dir == 1 ? High[0] >= o.ParkPx : Low[0] <= o.ParkPx)) o.ParkHit = true;	// latched
				if (Working(o.Entry)) continue;									// the cancel is still pending
				if (o.InTrade || o.ParkHit || ParkExpired(o, openMin, closeMin)) { o.Parked = false; Log(o.Sig + " parked order dropped" + (o.ParkHit ? " (level traded while blocked)" : "")); continue; }
				if (CurrentBars[0] <= deferUntil) continue;						// the module that parked it enters first
				if (OppBusy(o.Dir, o)) continue;
				o.Parked = false;
				Order r = null;
				if (o.ParkLimit) r = o.Dir == 1 ? EnterLongLimit(0, true, o.ParkQty, o.ParkPx, o.Sig) : EnterShortLimit(0, true, o.ParkQty, o.ParkPx, o.Sig);
				else if (PastLevel(o.Dir, o.ParkPx)) { Log(o.Sig + " parked order dropped (level passed)"); continue; }
				else r = o.Dir == 1 ? EnterLongStopMarket(0, true, o.ParkQty, o.ParkPx, o.Sig) : EnterShortStopMarket(0, true, o.ParkQty, o.ParkPx, o.Sig);
				if (r != null) o.Entry = r;
				Log(o.Sig + " parked order re-placed @ " + Fmt(o.ParkPx));
			}
		}

		private static bool Working(Order o)
		{
			if (o == null) return false;
			OrderState s = o.OrderState;
			return s != OrderState.Filled && s != OrderState.Cancelled && s != OrderState.Rejected && s != OrderState.Unknown;
		}
		private Mod BySig(string sig) { if (mods == null || string.IsNullOrEmpty(sig)) return null; foreach (Mod m in mods) if (m.Sig == sig) return m; return null; }

		protected override void OnOrderUpdate(Order order, double limitPrice, double stopPrice, int quantity, int filled, double averageFillPrice,
			OrderState orderState, DateTime time, ErrorCode error, string nativeError)
		{
			Mod m = BySig(order.Name);
			if (m != null && (m.Entry == null || m.Entry == order || !Working(m.Entry))) m.Entry = order;
			if (orderState == OrderState.Rejected)
			{
				Print(string.Format("NQMaster | {0} REJECTED: {1} {2}", order.Name, error, nativeError));
				// a rejected stop-loss / target leaves that module unprotected -> exit it; any other rejected exit -> flatten; a rejected entry is skipped
				if (m == null && Position.MarketPosition != MarketPosition.Flat)
				{
					Mod f = (order.Name == "Stop loss" || order.Name == "Profit target") ? BySig(order.FromEntrySignal) : null;
					if (f != null) { if (f.InTrade) ExitModule(f, "protective order rejected"); }
					else FlattenAll("exit order rejected");
				}
			}
		}

		protected override void OnExecutionUpdate(Execution execution, string executionId, double price, int quantity,
			MarketPosition marketPosition, string orderId, DateTime time)
		{
			if (execution.Order == null) return;
			Mod m = BySig(execution.Order.Name);
			if (m != null)
			{
				if (execution.Order.Filled <= 0) return;
				bool first = !m.InTrade;
				m.InTrade = true; m.EntryPx = execution.Order.AverageFillPrice;
				if (first)
				{
				if (m == orb) { orb.Trades++; if (orbFirstDir == 0) { orbFirstDir = orb.Dir; DateTime eo = ToEt(Times[0][0]).AddMinutes(-1); orbFirstMin = eo.Hour * 60 + eo.Minute; } }
				if (m == orb2) orb2.Trades++;
				if (m == volb) { volbDone = true; volb.EntryBar = CurrentBars[0]; }
				if (m == eng10) eng10.EntryBar = CurrentBars[0];
				if (m.Sig == "MOM11" && m11Dir == 0) m11Dir = m.Dir;
				if (m == lon || m.Sig == "ON07" || m.Sig == "REV06") onSum += m.Dir;
				if (m == lon && lonDir == 0) lonDir = lon.Dir;
				if (m == ict) ictTrades++;
				if (m.Kind == 1 || m == rsi) m.EntryBar = CurrentBars[0];
				// cancel opposite working entries
				foreach (Mod o in mods) if (o != m && Working(o.Entry) && o.Dir == -m.Dir) ParkOrder(o);
				}
				if (m.PriceTarget)
				{
					double fill = m.EntryPx; double risk = (fill - m.StopPx) * m.Dir;
					if (risk <= 0) { ExitModule(m, "filled beyond stop"); return; }
					double tgt = Instrument.MasterInstrument.RoundToTickSize(fill + m.Dir * m.R * risk);
					SetProfitTarget(m.Sig, CalculationMode.Price, tgt);
				}
				Log(string.Format("{0} filled @ {1}", m.Sig, Fmt(m.EntryPx)));
				return;
			}
			Mod from = BySig(execution.Order.FromEntrySignal);
			if (from != null && execution.Order.OrderState == OrderState.Filled) from.InTrade = false;
			if (Position.MarketPosition == MarketPosition.Flat) foreach (Mod x in mods) x.InTrade = false;
		}

		private void ProcessClosedTrades()
		{
			int count = SystemPerformance.AllTrades.Count;
			for (int i = tradesProcessed; i < count; i++)
			{
				double pnl = SystemPerformance.AllTrades[i].ProfitCurrency;
				totalTrades++; netPnl += pnl;
				if (pnl > 0) { totalWins++; grossWin += pnl; } else grossLoss -= pnl;
				if (netPnl > eqPeak) eqPeak = netPnl;
			}
			tradesProcessed = count;
			if (Position.MarketPosition == MarketPosition.Flat) foreach (Mod x in mods) x.InTrade = false;
		}

		private bool PauseActive()
		{
			if (string.IsNullOrWhiteSpace(PauseFile)) return false;
			try { string p = Path.IsPathRooted(PauseFile) ? PauseFile : Path.Combine(Core.Globals.UserDataDir, PauseFile); return File.Exists(p); }
			catch { return false; }
		}
		private DateTime ToEt(DateTime t)
		{
			if (etZone == null) return t;
			try { return TimeZoneInfo.ConvertTime(DateTime.SpecifyKind(t, DateTimeKind.Unspecified), Core.Globals.GeneralOptions.TimeZoneInfo, etZone); }
			catch { return t; }
		}
		private static int Hm(int hhmm) { return (hhmm / 100) * 60 + hhmm % 100; }
		private string Fmt(double p) { return Instrument.MasterInstrument.FormatPrice(p); }
		private void Log(string m) { if (PrintLog) Print(string.Format("{0} | NQM | {1}", Times[0][0].ToString("yyyy-MM-dd HH:mm", CultureInfo.InvariantCulture), m)); }
		private void UpdateDashboard()
		{
			if (!ShowDashboard || (State == State.Historical && CurrentBars[0] < Count - 2)) return;
			double pf = grossLoss > 0 ? grossWin / grossLoss : 0;
			StringBuilder mm = new StringBuilder();
			foreach (Mod m in mods) if (m.On) mm.Append(m.Sig + (m.InTrade ? "*" : Working(m.Entry) ? "~" : "") + " ");
			string txt = string.Format("NQ MASTER ({0}) | {1}\ntrend {2} | ATRd {3:0.0} | pullback day {4}\n{5}\nTotal {6} tr | WR {7:0.0}% | PF {8:0.00} | ${9:0.00}",
				Profile, status, trendDir == 1 ? "UP" : trendDir == -1 ? "DOWN" : "-", todayAtr, pullbackDay ? "yes" : "no", mm.ToString(),
				totalTrades, totalTrades > 0 ? 100.0 * totalWins / totalTrades : 0, pf, netPnl);
			if (EdgeMonitor && !double.IsNaN(edgeH) && edgeH > 0) txt += string.Format("\nEdge monitor: {0:0}% of alarm ({1} days){2}", 100 * edgeS / edgeH, edgeDays, edgeAlarm ? " | ALARM" : "");
			if (PropMode != NQMasterPropMode.Off) txt += string.Format("\nProp {0}: mode {1} | cushion ${2:0} (threshold ${3:0})", PropMode, gate, propCushion, propThr);
			if (PropMode == NQMasterPropMode.Funded && PropEquity() - StartBalance >= FundedPayoutAt) txt += string.Format("\nPAYOUT: profit >= ${0:0} -> request it", FundedPayoutAt);
			if (AtrStartMax > 0 && !double.IsNaN(atrStartRatio)) txt += string.Format("\nATR ratio {0:0.00}: {1}", atrStartRatio, atrStartRatio < AtrStartMax ? "OK to start a new eval" : "do NOT start a new eval today");
			Draw.TextFixed(this, "NQM_Dash", txt, TextPosition.TopRight, Brushes.White, dashFont, Brushes.Transparent, Brushes.Black, 75);
		}
		#endregion

		#region Properties
		[NinjaScriptProperty][Display(Name = "Profile", Order = 0, GroupName = "00. Profile")] public NQMasterProfile Profile { get; set; }
		[NinjaScriptProperty][Display(Name = "ORB on ", Order = 1, GroupName = "01. Module switches (any profile)")] public bool UseOrb { get; set; }
		[NinjaScriptProperty][Range(15, 120)][Display(Name = "ORB range min ", Order = 2, GroupName = "01. Module switches (any profile)")] public int OrbRangeMin { get; set; }
		[NinjaScriptProperty][Range(0.2, 5.0)][Display(Name = "ORB target R ", Order = 3, GroupName = "01. Module switches (any profile)")] public double OrbTargetR { get; set; }
		[NinjaScriptProperty][Display(Name = "ORB pullback-day filter ", Order = 4, GroupName = "01. Module switches (any profile)")] public bool OrbPullbackFilter { get; set; }
		[NinjaScriptProperty][Display(Name = "MSEQ on ", Order = 5, GroupName = "01. Module switches (any profile)")] public bool UseMseq { get; set; }
		[NinjaScriptProperty][Display(Name = "CRT11 on ", Order = 6, GroupName = "01. Module switches (any profile)")] public bool UseCrt { get; set; }
		[NinjaScriptProperty][Display(Name = "MOM11 on ", Order = 7, GroupName = "01. Module switches (any profile)")] public bool UseMom11 { get; set; }
		[NinjaScriptProperty][Display(Name = "MOM13 on ", Order = 8, GroupName = "01. Module switches (any profile)")] public bool UseMom13 { get; set; }
		[NinjaScriptProperty][Display(Name = "MOM1030 on ", Order = 9, GroupName = "01. Module switches (any profile)")] public bool UseMom1030 { get; set; }
		[NinjaScriptProperty][Display(Name = "ON07 on ", Order = 10, GroupName = "01. Module switches (any profile)")] public bool UseOn07 { get; set; }
		[NinjaScriptProperty][Display(Name = "REV06 on ", Order = 11, GroupName = "01. Module switches (any profile)")] public bool UseRev06 { get; set; }
		[NinjaScriptProperty][Display(Name = "LON on ", Order = 12, GroupName = "01. Module switches (any profile)")] public bool UseLon { get; set; }
		[NinjaScriptProperty][Display(Name = "ICT on ", Order = 13, GroupName = "01. Module switches (any profile)")] public bool UseIct { get; set; }
		[NinjaScriptProperty][Display(Name = "MOM1130 on ", Order = 14, GroupName = "01. Module switches (any profile)")] public bool UseMom1130 { get; set; }
		[NinjaScriptProperty][Display(Name = "RSI2 on ", Order = 15, GroupName = "01. Module switches (any profile)")] public bool UseRsi2 { get; set; }
		[NinjaScriptProperty][Display(Name = "ORB90 on ", Order = 16, GroupName = "01. Module switches (any profile)")] public bool UseOrb90 { get; set; }
		[NinjaScriptProperty][Display(Name = "MSEQS on ", Order = 17, GroupName = "01. Module switches (any profile)")] public bool UseMseqShort { get; set; }
		[NinjaScriptProperty][Display(Name = "LATE15 on (15:00 trend-day continuation; Ultra / WR70Plus / Core)", Order = 18, GroupName = "01. Module switches (any profile)")] public bool UseLate15 { get; set; }
		[NinjaScriptProperty][Display(Name = "ENG10 on (06-10 4H candle breakout with the trend; Ultra)", Order = 19, GroupName = "01. Module switches (any profile)")] public bool UseEng10 { get; set; }
		[NinjaScriptProperty][Display(Name = "LATEFH on (15:00, first half hour + RTH move agree; Ultra)", Order = 20, GroupName = "01. Module switches (any profile)")] public bool UseLateFh { get; set; }
		[NinjaScriptProperty][Display(Name = "VW13 wide on Ultra (0.15 ATR, x2 at 0.30)", Order = 21, GroupName = "01. Module switches (any profile)")] public bool Vw13Wide { get; set; }
		[NinjaScriptProperty][Display(Name = "NF05 on (05:00 fade of the move since 20:00; Ultra)", Order = 22, GroupName = "01. Module switches (any profile)")] public bool UseNf05 { get; set; }
		[NinjaScriptProperty][Display(Name = "LF0315 on (03:15 fade of the London first 15 min; Ultra, off by default)", Order = 23, GroupName = "01. Module switches (any profile)")] public bool UseLf0315 { get; set; }
		[NinjaScriptProperty][Display(Name = "LF06 on (06:00 fade of the move since 04:00; Ultra)", Order = 24, GroupName = "01. Module switches (any profile)")] public bool UseLf06 { get; set; }
		[NinjaScriptProperty][Display(Name = "LF0430 on (04:30 fade with the trend of the move since 04:00; Ultra)", Order = 25, GroupName = "01. Module switches (any profile)")] public bool UseLf0430 { get; set; }
		[NinjaScriptProperty][Display(Name = "Night modules also in WR70Plus (NF05 / LF06 / LF0430)", Order = 26, GroupName = "01. Module switches (any profile)")] public bool NightOnWr70 { get; set; }
		[NinjaScriptProperty][Range(-5.0, 5.0)][Display(Name = "Pullback max prior-day move (x ATRd)", Order = 20, GroupName = "02. Edge")] public double PullbackMaxRet { get; set; }
		[NinjaScriptProperty][Range(0.05, 1.0)][Display(Name = "ORB stop cap (x ATRd)", Order = 21, GroupName = "02. Edge")] public double StopCapAtr { get; set; }
		[NinjaScriptProperty][Range(1, 50)][Display(Name = "Contracts per module", Order = 30, GroupName = "03. Risk / account")] public int Contracts { get; set; }
		[NinjaScriptProperty][Range(1000, 1659)][Display(Name = "Flatten time (ET HHmm)", Order = 31, GroupName = "03. Risk / account")] public int FlattenTime { get; set; }
		[NinjaScriptProperty][Display(Name = "Skip FOMC days", Order = 32, GroupName = "03. Risk / account")] public bool SkipFomc { get; set; }
		[NinjaScriptProperty][Display(Name = "FOMC dates (yyyy-MM-dd list)", Order = 33, GroupName = "03. Risk / account")] public string FomcDates { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Start balance $", Order = 34, GroupName = "03. Risk / account")] public double StartBalance { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Eval target $ (0 = off, realtime)", Order = 35, GroupName = "03. Risk / account")] public double EvalTarget { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Max drawdown $ (0 = off, realtime)", Order = 36, GroupName = "03. Risk / account")] public double MaxDrawdown { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Drawdown buffer $", Order = 37, GroupName = "03. Risk / account")] public double DrawdownBuffer { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Daily loss limit $ (0 = off; eval: 800, funded: 500)", Order = 46, GroupName = "03. Risk / account")] public double DailyLossLimit { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Min daily ATR (points) to trade (0 = off)", Order = 47, GroupName = "03. Risk / account")] public double MinAtrPoints { get; set; }
		[NinjaScriptProperty][Display(Name = "Eval mode (late size-up)", Order = 1, GroupName = "05. Evaluation mode")] public bool EvalMode { get; set; }
		[NinjaScriptProperty][Display(Name = "Eval start date (yyyy-MM-dd)", Order = 2, GroupName = "05. Evaluation mode")] public string EvalStartDate { get; set; }
		[NinjaScriptProperty][Range(1, 30)][Display(Name = "Late day (sessions since start, 0-based)", Order = 3, GroupName = "05. Evaluation mode")] public int EvalLateDay { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Late goal $ (size up if profit below)", Order = 4, GroupName = "05. Evaluation mode")] public double EvalLateGoal { get; set; }
		[NinjaScriptProperty][Range(1, 50)][Display(Name = "Late contracts", Order = 5, GroupName = "05. Evaluation mode")] public int EvalLateContracts { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Late size only if cushion >= $ (0 = off; 'pass easy' 1000, needs PropMode Eval)", Order = 6, GroupName = "05. Evaluation mode")] public double EvalLateMinCushion { get; set; }
		[NinjaScriptProperty][Display(Name = "Pause file", Order = 38, GroupName = "03. Risk / account")] public string PauseFile { get; set; }
		[NinjaScriptProperty][Display(Name = "Context rules (MaxPlus2/Custom): x2 ORB60/ORB90/CRT11/MSEQ in favourable context, skip ON07 after a counter day", Order = 45, GroupName = "03. Risk / account")] public bool UseContextRules { get; set; }
		[NinjaScriptProperty][Display(Name = "VOLB on ", Order = 19, GroupName = "01. Module switches (any profile)")] public bool UseVolBreak { get; set; }
		[NinjaScriptProperty][Display(Name = "VW13 on ", Order = 18, GroupName = "01. Module switches (any profile)")] public bool UseVw13 { get; set; }
		[NinjaScriptProperty][Display(Name = "Confluence rules (MaxPlus/Custom): x2 late trades vs MOM11 + with overnight, skip REV06 after same-dir LON", Order = 44, GroupName = "03. Risk / account")] public bool UseConfluence { get; set; }
		[NinjaScriptProperty][Range(1, 5)][Display(Name = "ICT size multiplier (MaxPlus/Custom; equal-risk: ICT stops are the smallest)", Order = 43, GroupName = "03. Risk / account")] public int IctMultiplier { get; set; }
		[NinjaScriptProperty][Display(Name = "Adaptive size (eval mode)", Order = 39, GroupName = "03. Risk / account")] public bool AdaptiveSize { get; set; }
		[NinjaScriptProperty][Range(1, 50)][Display(Name = "Adaptive: size normal", Order = 40, GroupName = "03. Risk / account")] public int SizeHigh { get; set; }
		[NinjaScriptProperty][Range(1, 50)][Display(Name = "Adaptive: size after drawdown", Order = 41, GroupName = "03. Risk / account")] public int SizeLow { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Adaptive: drawdown $ to size down", Order = 42, GroupName = "03. Risk / account")] public double SizeDownDrawdown { get; set; }
		[Display(Name = "Show dashboard", Order = 50, GroupName = "04. Display")] public bool ShowDashboard { get; set; }
		[Display(Name = "Print log", Order = 51, GroupName = "04. Display")] public bool PrintLog { get; set; }
		[NinjaScriptProperty][Display(Name = "Edge monitor on (CUSUM of live vs backtested edge)", Order = 1, GroupName = "06. Edge monitor")] public bool EdgeMonitor { get; set; }
		[NinjaScriptProperty][Display(Name = "Pause new entries on alarm", Order = 2, GroupName = "06. Edge monitor")] public bool EdgeMonitorPause { get; set; }
		[NinjaScriptProperty][Display(Name = "Edge monitor start date (yyyy-MM-dd)", Order = 3, GroupName = "06. Edge monitor")] public string EdgeMonitorStart { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "k (0 = profile calibration)", Order = 4, GroupName = "06. Edge monitor")] public double EdgeK { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "h (0 = profile calibration)", Order = 5, GroupName = "06. Edge monitor")] public double EdgeH { get; set; }
		[NinjaScriptProperty][Display(Name = "Prop mode (Off / Eval / Funded)", Order = 1, GroupName = "07. Prop account (cushion gating)")] public NQMasterPropMode PropMode { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Trailing drawdown $ (EOD, locks at start+100)", Order = 2, GroupName = "07. Prop account (cushion gating)")] public double PropTrailingDD { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Eval: full mode when cushion >= $", Order = 3, GroupName = "07. Prop account (cushion gating)")] public double EvalCushionFull { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Eval: account daily stop $ (0 = off)", Order = 4, GroupName = "07. Prop account (cushion gating)")] public double EvalDailyStop { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Funded: safe mode when cushion < $", Order = 5, GroupName = "07. Prop account (cushion gating)")] public double FundedCushionSafe { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Funded: request payout at profit >= $", Order = 6, GroupName = "07. Prop account (cushion gating)")] public double FundedPayoutAt { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Highest end-of-day balance so far $ (0 = auto)", Order = 7, GroupName = "07. Prop account (cushion gating)")] public double PropPeakOverride { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Liquidation threshold $ override (0 = auto)", Order = 8, GroupName = "07. Prop account (cushion gating)")] public double PropThresholdOverride { get; set; }
		[NinjaScriptProperty][Range(0, 10)][Display(Name = "Show eval-start ATR check: ATR / 60-day median < (0 = off)", Order = 9, GroupName = "07. Prop account (cushion gating)")] public double AtrStartMax { get; set; }
		[NinjaScriptProperty][Display(Name = "Funded: full profile above the safe cushion (off = no x2)", Order = 10, GroupName = "07. Prop account (cushion gating)")] public bool FundedHighFull { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Funded: no-x2 between safe cushion and this $, full above (0 = off; EQ2: 1500)", Order = 13, GroupName = "07. Prop account (cushion gating)")] public double FundedCushionFull { get; set; }
		[NinjaScriptProperty][Range(0, 100)][Display(Name = "Eval consistency % (best day <= % of profit; Lucid 50, 0 = off)", Order = 11, GroupName = "07. Prop account (cushion gating)")] public double ConsistencyPct { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Eval: best day so far $ (after a restart)", Order = 12, GroupName = "07. Prop account (cushion gating)")] public double EvalBestDaySoFar { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Eval: stop the day at +$ (whole account; 1400 with 2 contracts, 700 with 1; 0 = off)", Order = 14, GroupName = "07. Prop account (cushion gating)")] public double EvalProfitStop { get; set; }
		#endregion
	}
}
