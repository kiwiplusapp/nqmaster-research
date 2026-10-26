//
// IFVG Sniper Strategy for NinjaTrader 8
// Port of "IFVG Sniper Entry Engine [trade_w_samet] v3" (TradingView Pine v6)
// plus automated execution (entry / SL / TP / sizing) and a prop-firm risk layer.
//
// Built for MNQ on a 1-minute chart. Designed for Calculate.OnBarClose.
//
#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Globalization;
using System.Text;
using System.Windows.Media;
using System.Xml.Serialization;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Tools;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.DrawingTools;
using NinjaTrader.NinjaScript.Indicators;
#endregion

//This namespace holds strategies in this folder and is required. Do not change it.
namespace NinjaTrader.NinjaScript.Strategies
{
	public enum IFVGFilterMode { Off, Loose, Balanced, Strict, Custom, Adaptive }
	public enum IFVGLinePrice { BrokenBoundary, ConfirmationClose, Midpoint }
	public enum IFVGOrderMode { LimitAtIfvgLine, MarketNextBar }
	public enum IFVGTradeDirection { Both, LongOnly, ShortOnly }

	public class IFVGSniperStrategy : Strategy
	{
		private const string SigLong		= "IFVG L";
		private const string SigShort		= "IFVG S";
		private const string SigFlat		= "IFVG Flat";
		private const int SessionReopenEt	= 18 * 60;	// CME Globex reopens 18:00 ET

		#region Internal types
		private class RawFvg
		{
			public double	Top;
			public double	Bot;
			public int		Dir;
			public int		Age;
			public double	GapAtr;
			public double	BodyRatio;
			public double	RangeAtr;
			public DateTime	OriginTime;
		}

		private class VisibleIfvg
		{
			public string	Tag;
			public double	Top;
			public double	Bot;
			public int		Dir;
		}
		#endregion

		#region Fields
		// Indicators
		private ATR		atr;
		private EMA		trendEma;
		private SMA		volumeSma;
		private MAX		highestHigh;
		private MIN		lowestLow;

		// Hidden FVG memory (mirrors the Pine arrays)
		private List<RawFvg>		rawFvgs;
		private List<double>		recentGapAtr;
		private List<VisibleIfvg>	visibleIfvgs;
		private Queue<string>		tradeDrawTags;
		private int					drawId;
		private SimpleFont			labelFont;
		private SimpleFont			dashFont;

		// Time
		private TimeZoneInfo	etZone;
		private List<int>		newsMinutes;

		// Orders / position
		private Order	entryOrder;
		private int		pendingDir;
		private int		pendingSubmitBar	= -1;
		private double	pendingTpPrice;
		private int		activeStopTicks;
		private int		activeQty;
		private double	activeRiskUsd;
		private bool	beMoved;
		private bool	entryCounted;
		private int		flattenBar			= -1;

		// Accounting (real fills)
		private int		tradesProcessed;
		private int		totalTrades;
		private int		totalWins;
		private int		totalLosses;
		private double	grossWin;
		private double	grossLoss;
		private double	netPnl;
		private double	totalR;
		private int		lossStreak;
		private int		cooldownUntilBar	= -1;
		private double	dailyPnl;
		private int		dailyTrades;
		private int		dailyWins;
		private int		dailyLosses;
		private int		dailyLossStreak;
		private bool	dailyHalted;
		private string	dailyHaltReason		= string.Empty;
		private bool	accountHalted;
		private string	accountHaltReason	= string.Empty;
		private bool	isLive;
		private double	liveBaseline;
		private double	livePeak;
		private double	liveEquity;

		// Diagnostics
		private int		filteredIfvg;
		private int		gatedSignals;
		private int		blockedSignals;
		private int		skippedRisk;
		private string	lastSkipReason		= "-";

		// Virtual Pine model (exact replica of the indicator's trade simulation)
		private bool	vActive;
		private int		vDir;
		private int		vBar;
		private double	vEntry;
		private double	vSl;
		private double	vTp;
		private int		vWins;
		private int		vLosses;
		private int		vLossStreak;
		private double	vTotalR;
		private int		vCooldownUntilBar	= -1;

		private bool	summaryPrinted;
		#endregion

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Description									= "IFVG Sniper Entry Engine v3 (trade_w_samet) ported to NinjaTrader 8 with automated execution, ATR-based SL/TP, fixed-dollar position sizing and a prop-firm risk layer.";
				Name										= "IFVGSniperStrategy";
				Calculate									= Calculate.OnBarClose;
				EntriesPerDirection							= 1;
				EntryHandling								= EntryHandling.AllEntries;
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

				// 01. IFVG Engine
				MaxHiddenFvg			= 500;
				MaxFvgAge				= 500;
				MinGapTicks				= 0;
				LinePrice				= IFVGLinePrice.Midpoint;

				// 02. IFVG Filter
				FilterMode				= IFVGFilterMode.Custom;
				CustomMinGapAtr			= 0.25;
				CustomMinBodyRatio		= 0.50;
				CustomMinRangeAtr		= 0.65;
				CustomBreakAtr			= 0.05;
				AdaptiveGapMultiplier	= 1.5;
				AdaptiveLookback		= 50;

				// 03. Entry & Exit
				OrderMode				= IFVGOrderMode.LimitAtIfvgLine;
				LimitExpiryBars			= 15;
				CancelIfTargetTouched	= true;
				AtrLength				= 14;
				SlAtrMultiplier			= 1.5;
				TargetRR				= 1.0;
				MinStopTicks			= 20;
				MaxStopTicks			= 200;
				UseBreakeven			= false;
				BreakevenTriggerR		= 0.75;
				BreakevenOffsetTicks	= 2;
				TradeDirection			= IFVGTradeDirection.Both;

				// 04. Signal Quality Filters
				UseTrendFilter			= false;
				TrendTimeframeMinutes	= 15;
				TrendEmaLength			= 200;
				UseVolatilityGuard		= true;
				MaxRangeAtrGuard		= 3.0;
				UseVolumeFilter			= false;
				VolumeMaLength			= 20;
				VolumeMultiplier		= 1.2;
				UseRoomFilter			= true;
				RoomLookback			= 20;
				RoomBufferAtr			= 0.0;
				UsePathFilter			= true;
				UseLossCooldown			= false;
				CooldownLossStreak		= 3;
				CooldownBars			= 20;

				// 05. Sessions (Eastern Time)
				UseSessionFilter		= true;
				Session1Start			= 930;
				Session1End				= 1530;
				UseSession2				= false;
				Session2Start			= 300;
				Session2End				= 600;
				LastEntryTime			= 1530;
				FlattenTime				= 1555;
				UseNewsBlackout			= true;
				NewsTimesEt				= "08:30,10:00,14:00";
				NewsMinutesBefore		= 2;
				NewsMinutesAfter		= 5;

				// 06. Risk & Prop Firm
				RiskPerTrade			= 100;
				MaxContracts			= 15;
				CommissionPerContract	= 1.00;
				StopSlippageTicks		= 1;
				DailyLossLimit			= 300;
				DailyProfitTarget		= 400;
				MaxTradesPerDay			= 8;
				MaxConsecLossesPerDay	= 3;
				MaxTrailingDrawdown		= 2000;
				DrawdownBuffer			= 200;
				AccountProfitTarget		= 0;

