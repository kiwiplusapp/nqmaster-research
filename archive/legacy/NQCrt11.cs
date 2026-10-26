//
// NQ CRT 11 - Candle Range Theory on the 11:00 ET hourly candle (MNQ, NinjaTrader 8, single file)
// ------------------------------------------------------------------------------------------------
// Candle 1 = the 10:00-11:00 ET hourly candle (H1/L1). Candle 2 = the 11:00-12:00 ET candle.
//   Bearish CRT: candle 2 trades ABOVE H1, does not take L1, and CLOSES back inside (L1 < close < H1) -> SHORT.
//   Bullish CRT: candle 2 trades BELOW L1, does not take H1, and CLOSES back inside -> LONG.
// Only in the direction of the daily trend (prior RTH close vs SMA20 of RTH closes) when UseTrendFilter = true.
// Entry: market at 12:00 ET (open of candle 3). Stop: 1 tick beyond the candle-2 extreme. Target: TargetR x risk
// measured from the fill. Skip if risk > MaxRiskAtr x daily ATR(14). Flat at FlattenTime.
// Research (research/crt2.py, NQ 1m 2020-01 -> 2026-09, 1 tick slippage, $1 RT): 285 trades (~0.8/week),
//   WR 48.8%, PF 1.62 (2R, flat 15:55), every year PF 1.41-2.07. CONFIRM ON REAL MNQ DATA IN THE STRATEGY ANALYZER.
// NEEDS: 1-MINUTE MNQ chart, CME US Index Futures ETH, ~25 RTH days of history before the first trade.
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
	public class NQCrt11 : Strategy
	{
		private const string Sig = "CRT";
		private const int RthOpen = 570, RthClose = 960;

		private TimeZoneInfo etZone;
		private SimpleFont dashFont;
		private bool badTimeframe;

		private int rthDay = -1, rthDaysSeen, atrCount;
		private double dayHigh, dayLow, dayClose, prevRthClose = double.NaN, atrDaily = double.NaN, atrPrevClose = double.NaN;
		private bool dayHasBars;
		private List<double> rthCloses;
		private int trendDir;
		private double todayAtr;

		private double c1H, c1L, c2H, c2L, c2C;
		private bool c1Has, c2Has, doneToday;
		private string dayStatus = "waiting";

		private double pendingStop, tradeStop, tradeTarget;
		private int tradesProcessed, totalTrades, totalWins;
		private double grossWin, grossLoss, netPnl;

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Description = "Candle Range Theory on the 11:00 ET hourly candle vs the 10:00 candle, with the daily trend. 2R target.";
				Name = "NQCrt11";
				Calculate = Calculate.OnBarClose;
				EntriesPerDirection = 1;
				EntryHandling = EntryHandling.UniqueEntries;
				IsExitOnSessionCloseStrategy = true;
				ExitOnSessionCloseSeconds = 30;
				IsFillLimitOnTouch = false;
				MaximumBarsLookBack = MaximumBarsLookBack.TwoHundredFiftySix;
				OrderFillResolution = OrderFillResolution.Standard;
				Slippage = 1;
				StartBehavior = StartBehavior.WaitUntilFlat;
				TimeInForce = TimeInForce.Gtc;
				RealtimeErrorHandling = RealtimeErrorHandling.StopCancelClose;
				StopTargetHandling = StopTargetHandling.PerEntryExecution;
				BarsRequiredToTrade = 20;
				IsInstantiatedOnEachOptimizationIteration = true;

				Candle2Hour = 11; TargetR = 2.0; MaxRiskAtr = 0.5; UseTrendFilter = true; FlattenTime = 1555;
				Contracts = 1; RiskPerTrade = 0; MaxContracts = 10; PauseFile = "pause_trading.txt";
				ShowDashboard = true; PrintLog = true;
			}
			else if (State == State.DataLoaded)
			{
				rthCloses = new List<double>();
				dashFont = new SimpleFont("Consolas", 12);
				try { etZone = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time"); } catch { etZone = null; }
				badTimeframe = !(BarsPeriod.BarsPeriodType == BarsPeriodType.Minute && BarsPeriod.Value == 1);
				if (badTimeframe) Print("NQCrt11 | Needs a 1-MINUTE MNQ chart (CME US Index Futures ETH).");
			}
			else if (State == State.Terminated)
			{
				if (rthCloses != null && totalTrades == 0 && rthDaysSeen < 25)
					Print(string.Format("NQCrt11 | 0 trades: only {0} RTH days loaded; needs ~25 days of warm-up. Start the test 2+ months earlier.", rthDaysSeen));
			}
		}

		public override string DisplayName { get { return "NQ CRT 11"; } }

		protected override void OnBarUpdate()
		{
			if (BarsInProgress != 0 || CurrentBar < 2 || badTimeframe) return;
			DateTime etClose = ToEt(Time[0]);
			DateTime etOpen = etClose.AddMinutes(-1);
			int openMin = etOpen.Hour * 60 + etOpen.Minute;
			int closeMin = etClose.Hour * 60 + etClose.Minute;
			int etDate = etOpen.Year * 10000 + etOpen.Month * 100 + etOpen.Day;

			ProcessClosedTrades();

			bool inRth = openMin >= RthOpen && openMin < RthClose;
			if (inRth && etDate != rthDay) StartRthDay(etDate);
			if (inRth && etDate == rthDay)
			{
				if (!dayHasBars) { dayHigh = High[0]; dayLow = Low[0]; dayHasBars = true; }
				else { dayHigh = Math.Max(dayHigh, High[0]); dayLow = Math.Min(dayLow, Low[0]); }
				dayClose = Close[0];
			}

			if (FlattenTime > 0 && closeMin >= Hm(FlattenTime) && closeMin < 18 * 60)
			{
				if (Position.MarketPosition == MarketPosition.Long) ExitLong();
				else if (Position.MarketPosition == MarketPosition.Short) ExitShort();
				UpdateDashboard();
				return;
			}

			if (etDate != rthDay) { UpdateDashboard(); return; }
			int h1s = (Candle2Hour - 1) * 60, h2s = Candle2Hour * 60;
			if (openMin >= h1s && openMin < h1s + 60)
			{
				if (!c1Has) { c1H = High[0]; c1L = Low[0]; c1Has = true; } else { c1H = Math.Max(c1H, High[0]); c1L = Math.Min(c1L, Low[0]); }
			}
			else if (openMin >= h2s && openMin < h2s + 60)
			{
				if (!c2Has) { c2H = High[0]; c2L = Low[0]; c2Has = true; } else { c2H = Math.Max(c2H, High[0]); c2L = Math.Min(c2L, Low[0]); }
				c2C = Close[0];
				if (openMin == h2s + 59) Evaluate();
			}
			UpdateDashboard();
		}

		private void Evaluate()
		{
			if (doneToday || !c1Has || !c2Has || Position.MarketPosition != MarketPosition.Flat) return;
			doneToday = true;
			if (double.IsNaN(todayAtr) || todayAtr <= 0 || atrCount < 14) { dayStatus = "warming up"; return; }
			if (PauseActive()) { dayStatus = "MANUAL PAUSE (file)"; return; }
			int d = 0;
			if (c2H > c1H && c2C < c1H && c2C > c1L && c2L >= c1L) d = -1;
			else if (c2L < c1L && c2C > c1L && c2C < c1H && c2H <= c1H) d = 1;
			if (d == 0) { dayStatus = "no CRT today"; return; }
			if (UseTrendFilter && d != trendDir) { dayStatus = "CRT against trend: skipped"; return; }
			double stop = d == 1 ? c2L - TickSize : c2H + TickSize;
			double estEntry = Close[0] + d * TickSize;
			double riskPts = (estEntry - stop) * d;
			if (riskPts <= 0 || riskPts > MaxRiskAtr * todayAtr) { dayStatus = "CRT risk too wide: skipped"; return; }
			int qty = Contracts;
			if (RiskPerTrade > 0) qty = Math.Max(1, (int)Math.Floor(RiskPerTrade / (riskPts * Instrument.MasterInstrument.PointValue + 1.0)));
			qty = Math.Min(qty, MaxContracts);
			pendingStop = stop;
			SetStopLoss(Sig, CalculationMode.Price, stop, false);
			SetProfitTarget(Sig, CalculationMode.Ticks, 4000);	// placeholder, replaced on fill
			if (d == 1) EnterLong(qty, Sig); else EnterShort(qty, Sig);
			dayStatus = string.Format("CRT {0} x{1} | SL {2}", d == 1 ? "LONG" : "SHORT", qty, Fmt(stop));
			Log(string.Format("CRT {0} x{1} | C1 {2}-{3} | C2 {4}-{5} close {6} | SL {7} | risk {8:0.00} pts", d == 1 ? "BUY" : "SELL", qty,
				Fmt(c1L), Fmt(c1H), Fmt(c2L), Fmt(c2H), Fmt(c2C), Fmt(stop), riskPts));
		}

		private void StartRthDay(int etDate)
		{
			if (dayHasBars)
			{
				double tr = double.IsNaN(atrPrevClose) ? dayHigh - dayLow : Math.Max(dayHigh - dayLow, Math.Max(Math.Abs(dayHigh - atrPrevClose), Math.Abs(dayLow - atrPrevClose)));
				atrCount++;
				int k = Math.Min(atrCount, 14);
				atrDaily = double.IsNaN(atrDaily) ? tr : ((k - 1) * atrDaily + tr) / k;
				atrPrevClose = dayClose; prevRthClose = dayClose;
				rthCloses.Add(dayClose);
				while (rthCloses.Count > 20) rthCloses.RemoveAt(0);
			}
			rthDaysSeen++;
			rthDay = etDate; dayHasBars = false; todayAtr = atrDaily;
			c1Has = false; c2Has = false; doneToday = false;
			trendDir = 0;
			if (rthCloses.Count >= 20 && !double.IsNaN(prevRthClose))
			{
				double s = 0; foreach (double x in rthCloses) s += x;
				double sma = s / rthCloses.Count;
				trendDir = prevRthClose > sma ? 1 : (prevRthClose < sma ? -1 : 0);
			}
			dayStatus = trendDir == 0 ? "no trend / warming up" : (trendDir == 1 ? "trend UP: waiting 12:00" : "trend DOWN: waiting 12:00");
		}

		protected override void OnExecutionUpdate(Execution execution, string executionId, double price, int quantity,
			MarketPosition marketPosition, string orderId, DateTime time)
		{
			if (execution.Order == null || execution.Order.Name != Sig || execution.Order.OrderState != OrderState.Filled) return;
			double fill = execution.Order.AverageFillPrice;
			int d = execution.Order.IsLong ? 1 : -1;
			tradeStop = pendingStop;
			double risk = (fill - tradeStop) * d;
			if (risk <= 0) { Log("filled beyond the stop -> exit"); if (d == 1) ExitLong(); else ExitShort(); return; }
			tradeTarget = Instrument.MasterInstrument.RoundToTickSize(fill + d * TargetR * risk);
			SetProfitTarget(Sig, CalculationMode.Price, tradeTarget);
			Log(string.Format("FILLED @ {0} | SL {1} | TP {2} ({3:0.#}R)", Fmt(fill), Fmt(tradeStop), Fmt(tradeTarget), TargetR));
		}

		private void ProcessClosedTrades()
		{
			int count = SystemPerformance.AllTrades.Count;
			for (int i = tradesProcessed; i < count; i++)
			{
				double pnl = SystemPerformance.AllTrades[i].ProfitCurrency;
				totalTrades++; netPnl += pnl;
				if (pnl > 0) { totalWins++; grossWin += pnl; } else grossLoss -= pnl;
				Log(string.Format("CLOSED ${0:0.00} | net ${1:0.00}", pnl, netPnl));
			}
			tradesProcessed = count;
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
		private void Log(string m) { if (PrintLog) Print(string.Format("{0} | CRT11 | {1}", Time[0].ToString("yyyy-MM-dd HH:mm", CultureInfo.InvariantCulture), m)); }
		private void UpdateDashboard()
		{
			if (!ShowDashboard || (State == State.Historical && CurrentBar < Count - 2)) return;
			double pf = grossLoss > 0 ? grossWin / grossLoss : 0;
			StringBuilder sb = new StringBuilder();
			sb.AppendLine("NQ CRT 11 (10:00 vs 11:00 ET candle)");
			sb.AppendLine(dayStatus);
			if (Position.MarketPosition != MarketPosition.Flat) sb.AppendLine(string.Format("{0} {1} | SL {2} | TP {3}", Position.MarketPosition, Position.Quantity, Fmt(tradeStop), Fmt(tradeTarget)));
			sb.AppendLine(string.Format("Total {0} tr | WR {1:0.0}% | PF {2:0.00} | ${3:0.00}", totalTrades, totalTrades > 0 ? 100.0 * totalWins / totalTrades : 0, pf, netPnl));
			Draw.TextFixed(this, "CRT11_Dash", sb.ToString(), TextPosition.TopRight, Brushes.White, dashFont, Brushes.Transparent, Brushes.Black, 75);
		}

		#region Properties
		[NinjaScriptProperty][Range(1, 15)][Display(Name = "Candle 2 hour (ET)", Order = 1, GroupName = "01. CRT")] public int Candle2Hour { get; set; }
		[NinjaScriptProperty][Range(0.5, 10.0)][Display(Name = "Target (R)", Order = 2, GroupName = "01. CRT")] public double TargetR { get; set; }
		[NinjaScriptProperty][Range(0.05, 5.0)][Display(Name = "Max risk (x daily ATR)", Order = 3, GroupName = "01. CRT")] public double MaxRiskAtr { get; set; }
		[NinjaScriptProperty][Display(Name = "Only with daily trend", Order = 4, GroupName = "01. CRT")] public bool UseTrendFilter { get; set; }
		[NinjaScriptProperty][Range(1200, 1659)][Display(Name = "Flatten time (ET HHmm)", Order = 5, GroupName = "01. CRT")] public int FlattenTime { get; set; }
		[NinjaScriptProperty][Range(1, 50)][Display(Name = "Contracts (fixed)", Order = 10, GroupName = "02. Risk")] public int Contracts { get; set; }
		[NinjaScriptProperty][Range(0.0, double.MaxValue)][Display(Name = "Risk per trade $ (0 = fixed contracts)", Order = 11, GroupName = "02. Risk")] public double RiskPerTrade { get; set; }
		[NinjaScriptProperty][Range(1, 100)][Display(Name = "Max contracts", Order = 12, GroupName = "02. Risk")] public int MaxContracts { get; set; }
		[NinjaScriptProperty][Display(Name = "Pause file (create it to pause)", Order = 13, GroupName = "02. Risk")] public string PauseFile { get; set; }
		[Display(Name = "Show dashboard", Order = 20, GroupName = "03. Display")] public bool ShowDashboard { get; set; }
		[Display(Name = "Print log", Order = 21, GroupName = "03. Display")] public bool PrintLog { get; set; }
		#endregion
	}
}
