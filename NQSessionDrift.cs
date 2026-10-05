//
// NQ Session Drift for NinjaTrader 8 - MNQ / NQ, 1-minute chart (CME US Index Futures ETH)
//
// Companion to NYOpeningRangeTrend (NQ Trend Day v2). Two long-only, time-of-day return streams that are
// nearly uncorrelated with the ORB / VWAP modules (research: 2020-2026 Nasdaq-100 1-minute data).
//
// Module RTH  : buy the 09:30 ET open, protective stop 0.20 x daily ATR(14), exit 15:55 ET. Every day.
// Module Night: buy after the 18:00 ET reopen, stop 0.30 x daily ATR(14), exit 08:00 ET.
//               Only when the last RTH close is above its SMA(50) (bull regime filter).
//
// Run it as a SEPARATE strategy instance next to NYOpeningRangeTrend on the same account.
//
#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Globalization;
using System.Text;
using System.Windows.Media;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Tools;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.DrawingTools;
#endregion

//This namespace holds strategies in this folder and is required. Do not change it.
namespace NinjaTrader.NinjaScript.Strategies
{
	public class NQSessionDrift : Strategy
	{
		private const string SigRth		= "DRIFT RTH";
		private const string SigNight	= "DRIFT NIGHT";
		private const int RthOpen		= 9 * 60 + 30;
		private const int RthClose		= 16 * 60;

		#region Fields
		private TimeZoneInfo	etZone;
		private SimpleFont		dashFont;
		private bool			badTimeframe;

		// RTH daily statistics (finalized at the RTH close)
		private int				rthDay			= -1;
		private double			dayHigh, dayLow, dayClose;
		private bool			dayHasBars;
		private bool			dayFinalized	= true;
		private double			lastRthClose	= double.NaN;
		private double			atrDaily		= double.NaN;
		private int				atrCount;
		private double			atrPrevClose	= double.NaN;
		private List<double>	rthCloses;

		private int				rthTradeDay		= -1;
		private int				nightTradeDay	= -1;
		private string			activeModule	= string.Empty;
		private double			activeRiskUsd;
		private int				tradesProcessed;
		private int				totalTrades, totalWins;
		private double			grossWin, grossLoss, netPnl;
		private string			lastAction		= "-";
		private int				exitBar			= -1;
		private bool			summaryPrinted;
		#endregion

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Description									= "NQ Session Drift: long 09:30-15:55 ET with a 0.2 ATR stop, and long 18:00-08:00 ET in bull regimes (close > SMA50) with a 0.3 ATR stop. Run next to NYOpeningRangeTrend.";
				Name										= "NQSessionDrift";
				Calculate									= Calculate.OnBarClose;
				EntriesPerDirection							= 1;
				EntryHandling								= EntryHandling.AllEntries;
				IsExitOnSessionCloseStrategy				= true;		// both modules live inside one Globex session (18:00-17:00)
				ExitOnSessionCloseSeconds					= 30;
				IsFillLimitOnTouch							= false;
				MaximumBarsLookBack							= MaximumBarsLookBack.TwoHundredFiftySix;
				OrderFillResolution							= OrderFillResolution.Standard;
				Slippage									= 0;
				StartBehavior								= StartBehavior.WaitUntilFlat;
				TimeInForce									= TimeInForce.Gtc;
				TraceOrders									= false;
				RealtimeErrorHandling						= RealtimeErrorHandling.StopCancelClose;
				StopTargetHandling							= StopTargetHandling.PerEntryExecution;
				BarsRequiredToTrade							= 20;
				IsInstantiatedOnEachOptimizationIteration	= true;

				UseRthModule		= true;
				RthStopAtr			= 0.20;
				RthExitTime			= 1555;
				UseNightModule		= true;
				NightEntryTime		= 1801;
				NightExitTime		= 800;
				NightStopAtr		= 0.30;
				NightRegimeSma		= 50;
				AtrLength			= 14;

				RiskPerTrade		= 100;
				OneContractMaxRisk	= 200;
				MaxContracts		= 10;
				CommissionPerContract = 1.00;
				StopSlippageTicks	= 1;