				// 07. Display
				ShowVisuals				= true;
				ShowDashboard			= true;
				PrintTradeLog			= true;
				MaxVisibleIfvg			= 20;
				IfvgLengthBars			= 50;
			}
			else if (State == State.Configure)
			{
				if (UseTrendFilter)
					AddDataSeries(BarsPeriodType.Minute, TrendTimeframeMinutes);
			}
			else if (State == State.DataLoaded)
			{
				atr			= ATR(AtrLength);
				volumeSma	= SMA(Volume, VolumeMaLength);
				highestHigh	= MAX(High, RoomLookback);
				lowestLow	= MIN(Low, RoomLookback);

				if (UseTrendFilter)
					trendEma = EMA(BarsArray[1], TrendEmaLength);

				rawFvgs			= new List<RawFvg>();
				recentGapAtr	= new List<double>();
				visibleIfvgs	= new List<VisibleIfvg>();
				tradeDrawTags	= new Queue<string>();
				labelFont		= new SimpleFont("Arial", 11);
				dashFont		= new SimpleFont("Consolas", 12);

				try { etZone = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time"); }
				catch { etZone = null; }

				newsMinutes = ParseTimes(NewsTimesEt);
			}
			else if (State == State.Realtime)
			{
				if (entryOrder != null)
					entryOrder = GetRealtimeOrder(entryOrder);

				// The prop firm tracks the real account from here on, not the historical simulation.
				isLive				= true;
				liveBaseline		= netPnl;
				livePeak			= 0;
				liveEquity			= 0;
				accountHalted		= false;
				accountHaltReason	= string.Empty;
				ResetDaily();

				PrintSummary("Historical warm-up complete");
				Print("IFVG Sniper | LIVE on " + Instrument.FullName + " | account " + Account.Name);
			}
			else if (State == State.Terminated)
			{
				if (rawFvgs != null && !summaryPrinted)
				{
					summaryPrinted = true;
					PrintSummary("Terminated");
				}
			}
		}

		public override string DisplayName
		{
			get { return "IFVG Sniper"; }
		}

		protected override void OnBarUpdate()
		{
			if (BarsInProgress != 0 || CurrentBar < 3)
				return;

			int etMin = EtMinutes(Time[0]);

			// Realized results first so today's P&L is attributed before any session reset.
			ProcessClosedTrades();

			if (Bars.IsFirstBarOfSession)
				ResetDaily();

			double safeAtr = atr[0] > 0 ? atr[0] : TickSize;

			RunRiskGuards(etMin);
			ManagePendingEntry(etMin);
			ManageOpenPosition();

			RunIfvgEngine(safeAtr, etMin);

			UpdateVirtualTrade();
			UpdateIfvgInvalidation();
			UpdateDashboard();
		}

		#region IFVG engine (Pine parity)
		private void RunIfvgEngine(double safeAtr, int etMin)
		{
			// Hidden FVG age update + expiry.
			for (int i = rawFvgs.Count - 1; i >= 0; i--)
			{
				rawFvgs[i].Age++;
				if (rawFvgs[i].Age > MaxFvgAge)
					rawFvgs.RemoveAt(i);
			}

			double minGap		= MinGapTicks * TickSize;
			double candleRange	= Math.Max(High[0] - Low[0], TickSize);
			double bodyRatio	= Math.Abs(Close[0] - Open[0]) / candleRange;
			double rangeAtr		= candleRange / safeAtr;

			if (Low[0] > High[2] && (Low[0] - High[2]) >= minGap)
			{
				double gapAtr = (Low[0] - High[2]) / safeAtr;
				rawFvgs.Add(new RawFvg { Top = Low[0], Bot = High[2], Dir = 1, Age = 0, GapAtr = gapAtr, BodyRatio = bodyRatio, RangeAtr = rangeAtr, OriginTime = Time[1] });
				recentGapAtr.Add(gapAtr);
			}

			if (High[0] < Low[2] && (Low[2] - High[0]) >= minGap)
			{
				double gapAtr = (Low[2] - High[0]) / safeAtr;
				rawFvgs.Add(new RawFvg { Top = Low[2], Bot = High[0], Dir = -1, Age = 0, GapAtr = gapAtr, BodyRatio = bodyRatio, RangeAtr = rangeAtr, OriginTime = Time[1] });
				recentGapAtr.Add(gapAtr);
			}

			while (recentGapAtr.Count > AdaptiveLookback)
				recentGapAtr.RemoveAt(0);

			while (rawFvgs.Count > MaxHiddenFvg)
				rawFvgs.RemoveAt(0);

			// Inversion: newest first, only one per bar (same as the Pine loop + break).
			double breakBuffer	= safeAtr * BreakBufferAtr();
			RawFvg inverted		= null;
			int invDir			= 0;

			for (int i = rawFvgs.Count - 1; i >= 0; i--)
			{
				RawFvg f		= rawFvgs[i];
				bool bullInv	= f.Dir == -1 && Close[0] > f.Top + breakBuffer;
				bool bearInv	= f.Dir == 1 && Close[0] < f.Bot - breakBuffer;

				if (bullInv || bearInv)
				{
					if (QualityPass(f))
					{
						inverted	= f;
						invDir		= bullInv ? 1 : -1;
					}
					else
						filteredIfvg++;

					rawFvgs.RemoveAt(i);
					break;
				}
			}

			if (inverted == null)
				return;

			double linePrice = LinePriceFor(inverted.Top, inverted.Bot, Close[0], invDir);
			AddVisibleIfvg(inverted, invDir, linePrice);

			// Trade model. LimitAtIfvgLine = Pine "IFVG Line" entry, MarketNextBar = Pine "Confirmation Close".
			double refEntry	= OrderMode == IFVGOrderMode.MarketNextBar ? Close[0] : linePrice;
			double risk		= atr[0] * SlAtrMultiplier;
			double sl		= invDir == 1 ? refEntry - risk : refEntry + risk;
			double tp		= invDir == 1 ? refEntry + risk * TargetRR : refEntry - risk * TargetRR;

			string gateReason = PineGateReason(invDir, refEntry, tp, safeAtr, candleRange, etMin);

			// Virtual Pine model uses its own cooldown/streak, exactly like the indicator.
			bool vCooldownOk = !UseLossCooldown || CurrentBar >= vCooldownUntilBar;
			if (!vActive && gateReason == null && vCooldownOk)
			{
				vActive	= true;
				vDir	= invDir;
				vBar	= CurrentBar;
				vEntry	= refEntry;
				vSl		= sl;
				vTp		= tp;
			}

			if (gateReason != null)
			{
				gatedSignals++;
				lastSkipReason = gateReason;
				Log(string.Format("{0} IFVG gated: {1}", invDir == 1 ? "Bull" : "Bear", gateReason));
				return;
			}

			if (Position.MarketPosition != MarketPosition.Flat || IsOrderWorking(entryOrder))
			{
				blockedSignals++;
				return;
			}

			TryEnter(invDir, refEntry, risk, etMin);
		}

