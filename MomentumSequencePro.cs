//
// NQ Momentum Sequence PRO - MNQ intraday long-only strategy for prop-firm accounts (NinjaTrader 8, single file)
// ------------------------------------------------------------------------------------------------
// EDGE: intraday momentum continuation inside a daily uptrend (research/wr60.py, NQ 1m 2020-01 -> 2026-09).
//   Daily filter : prior RTH close > SMA(20) of RTH closes (built from completed RTH days only).
//   Setup (5-min): a bearish "main" candle followed by N bullish candles, each closing higher than the previous one
//                  and all staying above the main candle's low. Signal bar must open inside the entry window (ET).
//   Entry        : market at the next bar's open.
//   Stop         : signal close - StopMult x (signal close - main candle low).
//   Target       : fill + TargetR x (fill - stop). Small target + wide structural stop = high win rate.
//   Time exit    : flat at FlattenTime (ET).
// Backtest of this exact logic (1 MNQ, 1 tick slippage, $1 RT): 535 trades, WR 65.4%, PF 1.52, every year positive.
// PROP-FIRM LAYER: daily loss limit (flattens + halts the day), max trades per day, max consecutive losses per day,
//   fixed contracts or $-risk sizing, max contracts, max $ risk per trade, trailing drawdown guard (live only),
//   news blackout times and a MANUAL PAUSE FILE (create it = no new entries; delete it = resume).
// NO LOOK-AHEAD: Calculate.OnBarClose, decisions on completed bars only.
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

//This namespace holds strategies in this folder and is required. Do not change it.
namespace NinjaTrader.NinjaScript.Strategies
{
	public class MomentumSequencePro : Strategy
	{
		private const string Sig = "MSEQ";
		private const int RthOpen = 570, RthClose = 960;

		#region Fields
		private TimeZoneInfo etZone;
		private SimpleFont dashFont;
		private bool badTimeframe;
		private int barMinutes = 5;

		// RTH daily statistics
		private int rthDay = -1;
		private double dayClose = double.NaN, prevRthClose = double.NaN;
		private bool dayHasBars;
		private List<double> rthCloses;

		// day state
		private bool upTrend, dayHalted;
		private string dayStatus = "waiting", haltReason = string.Empty;
		private int tradesToday, lossStreak;
		private double dailyPnl;
		private List<int> newsMinutes;

		// trade state
		private Order entryOrder;
		private double pendingStop, tradeStop, tradeTarget;
		private bool inTrade;
		private int tradesProcessed, totalTrades, totalWins, flattenBar = -1;
		private double grossWin, grossLoss, netPnl;

		// live guards
		private bool isLive, accountHalted;
		private double liveBaseline, livePeak, liveEquity;
		#endregion

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Description = "MNQ long-only momentum sequence (bear candle + N rising bull candles) inside a daily uptrend. Small R target, wide structural stop, prop-firm risk layer.";
				Name = "MomentumSequencePro";
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
				BarsRequiredToTrade = 10;
				IsInstantiatedOnEachOptimizationIteration = true;

				// strategy
				SequenceBars = 5; TargetR = 0.5; StopMult = 1.75; SmaDays = 20; UseTrendFilter = true;
				// hours (ET, HHmm) - signal bar OPEN time must be >= FirstEntry and < LastEntry
				FirstEntry = 1030; LastEntry = 1545; FlattenTime = 1555;
				NewsTimes = ""; NewsMinutesBefore = 2; NewsMinutesAfter = 5;
				PauseFile = "pause_trading.txt";
				// sizing & prop firm
				Contracts = 1; RiskPerTrade = 0; MaxContracts = 5; MaxRiskPerTrade = 0;
				DailyLossLimit = 600; DailyProfitTarget = 0; MaxTradesPerDay = 6; MaxConsecLosses = 0;
				MaxTrailingDrawdown = 0; DrawdownBuffer = 200;
				ShowDashboard = true; PrintLog = true;
			}
			else if (State == State.DataLoaded)
			{
				rthCloses = new List<double>();
				dashFont = new SimpleFont("Consolas", 12);
				try { etZone = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time"); } catch { etZone = null; }
				newsMinutes = ParseTimes(NewsTimes);
				badTimeframe = !(BarsPeriod.BarsPeriodType == BarsPeriodType.Minute && BarsPeriod.Value == 5);
				barMinutes = BarsPeriod.BarsPeriodType == BarsPeriodType.Minute ? BarsPeriod.Value : 5;
				if (badTimeframe)
					Print("MomentumSequencePro | Needs a 5-MINUTE MNQ chart (CME US Index Futures ETH). The backtest was built on 5-minute bars.");
			}
			else if (State == State.Realtime)
			{
				if (entryOrder != null) entryOrder = GetRealtimeOrder(entryOrder);
				isLive = true; liveBaseline = netPnl; livePeak = 0; liveEquity = 0; accountHalted = false;
				Print(string.Format("MomentumSequencePro | LIVE {0} on {1} | historical: {2} trades, net ${3:0.00}", Instrument.FullName, Account.Name, totalTrades, netPnl));
			}
		}