				ShowDashboard		= true;
				PrintTradeLog		= true;
			}
			else if (State == State.DataLoaded)
			{
				rthCloses	= new List<double>();
				dashFont	= new SimpleFont("Consolas", 12);
				try { etZone = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time"); }
				catch { etZone = null; }
				badTimeframe = !(BarsPeriod.BarsPeriodType == BarsPeriodType.Minute && BarsPeriod.Value == 1);
				if (badTimeframe)
					Print("NQSessionDrift | Must run on a 1-MINUTE chart with ETH trading hours.");
			}
			else if (State == State.Terminated)
			{
				if (rthCloses != null && !summaryPrinted)
				{
					summaryPrinted = true;
					double pf = grossLoss > 0 ? grossWin / grossLoss : 0;
					Print(string.Format("============ NQ Session Drift | trades {0} | WR {1:0.0}% | PF {2:0.00} | Net ${3:0.00}",
						totalTrades, totalTrades > 0 ? 100.0 * totalWins / totalTrades : 0, pf, netPnl));
				}
			}
		}

		public override string DisplayName
		{
			get { return "NQ Session Drift"; }
		}

		protected override void OnBarUpdate()
		{
			if (BarsInProgress != 0 || CurrentBar < 2 || badTimeframe)
				return;

			DateTime etClose = ToEt(Time[0]);
			DateTime etOpen	 = etClose.AddMinutes(-1);
			int openMin		 = etOpen.Hour * 60 + etOpen.Minute;
			int closeMin	 = etClose.Hour * 60 + etClose.Minute;
			int etDate		 = etOpen.Year * 10000 + etOpen.Month * 100 + etOpen.Day;
			// Globex session id: bars from 18:00 belong to the next day's session.
			DateTime sess	 = etOpen.AddHours(6);
			int sessionId	 = sess.Year * 10000 + sess.Month * 100 + sess.Day;

			ProcessClosedTrades();
			UpdateDailyStats(openMin, etDate);

			// ---------- exits (time based; stops are live at the exchange) ----------
			if (Position.MarketPosition == MarketPosition.Long)
			{
				bool rthExit	= activeModule == SigRth && closeMin >= HhmmToMinutes(RthExitTime) && closeMin < 18 * 60;
				bool nightExit	= activeModule == SigNight && closeMin >= HhmmToMinutes(NightExitTime) && closeMin < 17 * 60;
				if ((rthExit || nightExit) && exitBar != CurrentBar)
				{
					exitBar = CurrentBar;
					ExitLong("DRIFT exit", activeModule);
					Log("EXIT " + activeModule + " (time)");
				}
			}

			if (Position.MarketPosition != MarketPosition.Flat || double.IsNaN(atrDaily) || atrCount < AtrLength)
				return;

			// ---------- RTH module: order at the close of the 09:29 bar -> filled at the 09:30 open ----------
			if (UseRthModule && openMin == RthOpen - 1 && rthTradeDay != etDate)
			{
				rthTradeDay = etDate;
				Enter(SigRth, RthStopAtr);
			}

			// ---------- Night module: after the 18:00 reopen, bull regime only ----------
			if (UseNightModule && closeMin == HhmmToMinutes(NightEntryTime) && nightTradeDay != sessionId)
			{
				nightTradeDay = sessionId;
				if (BullRegime())
					Enter(SigNight, NightStopAtr);
				else
					lastAction = "night skipped: below SMA" + NightRegimeSma;
			}

			UpdateDashboard();
		}

		private void Enter(string sig, double stopAtr)
		{
			int stopTicks	= Math.Max(4, (int)Math.Round(stopAtr * atrDaily / TickSize));
			double per		= (stopTicks + StopSlippageTicks) * Instrument.MasterInstrument.PointValue * TickSize + CommissionPerContract;
			int qty			= (int)Math.Floor(RiskPerTrade / per);
			if (qty < 1 && per <= OneContractMaxRisk)
				qty = 1;
			qty = Math.Min(qty, MaxContracts);
			if (qty < 1)
			{
				lastAction = string.Format("{0} skipped: 1 lot risks ${1:0}", sig, per);
				Log(lastAction);
				return;
			}
			SetStopLoss(sig, CalculationMode.Ticks, stopTicks, false);
			EnterLong(qty, sig);
			activeModule	= sig;
			activeRiskUsd	= qty * per;
			lastAction		= string.Format("{0} BUY x{1} | stop {2}t | risk ${3:0}", sig, qty, stopTicks, activeRiskUsd);
			Log(lastAction);
		}