		private bool QualityPass(RawFvg f)
		{
			if (FilterMode == IFVGFilterMode.Off)
				return true;

			bool gapOk;
			if (FilterMode == IFVGFilterMode.Adaptive)
			{
				double sum = 0;
				for (int i = 0; i < recentGapAtr.Count; i++)
					sum += recentGapAtr[i];
				double avg = recentGapAtr.Count > 0 ? sum / recentGapAtr.Count : 0.0;
				gapOk = f.GapAtr >= avg * AdaptiveGapMultiplier;
			}
			else
				gapOk = f.GapAtr >= MinGapAtr();

			return gapOk && f.BodyRatio >= MinBodyRatio() && f.RangeAtr >= MinRangeAtr();
		}

		private double MinGapAtr()
		{
			switch (FilterMode)
			{
				case IFVGFilterMode.Off:		return 0.0;
				case IFVGFilterMode.Loose:		return 0.15;
				case IFVGFilterMode.Balanced:	return 0.25;
				case IFVGFilterMode.Strict:		return 0.40;
				default:						return CustomMinGapAtr;
			}
		}

		private double MinBodyRatio()
		{
			switch (FilterMode)
			{
				case IFVGFilterMode.Off:		return 0.0;
				case IFVGFilterMode.Loose:		return 0.40;
				case IFVGFilterMode.Balanced:	return 0.50;
				case IFVGFilterMode.Strict:		return 0.60;
				default:						return CustomMinBodyRatio;
			}
		}

		private double MinRangeAtr()
		{
			switch (FilterMode)
			{
				case IFVGFilterMode.Off:		return 0.0;
				case IFVGFilterMode.Loose:		return 0.40;
				case IFVGFilterMode.Balanced:	return 0.60;
				case IFVGFilterMode.Strict:		return 0.85;
				default:						return CustomMinRangeAtr;
			}
		}

		private double BreakBufferAtr()
		{
			switch (FilterMode)
			{
				case IFVGFilterMode.Off:		return 0.0;
				case IFVGFilterMode.Loose:		return 0.00;
				case IFVGFilterMode.Balanced:	return 0.05;
				case IFVGFilterMode.Strict:		return 0.10;
				default:						return CustomBreakAtr;
			}
		}

		private double LinePriceFor(double top, double bot, double confirmClose, int dir)
		{
			if (LinePrice == IFVGLinePrice.ConfirmationClose)
				return confirmClose;
			if (LinePrice == IFVGLinePrice.Midpoint)
				return (top + bot) / 2.0;
			return dir == 1 ? top : bot;
		}

		// Signal-quality gates from the Pine indicator (trend, session, volatility, volume, room, path).
		// Returns null when the signal passes.
		private string PineGateReason(int dir, double entry, double tp, double safeAtr, double candleRange, int etMin)
		{
			if (UseTrendFilter)
			{
				if (trendEma == null || CurrentBars[1] < TrendEmaLength)
					return "trend EMA not ready";
				double ema = trendEma[0];
				if (dir == 1 && !(Close[0] > ema))
					return "below HTF EMA";
				if (dir == -1 && !(Close[0] < ema))
					return "above HTF EMA";
			}

			if (UseSessionFilter && !InTradingSession(etMin))
				return "outside session";

			if (UseVolatilityGuard && candleRange / safeAtr > MaxRangeAtrGuard)
				return "extreme volatility candle";

			if (UseVolumeFilter && Volume[0] < volumeSma[0] * VolumeMultiplier)
				return "low volume";

			if (UseRoomFilter && CurrentBar > RoomLookback)
			{
				double roomBuffer = safeAtr * RoomBufferAtr;
				if (dir == 1)
				{
					double obstacle = highestHigh[1];
					if (!(obstacle >= tp + roomBuffer || obstacle <= entry))
						return "swing high blocks target";
				}
				else
				{
					double obstacle = lowestLow[1];
					if (!(obstacle <= tp - roomBuffer || obstacle >= entry))
						return "swing low blocks target";
				}
			}

			if (UsePathFilter && PathBlockedByFvg(entry, tp, dir))
				return "opposing FVG blocks path";

			return null;
		}

		private bool PathBlockedByFvg(double entry, double tp, int dir)
		{
			for (int i = 0; i < rawFvgs.Count; i++)
			{
				RawFvg f = rawFvgs[i];
				if (dir == 1 && f.Dir == -1 && f.Bot > entry && f.Bot < tp)
					return true;
				if (dir == -1 && f.Dir == 1 && f.Top < entry && f.Top > tp)
					return true;
			}
			return false;
		}
		#endregion

		#region Execution
		private void TryEnter(int dir, double refEntry, double riskPrice, int etMin)
		{
			string reason = RealEntryBlockReason(dir, etMin);
			if (reason != null)
			{
				SkipTrade(reason);
				return;
			}

			int stopTicks = Math.Max(1, (int)Math.Round(riskPrice / TickSize));
			if (stopTicks < MinStopTicks)
				stopTicks = MinStopTicks;
			if (MaxStopTicks > 0 && stopTicks > MaxStopTicks)
			{
				SkipTrade(string.Format("stop {0} ticks > max {1}", stopTicks, MaxStopTicks));
				return;
			}
			int targetTicks = Math.Max(1, (int)Math.Round(stopTicks * TargetRR));

			// Fixed-dollar sizing. Worst case per contract = stop + stop slippage + round-turn commission.
			double tickValue		= Instrument.MasterInstrument.PointValue * TickSize;
			double riskPerContract	= (stopTicks + StopSlippageTicks) * tickValue + CommissionPerContract;
			double budget			= RiskPerTrade;

			// Never let a single stop-out breach the daily loss limit or the trailing drawdown.
			if (DailyLossLimit > 0)
				budget = Math.Min(budget, DailyLossLimit + dailyPnl);
			if (isLive && MaxTrailingDrawdown > 0)
				budget = Math.Min(budget, (MaxTrailingDrawdown - DrawdownBuffer) - (livePeak - liveEquity));

			int qty = riskPerContract > 0 ? (int)Math.Floor(budget / riskPerContract) : 0;
			if (qty > MaxContracts)
				qty = MaxContracts;
			if (qty < 1)
			{
				SkipTrade(string.Format("risk budget ${0:0} < 1 contract (${1:0.00})", budget, riskPerContract));
				return;
			}

			string sig			= dir == 1 ? SigLong : SigShort;
			double entryPrice	= Instrument.MasterInstrument.RoundToTickSize(refEntry);

			// Protective orders are attached to the entry signal and go live the moment it fills.
			SetStopLoss(sig, CalculationMode.Ticks, stopTicks, false);
			SetProfitTarget(sig, CalculationMode.Ticks, targetTicks);

			if (OrderMode == IFVGOrderMode.LimitAtIfvgLine)
			{
				if (dir == 1)
					EnterLongLimit(0, true, qty, entryPrice, sig);
				else
					EnterShortLimit(0, true, qty, entryPrice, sig);
			}
			else
			{
				if (dir == 1)
					EnterLong(qty, sig);
				else
					EnterShort(qty, sig);
			}

			pendingDir			= dir;
			pendingSubmitBar	= CurrentBar;
			pendingTpPrice		= dir == 1 ? entryPrice + targetTicks * TickSize : entryPrice - targetTicks * TickSize;
			activeStopTicks		= stopTicks;
			activeQty			= qty;
			activeRiskUsd		= qty * riskPerContract;
			beMoved				= false;
			entryCounted		= false;

			double slPrice = dir == 1 ? entryPrice - stopTicks * TickSize : entryPrice + stopTicks * TickSize;
			Log(string.Format("{0} {1} x{2} @ {3} | SL {4} ({5}t) | TP {6} ({7}t) | risk ${8:0.00}",
				OrderMode == IFVGOrderMode.LimitAtIfvgLine ? "LIMIT" : "MARKET",
				dir == 1 ? "LONG" : "SHORT", qty, Fmt(entryPrice), Fmt(slPrice), stopTicks, Fmt(pendingTpPrice), targetTicks, activeRiskUsd));

			DrawTradeLevels(dir, entryPrice, slPrice, pendingTpPrice);
		}