		public override string DisplayName { get { return "NQ Momentum Sequence PRO"; } }

		protected override void OnBarUpdate()
		{
			if (BarsInProgress != 0 || CurrentBar < SequenceBars + 2 || badTimeframe)
				return;

			DateTime etClose = ToEt(Time[0]);
			DateTime etOpen = etClose.AddMinutes(-barMinutes);
			int openMin = etOpen.Hour * 60 + etOpen.Minute;
			int closeMin = etClose.Hour * 60 + etClose.Minute;
			int etDate = etOpen.Year * 10000 + etOpen.Month * 100 + etOpen.Day;

			ProcessClosedTrades();

			bool inRth = openMin >= RthOpen && openMin < RthClose;
			if (inRth && etDate != rthDay)
				StartRthDay(etDate);
			if (inRth && etDate == rthDay)
			{
				dayHasBars = true;
				dayClose = Close[0];
			}

			RiskGuards();

			if (FlattenTime > 0 && closeMin >= Hm(FlattenTime) && closeMin < 18 * 60)
			{
				FlattenAll("end of day");
				UpdateDashboard();
				return;
			}

			if (Position.MarketPosition == MarketPosition.Flat && !Working(entryOrder) && inRth && etDate == rthDay
				&& openMin >= Hm(FirstEntry) && openMin < Hm(LastEntry) && CanOpenNew(closeMin))
			{
				if (!UseTrendFilter || upTrend)
					CheckSignal();
			}
			UpdateDashboard();
		}

		#region Signal
		private void CheckSignal()
		{
			int n = SequenceBars;
			if (!(Close[n] < Open[n]))
				return;
			double mainLow = Low[n];
			for (int j = 0; j < n; j++)
			{
				if (Close[j] <= Open[j] || Low[j] <= mainLow) return;
				if (j < n - 1 && Close[j] <= Close[j + 1]) return;
			}
			double dist = (Close[0] - mainLow) * StopMult;
			if (dist <= 0) return;
			double stop = Instrument.MasterInstrument.RoundDownToTickSize(Close[0] - dist);
			int stopTicks = Math.Max(1, (int)Math.Round((Close[0] - stop) / TickSize));
			double riskPerContract = (stopTicks + 1) * TickSize * Instrument.MasterInstrument.PointValue + 1.0;

			int qty = Contracts;
			if (RiskPerTrade > 0)
				qty = Math.Max(1, (int)Math.Floor(RiskPerTrade / riskPerContract));
			qty = Math.Min(qty, MaxContracts);
			double risk = qty * riskPerContract;
			if (MaxRiskPerTrade > 0 && risk > MaxRiskPerTrade) { dayStatus = string.Format("skip: risk ${0:0} > max", risk); Log(dayStatus); return; }
			if (DailyLossLimit > 0 && dailyPnl - risk < -DailyLossLimit) { dayStatus = "skip: would breach daily loss"; return; }
			if (isLive && MaxTrailingDrawdown > 0 && (livePeak - liveEquity) + risk > MaxTrailingDrawdown - DrawdownBuffer) { dayStatus = "skip: drawdown headroom"; return; }

			pendingStop = stop;
			SetStopLoss(Sig, CalculationMode.Price, stop, false);
			SetProfitTarget(Sig, CalculationMode.Ticks, 4000);		// placeholder, replaced on fill
			EnterLong(qty, Sig);
			Log(string.Format("SIGNAL BUY x{0} | SL {1} ({2}t) | TP {3:0.##}R | risk ${4:0}", qty, Fmt(stop), stopTicks, TargetR, risk));
		}
		#endregion