		private bool BullRegime()
		{
			if (rthCloses.Count < (int)(NightRegimeSma * 0.8) || double.IsNaN(lastRthClose))
				return false;
			int n = Math.Min(NightRegimeSma, rthCloses.Count);
			double sum = 0;
			for (int i = rthCloses.Count - n; i < rthCloses.Count; i++)
				sum += rthCloses[i];
			return lastRthClose > sum / n;
		}

		private void UpdateDailyStats(int openMin, int etDate)
		{
			bool inRth = openMin >= RthOpen && openMin < RthClose;
			// Finalize the RTH day as soon as we are past it (16:00 or a new date).
			if (!dayFinalized && dayHasBars && (!inRth || etDate != rthDay))
			{
				double tr = double.IsNaN(atrPrevClose) ? dayHigh - dayLow
					: Math.Max(dayHigh - dayLow, Math.Max(Math.Abs(dayHigh - atrPrevClose), Math.Abs(dayLow - atrPrevClose)));
				atrCount++;
				int k = Math.Min(atrCount, AtrLength);
				atrDaily		= double.IsNaN(atrDaily) ? tr : ((k - 1) * atrDaily + tr) / k;
				atrPrevClose	= dayClose;
				lastRthClose	= dayClose;
				rthCloses.Add(dayClose);
				while (rthCloses.Count > Math.Max(NightRegimeSma, 20))
					rthCloses.RemoveAt(0);
				dayFinalized = true;
			}
			if (inRth)
			{
				if (etDate != rthDay)
				{
					rthDay = etDate; dayHasBars = false; dayFinalized = false;
				}
				if (!dayHasBars) { dayHigh = High[0]; dayLow = Low[0]; dayHasBars = true; }
				else { dayHigh = Math.Max(dayHigh, High[0]); dayLow = Math.Min(dayLow, Low[0]); }
				dayClose = Close[0];
			}
		}

		private void ProcessClosedTrades()
		{
			int count = SystemPerformance.AllTrades.Count;
			if (count <= tradesProcessed || Position.MarketPosition != MarketPosition.Flat)
				return;
			double pnl = 0;
			for (int i = tradesProcessed; i < count; i++)
				pnl += SystemPerformance.AllTrades[i].ProfitCurrency;
			tradesProcessed = count;
			totalTrades++;
			netPnl += pnl;
			if (pnl > 0) { totalWins++; grossWin += pnl; } else grossLoss += -pnl;
			Log(string.Format("CLOSED {0} ${1:0.00} ({2:+0.00;-0.00}R) | net ${3:0.00}", activeModule, pnl, activeRiskUsd > 0 ? pnl / activeRiskUsd : 0, netPnl));
			activeModule = string.Empty;
		}

		private DateTime ToEt(DateTime t)
		{
			if (etZone == null)
				return t;
			try { return TimeZoneInfo.ConvertTime(DateTime.SpecifyKind(t, DateTimeKind.Unspecified), Core.Globals.GeneralOptions.TimeZoneInfo, etZone); }
			catch { return t; }
		}

		private static int HhmmToMinutes(int hhmm)
		{
			return (hhmm / 100) * 60 + (hhmm % 100);
		}

		private void Log(string message)
		{
			if (PrintTradeLog)
				Print(string.Format("{0} | DRIFT | {1}", Time[0].ToString("yyyy-MM-dd HH:mm", CultureInfo.InvariantCulture), message));
		}