		private string RealEntryBlockReason(int dir, int etMin)
		{
			if (accountHalted)
				return "account halted: " + accountHaltReason;
			if (dailyHalted)
				return "day halted: " + dailyHaltReason;
			if (TradeDirection == IFVGTradeDirection.LongOnly && dir == -1)
				return "shorts disabled";
			if (TradeDirection == IFVGTradeDirection.ShortOnly && dir == 1)
				return "longs disabled";
			if (InNoEntryWindow(etMin))
				return "after last entry time";
			if (UseNewsBlackout && InNewsBlackout(etMin))
				return "news blackout";
			if (MaxTradesPerDay > 0 && dailyTrades >= MaxTradesPerDay)
				return "max trades per day";
			if (UseLossCooldown && CurrentBar < cooldownUntilBar)
				return "loss-streak cooldown";
			if (State == State.Historical && CurrentBar < BarsRequiredToTrade)
				return "warming up";
			return null;
		}

		private void SkipTrade(string reason)
		{
			skippedRisk++;
			lastSkipReason = reason;
			Log("Signal skipped: " + reason);
		}

		private void ManagePendingEntry(int etMin)
		{
			if (!IsOrderWorking(entryOrder))
				return;

			string why = null;

			if (accountHalted || dailyHalted)
				why = "halted";
			else if (InNoEntryWindow(etMin) || InFlattenWindow(etMin))
				why = "entry window closed";
			else if (OrderMode == IFVGOrderMode.LimitAtIfvgLine && LimitExpiryBars > 0 && CurrentBar - pendingSubmitBar >= LimitExpiryBars)
				why = "limit expired";
			else if (CancelIfTargetTouched && CurrentBar > pendingSubmitBar
				&& ((pendingDir == 1 && High[0] >= pendingTpPrice) || (pendingDir == -1 && Low[0] <= pendingTpPrice)))
				why = "price reached target before fill";

			if (why != null)
			{
				CancelOrder(entryOrder);
				Log("Cancel pending entry: " + why);
			}
		}

		private void ManageOpenPosition()
		{
			if (!UseBreakeven || beMoved || Position.MarketPosition == MarketPosition.Flat || activeStopTicks <= 0)
				return;

			double avg		= Position.AveragePrice;
			double riskPx	= activeStopTicks * TickSize;

			if (Position.MarketPosition == MarketPosition.Long && High[0] >= avg + BreakevenTriggerR * riskPx)
			{
				double be = Instrument.MasterInstrument.RoundToTickSize(avg + BreakevenOffsetTicks * TickSize);
				// Keep a few ticks between the new stop and the market so the change is never rejected.
				if (be <= Close[0] - 4 * TickSize)
				{
					SetStopLoss(SigLong, CalculationMode.Price, be, false);
					beMoved = true;
					Log("Stop -> breakeven " + Fmt(be));
				}
			}
			else if (Position.MarketPosition == MarketPosition.Short && Low[0] <= avg - BreakevenTriggerR * riskPx)
			{
				double be = Instrument.MasterInstrument.RoundToTickSize(avg - BreakevenOffsetTicks * TickSize);
				if (be >= Close[0] + 4 * TickSize)
				{
					SetStopLoss(SigShort, CalculationMode.Price, be, false);
					beMoved = true;
					Log("Stop -> breakeven " + Fmt(be));
				}
			}
		}

		private void FlattenAll(string reason)
		{
			if (IsOrderWorking(entryOrder))
				CancelOrder(entryOrder);

			if (Position.MarketPosition == MarketPosition.Flat || flattenBar == CurrentBar)
				return;

			flattenBar = CurrentBar;
			if (Position.MarketPosition == MarketPosition.Long)
				ExitLong(SigFlat, SigLong);
			else
				ExitShort(SigFlat, SigShort);

			Log("FLATTEN: " + reason);
		}

		private static bool IsOrderWorking(Order order)
		{
			if (order == null)
				return false;
			OrderState s = order.OrderState;
			return s != OrderState.Filled && s != OrderState.Cancelled && s != OrderState.Rejected && s != OrderState.Unknown;
		}

		protected override void OnOrderUpdate(Order order, double limitPrice, double stopPrice, int quantity, int filled, double averageFillPrice,
			OrderState orderState, DateTime time, ErrorCode error, string nativeError)
		{
			if (order.Name == SigLong || order.Name == SigShort)
			{
				entryOrder = order;

				if (orderState == OrderState.Rejected)
					Print(string.Format("IFVG Sniper | entry REJECTED: {0} {1}", error, nativeError));
			}
		}

		protected override void OnExecutionUpdate(Execution execution, string executionId, double price, int quantity,
			MarketPosition marketPosition, string orderId, DateTime time)
		{
			if (execution.Order == null)
				return;

			string name = execution.Order.Name;
			if ((name == SigLong || name == SigShort) && !entryCounted)
			{
				entryCounted = true;
				dailyTrades++;
				Log(string.Format("FILLED {0} x{1} @ {2}", name == SigLong ? "LONG" : "SHORT", quantity, Fmt(price)));

				if (ShowVisuals)
				{
					string tag = "IFVG_Fill_" + (++drawId);
					if (name == SigLong)
						Draw.ArrowUp(this, tag, false, time, price - 2 * TickSize, Brushes.LimeGreen);
					else
						Draw.ArrowDown(this, tag, false, time, price + 2 * TickSize, Brushes.OrangeRed);
					RememberTradeTag(tag);
				}
			}
		}
		#endregion