		#region Daily statistics
		private void StartRthDay(int etDate)
		{
			if (dayHasBars && !double.IsNaN(dayClose))
			{
				prevRthClose = dayClose;
				rthCloses.Add(dayClose);
				while (rthCloses.Count > SmaDays) rthCloses.RemoveAt(0);
			}
			rthDay = etDate; dayHasBars = false;
			dayHalted = false; haltReason = string.Empty; tradesToday = 0; lossStreak = 0; dailyPnl = 0;
			upTrend = false;
			if (rthCloses.Count >= SmaDays && !double.IsNaN(prevRthClose))
			{
				double s = 0; foreach (double x in rthCloses) s += x;
				upTrend = prevRthClose > s / rthCloses.Count;
				dayStatus = upTrend ? "uptrend: armed" : "no uptrend: idle";
			}
			else
				dayStatus = "warming up (" + rthCloses.Count + "/" + SmaDays + " days)";
		}
		#endregion

		#region Risk layer
		private bool CanOpenNew(int closeMin)
		{
			if (accountHalted || dayHalted) return false;
			if (MaxTradesPerDay > 0 && tradesToday >= MaxTradesPerDay) { dayStatus = "max trades reached"; return false; }
			if (InNews(closeMin)) { dayStatus = "news blackout"; return false; }
			if (PauseActive()) { dayStatus = "MANUAL PAUSE (file)"; return false; }
			return true;
		}

