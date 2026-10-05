//
// NQ London FVG - London-session breakout + return to a fair value gap (MNQ, NinjaTrader 8, single file)
// ------------------------------------------------------------------------------------------------
// Range = 00:00-03:00 ET. From 03:00 to BreakDeadline (06:00) the first 1-min CLOSE beyond the range sets the direction,
// only if it matches the daily trend (prior RTH close vs SMA20 of RTH closes).
// Then the first fair value gap in that direction (3-bar gap) formed after the break arms a LIMIT at its proximal edge
// (valid until EntryDeadline 08:00). Stop = opposite side of the range. Target = TargetR x risk from the fill.
// Skip if risk > MaxRiskAtr x daily ATR(14). Everything flat at ExitTime (09:30 ET).
// Research (research/london.py): PF 1.19 / 1.37 / 1.39, WR ~40% at 2R on CFD 2020-23 / CFD 2024-26 / REAL MNQ 2024-26.
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
	public class NQLondonFvg : Strategy
	{
		private const string Sig = "LON";
		private const int RthOpen = 570, RthClose = 960;

		private TimeZoneInfo etZone;
		private SimpleFont dashFont;
		private bool badTimeframe;

		private int rthDay = -1, rthDaysSeen, atrCount, trendDir;
		private double dayHigh, dayLow, dayClose, atrDaily = double.NaN, atrPrevClose = double.NaN;
		private bool dayHasBars;
		private List<double> rthCloses;

		// session state: 0 building range, 1 waiting break, 2 waiting FVG, 3 limit working / in trade, 4 done
		private int stage;
		private double rH, rL, limPx, stopPx, tgtPx;
		private bool rHas;
		private int dir;
		private Order entryOrder;
		private string status = "waiting";

		private int tradesProcessed, totalTrades, totalWins;
		private double grossWin, grossLoss, netPnl;

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Description = "London breakout (00:00-03:00 ET range) + limit at the first FVG after the break, with the daily trend. Flat at 09:30 ET.";
				Name = "NQLondonFvg";
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

				RangeStart = 0; RangeEnd = 300; BreakDeadline = 600; EntryDeadline = 800; ExitTime = 930;
				TargetR = 2.0; MaxRiskAtr = 0.25; UseTrendFilter = true;
				Contracts = 1; PauseFile = "pause_trading.txt"; ShowDashboard = true; PrintLog = true;
			}
			else if (State == State.DataLoaded)
			{
				rthCloses = new List<double>();
				dashFont = new SimpleFont("Consolas", 11);
				try { etZone = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time"); } catch { etZone = null; }
				badTimeframe = !(BarsPeriod.BarsPeriodType == BarsPeriodType.Minute && BarsPeriod.Value == 1);
				if (badTimeframe) Print("NQLondonFvg | Needs a 1-MINUTE MNQ chart (CME US Index Futures ETH).");
			}
			else if (State == State.Realtime)
			{
				if (entryOrder != null) entryOrder = GetRealtimeOrder(entryOrder);
			}
		}

		public override string DisplayName { get { return "NQ London FVG"; } }

		protected override void OnBarUpdate()
		{
			if (BarsInProgress != 0 || CurrentBar < 3 || badTimeframe) return;
			DateTime etClose = ToEt(Time[0]);
			DateTime etOpen = etClose.AddMinutes(-1);
			int openMin = etOpen.Hour * 60 + etOpen.Minute;
			int closeMin = etClose.Hour * 60 + etClose.Minute;
			int etDate = etOpen.Year * 10000 + etOpen.Month * 100 + etOpen.Day;

			ProcessClosedTrades();

			if (Bars.IsFirstBarOfSession)
			{
				FinalizeRthDay();
				stage = 0; rHas = false; dir = 0; status = "building range";
				if (Working(entryOrder)) CancelOrder(entryOrder);
			}
			bool inRth = openMin >= RthOpen && openMin < RthClose;
			if (inRth)
			{
				if (etDate != rthDay) { FinalizeRthDay(); rthDay = etDate; dayHasBars = false; }
				if (!dayHasBars) { dayHigh = High[0]; dayLow = Low[0]; dayHasBars = true; }
				else { dayHigh = Math.Max(dayHigh, High[0]); dayLow = Math.Min(dayLow, Low[0]); }
				dayClose = Close[0];
			}

			int rs = Hm(RangeStart), re = Hm(RangeEnd), bd = Hm(BreakDeadline), ed = Hm(EntryDeadline), xt = Hm(ExitTime);
			bool overnight = openMin < RthOpen;		// 00:00-09:29 part of the session

			// exit at ExitTime
			if (overnight == false || openMin >= xt)
			{
				if (Position.MarketPosition != MarketPosition.Flat && openMin >= xt && openMin < 18 * 60)
				{
					if (Position.MarketPosition == MarketPosition.Long) ExitLong(); else ExitShort();
					Log("exit at deadline");
				}
				if (Working(entryOrder)) CancelOrder(entryOrder);
				if (stage < 4 && openMin >= xt && openMin < 18 * 60) stage = 4;
			}

			if (overnight && stage == 0 && openMin >= rs && openMin < re)
			{
				if (!rHas) { rH = High[0]; rL = Low[0]; rHas = true; } else { rH = Math.Max(rH, High[0]); rL = Math.Min(rL, Low[0]); }
			}
			if (overnight && stage == 0 && openMin >= re && rHas)
			{
				stage = 1; status = string.Format("range {0}-{1}", Fmt(rL), Fmt(rH));
			}
			if (stage == 1)
			{
				if (openMin >= bd || !overnight) { stage = 4; status = "no break"; }
				else if (Close[0] > rH || Close[0] < rL)
				{
					int d = Close[0] > rH ? 1 : -1;
					if (atrCount < 14 || double.IsNaN(atrDaily) || atrDaily <= 0) { stage = 4; status = "warming up"; }
					else if (UseTrendFilter && d != trendDir) { stage = 4; status = "break against trend"; }
					else { dir = d; stage = 2; status = d == 1 ? "break UP: waiting FVG" : "break DOWN: waiting FVG"; CheckFvg(); return; }
				}
			}
			else if (stage == 2)
			{
				if (openMin >= ed || !overnight) { stage = 4; status = "no FVG entry"; }
				else CheckFvg();
			}
			else if (stage == 3)
			{
				if (Working(entryOrder) && (openMin >= ed || !overnight)) { CancelOrder(entryOrder); stage = 4; status = "limit expired"; }
			}
			UpdateDashboard();
		}

		private void CheckFvg()
		{
			bool gap = dir == 1 ? Low[0] > High[2] : High[0] < Low[2];
			if (!gap) return;
			if (PauseActive()) { stage = 4; status = "MANUAL PAUSE (file)"; return; }
			limPx = dir == 1 ? Low[0] : High[0];
			stopPx = dir == 1 ? rL : rH;
			double risk = (limPx - stopPx) * dir;
			if (risk <= 0 || risk > MaxRiskAtr * atrDaily) { stage = 4; status = "risk too wide: skip"; return; }
			SetStopLoss(Sig, CalculationMode.Price, stopPx, false);
			SetProfitTarget(Sig, CalculationMode.Ticks, 4000);	// placeholder, replaced on fill
			if (dir == 1) EnterLongLimit(0, true, Contracts, limPx, Sig); else EnterShortLimit(0, true, Contracts, limPx, Sig);
			stage = 3;
			status = string.Format("{0} LIMIT @ {1} | SL {2}", dir == 1 ? "BUY" : "SELL", Fmt(limPx), Fmt(stopPx));
			Log(status);
		}

		protected override void OnOrderUpdate(Order order, double limitPrice, double stopPrice, int quantity, int filled, double averageFillPrice,
			OrderState orderState, DateTime time, ErrorCode error, string nativeError)
		{
			if (order.Name == Sig) entryOrder = order;
		}

		protected override void OnExecutionUpdate(Execution execution, string executionId, double price, int quantity,
			MarketPosition marketPosition, string orderId, DateTime time)
		{
			if (execution.Order == null || execution.Order.Name != Sig || execution.Order.OrderState != OrderState.Filled) return;
			double fill = execution.Order.AverageFillPrice;
			double risk = (fill - stopPx) * dir;
			if (risk <= 0) { if (dir == 1) ExitLong(); else ExitShort(); return; }
			tgtPx = Instrument.MasterInstrument.RoundToTickSize(fill + dir * TargetR * risk);
			SetProfitTarget(Sig, CalculationMode.Price, tgtPx);
			status = string.Format("IN {0} @ {1} | SL {2} | TP {3}", dir == 1 ? "LONG" : "SHORT", Fmt(fill), Fmt(stopPx), Fmt(tgtPx));
			Log(status);
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
			rthDaysSeen++; dayHasBars = false;
		}

		private static bool Working(Order o)
		{
			if (o == null) return false;
			OrderState s = o.OrderState;
			return s != OrderState.Filled && s != OrderState.Cancelled && s != OrderState.Rejected && s != OrderState.Unknown;
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
		private void Log(string m) { if (PrintLog) Print(string.Format("{0} | LON | {1}", Time[0].ToString("yyyy-MM-dd HH:mm", CultureInfo.InvariantCulture), m)); }
		private void UpdateDashboard()
		{
			if (!ShowDashboard || (State == State.Historical && CurrentBar < Count - 2)) return;
			double pf = grossLoss > 0 ? grossWin / grossLoss : 0;
			Draw.TextFixed(this, "LON_Dash", string.Format("LONDON FVG: {0}\nTotal {1} tr | WR {2:0.0}% | PF {3:0.00} | ${4:0.00}", status, totalTrades,
				totalTrades > 0 ? 100.0 * totalWins / totalTrades : 0, pf, netPnl), TextPosition.TopLeft, Brushes.White, dashFont, Brushes.Transparent, Brushes.Black, 75);
		}

		#region Properties
		[NinjaScriptProperty][Range(0, 2359)][Display(Name = "Range start (ET HHmm)", Order = 1, GroupName = "01. London")] public int RangeStart { get; set; }
		[NinjaScriptProperty][Range(0, 2359)][Display(Name = "Range end / break start (ET HHmm)", Order = 2, GroupName = "01. London")] public int RangeEnd { get; set; }
		[NinjaScriptProperty][Range(0, 2359)][Display(Name = "Break deadline (ET HHmm)", Order = 3, GroupName = "01. London")] public int BreakDeadline { get; set; }
		[NinjaScriptProperty][Range(0, 2359)][Display(Name = "Entry deadline (ET HHmm)", Order = 4, GroupName = "01. London")] public int EntryDeadline { get; set; }
		[NinjaScriptProperty][Range(0, 2359)][Display(Name = "Exit time (ET HHmm)", Order = 5, GroupName = "01. London")] public int ExitTime { get; set; }
		[NinjaScriptProperty][Range(0.5, 10.0)][Display(Name = "Target (R)", Order = 6, GroupName = "01. London")] public double TargetR { get; set; }
		[NinjaScriptProperty][Range(0.05, 2.0)][Display(Name = "Max risk (x daily ATR)", Order = 7, GroupName = "01. London")] public double MaxRiskAtr { get; set; }
		[NinjaScriptProperty][Display(Name = "Only with daily trend", Order = 8, GroupName = "01. London")] public bool UseTrendFilter { get; set; }
		[NinjaScriptProperty][Range(1, 50)][Display(Name = "Contracts", Order = 10, GroupName = "02. Risk")] public int Contracts { get; set; }
		[NinjaScriptProperty][Display(Name = "Pause file (create it to pause)", Order = 11, GroupName = "02. Risk")] public string PauseFile { get; set; }
		[Display(Name = "Show dashboard", Order = 20, GroupName = "03. Display")] public bool ShowDashboard { get; set; }
		[Display(Name = "Print log", Order = 21, GroupName = "03. Display")] public bool PrintLog { get; set; }
		#endregion
	}
}