		#region Accounting & risk guards
		private void ProcessClosedTrades()
		{
			int count = SystemPerformance.AllTrades.Count;
			if (count <= tradesProcessed || Position.MarketPosition != MarketPosition.Flat)
				return;

			double pnl = 0;
			for (int i = tradesProcessed; i < count; i++)
				pnl += SystemPerformance.AllTrades[i].ProfitCurrency;
			tradesProcessed = count;

			double r = activeRiskUsd > 0 ? pnl / activeRiskUsd : 0;

			totalTrades++;
			netPnl		+= pnl;
			dailyPnl	+= pnl;
			totalR		+= r;

			if (pnl > 0)
			{
				totalWins++;
				dailyWins++;
				grossWin		+= pnl;
				lossStreak		= 0;
				dailyLossStreak	= 0;
			}
			else
			{
				totalLosses++;
				dailyLosses++;
				grossLoss		+= -pnl;
				lossStreak++;
				dailyLossStreak++;

				if (UseLossCooldown && lossStreak >= CooldownLossStreak)
					cooldownUntilBar = CurrentBar + CooldownBars;
			}

			Log(string.Format("CLOSED {0} ${1:0.00} ({2:+0.00;-0.00}R) | day ${3:0.00} | net ${4:0.00}",
				pnl > 0 ? "WIN " : "LOSS", pnl, r, dailyPnl, netPnl));

			activeStopTicks	= 0;
			activeRiskUsd	= 0;
		}

		private void RunRiskGuards(int etMin)
		{
			double unreal = Position.MarketPosition == MarketPosition.Flat ? 0 : Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Close[0]);

			if (!dailyHalted)
			{
				if (DailyLossLimit > 0 && dailyPnl + unreal <= -DailyLossLimit)
				{
					HaltDay("daily loss limit");
					FlattenAll("daily loss limit");
				}
				else if (DailyProfitTarget > 0 && dailyPnl >= DailyProfitTarget)
					HaltDay("daily profit target");
				else if (MaxConsecLossesPerDay > 0 && dailyLossStreak >= MaxConsecLossesPerDay)
					HaltDay(dailyLossStreak + " consecutive losses");
			}

			// Account-level guards follow the real account only (live), so backtests show the full curve.
			if (isLive)
			{
				liveEquity	= (netPnl - liveBaseline) + unreal;
				livePeak	= Math.Max(livePeak, liveEquity);

				if (!accountHalted && MaxTrailingDrawdown > 0 && livePeak - liveEquity >= MaxTrailingDrawdown - DrawdownBuffer)
				{
					HaltAccount("trailing drawdown guard");
					FlattenAll("trailing drawdown guard");
				}
				else if (!accountHalted && AccountProfitTarget > 0 && netPnl - liveBaseline >= AccountProfitTarget)
					HaltAccount("account profit target reached");
			}