		private void RiskGuards()
		{
			double unreal = Position.MarketPosition == MarketPosition.Flat ? 0 : Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Close[0]);
			if (!dayHalted && DailyLossLimit > 0 && dailyPnl + unreal <= -DailyLossLimit)
			{
				dayHalted = true; haltReason = "daily loss limit";
				FlattenAll(haltReason);
			}
			if (!dayHalted && DailyProfitTarget > 0 && dailyPnl >= DailyProfitTarget)
			{
				dayHalted = true; haltReason = "daily profit target";
			}
			if (isLive)
			{
				liveEquity = (netPnl - liveBaseline) + unreal;
				livePeak = Math.Max(livePeak, liveEquity);
				if (!accountHalted && MaxTrailingDrawdown > 0 && livePeak - liveEquity >= MaxTrailingDrawdown - DrawdownBuffer)
				{
					accountHalted = true; haltReason = "trailing drawdown guard";
					FlattenAll(haltReason);
					Print("MomentumSequencePro | ACCOUNT HALTED: trailing drawdown guard");
				}
			}
		}

		private void FlattenAll(string why)
		{
			if (Working(entryOrder)) CancelOrder(entryOrder);
			if (Position.MarketPosition == MarketPosition.Flat || flattenBar == CurrentBar) return;
			flattenBar = CurrentBar;
			ExitLong();
			Log("FLATTEN: " + why);
		}

		private bool PauseActive()
		{
			if (string.IsNullOrWhiteSpace(PauseFile)) return false;
			try
			{
				string path = Path.IsPathRooted(PauseFile) ? PauseFile : Path.Combine(Core.Globals.UserDataDir, PauseFile);
				return File.Exists(path);
			}
			catch { return false; }
		}

		private bool InNews(int m)
		{
			foreach (int n in newsMinutes)
				if (m >= n - NewsMinutesBefore && m <= n + NewsMinutesAfter) return true;
			return false;
		}
		#endregion

		#region Order / execution events
		private static bool Working(Order o)
		{
			if (o == null) return false;
			OrderState s = o.OrderState;
			return s != OrderState.Filled && s != OrderState.Cancelled && s != OrderState.Rejected && s != OrderState.Unknown;
		}

		protected override void OnOrderUpdate(Order order, double limitPrice, double stopPrice, int quantity, int filled, double averageFillPrice,
			OrderState orderState, DateTime time, ErrorCode error, string nativeError)
		{
			if (order.Name == Sig) entryOrder = order;
			if (orderState == OrderState.Rejected)
				Print(string.Format("MomentumSequencePro | {0} REJECTED: {1} {2}", order.Name, error, nativeError));
		}

		protected override void OnExecutionUpdate(Execution execution, string executionId, double price, int quantity,
			MarketPosition marketPosition, string orderId, DateTime time)
		{
			if (execution.Order == null || execution.Order.Name != Sig) return;
			if (execution.Order.OrderState != OrderState.Filled) return;
			double fill = execution.Order.AverageFillPrice;
			if (!inTrade) { inTrade = true; tradesToday++; }
			tradeStop = pendingStop;
			if (fill <= tradeStop)
			{
				Log("filled below the stop -> exit");
				ExitLong();
				return;
			}
			tradeTarget = Instrument.MasterInstrument.RoundToTickSize(fill + TargetR * (fill - tradeStop));
			if (tradeTarget <= fill) tradeTarget = fill + TickSize;
			SetProfitTarget(Sig, CalculationMode.Price, tradeTarget);
			Log(string.Format("FILLED @ {0} | SL {1} | TP {2}", Fmt(fill), Fmt(tradeStop), Fmt(tradeTarget)));
		}

		private void ProcessClosedTrades()
		{
			int count = SystemPerformance.AllTrades.Count;
			double pnl = 0; bool any = false;
			for (int i = tradesProcessed; i < count; i++)
			{
				pnl += SystemPerformance.AllTrades[i].ProfitCurrency; any = true;
			}
			tradesProcessed = count;
			if (any && Position.MarketPosition == MarketPosition.Flat)
			{
				inTrade = false;
				totalTrades++; netPnl += pnl; dailyPnl += pnl;
				if (pnl > 0) { totalWins++; grossWin += pnl; lossStreak = 0; }
				else { grossLoss -= pnl; lossStreak++; }
				Log(string.Format("CLOSED ${0:0.00} | day ${1:0.00} | net ${2:0.00}", pnl, dailyPnl, netPnl));
				if (MaxConsecLosses > 0 && lossStreak >= MaxConsecLosses && !dayHalted)
				{
					dayHalted = true; haltReason = lossStreak + " consecutive losses";
				}
			}
		}
		#endregion

		#region Helpers
		private DateTime ToEt(DateTime t)
		{
			if (etZone == null) return t;
			try { return TimeZoneInfo.ConvertTime(DateTime.SpecifyKind(t, DateTimeKind.Unspecified), Core.Globals.GeneralOptions.TimeZoneInfo, etZone); }
			catch { return t; }
		}
		private static int Hm(int hhmm) { return (hhmm / 100) * 60 + hhmm % 100; }
		private string Fmt(double p) { return Instrument.MasterInstrument.FormatPrice(p); }
		private void Log(string m) { if (PrintLog) Print(string.Format("{0} | MSEQ | {1}", Time[0].ToString("yyyy-MM-dd HH:mm", CultureInfo.InvariantCulture), m)); }
		private static List<int> ParseTimes(string csv)
		{
			List<int> r = new List<int>();
			if (string.IsNullOrWhiteSpace(csv)) return r;
			foreach (string raw in csv.Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries))
			{
				string[] p = raw.Trim().Split(':'); int hh, mm;
				if (p.Length == 2 && int.TryParse(p[0], out hh) && int.TryParse(p[1], out mm)) r.Add(hh * 60 + mm);
			}
			return r;
		}
		private void UpdateDashboard()
		{
			if (!ShowDashboard || (State == State.Historical && CurrentBar < Count - 2)) return;
			double pf = grossLoss > 0 ? grossWin / grossLoss : 0;
			StringBuilder sb = new StringBuilder();
			sb.AppendLine("NQ MOMENTUM SEQUENCE PRO");
			sb.AppendLine(string.Format("Daily trend {0} | trades today {1}/{2}", upTrend ? "UP (armed)" : "not up (idle)", tradesToday, MaxTradesPerDay));
			if (Position.MarketPosition == MarketPosition.Long)
				sb.AppendLine(string.Format("LONG {0} | SL {1} | TP {2}", Position.Quantity, Fmt(tradeStop), Fmt(tradeTarget)));
			sb.AppendLine(string.Format("Day ${0:0.00} | {1}{2}", dailyPnl, dayStatus, dayHalted ? " | HALTED: " + haltReason : ""));
			sb.AppendLine(string.Format("Total {0} tr | WR {1:0.0}% | PF {2:0.00} | ${3:0.00}", totalTrades, totalTrades > 0 ? 100.0 * totalWins / totalTrades : 0, pf, netPnl));
			if (isLive && MaxTrailingDrawdown > 0) sb.AppendLine(string.Format("Live DD ${0:0.00} / ${1:0}{2}", livePeak - liveEquity, MaxTrailingDrawdown, accountHalted ? " ACCOUNT HALTED" : ""));
			Draw.TextFixed(this, "MSEQ_Dash", sb.ToString(), TextPosition.TopRight, Brushes.White, dashFont, Brushes.Transparent, Brushes.Black, 75);
		}
		#endregion

		#region Properties
		[NinjaScriptProperty][Range(2, 8)][Display(Name = "Sequence candles (N)", Order = 1, GroupName = "01. Strategy")] public int SequenceBars { get; set; }
		[NinjaScriptProperty][Range(0.2, 5.0)][Display(Name = "Target (R)", Order = 2, GroupName = "01. Strategy")] public double TargetR { get; set; }
		[NinjaScriptProperty][Range(0.5, 5.0)][Display(Name = "Stop multiplier (x distance to main low)", Order = 3, GroupName = "01. Strategy")] public double StopMult { get; set; }
		[NinjaScriptProperty][Range(5, 200)][Display(Name = "Trend SMA (RTH days)", Order = 4, GroupName = "01. Strategy")] public int SmaDays { get; set; }
		[NinjaScriptProperty][Display(Name = "Use daily trend filter", Order = 5, GroupName = "01. Strategy")] public bool UseTrendFilter { get; set; }

		[NinjaScriptProperty][Range(930, 1559)][Display(Name = "First entry (signal bar open, ET HHmm)", Order = 20, GroupName = "02. Hours (ET)")] public int FirstEntry { get; set; }
		[NinjaScriptProperty][Range(930, 1559)][Display(Name = "Last entry (signal bar open, ET HHmm)", Order = 21, GroupName = "02. Hours (ET)")] public int LastEntry { get; set; }
		[NinjaScriptProperty][Range(1000, 1659)][Display(Name = "Flatten time (ET HHmm)", Order = 22, GroupName = "02. Hours (ET)")] public int FlattenTime { get; set; }
		[NinjaScriptProperty][Display(Name = "News times (ET HH:mm list)", Order = 23, GroupName = "02. Hours (ET)")] public string NewsTimes { get; set; }
		[NinjaScriptProperty][Range(0, 120)][Display(Name = "News minutes before", Order = 24, GroupName = "02. Hours (ET)")] public int NewsMinutesBefore { get; set; }
		[NinjaScriptProperty][Range(0, 120)][Display(Name = "News minutes after", Order = 25, GroupName = "02. Hours (ET)")] public int NewsMinutesAfter { get; set; }
		[NinjaScriptProperty][Display(Name = "Pause file (create it to pause)", Order = 26, GroupName = "02. Hours (ET)")] public string PauseFile { get; set; }

		[NinjaScriptProperty][Range(1, 50)][Display(Name = "Contracts (fixed)", Order = 30, GroupName = "03. Prop firm")] public int Contracts { get; set; }
		[NinjaScriptProperty][Range(0.0, double.MaxValue)][Display(Name = "Risk per trade $ (0 = use fixed contracts)", Order = 31, GroupName = "03. Prop firm")] public double RiskPerTrade { get; set; }
		[NinjaScriptProperty][Range(1, 100)][Display(Name = "Max contracts", Order = 32, GroupName = "03. Prop firm")] public int MaxContracts { get; set; }
		[NinjaScriptProperty][Range(0.0, double.MaxValue)][Display(Name = "Max $ risk per trade (0 = off)", Order = 33, GroupName = "03. Prop firm")] public double MaxRiskPerTrade { get; set; }
		[NinjaScriptProperty][Range(0.0, double.MaxValue)][Display(Name = "Daily loss limit $ (flattens, 0 = off)", Order = 34, GroupName = "03. Prop firm")] public double DailyLossLimit { get; set; }
		[NinjaScriptProperty][Range(0.0, double.MaxValue)][Display(Name = "Daily profit target $ (0 = off)", Order = 35, GroupName = "03. Prop firm")] public double DailyProfitTarget { get; set; }
		[NinjaScriptProperty][Range(1, 50)][Display(Name = "Max trades per day (hard)", Order = 36, GroupName = "03. Prop firm")] public int MaxTradesPerDay { get; set; }
		[NinjaScriptProperty][Range(0, 20)][Display(Name = "Stop day after N losses (0 = off)", Order = 37, GroupName = "03. Prop firm")] public int MaxConsecLosses { get; set; }
		[NinjaScriptProperty][Range(0.0, double.MaxValue)][Display(Name = "Trailing drawdown $ (live, 0 = off)", Order = 38, GroupName = "03. Prop firm")] public double MaxTrailingDrawdown { get; set; }
		[NinjaScriptProperty][Range(0.0, double.MaxValue)][Display(Name = "Drawdown buffer $", Order = 39, GroupName = "03. Prop firm")] public double DrawdownBuffer { get; set; }

		[Display(Name = "Show dashboard", Order = 50, GroupName = "04. Display")] public bool ShowDashboard { get; set; }
		[Display(Name = "Print log", Order = 51, GroupName = "04. Display")] public bool PrintLog { get; set; }
		#endregion
	}
}
