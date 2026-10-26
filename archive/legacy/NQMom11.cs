//
// NQ MOM 11 - intraday momentum at 11:00 ET (MNQ, NinjaTrader 8, single file). Trades (almost) every day.
// ------------------------------------------------------------------------------------------------
// At 11:00 ET: if price is above the RTH open (09:30) -> BUY, below -> SELL (market, open of the 11:00 bar).
// Stop = StopAtr x daily ATR(14) (RTH days). Target = TargetR x stop (small target -> high win rate). Flat at FlattenTime.
// Research (research/timefill.py): WR 78.6% / 79.1% / 80.7% and PF 1.10 / 1.20 / 1.29 on CFD 2020-23 / CFD 2024-26 /
// REAL MNQ 2024-26 (1 tick slippage, $1 RT). Neighbouring settings (10:30-11:00, VWAP instead of open) similar.
// Meant to run next to NQPullbackDayEngine (ORB60 + VWAP60 + MSEQ) and NQCrt11 as the "daily" portfolio.
// NEEDS: 1-MINUTE MNQ chart, CME US Index Futures ETH, ~20 RTH days of warm-up for the ATR.
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
	public class NQMom11 : Strategy
	{
		private const string Sig = "MOM11";
		private const int RthOpen = 570, RthClose = 960;

		private TimeZoneInfo etZone;
		private SimpleFont dashFont;
		private bool badTimeframe;

		private int rthDay = -1, rthDaysSeen, atrCount;
		private double dayHigh, dayLow, dayClose, rthOpenPx = double.NaN, atrDaily = double.NaN, atrPrevClose = double.NaN, todayAtr = double.NaN;
		private bool dayHasBars, doneToday;
		private string dayStatus = "waiting";

		private int tradesProcessed, totalTrades, totalWins;
		private double grossWin, grossLoss, netPnl;

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Description = "Intraday momentum at 11:00 ET: trade in the direction of price vs the RTH open, small target, every day.";
				Name = "NQMom11";
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

				EntryTime = 1100; StopAtr = 0.25; TargetR = 0.3; FlattenTime = 1555;
				Contracts = 1; PauseFile = "pause_trading.txt"; ShowDashboard = true; PrintLog = true;
			}
			else if (State == State.DataLoaded)
			{
				dashFont = new SimpleFont("Consolas", 12);
				try { etZone = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time"); } catch { etZone = null; }
				badTimeframe = !(BarsPeriod.BarsPeriodType == BarsPeriodType.Minute && BarsPeriod.Value == 1);
				if (badTimeframe) Print("NQMom11 | Needs a 1-MINUTE MNQ chart (CME US Index Futures ETH).");
			}
			else if (State == State.Terminated)
			{
				if (totalTrades == 0 && rthDaysSeen < 20)
					Print(string.Format("NQMom11 | 0 trades: only {0} RTH days loaded; needs ~20 days of warm-up for the ATR.", rthDaysSeen));
			}
		}

		public override string DisplayName { get { return "NQ MOM 11"; } }

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
				if (!dayHasBars) { dayHigh = High[0]; dayLow = Low[0]; dayHasBars = true; rthOpenPx = Open[0]; }
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

			if (etDate == rthDay && !doneToday && closeMin == Hm(EntryTime))
			{
				doneToday = true;
				if (atrCount < 14 || double.IsNaN(todayAtr) || todayAtr <= 0 || double.IsNaN(rthOpenPx)) dayStatus = "warming up";
				else if (PauseActive()) dayStatus = "MANUAL PAUSE (file)";
				else if (Position.MarketPosition != MarketPosition.Flat) dayStatus = "already in position";
				else
				{
					int d = Close[0] > rthOpenPx ? 1 : (Close[0] < rthOpenPx ? -1 : 0);
					if (d != 0)
					{
						int st = Math.Max(4, (int)Math.Round(StopAtr * todayAtr / TickSize));
						int tp = Math.Max(1, (int)Math.Round(TargetR * st));
						SetStopLoss(Sig, CalculationMode.Ticks, st, false);
						SetProfitTarget(Sig, CalculationMode.Ticks, tp);
						if (d == 1) EnterLong(Contracts, Sig); else EnterShort(Contracts, Sig);
						dayStatus = string.Format("{0} x{1} | SL {2}t TP {3}t", d == 1 ? "LONG" : "SHORT", Contracts, st, tp);
						Log(string.Format("MOM11 {0} | price {1} vs RTH open {2} | SL {3}t TP {4}t", d == 1 ? "BUY" : "SELL", Fmt(Close[0]), Fmt(rthOpenPx), st, tp));
					}
				}
			}
			UpdateDashboard();
		}

		private void StartRthDay(int etDate)
		{
			if (dayHasBars)
			{
				double tr = double.IsNaN(atrPrevClose) ? dayHigh - dayLow : Math.Max(dayHigh - dayLow, Math.Max(Math.Abs(dayHigh - atrPrevClose), Math.Abs(dayLow - atrPrevClose)));
				atrCount++;
				int k = Math.Min(atrCount, 14);
				atrDaily = double.IsNaN(atrDaily) ? tr : ((k - 1) * atrDaily + tr) / k;
				atrPrevClose = dayClose;
			}
			rthDaysSeen++;
			rthDay = etDate; dayHasBars = false; doneToday = false; rthOpenPx = double.NaN; todayAtr = atrDaily;
			dayStatus = "waiting 11:00";
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
		private void Log(string m) { if (PrintLog) Print(string.Format("{0} | MOM11 | {1}", Time[0].ToString("yyyy-MM-dd HH:mm", CultureInfo.InvariantCulture), m)); }
		private void UpdateDashboard()
		{
			if (!ShowDashboard || (State == State.Historical && CurrentBar < Count - 2)) return;
			double pf = grossLoss > 0 ? grossWin / grossLoss : 0;
			StringBuilder sb = new StringBuilder();
			sb.AppendLine("NQ MOM 11");
			sb.AppendLine(dayStatus);
			sb.AppendLine(string.Format("Total {0} tr | WR {1:0.0}% | PF {2:0.00} | ${3:0.00}", totalTrades, totalTrades > 0 ? 100.0 * totalWins / totalTrades : 0, pf, netPnl));
			Draw.TextFixed(this, "MOM11_Dash", sb.ToString(), TextPosition.BottomRight, Brushes.White, dashFont, Brushes.Transparent, Brushes.Black, 75);
		}

		#region Properties
		[NinjaScriptProperty][Range(1000, 1500)][Display(Name = "Entry time (ET HHmm, bar close)", Order = 1, GroupName = "01. MOM")] public int EntryTime { get; set; }
		[NinjaScriptProperty][Range(0.05, 2.0)][Display(Name = "Stop (x daily ATR)", Order = 2, GroupName = "01. MOM")] public double StopAtr { get; set; }
		[NinjaScriptProperty][Range(0.1, 5.0)][Display(Name = "Target (R)", Order = 3, GroupName = "01. MOM")] public double TargetR { get; set; }
		[NinjaScriptProperty][Range(1100, 1659)][Display(Name = "Flatten time (ET HHmm)", Order = 4, GroupName = "01. MOM")] public int FlattenTime { get; set; }
		[NinjaScriptProperty][Range(1, 50)][Display(Name = "Contracts", Order = 10, GroupName = "02. Risk")] public int Contracts { get; set; }
		[NinjaScriptProperty][Display(Name = "Pause file (create it to pause)", Order = 11, GroupName = "02. Risk")] public string PauseFile { get; set; }
		[Display(Name = "Show dashboard", Order = 20, GroupName = "03. Display")] public bool ShowDashboard { get; set; }
		[Display(Name = "Print log", Order = 21, GroupName = "03. Display")] public bool PrintLog { get; set; }
		#endregion
	}
}