			if (InFlattenWindow(etMin))
				FlattenAll("end-of-day flatten");
		}

		private void HaltDay(string reason)
		{
			dailyHalted		= true;
			dailyHaltReason	= reason;
			Log("DAY HALTED: " + reason);
		}

		private void HaltAccount(string reason)
		{
			accountHalted		= true;
			accountHaltReason	= reason;
			Print("IFVG Sniper | ACCOUNT HALTED: " + reason);
		}

		private void ResetDaily()
		{
			dailyPnl		= 0;
			dailyTrades		= 0;
			dailyWins		= 0;
			dailyLosses		= 0;
			dailyLossStreak	= 0;
			dailyHalted		= false;
			dailyHaltReason	= string.Empty;
		}
		#endregion

		#region Virtual Pine model
		private void UpdateVirtualTrade()
		{
			if (!vActive || CurrentBar <= vBar)
				return;

			bool hitSl = vDir == 1 ? Low[0] <= vSl : High[0] >= vSl;
			bool hitTp = vDir == 1 ? High[0] >= vTp : Low[0] <= vTp;

			// Conservative priority, same as the indicator: SL counted first if both touched.
			if (hitSl)
			{
				vActive = false;
				vLosses++;
				vTotalR -= 1.0;
				vLossStreak++;
				if (UseLossCooldown && vLossStreak >= CooldownLossStreak)
					vCooldownUntilBar = CurrentBar + CooldownBars;
			}
			else if (hitTp)
			{
				vActive = false;
				vWins++;
				vTotalR += TargetRR;
				vLossStreak = 0;
			}
		}
		#endregion

		#region Time helpers
		private int EtMinutes(DateTime t)
		{
			DateTime et = t;
			if (etZone != null)
			{
				try { et = TimeZoneInfo.ConvertTime(DateTime.SpecifyKind(t, DateTimeKind.Unspecified), Core.Globals.GeneralOptions.TimeZoneInfo, etZone); }
				catch { et = t; }
			}
			return et.Hour * 60 + et.Minute;
		}

		private static int HhmmToMinutes(int hhmm)
		{
			return (hhmm / 100) * 60 + (hhmm % 100);
		}

		// Bar timestamps are close times: a bar closing at 09:31 belongs to the window starting 09:30.
		private static bool InWindow(int m, int startHhmm, int endHhmm)
		{
			int s = HhmmToMinutes(startHhmm);
			int e = HhmmToMinutes(endHhmm);
			if (s == e)
				return true;
			return s < e ? (m > s && m <= e) : (m > s || m <= e);
		}

		private bool InTradingSession(int m)
		{
			return InWindow(m, Session1Start, Session1End) || (UseSession2 && InWindow(m, Session2Start, Session2End));
		}

		private bool InNoEntryWindow(int m)
		{
			return LastEntryTime > 0 && m >= HhmmToMinutes(LastEntryTime) && m < SessionReopenEt;
		}

		private bool InFlattenWindow(int m)
		{
			return FlattenTime > 0 && m >= HhmmToMinutes(FlattenTime) && m < SessionReopenEt;
		}

		private bool InNewsBlackout(int m)
		{
			for (int i = 0; i < newsMinutes.Count; i++)
			{
				int n = newsMinutes[i];
				if (m >= n - NewsMinutesBefore && m <= n + NewsMinutesAfter)
					return true;
			}
			return false;
		}

		private static List<int> ParseTimes(string csv)
		{
			List<int> result = new List<int>();
			if (string.IsNullOrWhiteSpace(csv))
				return result;

			foreach (string raw in csv.Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries))
			{
				string[] parts = raw.Trim().Split(':');
				int h, mi;
				if (parts.Length == 2 && int.TryParse(parts[0], out h) && int.TryParse(parts[1], out mi) && h >= 0 && h < 24 && mi >= 0 && mi < 60)
					result.Add(h * 60 + mi);
			}
			return result;
		}

		private TimeSpan BarSpan(int bars)
		{
			if (BarsPeriod.BarsPeriodType == BarsPeriodType.Minute)
				return TimeSpan.FromMinutes(BarsPeriod.Value * bars);
			if (BarsPeriod.BarsPeriodType == BarsPeriodType.Second)
				return TimeSpan.FromSeconds(BarsPeriod.Value * bars);
			return TimeSpan.FromMinutes(bars);
		}
		#endregion

		#region Visuals
		private void AddVisibleIfvg(RawFvg f, int dir, double linePrice)
		{
			if (!ShowVisuals)
				return;

			string tag		= "IFVG_Z" + (++drawId);
			Brush color		= dir == 1 ? Brushes.DodgerBlue : Brushes.Crimson;
			DateTime end	= Time[0] + BarSpan(IfvgLengthBars);

			Draw.Rectangle(this, tag + "_box", false, f.OriginTime, f.Top, end, f.Bot, color, color, 12);
			Draw.Line(this, tag + "_line", false, Time[0], linePrice, end, linePrice, color, DashStyleHelper.Dot, 2);
			Draw.Text(this, tag + "_txt", false, dir == 1 ? "IFVG+" : "IFVG-", end, linePrice, 0, color, labelFont,
				System.Windows.TextAlignment.Left, Brushes.Transparent, Brushes.Transparent, 0);

			visibleIfvgs.Add(new VisibleIfvg { Tag = tag, Top = f.Top, Bot = f.Bot, Dir = dir });

			while (visibleIfvgs.Count > MaxVisibleIfvg)
			{
				RemoveIfvgDrawings(visibleIfvgs[0].Tag);
				visibleIfvgs.RemoveAt(0);
			}
		}

		private void RemoveIfvgDrawings(string tag)
		{
			RemoveDrawObject(tag + "_box");
			RemoveDrawObject(tag + "_line");
			RemoveDrawObject(tag + "_txt");
		}

		private void UpdateIfvgInvalidation()
		{
			if (!ShowVisuals)
				return;

			for (int i = visibleIfvgs.Count - 1; i >= 0; i--)
			{
				VisibleIfvg v = visibleIfvgs[i];
				if ((v.Dir == 1 && Close[0] < v.Bot) || (v.Dir == -1 && Close[0] > v.Top))
				{
					RemoveIfvgDrawings(v.Tag);
					visibleIfvgs.RemoveAt(i);
				}
			}
		}

		private void DrawTradeLevels(int dir, double entry, double sl, double tp)
		{
			if (!ShowVisuals)
				return;

			string tag		= "IFVG_T" + (++drawId);
			DateTime end	= Time[0] + BarSpan(15);

			Draw.Line(this, tag + "_e", false, Time[0], entry, end, entry, Brushes.White, DashStyleHelper.Solid, 2);
			Draw.Line(this, tag + "_s", false, Time[0], sl, end, sl, Brushes.Red, DashStyleHelper.Solid, 2);
			Draw.Line(this, tag + "_t", false, Time[0], tp, end, tp, Brushes.LimeGreen, DashStyleHelper.Solid, 2);

			RememberTradeTag(tag + "_e");
			RememberTradeTag(tag + "_s");
			RememberTradeTag(tag + "_t");
		}

		private void RememberTradeTag(string tag)
		{
			tradeDrawTags.Enqueue(tag);
			while (tradeDrawTags.Count > 200)
				RemoveDrawObject(tradeDrawTags.Dequeue());
		}

		private void UpdateDashboard()
		{
			if (!ShowDashboard || (State == State.Historical && CurrentBar < Count - 2))
				return;

			int vClosed		= vWins + vLosses;
			double wr		= totalTrades > 0 ? 100.0 * totalWins / totalTrades : 0;
			double vWr		= vClosed > 0 ? 100.0 * vWins / vClosed : 0;
			double pf		= grossLoss > 0 ? grossWin / grossLoss : 0;

			string status;
			if (Position.MarketPosition != MarketPosition.Flat)
				status = string.Format("{0} x{1} @ {2}", Position.MarketPosition.ToString().ToUpper(), Position.Quantity, Fmt(Position.AveragePrice));
			else if (IsOrderWorking(entryOrder))
				status = string.Format("PENDING {0} limit", pendingDir == 1 ? "LONG" : "SHORT");
			else
				status = "FLAT - waiting for IFVG";

			string guard = accountHalted ? "HALTED: " + accountHaltReason
				: dailyHalted ? "DAY STOP: " + dailyHaltReason
				: "OK";

			StringBuilder sb = new StringBuilder();
			sb.AppendLine("IFVG SNIPER  |  NT8");
			sb.AppendLine(string.Format("{0}  |  {1:0.##}R  |  SL {2:0.##} ATR", OrderMode, TargetRR, SlAtrMultiplier));
			sb.AppendLine("Status : " + status);
			sb.AppendLine("Guard  : " + guard);
			sb.AppendLine(string.Format("Today  : ${0:0.00}  |  trades {1}/{2}  |  L-streak {3}/{4}", dailyPnl, dailyTrades, MaxTradesPerDay, dailyLossStreak, MaxConsecLossesPerDay));
			sb.AppendLine(string.Format("Real   : {0} tr  |  WR {1:0.0}%  |  PF {2:0.00}  |  ${3:0.00}  |  {4:+0.0;-0.0}R", totalTrades, wr, pf, netPnl, totalR));
			sb.AppendLine(string.Format("Pine   : {0} tr  |  WR {1:0.0}%  |  {2:+0.0;-0.0}R", vClosed, vWr, vTotalR));
			if (isLive)
				sb.AppendLine(string.Format("Live DD: ${0:0.00} / ${1:0}", livePeak - liveEquity, MaxTrailingDrawdown));
			sb.Append("Last skip: " + lastSkipReason);

			Draw.TextFixed(this, "IFVG_Dashboard", sb.ToString(), TextPosition.TopRight, Brushes.White, dashFont, Brushes.Transparent, Brushes.Black, 75);
		}
		#endregion

		#region Logging
		private string Fmt(double price)
		{
			return Instrument.MasterInstrument.FormatPrice(price);
		}

		private void Log(string message)
		{
			if (!PrintTradeLog)
				return;
			Print(string.Format("{0} | IFVG | {1}", Time[0].ToString("yyyy-MM-dd HH:mm", CultureInfo.InvariantCulture), message));
		}

		private void PrintSummary(string title)
		{
			int vClosed	= vWins + vLosses;
			double pf	= grossLoss > 0 ? grossWin / grossLoss : 0;

			Print("==================== IFVG Sniper | " + title + " ====================");
			Print(string.Format("Real fills : {0} trades | {1} W / {2} L | WR {3:0.0}% | PF {4:0.00} | Net ${5:0.00} | {6:+0.00;-0.00}R",
				totalTrades, totalWins, totalLosses, totalTrades > 0 ? 100.0 * totalWins / totalTrades : 0, pf, netPnl, totalR));
			Print(string.Format("Pine model : {0} trades | {1} W / {2} L | WR {3:0.0}% | {4:+0.00;-0.00}R  (indicator-style, assumes every signal fills)",
				vClosed, vWins, vLosses, vClosed > 0 ? 100.0 * vWins / vClosed : 0, vTotalR));
			Print(string.Format("Signals    : filtered IFVG {0} | gated {1} | blocked (in trade) {2} | skipped by risk/time {3}",
				filteredIfvg, gatedSignals, blockedSignals, skippedRisk));
		}
		#endregion

		#region Properties
		// ---------- 01. IFVG Engine ----------
		[NinjaScriptProperty]
		[Range(10, 500)]
		[Display(Name = "Hidden FVG memory", Order = 1, GroupName = "01. IFVG Engine")]
		public int MaxHiddenFvg { get; set; }

		[NinjaScriptProperty]
		[Range(5, 500)]
		[Display(Name = "Max hidden FVG age (bars)", Order = 2, GroupName = "01. IFVG Engine")]
		public int MaxFvgAge { get; set; }

		[NinjaScriptProperty]
		[Range(0, int.MaxValue)]
		[Display(Name = "Minimum FVG size (ticks)", Order = 3, GroupName = "01. IFVG Engine")]
		public int MinGapTicks { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "IFVG line price", Description = "Level used as the limit entry price.", Order = 4, GroupName = "01. IFVG Engine")]
		public IFVGLinePrice LinePrice { get; set; }

		// ---------- 02. IFVG Filter ----------
		[NinjaScriptProperty]
		[Display(Name = "Filter mode", Order = 10, GroupName = "02. IFVG Filter")]
		public IFVGFilterMode FilterMode { get; set; }

		[NinjaScriptProperty]
		[Range(0.0, double.MaxValue)]
		[Display(Name = "Custom min gap / ATR", Order = 11, GroupName = "02. IFVG Filter")]
		public double CustomMinGapAtr { get; set; }

		[NinjaScriptProperty]
		[Range(0.0, 1.0)]
		[Display(Name = "Custom min body ratio", Order = 12, GroupName = "02. IFVG Filter")]
		public double CustomMinBodyRatio { get; set; }

		[NinjaScriptProperty]
		[Range(0.0, double.MaxValue)]
		[Display(Name = "Custom min range / ATR", Order = 13, GroupName = "02. IFVG Filter")]
		public double CustomMinRangeAtr { get; set; }

		[NinjaScriptProperty]
		[Range(0.0, double.MaxValue)]
		[Display(Name = "Custom clean-break buffer / ATR", Order = 14, GroupName = "02. IFVG Filter")]
		public double CustomBreakAtr { get; set; }

		[NinjaScriptProperty]
		[Range(0.5, double.MaxValue)]
		[Display(Name = "Adaptive gap multiplier", Order = 15, GroupName = "02. IFVG Filter")]
		public double AdaptiveGapMultiplier { get; set; }

		[NinjaScriptProperty]
		[Range(10, 200)]
		[Display(Name = "Adaptive lookback (gaps)", Order = 16, GroupName = "02. IFVG Filter")]
		public int AdaptiveLookback { get; set; }

		// ---------- 03. Entry & Exit ----------
		[NinjaScriptProperty]
		[Display(Name = "Order mode", Description = "LimitAtIfvgLine = limit at the IFVG line (indicator default). MarketNextBar = market order at the open after the confirmation close.", Order = 20, GroupName = "03. Entry & Exit")]
		public IFVGOrderMode OrderMode { get; set; }

		[NinjaScriptProperty]
		[Range(0, 500)]
		[Display(Name = "Limit expiry (bars, 0 = never)", Order = 21, GroupName = "03. Entry & Exit")]
		public int LimitExpiryBars { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Cancel if target touched before fill", Order = 22, GroupName = "03. Entry & Exit")]
		public bool CancelIfTargetTouched { get; set; }

		[NinjaScriptProperty]
		[Range(1, int.MaxValue)]
		[Display(Name = "ATR length", Order = 23, GroupName = "03. Entry & Exit")]
		public int AtrLength { get; set; }

		[NinjaScriptProperty]
		[Range(0.1, double.MaxValue)]
		[Display(Name = "SL ATR multiplier", Order = 24, GroupName = "03. Entry & Exit")]
		public double SlAtrMultiplier { get; set; }

		[NinjaScriptProperty]
		[Range(0.25, 10.0)]
		[Display(Name = "Target RR", Order = 25, GroupName = "03. Entry & Exit")]
		public double TargetRR { get; set; }

		[NinjaScriptProperty]
		[Range(1, int.MaxValue)]
		[Display(Name = "Min stop (ticks)", Description = "Stops tighter than this are widened (MNQ: 4 ticks = 1 point).", Order = 26, GroupName = "03. Entry & Exit")]
		public int MinStopTicks { get; set; }

		[NinjaScriptProperty]
		[Range(0, int.MaxValue)]
		[Display(Name = "Max stop (ticks, 0 = off)", Description = "Signals needing a wider stop are skipped.", Order = 27, GroupName = "03. Entry & Exit")]
		public int MaxStopTicks { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Use breakeven", Order = 28, GroupName = "03. Entry & Exit")]
		public bool UseBreakeven { get; set; }

		[NinjaScriptProperty]
		[Range(0.1, 10.0)]
		[Display(Name = "Breakeven trigger (R)", Order = 29, GroupName = "03. Entry & Exit")]
		public double BreakevenTriggerR { get; set; }

		[NinjaScriptProperty]
		[Range(0, 100)]
		[Display(Name = "Breakeven offset (ticks)", Order = 30, GroupName = "03. Entry & Exit")]
		public int BreakevenOffsetTicks { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Trade direction", Order = 31, GroupName = "03. Entry & Exit")]
		public IFVGTradeDirection TradeDirection { get; set; }

		// ---------- 04. Signal Quality Filters ----------
		[NinjaScriptProperty]
		[Display(Name = "Use HTF trend filter", Order = 40, GroupName = "04. Signal Quality Filters")]
		public bool UseTrendFilter { get; set; }

		[NinjaScriptProperty]
		[Range(1, 1440)]
		[Display(Name = "Trend timeframe (minutes)", Order = 41, GroupName = "04. Signal Quality Filters")]
		public int TrendTimeframeMinutes { get; set; }

		[NinjaScriptProperty]
		[Range(2, 1000)]
		[Display(Name = "Trend EMA length", Order = 42, GroupName = "04. Signal Quality Filters")]
		public int TrendEmaLength { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Skip extreme volatility candles", Order = 43, GroupName = "04. Signal Quality Filters")]
		public bool UseVolatilityGuard { get; set; }

		[NinjaScriptProperty]
		[Range(1.0, double.MaxValue)]
		[Display(Name = "Max confirmation range / ATR", Order = 44, GroupName = "04. Signal Quality Filters")]
		public double MaxRangeAtrGuard { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Require above-average volume", Order = 45, GroupName = "04. Signal Quality Filters")]
		public bool UseVolumeFilter { get; set; }

		[NinjaScriptProperty]
		[Range(2, 500)]
		[Display(Name = "Volume MA length", Order = 46, GroupName = "04. Signal Quality Filters")]
		public int VolumeMaLength { get; set; }

		[NinjaScriptProperty]
		[Range(0.1, double.MaxValue)]
		[Display(Name = "Volume multiplier", Order = 47, GroupName = "04. Signal Quality Filters")]
		public double VolumeMultiplier { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Require clear room to target", Order = 48, GroupName = "04. Signal Quality Filters")]
		public bool UseRoomFilter { get; set; }

		[NinjaScriptProperty]
		[Range(3, 200)]
		[Display(Name = "Obstacle lookback (bars)", Order = 49, GroupName = "04. Signal Quality Filters")]
		public int RoomLookback { get; set; }

		[NinjaScriptProperty]
		[Range(0.0, double.MaxValue)]
		[Display(Name = "Room buffer / ATR", Order = 50, GroupName = "04. Signal Quality Filters")]
		public double RoomBufferAtr { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Skip if opposing FVG blocks path", Order = 51, GroupName = "04. Signal Quality Filters")]
		public bool UsePathFilter { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Cooldown after loss streak", Order = 52, GroupName = "04. Signal Quality Filters")]
		public bool UseLossCooldown { get; set; }

		[NinjaScriptProperty]
		[Range(1, 50)]
		[Display(Name = "Loss streak for cooldown", Order = 53, GroupName = "04. Signal Quality Filters")]
		public int CooldownLossStreak { get; set; }

		[NinjaScriptProperty]
		[Range(1, 500)]
		[Display(Name = "Cooldown length (bars)", Order = 54, GroupName = "04. Signal Quality Filters")]
		public int CooldownBars { get; set; }

		// ---------- 05. Sessions (Eastern Time) ----------
		[NinjaScriptProperty]
		[Display(Name = "Use session filter", Description = "Only take IFVG entries inside the session window(s). Times are New York (ET), HHmm.", Order = 60, GroupName = "05. Sessions (ET, HHmm)")]
		public bool UseSessionFilter { get; set; }

		[NinjaScriptProperty]
		[Range(0, 2359)]
		[Display(Name = "Session 1 start", Order = 61, GroupName = "05. Sessions (ET, HHmm)")]
		public int Session1Start { get; set; }

		[NinjaScriptProperty]
		[Range(0, 2359)]
		[Display(Name = "Session 1 end", Order = 62, GroupName = "05. Sessions (ET, HHmm)")]
		public int Session1End { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Use session 2", Order = 63, GroupName = "05. Sessions (ET, HHmm)")]
		public bool UseSession2 { get; set; }

		[NinjaScriptProperty]
		[Range(0, 2359)]
		[Display(Name = "Session 2 start", Order = 64, GroupName = "05. Sessions (ET, HHmm)")]
		public int Session2Start { get; set; }

		[NinjaScriptProperty]
		[Range(0, 2359)]
		[Display(Name = "Session 2 end", Order = 65, GroupName = "05. Sessions (ET, HHmm)")]
		public int Session2End { get; set; }

		[NinjaScriptProperty]
		[Range(0, 2359)]
		[Display(Name = "Last entry time (0 = off)", Description = "No new entries from this time until the 18:00 ET reopen.", Order = 66, GroupName = "05. Sessions (ET, HHmm)")]
		public int LastEntryTime { get; set; }

		[NinjaScriptProperty]
		[Range(0, 2359)]
		[Display(Name = "Flatten time (0 = off)", Description = "Closes any position and cancels pending entries at this time (prop-firm end-of-day rule).", Order = 67, GroupName = "05. Sessions (ET, HHmm)")]
		public int FlattenTime { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Use news blackout", Order = 68, GroupName = "05. Sessions (ET, HHmm)")]
		public bool UseNewsBlackout { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "News times (ET, HH:mm list)", Order = 69, GroupName = "05. Sessions (ET, HHmm)")]
		public string NewsTimesEt { get; set; }

		[NinjaScriptProperty]
		[Range(0, 120)]
		[Display(Name = "News minutes before", Order = 70, GroupName = "05. Sessions (ET, HHmm)")]
		public int NewsMinutesBefore { get; set; }

		[NinjaScriptProperty]
		[Range(0, 120)]
		[Display(Name = "News minutes after", Order = 71, GroupName = "05. Sessions (ET, HHmm)")]
		public int NewsMinutesAfter { get; set; }

		// ---------- 06. Risk & Prop Firm ----------
		[NinjaScriptProperty]
		[Range(1.0, double.MaxValue)]
		[Display(Name = "Risk per trade ($)", Order = 80, GroupName = "06. Risk & Prop Firm")]
		public double RiskPerTrade { get; set; }

		[NinjaScriptProperty]
		[Range(1, 1000)]
		[Display(Name = "Max contracts", Order = 81, GroupName = "06. Risk & Prop Firm")]
		public int MaxContracts { get; set; }

		[NinjaScriptProperty]
		[Range(0.0, double.MaxValue)]
		[Display(Name = "Commission per contract, round turn ($)", Order = 82, GroupName = "06. Risk & Prop Firm")]
		public double CommissionPerContract { get; set; }

		[NinjaScriptProperty]
		[Range(0, 100)]
		[Display(Name = "Stop slippage allowance (ticks)", Description = "Added to the stop distance when sizing so a slipped stop still stays within the $ risk.", Order = 83, GroupName = "06. Risk & Prop Firm")]
		public int StopSlippageTicks { get; set; }

		[NinjaScriptProperty]
		[Range(0.0, double.MaxValue)]
		[Display(Name = "Daily loss limit ($, 0 = off)", Order = 84, GroupName = "06. Risk & Prop Firm")]
		public double DailyLossLimit { get; set; }

		[NinjaScriptProperty]
		[Range(0.0, double.MaxValue)]
		[Display(Name = "Daily profit target ($, 0 = off)", Description = "Stops trading for the day once reached (helps prop-firm consistency rules).", Order = 85, GroupName = "06. Risk & Prop Firm")]
		public double DailyProfitTarget { get; set; }

		[NinjaScriptProperty]
		[Range(0, 100)]
		[Display(Name = "Max trades per day (0 = off)", Order = 86, GroupName = "06. Risk & Prop Firm")]
		public int MaxTradesPerDay { get; set; }

		[NinjaScriptProperty]
		[Range(0, 50)]
		[Display(Name = "Max consecutive losses per day (0 = off)", Order = 87, GroupName = "06. Risk & Prop Firm")]
		public int MaxConsecLossesPerDay { get; set; }

		[NinjaScriptProperty]
		[Range(0.0, double.MaxValue)]
		[Display(Name = "Max trailing drawdown ($, live, 0 = off)", Order = 88, GroupName = "06. Risk & Prop Firm")]
		public double MaxTrailingDrawdown { get; set; }

		[NinjaScriptProperty]
		[Range(0.0, double.MaxValue)]
		[Display(Name = "Drawdown safety buffer ($)", Order = 89, GroupName = "06. Risk & Prop Firm")]
		public double DrawdownBuffer { get; set; }

		[NinjaScriptProperty]
		[Range(0.0, double.MaxValue)]
		[Display(Name = "Account profit target ($, live, 0 = off)", Description = "Stops trading once the evaluation target is reached.", Order = 90, GroupName = "06. Risk & Prop Firm")]
		public double AccountProfitTarget { get; set; }

		// ---------- 07. Display ----------
		[Display(Name = "Show IFVG zones & trade levels", Order = 100, GroupName = "07. Display")]
		public bool ShowVisuals { get; set; }

		[Display(Name = "Show dashboard", Order = 101, GroupName = "07. Display")]
		public bool ShowDashboard { get; set; }

		[Display(Name = "Print trade log (Output window)", Order = 102, GroupName = "07. Display")]
		public bool PrintTradeLog { get; set; }

		[Range(1, 100)]
		[Display(Name = "Max visible IFVG", Order = 103, GroupName = "07. Display")]
		public int MaxVisibleIfvg { get; set; }

		[Range(5, 500)]
		[Display(Name = "IFVG zone length (bars)", Order = 104, GroupName = "07. Display")]
		public int IfvgLengthBars { get; set; }
		#endregion
	}
}
