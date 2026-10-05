//
// NQ Trend Day (v2) for NinjaTrader 8 - MNQ / NQ, 1-minute chart
//
// Research-validated on 2020-2026 Nasdaq-100 1-minute data (see research/ and RESULTADOS.md).
// Daily bias: prior RTH close vs SMA(20) of RTH closes. Both modules trade ONLY in the bias direction.
//
// Module 1 - Opening Range Breakout
//   Range 09:30-10:30 ET. From 10:30 to 13:00 a stop order waits 1 tick beyond the range.
//   Stop = opposite side of the range, capped at 0.20 x daily ATR(14). Target = 2R (0.5R option = ~70% WR, less $).
//   After an exit it re-arms once price closes back inside the range (max 2 per day).
//
// Module 2 - VWAP pullback
//   After 10:30, once a bar closes beyond the range AND at least 0.10 x daily ATR away from VWAP,
//   a limit order rests at VWAP (updated every bar) until 14:30. Stop = 0.20 x daily ATR. Target = 2R.
//   One per day.
//
// Everything is flat at 15:55 ET. The day stops after 2 consecutive losses.
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
	public enum ORTSizingMode { RiskPerTrade, FixedContracts }

	public class NYOpeningRangeTrend : Strategy
	{
		private const string OrbLong	= "ORB L";
		private const string OrbShort	= "ORB S";
		private const string VwpLong	= "VWP L";
		private const string VwpShort	= "VWP S";
		private const string SigFlat	= "TD Flat";
		private const int RthOpen		= 9 * 60 + 30;
		private const int RthClose		= 16 * 60;

		#region Fields
		private TimeZoneInfo	etZone;
		private SimpleFont		dashFont;
		private bool			badTimeframe;

		// RTH daily statistics
		private int				rthDay			= -1;
		private double			dayHigh, dayLow, dayClose;
		private bool			dayHasBars;
		private double			prevRthClose	= double.NaN;
		private double			atrDaily		= double.NaN;
		private int				atrCount;
		private double			atrPrevClose	= double.NaN;
		private List<double>	rthCloses;

		// Day state
		private int				trendDir;
		private double			todayAtr;
		private bool			dayTradable;
		private string			dayStatus		= "waiting for 09:30 ET";
		private double			orHigh, orLow;
		private int				orBars;
		private bool			orReady;
		private double			vwapPv, vwapVol, vwap;
		private int				dayLossStreak;
		private bool			dayHalted;

		// Module 1 - ORB
		private Order			orbOrder;
		private bool			orbArmed;
		private int				orbTrades;
		private int				orbQtyOpen;
		private double			orbPnlAcc;
		private double			orbRiskUsd;
		private bool			orbInTrade;

		// Module 2 - VWAP pullback
		private Order			vwpOrder;
		private bool			vwpArmed;
		private bool			vwpDone;
		private int				vwpQtyOpen;
		private double			vwpPnlAcc;
		private double			vwpRiskUsd;
		private bool			vwpInTrade;

		// Accounting
		private int				tradesProcessed;
		private int				totalTrades, totalWins, totalLosses;
		private double			grossWin, grossLoss, netPnl, totalR;
		private double			dailyPnl;
		private int				flattenBar		= -1;
		private bool			isLive;
		private double			liveBaseline, livePeak, liveEquity;
		private bool			accountHalted;
		private string			accountHaltReason	= string.Empty;
		private bool			summaryPrinted;
		#endregion

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Description									= "NQ Trend Day v2: 60-min opening range breakout + VWAP pullback, both only in the daily trend direction (prior close vs SMA20). 2R targets, flat 15:55 ET. Research-validated 2020-2026.";
				Name										= "NYOpeningRangeTrend";
				Calculate									= Calculate.OnBarClose;
				EntriesPerDirection							= 1;
				EntryHandling								= EntryHandling.UniqueEntries;
				IsExitOnSessionCloseStrategy				= true;
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

				// 01. Daily bias
				TrendSmaLength			= 20;
				AtrLength				= 14;
				RangeMinutes			= 60;
				FlattenTime				= 1555;
				MaxConsecLossesPerDay	= 2;

				// 02. Module 1 - ORB
				UseOrb					= true;
				OrbLastEntryTime		= 1300;
				OrbStopCapAtr			= 0.20;
				OrbTargetR				= 2.0;		// 2R = most $ per day (~47% WR). 0.5R = ~70% WR but ~1/3 of the profit.
				OrbMaxTradesPerDay		= 2;

				// 03. Module 2 - VWAP pullback
				UseVwap					= true;
				VwapExtensionAtr		= 0.10;
				VwapStopAtr				= 0.20;
				VwapTargetR				= 2.0;
				VwapLastEntryTime		= 1430;

				// 04. Position sizing
				SizingMode				= ORTSizingMode.RiskPerTrade;
				RiskPerTrade			= 100;
				OneContractMaxRisk		= 200;
				FixedContracts			= 1;
				MaxContracts			= 3;		// 25K funded plan: 1 MNQ most of the time, never more than 3
				CommissionPerContract	= 1.00;
				StopSlippageTicks		= 1;

				// 05. Prop-firm guards
				DailyLossLimit			= 450;		// 25K plan: no new trades after -$450 on the day
				MaxTrailingDrawdown		= 1200;		// set to YOUR firm's trailing drawdown (25K: 1000-1500)
				DrawdownBuffer			= 150;
				AccountProfitTarget		= 0;

				// 06. Display
				ShowVisuals				= true;
				ShowDashboard			= true;
				PrintTradeLog			= true;
			}
			else if (State == State.DataLoaded)
			{
				rthCloses	= new List<double>();
				dashFont	= new SimpleFont("Consolas", 12);
				try { etZone = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time"); }
				catch { etZone = null; }

				badTimeframe = !(BarsPeriod.BarsPeriodType == BarsPeriodType.Minute && BarsPeriod.Value == 1);
				if (badTimeframe)
					Print("NQ Trend Day | This strategy must run on a 1-MINUTE chart. It will not trade on " + BarsPeriod);
			}
			else if (State == State.Realtime)
			{
				if (orbOrder != null)
					orbOrder = GetRealtimeOrder(orbOrder);
				if (vwpOrder != null)
					vwpOrder = GetRealtimeOrder(vwpOrder);

				isLive				= true;
				liveBaseline		= netPnl;
				livePeak			= 0;
				liveEquity			= 0;
				accountHalted		= false;
				accountHaltReason	= string.Empty;
				PrintSummary("Historical warm-up complete");
				Print("NQ Trend Day | LIVE on " + Instrument.FullName + " | account " + Account.Name);
			}
			else if (State == State.Terminated)
			{
				if (rthCloses != null && !summaryPrinted)
				{
					summaryPrinted = true;
					PrintSummary("Terminated");
				}
			}
		}

		public override string DisplayName
		{
			get { return "NQ Trend Day v2"; }
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

			if (Bars.IsFirstBarOfSession)
				dailyPnl = 0;

			ProcessClosedTrades();

			bool inRth = openMin >= RthOpen && openMin < RthClose;
			if (inRth && etDate != rthDay)
				StartRthDay(etDate);

			if (inRth && etDate == rthDay)
			{
				if (!dayHasBars) { dayHigh = High[0]; dayLow = Low[0]; dayHasBars = true; }
				else { dayHigh = Math.Max(dayHigh, High[0]); dayLow = Math.Min(dayLow, Low[0]); }
				dayClose = Close[0];

				double vol = Volume[0] > 0 ? Volume[0] : 1.0;
				vwapPv	+= (High[0] + Low[0] + Close[0]) / 3.0 * vol;
				vwapVol	+= vol;
				vwap	 = vwapPv / vwapVol;

				if (openMin < RthOpen + RangeMinutes)
				{
					if (orBars == 0) { orHigh = High[0]; orLow = Low[0]; }
					else { orHigh = Math.Max(orHigh, High[0]); orLow = Math.Min(orLow, Low[0]); }
					orBars++;
					if (openMin == RthOpen + RangeMinutes - 1)
						OnRangeComplete();
				}
			}

			RunGuards();

			if (FlattenTime > 0 && closeMin >= HhmmToMinutes(FlattenTime) && closeMin < 18 * 60)
			{
				FlattenAll("end of day");
				return;
			}

			if (inRth && etDate == rthDay && orReady && dayTradable)
			{
				ManageOrb(openMin, closeMin);
				ManageVwap(openMin, closeMin);
			}

			UpdateDashboard();
		}

		#region Daily statistics
		private void StartRthDay(int etDate)
		{
			if (dayHasBars)
			{
				double tr = double.IsNaN(atrPrevClose) ? dayHigh - dayLow
					: Math.Max(dayHigh - dayLow, Math.Max(Math.Abs(dayHigh - atrPrevClose), Math.Abs(dayLow - atrPrevClose)));
				atrCount++;
				int k = Math.Min(atrCount, AtrLength);
				atrDaily		= double.IsNaN(atrDaily) ? tr : ((k - 1) * atrDaily + tr) / k;
				atrPrevClose	= dayClose;
				prevRthClose	= dayClose;
				rthCloses.Add(dayClose);
				while (rthCloses.Count > TrendSmaLength)
					rthCloses.RemoveAt(0);
			}

			rthDay			= etDate;
			dayHasBars		= false;
			orBars			= 0;
			orReady			= false;
			vwapPv			= 0;
			vwapVol			= 0;
			vwap			= 0;
			todayAtr		= atrDaily;
			trendDir		= 0;
			dayLossStreak	= 0;
			dayHalted		= false;
			orbArmed		= false;
			orbTrades		= 0;
			vwpArmed		= false;
			vwpDone			= false;

			int minCloses = Math.Max(2, (int)Math.Ceiling(TrendSmaLength * 0.75));
			if (rthCloses.Count >= minCloses && !double.IsNaN(prevRthClose))
			{
				double sum = 0;
				for (int i = 0; i < rthCloses.Count; i++)
					sum += rthCloses[i];
				double sma = sum / rthCloses.Count;
				trendDir = prevRthClose > sma ? 1 : (prevRthClose < sma ? -1 : 0);
			}

			dayTradable = trendDir != 0 && !double.IsNaN(todayAtr) && atrCount >= AtrLength;
			if (!dayTradable)
				dayStatus = atrCount < AtrLength ? string.Format("warming up ({0}/{1} RTH days)", atrCount, AtrLength) : "no trade: trend undefined";
			else
				dayStatus = string.Format("bias {0} - building range", trendDir == 1 ? "LONG" : "SHORT");
		}

		private void OnRangeComplete()
		{
			orReady		= true;
			orbArmed	= true;
			if (ShowVisuals)
				Draw.Rectangle(this, "TD_" + rthDay + "_box", false, RangeMinutes - 1, orHigh, 0, orLow, Brushes.SlateGray, Brushes.SlateGray, 10);
		}
		#endregion

		#region Module 1 - ORB
		private void ManageOrb(int openMin, int closeMin)
		{
			if (!UseOrb)
				return;

			bool windowOpen = closeMin < HhmmToMinutes(OrbLastEntryTime);

			if (IsOrderWorking(orbOrder) && (!windowOpen || !CanOpenNew()))
			{
				CancelOrder(orbOrder);
				return;
			}

			// Re-arm after the previous ORB trade once price closes back inside the range.
			if (!orbArmed && !orbInTrade && !IsOrderWorking(orbOrder) && orbTrades > 0 && orbTrades < OrbMaxTradesPerDay
				&& Close[0] < orHigh && Close[0] > orLow)
			{
				orbArmed = true;	// the stop order goes out now and is live from the next bar, like the research model
			}

			if (!orbArmed || orbInTrade || IsOrderWorking(orbOrder) || orbTrades >= OrbMaxTradesPerDay || !windowOpen || !CanOpenNew())
				return;

			int d = trendDir;
			double entry	= d == 1 ? orHigh + TickSize : orLow - TickSize;
			double oppStop	= d == 1 ? orLow - TickSize : orHigh + TickSize;
			double dist		= Math.Min(Math.Abs(entry - oppStop), OrbStopCapAtr * todayAtr);
			int stopTicks	= Math.Max(2, (int)Math.Round(dist / TickSize));
			int tgtTicks	= Math.Max(1, (int)Math.Round(stopTicks * OrbTargetR));
			int qty			= ComputeQuantity(stopTicks);
			if (qty < 1)
			{
				dayStatus = string.Format("ORB skip: 1 lot risks ${0:0}", RiskPerContract(stopTicks));
				orbArmed = false;
				return;
			}

			string sig = d == 1 ? OrbLong : OrbShort;
			SetStopLoss(sig, CalculationMode.Ticks, stopTicks, false);
			SetProfitTarget(sig, CalculationMode.Ticks, tgtTicks);

			bool through = d == 1 ? GetCurrentAsk() >= entry : GetCurrentBid() <= entry;
			if (d == 1) { if (through) EnterLong(qty, sig); else EnterLongStopMarket(0, true, qty, entry, sig); }
			else { if (through) EnterShort(qty, sig); else EnterShortStopMarket(0, true, qty, entry, sig); }

			orbArmed	= false;
			orbRiskUsd	= qty * RiskPerContract(stopTicks);
			dayStatus	= string.Format("ORB {0} STOP x{1} @ {2}", d == 1 ? "BUY" : "SELL", qty, Fmt(entry));
			Log(string.Format("ORB {0} x{1} @ {2} | range {3}-{4} | SL {5}t | TP {6}t | risk ${7:0.00}",
				d == 1 ? "BUY STOP" : "SELL STOP", qty, Fmt(entry), Fmt(orLow), Fmt(orHigh), stopTicks, tgtTicks, orbRiskUsd));

			if (ShowVisuals)
			{
				DateTime end = Time[0].AddMinutes(120);
				double sl = d == 1 ? entry - stopTicks * TickSize : entry + stopTicks * TickSize;
				double tp = d == 1 ? entry + tgtTicks * TickSize : entry - tgtTicks * TickSize;
				string tag = "TD_" + rthDay + "_orb" + orbTrades;
				Draw.Line(this, tag + "_e", false, Time[0], entry, end, entry, Brushes.White, DashStyleHelper.Dash, 2);
				Draw.Line(this, tag + "_s", false, Time[0], sl, end, sl, Brushes.Red, DashStyleHelper.Dash, 1);
				Draw.Line(this, tag + "_t", false, Time[0], tp, end, tp, Brushes.LimeGreen, DashStyleHelper.Dash, 1);
			}
		}
		#endregion

		#region Module 2 - VWAP pullback
		private void ManageVwap(int openMin, int closeMin)
		{
			if (!UseVwap)
				return;

			bool windowOpen = closeMin < HhmmToMinutes(VwapLastEntryTime);

			if (IsOrderWorking(vwpOrder))
			{
				if (!windowOpen || !CanOpenNew())
				{
					CancelOrder(vwpOrder);
					vwpArmed = false;
					vwpDone	 = true;
					return;
				}
				// Follow VWAP: the resting limit always sits at the latest VWAP.
				double follow = Instrument.MasterInstrument.RoundToTickSize(vwap);
				if (Math.Abs(follow - vwpOrder.LimitPrice) >= TickSize / 2.0)
					ChangeOrder(vwpOrder, vwpOrder.Quantity, follow, 0);
				return;
			}

			if (vwpDone || vwpInTrade || vwpArmed || !windowOpen || !CanOpenNew() || openMin < RthOpen + RangeMinutes)
				return;

			int d = trendDir;
			bool extended = d == 1
				? Close[0] > orHigh && Close[0] >= vwap + VwapExtensionAtr * todayAtr
				: Close[0] < orLow && Close[0] <= vwap - VwapExtensionAtr * todayAtr;
			if (!extended)
				return;

			int stopTicks	= Math.Max(2, (int)Math.Round(VwapStopAtr * todayAtr / TickSize));
			int tgtTicks	= Math.Max(1, (int)Math.Round(stopTicks * VwapTargetR));
			int qty			= ComputeQuantity(stopTicks);
			if (qty < 1)
			{
				dayStatus	= string.Format("VWAP skip: 1 lot risks ${0:0}", RiskPerContract(stopTicks));
				vwpDone		= true;
				return;
			}

			string sig	= d == 1 ? VwpLong : VwpShort;
			double px	= Instrument.MasterInstrument.RoundToTickSize(vwap);
			SetStopLoss(sig, CalculationMode.Ticks, stopTicks, false);
			SetProfitTarget(sig, CalculationMode.Ticks, tgtTicks);
			if (d == 1)
				EnterLongLimit(0, true, qty, px, sig);
			else
				EnterShortLimit(0, true, qty, px, sig);

			vwpArmed	= true;
			vwpRiskUsd	= qty * RiskPerContract(stopTicks);
			Log(string.Format("VWAP {0} LIMIT x{1} @ {2} (follows VWAP) | SL {3}t | TP {4}t | risk ${5:0.00}",
				d == 1 ? "BUY" : "SELL", qty, Fmt(px), stopTicks, tgtTicks, vwpRiskUsd));
		}
		#endregion

		#region Orders, sizing, accounting
		private bool CanOpenNew()
		{
			if (accountHalted || dayHalted)
				return false;
			if (DailyLossLimit > 0 && dailyPnl <= -DailyLossLimit)
				return false;
			return true;
		}

		private double RiskPerContract(int stopTicks)
		{
			double tickValue = Instrument.MasterInstrument.PointValue * TickSize;
			return (stopTicks + StopSlippageTicks) * tickValue + CommissionPerContract;
		}

		private int ComputeQuantity(int stopTicks)
		{
			double perContract = RiskPerContract(stopTicks);
			int qty;
			if (SizingMode == ORTSizingMode.FixedContracts)
				qty = perContract <= OneContractMaxRisk ? FixedContracts : 0;
			else
			{
				qty = (int)Math.Floor(RiskPerTrade / perContract);
				if (qty < 1 && perContract <= OneContractMaxRisk)
					qty = 1;
			}

			if (DailyLossLimit > 0)
				qty = Math.Min(qty, (int)Math.Floor((DailyLossLimit + dailyPnl) / perContract));
			if (isLive && MaxTrailingDrawdown > 0)
				qty = Math.Min(qty, (int)Math.Floor(((MaxTrailingDrawdown - DrawdownBuffer) - (livePeak - liveEquity)) / perContract));
			return Math.Min(qty, MaxContracts);
		}

		private void FlattenAll(string reason)
		{
			if (IsOrderWorking(orbOrder))
				CancelOrder(orbOrder);
			if (IsOrderWorking(vwpOrder))
				CancelOrder(vwpOrder);
			if (Position.MarketPosition == MarketPosition.Flat || flattenBar == CurrentBar)
				return;
			flattenBar = CurrentBar;
			if (Position.MarketPosition == MarketPosition.Long)
				ExitLong();
			else
				ExitShort();
			Log("FLATTEN: " + reason);
		}

		private static bool IsOrderWorking(Order order)
		{
			if (order == null)
				return false;
			OrderState s = order.OrderState;
			return s != OrderState.Filled && s != OrderState.Cancelled && s != OrderState.Rejected && s != OrderState.Unknown;
		}

		private static bool IsOrb(string name)
		{
			return name == OrbLong || name == OrbShort;
		}

		private static bool IsVwp(string name)
		{
			return name == VwpLong || name == VwpShort;
		}

		protected override void OnOrderUpdate(Order order, double limitPrice, double stopPrice, int quantity, int filled, double averageFillPrice,
			OrderState orderState, DateTime time, ErrorCode error, string nativeError)
		{
			if (IsOrb(order.Name))
				orbOrder = order;
			else if (IsVwp(order.Name))
				vwpOrder = order;
			else
				return;

			if (orderState == OrderState.Rejected)
				Print(string.Format("NQ Trend Day | {0} REJECTED: {1} {2}", order.Name, error, nativeError));
		}

		protected override void OnExecutionUpdate(Execution execution, string executionId, double price, int quantity,
			MarketPosition marketPosition, string orderId, DateTime time)
		{
			if (execution.Order == null)
				return;
			string name = execution.Order.Name;
			string from = execution.Order.FromEntrySignal;

			if (IsOrb(name))
			{
				if (!orbInTrade)
				{
					orbInTrade = true;
					orbTrades++;
					Log(string.Format("ORB FILLED {0} @ {1}", name, Fmt(price)));
					DrawFill(name == OrbLong, time, price);
				}
				orbQtyOpen += quantity;
			}
			else if (IsVwp(name))
			{
				if (!vwpInTrade)
				{
					vwpInTrade	= true;
					vwpDone		= true;
					vwpArmed	= false;
					Log(string.Format("VWAP FILLED {0} @ {1}", name, Fmt(price)));
					DrawFill(name == VwpLong, time, price);
				}
				vwpQtyOpen += quantity;
			}
			else if (IsOrb(from))
				orbQtyOpen = Math.Max(0, orbQtyOpen - quantity);
			else if (IsVwp(from))
				vwpQtyOpen = Math.Max(0, vwpQtyOpen - quantity);
		}

		private void DrawFill(bool isLong, DateTime time, double price)
		{
			if (!ShowVisuals)
				return;
			string tag = "TD_fill_" + time.Ticks;
			if (isLong)
				Draw.ArrowUp(this, tag, false, time, price - 4 * TickSize, Brushes.LimeGreen);
			else
				Draw.ArrowDown(this, tag, false, time, price + 4 * TickSize, Brushes.OrangeRed);
		}

		private void ProcessClosedTrades()
		{
			int count = SystemPerformance.AllTrades.Count;
			for (int i = tradesProcessed; i < count; i++)
			{
				Trade tr = SystemPerformance.AllTrades[i];
				string entryName = tr.Entry != null && tr.Entry.Order != null ? tr.Entry.Order.Name : string.Empty;
				if (IsVwp(entryName))
					vwpPnlAcc += tr.ProfitCurrency;
				else
					orbPnlAcc += tr.ProfitCurrency;
			}
			tradesProcessed = count;

			bool flat = Position.MarketPosition == MarketPosition.Flat;
			if (orbInTrade && (orbQtyOpen <= 0 || flat))
			{
				FinishTrade("ORB", orbPnlAcc, orbRiskUsd);
				orbInTrade = false; orbQtyOpen = 0; orbPnlAcc = 0;
			}
			if (vwpInTrade && (vwpQtyOpen <= 0 || flat))
			{
				FinishTrade("VWAP", vwpPnlAcc, vwpRiskUsd);
				vwpInTrade = false; vwpQtyOpen = 0; vwpPnlAcc = 0;
			}
		}

		private void FinishTrade(string module, double pnl, double riskUsd)
		{
			double r = riskUsd > 0 ? pnl / riskUsd : 0;
			totalTrades++;
			netPnl		+= pnl;
			dailyPnl	+= pnl;
			totalR		+= r;
			if (pnl > 0)
			{
				totalWins++; grossWin += pnl; dayLossStreak = 0;
			}
			else
			{
				totalLosses++; grossLoss += -pnl; dayLossStreak++;
				if (MaxConsecLossesPerDay > 0 && dayLossStreak >= MaxConsecLossesPerDay && !dayHalted)
				{
					dayHalted = true;
					if (IsOrderWorking(orbOrder)) CancelOrder(orbOrder);
					if (IsOrderWorking(vwpOrder)) CancelOrder(vwpOrder);
					Log("DAY STOP after " + dayLossStreak + " consecutive losses");
				}
			}
			dayStatus = string.Format("{0} {1} ${2:0.00} ({3:+0.00;-0.00}R)", module, pnl > 0 ? "WIN" : "LOSS", pnl, r);
			Log(string.Format("CLOSED {0} {1} ${2:0.00} ({3:+0.00;-0.00}R) | day ${4:0.00} | net ${5:0.00}", module, pnl > 0 ? "WIN " : "LOSS", pnl, r, dailyPnl, netPnl));
		}

		private void RunGuards()
		{
			if (!isLive)
				return;
			double unreal = Position.MarketPosition == MarketPosition.Flat ? 0 : Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Close[0]);
			liveEquity	= (netPnl - liveBaseline) + unreal;
			livePeak	= Math.Max(livePeak, liveEquity);

			if (!accountHalted && MaxTrailingDrawdown > 0 && livePeak - liveEquity >= MaxTrailingDrawdown - DrawdownBuffer)
			{
				accountHalted		= true;
				accountHaltReason	= "trailing drawdown guard";
				Print("NQ Trend Day | ACCOUNT HALTED: " + accountHaltReason);
				FlattenAll(accountHaltReason);
			}
			else if (!accountHalted && AccountProfitTarget > 0 && netPnl - liveBaseline >= AccountProfitTarget)
			{
				accountHalted		= true;
				accountHaltReason	= "account profit target reached";
				Print("NQ Trend Day | " + accountHaltReason + " - no new trades.");
			}
		}
		#endregion

		#region Helpers
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

		private string Fmt(double price)
		{
			return Instrument.MasterInstrument.FormatPrice(price);
		}

		private void Log(string message)
		{
			if (!PrintTradeLog)
				return;
			Print(string.Format("{0} | TD | {1}", Time[0].ToString("yyyy-MM-dd HH:mm", CultureInfo.InvariantCulture), message));
		}

		private void PrintSummary(string title)
		{
			double pf = grossLoss > 0 ? grossWin / grossLoss : 0;
			Print("============ NQ Trend Day v2 | " + title + " ============");
			Print(string.Format("Trades {0} | {1} W / {2} L | WR {3:0.0}% | PF {4:0.00} | Net ${5:0.00} | {6:+0.00;-0.00}R",
				totalTrades, totalWins, totalLosses, totalTrades > 0 ? 100.0 * totalWins / totalTrades : 0, pf, netPnl, totalR));
		}

		private void UpdateDashboard()
		{
			if (!ShowDashboard || (State == State.Historical && CurrentBar < Count - 2))
				return;
			double pf = grossLoss > 0 ? grossWin / grossLoss : 0;
			StringBuilder sb = new StringBuilder();
			sb.AppendLine("NQ TREND DAY v2  |  ORB + VWAP pullback");
			sb.AppendLine(string.Format("Bias   : {0}   ATRd {1:0.0}", trendDir == 1 ? "LONG only" : trendDir == -1 ? "SHORT only" : "-", todayAtr));
			sb.AppendLine(orReady ? string.Format("Range  : {0} - {1}   VWAP {2}", Fmt(orLow), Fmt(orHigh), Fmt(vwap)) : "Range  : building...");
			sb.AppendLine(string.Format("ORB    : {0} trade(s) today{1}", orbTrades, IsOrderWorking(orbOrder) ? " | stop order working" : orbInTrade ? " | IN TRADE" : ""));
			sb.AppendLine(string.Format("VWAP   : {0}", vwpInTrade ? "IN TRADE" : IsOrderWorking(vwpOrder) ? "limit working at VWAP" : vwpDone ? "done" : "waiting for extension"));
			sb.AppendLine("Today  : " + dayStatus + (dayHalted ? "  [DAY STOP]" : ""));
			sb.AppendLine(string.Format("Stats  : {0} tr | WR {1:0.0}% | PF {2:0.00} | ${3:0.00} | {4:+0.0;-0.0}R",
				totalTrades, totalTrades > 0 ? 100.0 * totalWins / totalTrades : 0, pf, netPnl, totalR));
			if (isLive)
				sb.AppendLine(string.Format("Live DD: ${0:0.00} / ${1:0}{2}", livePeak - liveEquity, MaxTrailingDrawdown, accountHalted ? "  HALTED: " + accountHaltReason : ""));
			Draw.TextFixed(this, "TD_Dashboard", sb.ToString(), TextPosition.TopRight, Brushes.White, dashFont, Brushes.Transparent, Brushes.Black, 75);
		}
		#endregion

		#region Properties
		[NinjaScriptProperty]
		[Range(2, 200)]
		[Display(Name = "Trend SMA length (RTH closes)", Order = 1, GroupName = "01. Daily bias")]
		public int TrendSmaLength { get; set; }

		[NinjaScriptProperty]
		[Range(2, 100)]
		[Display(Name = "Daily ATR length", Order = 2, GroupName = "01. Daily bias")]
		public int AtrLength { get; set; }

		[NinjaScriptProperty]
		[Range(5, 120)]
		[Display(Name = "Opening range (minutes)", Order = 3, GroupName = "01. Daily bias")]
		public int RangeMinutes { get; set; }

		[NinjaScriptProperty]
		[Range(0, 1659)]
		[Display(Name = "Flatten time (ET, HHmm)", Order = 4, GroupName = "01. Daily bias")]
		public int FlattenTime { get; set; }

		[NinjaScriptProperty]
		[Range(0, 10)]
		[Display(Name = "Stop day after N consecutive losses (0 = off)", Order = 5, GroupName = "01. Daily bias")]
		public int MaxConsecLossesPerDay { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Enable ORB module", Order = 10, GroupName = "02. Module 1 - ORB")]
		public bool UseOrb { get; set; }

		[NinjaScriptProperty]
		[Range(1000, 1559)]
		[Display(Name = "ORB last entry (ET, HHmm)", Order = 11, GroupName = "02. Module 1 - ORB")]
		public int OrbLastEntryTime { get; set; }

		[NinjaScriptProperty]
		[Range(0.02, 2.0)]
		[Display(Name = "ORB stop cap (x daily ATR)", Order = 12, GroupName = "02. Module 1 - ORB")]
		public double OrbStopCapAtr { get; set; }

		[NinjaScriptProperty]
		[Range(0.5, 10.0)]
		[Display(Name = "ORB target (R)", Order = 13, GroupName = "02. Module 1 - ORB")]
		public double OrbTargetR { get; set; }

		[NinjaScriptProperty]
		[Range(1, 5)]
		[Display(Name = "ORB max trades per day", Order = 14, GroupName = "02. Module 1 - ORB")]
		public int OrbMaxTradesPerDay { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Enable VWAP pullback module", Order = 20, GroupName = "03. Module 2 - VWAP pullback")]
		public bool UseVwap { get; set; }

		[NinjaScriptProperty]
		[Range(0.0, 2.0)]
		[Display(Name = "Extension beyond VWAP (x daily ATR)", Order = 21, GroupName = "03. Module 2 - VWAP pullback")]
		public double VwapExtensionAtr { get; set; }

		[NinjaScriptProperty]
		[Range(0.02, 2.0)]
		[Display(Name = "VWAP stop (x daily ATR)", Order = 22, GroupName = "03. Module 2 - VWAP pullback")]
		public double VwapStopAtr { get; set; }

		[NinjaScriptProperty]
		[Range(0.5, 10.0)]
		[Display(Name = "VWAP target (R)", Order = 23, GroupName = "03. Module 2 - VWAP pullback")]
		public double VwapTargetR { get; set; }

		[NinjaScriptProperty]
		[Range(1000, 1559)]
		[Display(Name = "VWAP last entry (ET, HHmm)", Order = 24, GroupName = "03. Module 2 - VWAP pullback")]
		public int VwapLastEntryTime { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Sizing mode", Order = 30, GroupName = "04. Position sizing")]
		public ORTSizingMode SizingMode { get; set; }

		[NinjaScriptProperty]
		[Range(1.0, double.MaxValue)]
		[Display(Name = "Risk per trade ($)", Order = 31, GroupName = "04. Position sizing")]
		public double RiskPerTrade { get; set; }

		[NinjaScriptProperty]
		[Range(0.0, double.MaxValue)]
		[Display(Name = "1-contract max risk ($)", Description = "If one contract risks more than 'Risk per trade', still trade 1 lot when its risk is at most this value. Set equal to Risk per trade for strict sizing.", Order = 32, GroupName = "04. Position sizing")]
		public double OneContractMaxRisk { get; set; }

		[NinjaScriptProperty]
		[Range(1, 100)]
		[Display(Name = "Fixed contracts", Order = 33, GroupName = "04. Position sizing")]
		public int FixedContracts { get; set; }

		[NinjaScriptProperty]
		[Range(1, 100)]
		[Display(Name = "Max contracts", Order = 34, GroupName = "04. Position sizing")]
		public int MaxContracts { get; set; }

		[NinjaScriptProperty]
		[Range(0.0, double.MaxValue)]
		[Display(Name = "Commission per contract, round turn ($)", Order = 35, GroupName = "04. Position sizing")]
		public double CommissionPerContract { get; set; }

		[NinjaScriptProperty]
		[Range(0, 100)]
		[Display(Name = "Stop slippage allowance (ticks)", Order = 36, GroupName = "04. Position sizing")]
		public int StopSlippageTicks { get; set; }

		[NinjaScriptProperty]
		[Range(0.0, double.MaxValue)]
		[Display(Name = "Daily loss limit ($, 0 = off)", Order = 40, GroupName = "05. Prop-firm guards")]
		public double DailyLossLimit { get; set; }

		[NinjaScriptProperty]
		[Range(0.0, double.MaxValue)]
		[Display(Name = "Max trailing drawdown ($, live, 0 = off)", Order = 41, GroupName = "05. Prop-firm guards")]
		public double MaxTrailingDrawdown { get; set; }

		[NinjaScriptProperty]
		[Range(0.0, double.MaxValue)]
		[Display(Name = "Drawdown safety buffer ($)", Order = 42, GroupName = "05. Prop-firm guards")]
		public double DrawdownBuffer { get; set; }

		[NinjaScriptProperty]
		[Range(0.0, double.MaxValue)]
		[Display(Name = "Account profit target ($, live, 0 = off)", Order = 43, GroupName = "05. Prop-firm guards")]
		public double AccountProfitTarget { get; set; }

		[Display(Name = "Show range & levels", Order = 50, GroupName = "06. Display")]
		public bool ShowVisuals { get; set; }

		[Display(Name = "Show dashboard", Order = 51, GroupName = "06. Display")]
		public bool ShowDashboard { get; set; }

		[Display(Name = "Print trade log", Order = 52, GroupName = "06. Display")]
		public bool PrintTradeLog { get; set; }
		#endregion
	}
}
