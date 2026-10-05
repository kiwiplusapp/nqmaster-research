//
// NQ Time Momentum - one configurable clock-time module (MNQ, NinjaTrader 8, single file). Run one instance per module.
// ------------------------------------------------------------------------------------------------
// At EntryTime (ET, bar close) compare the price with a reference:
//   Lookback > 0  : the close Lookback minutes earlier
//   Lookback = -1 : the Globex session open (18:00 ET)
//   Lookback = -2 : the RTH open (09:30 ET)
// Direction = price above the reference -> BUY, below -> SELL (Reverse = true flips it).
// Filters: TrendFilter = only in the direction of the daily trend (prior RTH close vs SMA20 of RTH closes);
//          VwapAgree   = only if price vs RTH VWAP agrees with the direction (RTH entries only).
// Exit: stop StopAtr x daily ATR(14), target TargetR x stop, time exit after MaxHoldMin minutes, flat at FlattenTime.
// Presets from research/tmom.py + mom11_feat.py (real MNQ 2024-26 Sharpe in brackets):
//   MOM11   : 1100, -2, no rev, 0.25, 0.3R, hold 0 (none), trend off, VWAP on   [2.00]
//   MOM13   : 1300, -2, no rev, 0.20, 1.0R, hold 240, trend on                  [0.59]
//   MOM1030 : 1030, -2, no rev, 0.20, 0.3R, hold 60,  trend on                  [0.59]
//   ON07    : 0700, 30, no rev, 0.20, 1.0R, hold 60,  trend on                  [0.95]
//   REV06   : 0600, 30, REVERSE, 0.20, 0.3R, hold 240, trend on                 [0.79]
// NEEDS: 1-MINUTE MNQ chart, CME US Index Futures ETH, ~25 RTH days of warm-up.
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
	public class NQTimeMom : Strategy
	{
		private const int RthOpen = 570, RthClose = 960;

		private TimeZoneInfo etZone;
		private SimpleFont dashFont;
		private bool badTimeframe;

		// completed RTH day statistics
		private int rthDay = -1, rthDaysSeen, atrCount;
		private double dayHigh, dayLow, dayClose, atrDaily = double.NaN, atrPrevClose = double.NaN;
		private bool dayHasBars;
		private List<double> rthCloses;
		private int trendDir;

		// session state
		private double sessionOpenPx = double.NaN, rthOpenPx = double.NaN, vwPv, vwV;
		private bool doneThisSession;
		private int entryBar = -1;
		private string status = "waiting";
		private string sig;

		private int tradesProcessed, totalTrades, totalWins;
		private double grossWin, grossLoss, netPnl;

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Description = "Clock-time momentum/reversal module for MNQ. Configure one instance per preset (MOM11, MOM13, MOM1030, ON07, REV06).";
				Name = "NQTimeMom";
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
				RealtimeErrorHandling = RealtimeErrorHandling.StopCancelClose;
				StopTargetHandling = StopTargetHandling.PerEntryExecution;
				BarsRequiredToTrade = 20;
				IsInstantiatedOnEachOptimizationIteration = true;

				ModuleName = "MOM11"; EntryTime = 1100; Lookback = -2; Reverse = false; StopAtr = 0.25; TargetR = 0.3; MaxHoldMin = 0;
				TrendFilter = false; VwapAgree = true; FlattenTime = 1555;
				Contracts = 1; PauseFile = "pause_trading.txt"; ShowDashboard = true; PrintLog = true;
			}
			else if (State == State.DataLoaded)
			{
				rthCloses = new List<double>();
				dashFont = new SimpleFont("Consolas", 11);
				try { etZone = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time"); } catch { etZone = null; }
				badTimeframe = !(BarsPeriod.BarsPeriodType == BarsPeriodType.Minute && BarsPeriod.Value == 1);
				if (badTimeframe) Print("NQTimeMom | Needs a 1-MINUTE MNQ chart (CME US Index Futures ETH).");
				sig = string.IsNullOrWhiteSpace(ModuleName) ? "TMOM" : ModuleName.Trim();
			}
			else if (State == State.Terminated)
			{
				if (rthCloses != null && totalTrades == 0 && rthDaysSeen < 25)
					Print(string.Format("NQTimeMom {0} | 0 trades: only {1} RTH days loaded; needs ~25 days of warm-up.", sig, rthDaysSeen));
			}
		}

		public override string DisplayName { get { return "NQ TimeMom " + (string.IsNullOrWhiteSpace(ModuleName) ? "" : ModuleName); } }

		protected override void OnBarUpdate()
		{
			if (BarsInProgress != 0 || CurrentBar < 2 || badTimeframe) return;
			DateTime etClose = ToEt(Time[0]);
			DateTime etOpen = etClose.AddMinutes(-1);
			int openMin = etOpen.Hour * 60 + etOpen.Minute;
			int closeMin = etClose.Hour * 60 + etClose.Minute;
			int etDate = etOpen.Year * 10000 + etOpen.Month * 100 + etOpen.Day;

			ProcessClosedTrades();

			if (Bars.IsFirstBarOfSession)
			{
				FinalizeRthDay();
				sessionOpenPx = Open[0]; rthOpenPx = double.NaN; vwPv = 0; vwV = 0; doneThisSession = false;
			}

			bool inRth = openMin >= RthOpen && openMin < RthClose;
			if (inRth)
			{
				if (etDate != rthDay) { FinalizeRthDay(); rthDay = etDate; dayHasBars = false; }
				if (!dayHasBars) { dayHigh = High[0]; dayLow = Low[0]; dayHasBars = true; rthOpenPx = Open[0]; }
				else { dayHigh = Math.Max(dayHigh, High[0]); dayLow = Math.Min(dayLow, Low[0]); }
				dayClose = Close[0];
				double vol = Volume[0] > 0 ? Volume[0] : 1.0;
				vwPv += (High[0] + Low[0] + Close[0]) / 3.0 * vol; vwV += vol;
			}

			// exits: time stop and flatten
			if (Position.MarketPosition != MarketPosition.Flat)
			{
				bool flat = FlattenTime > 0 && closeMin >= Hm(FlattenTime) && closeMin < 18 * 60;
				bool timeUp = MaxHoldMin > 0 && entryBar >= 0 && CurrentBar - entryBar >= MaxHoldMin;
				if (flat || timeUp)
				{
					if (Position.MarketPosition == MarketPosition.Long) ExitLong(); else ExitShort();
					Log(flat ? "flatten" : "time exit");
				}
			}

			if (!doneThisSession && closeMin == Hm(EntryTime))
			{
				doneThisSession = true;
				TryEnter(openMin);
			}
			UpdateDashboard();
		}

		private void TryEnter(int openMin)
		{
			if (atrCount < 14 || double.IsNaN(atrDaily) || atrDaily <= 0) { status = "warming up"; return; }
			if (PauseActive()) { status = "MANUAL PAUSE (file)"; return; }
			if (Position.MarketPosition != MarketPosition.Flat) { status = "already in position"; return; }
			double reference = double.NaN;
			if (Lookback == -1) reference = sessionOpenPx;
			else if (Lookback == -2) reference = rthOpenPx;
			if (Lookback > 0 && CurrentBar > Lookback) reference = Close[Lookback - 1];
			if (double.IsNaN(reference) || Close[0] == reference) { status = "no reference / flat"; return; }
			int d = Close[0] > reference ? 1 : -1;
			if (Reverse) d = -d;
			if (TrendFilter && d != trendDir) { status = "against trend: skip"; return; }
			if (VwapAgree)
			{
				if (vwV <= 0) { status = "no VWAP yet"; return; }
				double vw = vwPv / vwV;
				int vd = Close[0] > vw ? 1 : (Close[0] < vw ? -1 : 0);
				int md = Close[0] > reference ? 1 : -1;
				if (vd != md) { status = "VWAP disagrees: skip"; return; }
			}
			int st = Math.Max(4, (int)Math.Round(StopAtr * atrDaily / TickSize));
			int tp = Math.Max(1, (int)Math.Round(TargetR * st));
			SetStopLoss(sig, CalculationMode.Ticks, st, false);
			SetProfitTarget(sig, CalculationMode.Ticks, tp);
			if (d == 1) EnterLong(Contracts, sig); else EnterShort(Contracts, sig);
			entryBar = CurrentBar + 1;
			status = string.Format("{0} x{1} | SL {2}t TP {3}t", d == 1 ? "LONG" : "SHORT", Contracts, st, tp);
			Log(string.Format("{0} {1} | ref {2} | SL {3}t TP {4}t", sig, d == 1 ? "BUY" : "SELL", Fmt(reference), st, tp));
		}

		private void FinalizeRthDay()
		{
			if (!dayHasBars) return;
			double tr = double.IsNaN(atrPrevClose) ? dayHigh - dayLow : Math.Max(dayHigh - dayLow, Math.Max(Math.Abs(dayHigh - atrPrevClose), Math.Abs(dayLow - atrPrevClose)));
			atrCount++;
			int k = Math.Min(atrCount, 14);
			atrDaily = double.IsNaN(atrDaily) ? tr : ((k - 1) * atrDaily + tr) / k;
			atrPrevClose = dayClose;
			rthCloses.Add(dayClose);
			while (rthCloses.Count > 20) rthCloses.RemoveAt(0);
			trendDir = 0;
			if (rthCloses.Count >= 20)
			{
				double s = 0; foreach (double x in rthCloses) s += x;
				trendDir = dayClose > s / rthCloses.Count ? 1 : (dayClose < s / rthCloses.Count ? -1 : 0);
			}
			rthDaysSeen++;
			dayHasBars = false;
		}

		private void ProcessClosedTrades()
		{
			int count = SystemPerformance.AllTrades.Count;
			for (int i = tradesProcessed; i < count; i++)
			{
				double pnl = SystemPerformance.AllTrades[i].ProfitCurrency;
				totalTrades++; netPnl += pnl;
				if (pnl > 0) { totalWins++; grossWin += pnl; } else grossLoss -= pnl;
			}
			tradesProcessed = count;
			if (Position.MarketPosition == MarketPosition.Flat) entryBar = -1;
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
		private void Log(string m) { if (PrintLog) Print(string.Format("{0} | {1} | {2}", Time[0].ToString("yyyy-MM-dd HH:mm", CultureInfo.InvariantCulture), sig, m)); }
		private void UpdateDashboard()
		{
			if (!ShowDashboard || (State == State.Historical && CurrentBar < Count - 2)) return;
			double pf = grossLoss > 0 ? grossWin / grossLoss : 0;
			string txt = string.Format("{0}: {1}\nTotal {2} tr | WR {3:0.0}% | PF {4:0.00} | ${5:0.00}", sig, status, totalTrades,
				totalTrades > 0 ? 100.0 * totalWins / totalTrades : 0, pf, netPnl);
			Draw.TextFixed(this, "TMOM_" + sig, txt, TextPosition.BottomLeft, Brushes.White, dashFont, Brushes.Transparent, Brushes.Black, 75);
		}

		#region Properties
		[NinjaScriptProperty][Display(Name = "Module name (signal)", Order = 0, GroupName = "01. Module")] public string ModuleName { get; set; }
		[NinjaScriptProperty][Range(0, 2359)][Display(Name = "Entry time (ET HHmm, bar close)", Order = 1, GroupName = "01. Module")] public int EntryTime { get; set; }
		[NinjaScriptProperty][Range(-2, 600)][Display(Name = "Lookback (min; -1 session open, -2 RTH open)", Order = 2, GroupName = "01. Module")] public int Lookback { get; set; }
		[NinjaScriptProperty][Display(Name = "Reverse (fade)", Order = 3, GroupName = "01. Module")] public bool Reverse { get; set; }
		[NinjaScriptProperty][Range(0.02, 2.0)][Display(Name = "Stop (x daily ATR)", Order = 4, GroupName = "01. Module")] public double StopAtr { get; set; }
		[NinjaScriptProperty][Range(0.1, 5.0)][Display(Name = "Target (R)", Order = 5, GroupName = "01. Module")] public double TargetR { get; set; }
		[NinjaScriptProperty][Range(0, 2000)][Display(Name = "Max hold (min, 0 = until flatten)", Order = 6, GroupName = "01. Module")] public int MaxHoldMin { get; set; }
		[NinjaScriptProperty][Display(Name = "Only with daily trend", Order = 7, GroupName = "01. Module")] public bool TrendFilter { get; set; }
		[NinjaScriptProperty][Display(Name = "Require VWAP agreement (RTH)", Order = 8, GroupName = "01. Module")] public bool VwapAgree { get; set; }
		[NinjaScriptProperty][Range(0, 1659)][Display(Name = "Flatten time (ET HHmm)", Order = 9, GroupName = "01. Module")] public int FlattenTime { get; set; }
		[NinjaScriptProperty][Range(1, 50)][Display(Name = "Contracts", Order = 10, GroupName = "02. Risk")] public int Contracts { get; set; }
		[NinjaScriptProperty][Display(Name = "Pause file (create it to pause)", Order = 11, GroupName = "02. Risk")] public string PauseFile { get; set; }
		[Display(Name = "Show dashboard", Order = 20, GroupName = "03. Display")] public bool ShowDashboard { get; set; }
		[Display(Name = "Print log", Order = 21, GroupName = "03. Display")] public bool PrintLog { get; set; }
		#endregion
	}
}