		private void UpdateDashboard()
		{
			if (!ShowDashboard || (State == State.Historical && CurrentBar < Count - 2))
				return;
			double pf = grossLoss > 0 ? grossWin / grossLoss : 0;
			StringBuilder sb = new StringBuilder();
			sb.AppendLine("NQ SESSION DRIFT  |  RTH + Night (long)");
			sb.AppendLine(string.Format("ATRd {0:0.0} | regime {1}", atrDaily, BullRegime() ? "BULL (night on)" : "not bull (night off)"));
			sb.AppendLine("Last   : " + lastAction);
			sb.AppendLine(string.Format("Stats  : {0} tr | WR {1:0.0}% | PF {2:0.00} | ${3:0.00}", totalTrades, totalTrades > 0 ? 100.0 * totalWins / totalTrades : 0, pf, netPnl));
			Draw.TextFixed(this, "DRIFT_Dash", sb.ToString(), TextPosition.BottomRight, Brushes.White, dashFont, Brushes.Transparent, Brushes.Black, 75);
		}

		#region Properties
		[NinjaScriptProperty]
		[Display(Name = "Enable RTH module", Order = 1, GroupName = "01. RTH module")]
		public bool UseRthModule { get; set; }

		[NinjaScriptProperty]
		[Range(0.02, 2.0)]
		[Display(Name = "RTH stop (x daily ATR)", Order = 2, GroupName = "01. RTH module")]
		public double RthStopAtr { get; set; }

		[NinjaScriptProperty]
		[Range(1000, 1659)]
		[Display(Name = "RTH exit time (ET, HHmm)", Order = 3, GroupName = "01. RTH module")]
		public int RthExitTime { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Enable night module", Order = 10, GroupName = "02. Night module")]
		public bool UseNightModule { get; set; }

		[NinjaScriptProperty]
		[Range(1800, 2359)]
		[Display(Name = "Night entry time (ET, HHmm)", Order = 11, GroupName = "02. Night module")]
		public int NightEntryTime { get; set; }

		[NinjaScriptProperty]
		[Range(100, 925)]
		[Display(Name = "Night exit time (ET, HHmm)", Order = 12, GroupName = "02. Night module")]
		public int NightExitTime { get; set; }

		[NinjaScriptProperty]
		[Range(0.02, 2.0)]
		[Display(Name = "Night stop (x daily ATR)", Order = 13, GroupName = "02. Night module")]
		public double NightStopAtr { get; set; }

		[NinjaScriptProperty]
		[Range(5, 250)]
		[Display(Name = "Night regime SMA (RTH closes)", Order = 14, GroupName = "02. Night module")]
		public int NightRegimeSma { get; set; }

		[NinjaScriptProperty]
		[Range(2, 100)]
		[Display(Name = "Daily ATR length", Order = 20, GroupName = "03. Risk")]
		public int AtrLength { get; set; }

		[NinjaScriptProperty]
		[Range(1.0, double.MaxValue)]
		[Display(Name = "Risk per trade ($)", Order = 21, GroupName = "03. Risk")]
		public double RiskPerTrade { get; set; }

		[NinjaScriptProperty]
		[Range(0.0, double.MaxValue)]
		[Display(Name = "1-contract max risk ($)", Order = 22, GroupName = "03. Risk")]
		public double OneContractMaxRisk { get; set; }

		[NinjaScriptProperty]
		[Range(1, 100)]
		[Display(Name = "Max contracts", Order = 23, GroupName = "03. Risk")]
		public int MaxContracts { get; set; }

		[NinjaScriptProperty]
		[Range(0.0, double.MaxValue)]
		[Display(Name = "Commission per contract, round turn ($)", Order = 24, GroupName = "03. Risk")]
		public double CommissionPerContract { get; set; }

		[NinjaScriptProperty]
		[Range(0, 100)]
		[Display(Name = "Stop slippage allowance (ticks)", Order = 25, GroupName = "03. Risk")]
		public int StopSlippageTicks { get; set; }

		[Display(Name = "Show dashboard", Order = 30, GroupName = "04. Display")]
		public bool ShowDashboard { get; set; }

		[Display(Name = "Print trade log", Order = 31, GroupName = "04. Display")]
		public bool PrintTradeLog { get; set; }
		#endregion
	}
}
