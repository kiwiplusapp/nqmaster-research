//
// NQ ICT Open - liquidity sweep + CISD at the New York open, with the daily trend (MNQ, NinjaTrader 8, single file)
// ------------------------------------------------------------------------------------------------
// RUN ON A 5-MINUTE MNQ CHART (CME US Index Futures ETH).
// Levels (untaken at 09:30): prior RTH high/low, overnight high/low (18:00-09:29), London high/low (02:00-04:59).
// 09:30-10:30 ET (bar open): when a 5-min bar trades beyond an untaken level (sweep) the extreme is tracked.
// CISD = open of the first candle of the run that made the extreme. A close back through the CISD within K bars confirms.
// Only in the direction of the daily trend (prior RTH close vs SMA20). Entry: LIMIT at the CISD level (retest),
// valid ExpiryBars bars, cancelled if the sweep extreme is exceeded. Stop 1 tick beyond the extreme, target TargetR.
// Skip if risk > MaxRiskAtr x daily ATR. Max 3 trades/day. Flat at 15:55 ET.
// Research (research/ict.py): PF 1.47 / 1.53 / 1.49-1.63, WR 59-64% (CFD 2020-23 / CFD 2024-26 / REAL MNQ 2024-26).
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
	public class NQIctOpen : Strategy
	{
		private const string Sig = "ICT";
		private const int RthOpen = 570, RthClose = 960;

		private TimeZoneInfo etZone;
		private SimpleFont dashFont;
		private bool badTimeframe;

		// completed RTH days
		private int rthDay = -1, rthDaysSeen, atrCount, trendDir;
		private double dayHigh, dayLow, dayClose, atrDaily = double.NaN, atrPrevClose = double.NaN, prevRthHigh = double.NaN, prevRthLow = double.NaN;
		private bool dayHasBars;
		private List<double> rthCloses;

		// session levels
		private double onH, onL, lonH, lonL, postH, postL;
		private bool onHas, lonHas, postHas;
		private double[] lvl = new double[6];
		private bool[] taken = new bool[6];
		private bool levelsReady;

		// sweep state per side: 0 bear (from highs), 1 bull (from lows)
		private bool[] act = new bool[2];
		private double[] ext = new double[2];
		private int[] extBar = new int[2];
		private int tradesToday;
		private Order entryOrder;
		private int pendDir, pendExpiry;
		private double pendStop, pendExt, tgtPx;
		private string status = "waiting";

		private int tradesProcessed, totalTrades, totalWins;
		private double grossWin, grossLoss, netPnl;

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Description = "ICT-style NY open model: sweep of PDH/PDL/overnight/London level + CISD, limit at the CISD retest, with the daily trend. 5-minute chart.";
				Name = "NQIctOpen";
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

				WindowStart = 930; WindowEnd = 1030; SweepBars = 4; ExpiryBars = 20; TargetR = 1.0; MaxRiskAtr = 0.25; MaxTradesPerDay = 3;
				UseTrendFilter = true; FlattenTime = 1555; Contracts = 1; PauseFile = "pause_trading.txt"; ShowDashboard = true; PrintLog = true;
			}
			else if (State == State.DataLoaded)
			{
				rthCloses = new List<double>();
				dashFont = new SimpleFont("Consolas", 11);
				try { etZone = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time"); } catch { etZone = null; }
				badTimeframe = !(BarsPeriod.BarsPeriodType == BarsPeriodType.Minute && BarsPeriod.Value == 5);
				if (badTimeframe) Print("NQIctOpen | Needs a 5-MINUTE MNQ chart (CME US Index Futures ETH).");
			}
			else if (State == State.Realtime)
			{
				if (entryOrder != null) entryOrder = GetRealtimeOrder(entryOrder);
			}
		}

		public override string DisplayName { get { return "NQ ICT Open"; } }

		protected override void OnBarUpdate()
		{
			if (BarsInProgress != 0 || CurrentBar < 5 || badTimeframe) return;
			DateTime etClose = ToEt(Time[0]);
			DateTime etOpen = etClose.AddMinutes(-5);
			int openMin = etOpen.Hour * 60 + etOpen.Minute;
			int etDate = etOpen.Year * 10000 + etOpen.Month * 100 + etOpen.Day;

			ProcessClosedTrades();

			if (Bars.IsFirstBarOfSession)
			{
				FinalizeRthDay();
				onHas = false; lonHas = false; postHas = false; levelsReady = false; act[0] = act[1] = false; tradesToday = 0; pendDir = 0;
				if (Working(entryOrder)) CancelOrder(entryOrder);
				status = "collecting levels";
			}
			bool inRth = openMin >= RthOpen && openMin < RthClose;
			bool overnight = !inRth && !(openMin >= RthClose && openMin < 18 * 60);

			// overnight and London ranges (before the RTH open)
			if (overnight && openMin != RthOpen)
			{
				if (!onHas) { onH = High[0]; onL = Low[0]; onHas = true; } else { onH = Math.Max(onH, High[0]); onL = Math.Min(onL, Low[0]); }
				if (openMin >= 120 && openMin < 300)
				{
					if (!lonHas) { lonH = High[0]; lonL = Low[0]; lonHas = true; } else { lonH = Math.Max(lonH, High[0]); lonL = Math.Min(lonL, Low[0]); }
				}
				else if (openMin >= 300 && openMin < RthOpen)
				{
					if (!postHas) { postH = High[0]; postL = Low[0]; postHas = true; } else { postH = Math.Max(postH, High[0]); postL = Math.Min(postL, Low[0]); }
				}
			}
			if (inRth)
			{
				if (etDate != rthDay) { FinalizeRthDay(); rthDay = etDate; dayHasBars = false; }
				if (!levelsReady && openMin >= RthOpen) SetupLevels();
				if (!dayHasBars) { dayHigh = High[0]; dayLow = Low[0]; dayHasBars = true; }
				else { dayHigh = Math.Max(dayHigh, High[0]); dayLow = Math.Min(dayLow, Low[0]); }
				dayClose = Close[0];
			}

			int closeMin = etClose.Hour * 60 + etClose.Minute;
			if (FlattenTime > 0 && closeMin >= Hm(FlattenTime) && closeMin < 18 * 60)
			{
				if (Working(entryOrder)) CancelOrder(entryOrder);
				if (Position.MarketPosition == MarketPosition.Long) ExitLong(); else if (Position.MarketPosition == MarketPosition.Short) ExitShort();
				UpdateDashboard();
				return;
			}

			// pending limit management
			if (Working(entryOrder))
			{
				bool invalid = (pendDir == -1 && High[0] > pendExt) || (pendDir == 1 && Low[0] < pendExt);
				if (CurrentBar >= pendExpiry || invalid) { CancelOrder(entryOrder); status = invalid ? "extreme exceeded: cancelled" : "limit expired"; }
			}

			if (!levelsReady) { UpdateDashboard(); return; }
			bool inWin = openMin >= Hm(WindowStart) && openMin < Hm(WindowEnd);
			for (int q = 0; q < 6; q++)
			{
				if (taken[q]) continue;
				bool hit = q < 3 ? High[0] > lvl[q] : Low[0] < lvl[q];
				if (!hit) continue;
				taken[q] = true;
				if (!inWin) continue;
				int s = q < 3 ? 0 : 1;
				if (s == 0 && (!act[0] || High[0] > ext[0])) { act[0] = true; ext[0] = High[0]; extBar[0] = CurrentBar; }
				if (s == 1 && (!act[1] || Low[0] < ext[1])) { act[1] = true; ext[1] = Low[0]; extBar[1] = CurrentBar; }
			}
			if (!inWin) { act[0] = act[1] = false; UpdateDashboard(); return; }

			for (int s = 0; s < 2; s++)
			{
				if (!act[s]) continue;
				if (s == 0 && High[0] > ext[0]) { ext[0] = High[0]; extBar[0] = CurrentBar; }
				if (s == 1 && Low[0] < ext[1]) { ext[1] = Low[0]; extBar[1] = CurrentBar; }
				if (CurrentBar - extBar[s] > SweepBars) { act[s] = false; continue; }
				if (CurrentBar == extBar[s]) continue;
				// CISD level: open of the first candle of the run into the extreme
				int j = CurrentBar - extBar[s];		// bars ago of the extreme bar
				if (s == 0)
				{
					if (Close[j] <= Open[j]) j++;
					while (j + 1 <= CurrentBar && Close[j] > Open[j] && Close[j + 1] > Open[j + 1]) j++;
				}
				else
				{
					if (Close[j] >= Open[j]) j++;
					while (j + 1 <= CurrentBar && Close[j] < Open[j] && Close[j + 1] < Open[j + 1]) j++;
				}
				double cisd = Open[j];
				bool trig = s == 0 ? Close[0] < cisd : Close[0] > cisd;
				if (!trig) continue;
				act[s] = false;
				int d = s == 0 ? -1 : 1;
				if (Position.MarketPosition != MarketPosition.Flat || Working(entryOrder) || tradesToday >= MaxTradesPerDay) continue;
				if (UseTrendFilter && d != trendDir) { status = "CISD against trend: skip"; continue; }
				if (PauseActive()) { status = "MANUAL PAUSE (file)"; continue; }
				if (atrCount < 14 || double.IsNaN(atrDaily) || atrDaily <= 0) { status = "warming up"; continue; }
				double stop = d == -1 ? ext[s] + TickSize : ext[s] - TickSize;
				double lim = Instrument.MasterInstrument.RoundToTickSize(cisd);
				if ((d == -1 && lim <= Close[0]) || (d == 1 && lim >= Close[0])) continue;
				double risk = (stop - lim) * (-d);
				if (risk <= 0 || risk > MaxRiskAtr * atrDaily) { status = "risk too wide: skip"; continue; }
				pendDir = d; pendStop = stop; pendExt = ext[s]; pendExpiry = CurrentBar + ExpiryBars;
				SetStopLoss(Sig, CalculationMode.Price, stop, false);
				SetProfitTarget(Sig, CalculationMode.Ticks, 4000);	// placeholder, replaced on fill
				if (d == 1) EnterLongLimit(0, true, Contracts, lim, Sig); else EnterShortLimit(0, true, Contracts, lim, Sig);
				status = string.Format("{0} LIMIT @ CISD {1} | SL {2}", d == 1 ? "BUY" : "SELL", Fmt(lim), Fmt(stop));
				Log(status);
			}
			UpdateDashboard();
		}

		private void SetupLevels()
		{
			lvl[0] = prevRthHigh; lvl[1] = onHas ? onH : double.NaN; lvl[2] = lonHas ? lonH : double.NaN;
			lvl[3] = prevRthLow; lvl[4] = onHas ? onL : double.NaN; lvl[5] = lonHas ? lonL : double.NaN;
			for (int q = 0; q < 6; q++) taken[q] = double.IsNaN(lvl[q]);
			// prior-day levels already taken during the overnight session are consumed
			if (onHas)
			{
				if (!taken[0] && onH > lvl[0]) taken[0] = true;
				if (!taken[3] && onL < lvl[3]) taken[3] = true;
			}
			// London levels already taken between 05:00 and 09:29 are consumed
			if (postHas)
			{
				if (!taken[2] && postH > lvl[2]) taken[2] = true;
				if (!taken[5] && postL < lvl[5]) taken[5] = true;
			}
			levelsReady = true; status = "levels ready";
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
			tradesToday++;
			double fill = execution.Order.AverageFillPrice;
			double risk = (pendStop - fill) * (-pendDir);
			if (risk <= 0) { if (pendDir == 1) ExitLong(); else ExitShort(); return; }
			tgtPx = Instrument.MasterInstrument.RoundToTickSize(fill + pendDir * TargetR * risk);
			SetProfitTarget(Sig, CalculationMode.Price, tgtPx);
			status = string.Format("IN {0} @ {1} | SL {2} | TP {3}", pendDir == 1 ? "LONG" : "SHORT", Fmt(fill), Fmt(pendStop), Fmt(tgtPx));
			Log(status);
		}

		private void FinalizeRthDay()
		{
			if (!dayHasBars) return;
			double tr = double.IsNaN(atrPrevClose) ? dayHigh - dayLow : Math.Max(dayHigh - dayLow, Math.Max(Math.Abs(dayHigh - atrPrevClose), Math.Abs(dayLow - atrPrevClose)));
			atrCount++;
			int k = Math.Min(atrCount, 14);
			atrDaily = double.IsNaN(atrDaily) ? tr : ((k - 1) * atrDaily + tr) / k;
			atrPrevClose = dayClose; prevRthHigh = dayHigh; prevRthLow = dayLow;
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
		private void Log(string m) { if (PrintLog) Print(string.Format("{0} | ICT | {1}", Time[0].ToString("yyyy-MM-dd HH:mm", CultureInfo.InvariantCulture), m)); }
		private void UpdateDashboard()
		{
			if (!ShowDashboard || (State == State.Historical && CurrentBar < Count - 2)) return;
			double pf = grossLoss > 0 ? grossWin / grossLoss : 0;
			Draw.TextFixed(this, "ICT_Dash", string.Format("ICT OPEN: {0}\nTotal {1} tr | WR {2:0.0}% | PF {3:0.00} | ${4:0.00}", status, totalTrades,
				totalTrades > 0 ? 100.0 * totalWins / totalTrades : 0, pf, netPnl), TextPosition.TopLeft, Brushes.White, dashFont, Brushes.Transparent, Brushes.Black, 75);
		}

		#region Properties
		[NinjaScriptProperty][Range(0, 2359)][Display(Name = "Window start (ET HHmm, bar open)", Order = 1, GroupName = "01. ICT")] public int WindowStart { get; set; }
		[NinjaScriptProperty][Range(0, 2359)][Display(Name = "Window end (ET HHmm, bar open)", Order = 2, GroupName = "01. ICT")] public int WindowEnd { get; set; }
		[NinjaScriptProperty][Range(1, 50)][Display(Name = "CISD within N bars of the extreme", Order = 3, GroupName = "01. ICT")] public int SweepBars { get; set; }
		[NinjaScriptProperty][Range(1, 200)][Display(Name = "Limit expiry (bars)", Order = 4, GroupName = "01. ICT")] public int ExpiryBars { get; set; }
		[NinjaScriptProperty][Range(0.3, 10.0)][Display(Name = "Target (R)", Order = 5, GroupName = "01. ICT")] public double TargetR { get; set; }
		[NinjaScriptProperty][Range(0.05, 2.0)][Display(Name = "Max risk (x daily ATR)", Order = 6, GroupName = "01. ICT")] public double MaxRiskAtr { get; set; }
		[NinjaScriptProperty][Range(1, 10)][Display(Name = "Max trades per day", Order = 7, GroupName = "01. ICT")] public int MaxTradesPerDay { get; set; }
		[NinjaScriptProperty][Display(Name = "Only with daily trend", Order = 8, GroupName = "01. ICT")] public bool UseTrendFilter { get; set; }
		[NinjaScriptProperty][Range(1000, 1659)][Display(Name = "Flatten time (ET HHmm)", Order = 9, GroupName = "01. ICT")] public int FlattenTime { get; set; }
		[NinjaScriptProperty][Range(1, 50)][Display(Name = "Contracts", Order = 10, GroupName = "02. Risk")] public int Contracts { get; set; }
		[NinjaScriptProperty][Display(Name = "Pause file (create it to pause)", Order = 11, GroupName = "02. Risk")] public string PauseFile { get; set; }
		[Display(Name = "Show dashboard", Order = 20, GroupName = "03. Display")] public bool ShowDashboard { get; set; }
		[Display(Name = "Print log", Order = 21, GroupName = "03. Display")] public bool PrintLog { get; set; }
		#endregion
	}
}
