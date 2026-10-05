//
// NQ Pullback-Day Engine - MNQ intraday multi-module strategy for prop-firm accounts (NinjaTrader 8, single file)
// ------------------------------------------------------------------------------------------------
// EDGE (research/pullday*.py, NQ 1m 2020-01 -> 2026-09): trend continuation on "pullback days".
//   Daily trend   : prior RTH close vs SMA(20) of RTH closes (+1 up / -1 down). Only trend-direction trades.
//   Pullback day  : the prior RTH day moved AGAINST the trend, or only slightly with it:
//                   (prevClose - prevPrevClose) / ATRd x trend < PullbackMaxRet (0.20), AND the 2-day move with the
//                   trend is not larger than SkipTwoDayMove (0.63 ATRd).
//                   On those days trend continuation is strong; after big with-trend days it is not.
// MODULES (each its own signal name, 1 position each, all in the trend direction):
//   ORB60 / ORB30 / ORB15 : breakout of the 60/30/15-minute opening range, stop order 1 tick beyond (market if
//                           already through), orders from EntryStart to OrbLastEntry, re-arm after a close back
//                           inside the range, max 2 per module per day. Stop = opposite side capped at StopCapAtr x ATRd.
//   VWP60 / VWP30         : after a close beyond the 60/30-min range and >= 0.10 ATRd from VWAP, a limit rests at
//                           VWAP (follows it) until VwapLastEntry. 1 per module per day. Stop = StopCapAtr x ATRd.
//   MSEQ (5-min series)   : uptrend days only (no pullback filter): bearish 5-min candle + 5 bullish candles closing
//                           higher each time and holding above its low. Stop 1.75 x distance to that low, target 0.5R.
//   Targets are small fractions of R (0.5-0.75R) -> high win rate. Everything flat at FlattenTime.
// Backtest of this logic (1 MNQ per module, 1 tick slippage, $1 RT): 5.6 trades/week, WR 67.7%, PF 1.65,
//   Sharpe IS 2020-23 2.41 / OOS 2024-26 1.70. (v1 defaults 0.44 / 0 -> 8.65 trades/week, WR 64.2%, PF 1.39.)
// PROP-FIRM LAYER: daily loss limit (flattens + halts), daily profit target, max trades/day, max consecutive losses,
//   max open modules, max $ risk per trade, trailing drawdown guard (live), news blackout, MANUAL PAUSE FILE.
// NO LOOK-AHEAD: Calculate.OnBarClose; daily stats from completed RTH days only.
// NEEDS: 1-MINUTE MNQ chart, CME US Index Futures ETH, and ~25 RTH days of history before the first trade
//   (Strategy Analyzer: start the test at least 2 months before the period you want to see).
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
	public class NQPullbackDayEngine : Strategy
	{
		private const int RthOpen = 570, RthClose = 960;
		private const int KindOrb = 0, KindVwap = 1, KindSeq = 2;

		private class Mod
		{
			public string Sig; public int Kind; public int Range; public double TargetR; public double StopCap; public bool Enabled; public bool UsePullback;
			public double OrH, OrL; public int OrBars; public bool OrReady;
			public bool Armed, InTrade, Done; public int Trades, OpenQty;
			public Order Entry; public double EntryPx, PendingStop, Tgt;
			public void NewDay() { OrH = 0; OrL = 0; OrBars = 0; OrReady = false; Armed = false; Done = false; Trades = 0; }
		}

		#region Fields
		private TimeZoneInfo etZone;
		private SimpleFont dashFont;
		private bool badTimeframe;
		private List<Mod> mods;
		private Mod mseq;

		private int rthDay = -1;
		private double dayHigh, dayLow, dayClose, prevRthClose = double.NaN, prev2RthClose = double.NaN, prev3RthClose = double.NaN, atrDaily = double.NaN, atrPrevClose = double.NaN;
		private bool dayHasBars;
		private int dayLastOpen = -1, sessionsSinceRth;
		private double full1 = double.NaN, full2 = double.NaN, full3 = double.NaN;	// RTH closes of complete days only (NaN = holiday / early close)
		private int atrCount, rthDaysSeen;
		private List<double> rthCloses;

		private int trendDir;
		private double todayAtr, prevRet = double.NaN, prevRet2 = double.NaN, vwapPv, vwapVol, vwap;
		private bool dayTradable, pullbackDay, dayHalted;
		private string dayStatus = "waiting", haltReason = string.Empty;
		private int tradesToday, lossStreak;
		private double dailyPnl;
		private List<int> newsMinutes;

		private int tradesProcessed, totalTrades, totalWins, flattenBar = -1;
		private double grossWin, grossLoss, netPnl;
		private bool isLive, accountHalted;
		private double liveBaseline, livePeak, liveEquity;
		#endregion

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Description = "MNQ trend continuation on pullback days: ORB 60/30/15 + VWAP 60/30 + 5-min momentum sequence, small R targets, prop-firm risk layer.";
				Name = "NQPullbackDayEngine";
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

				UsePullbackFilter = true; PullbackMaxRet = 0.20; SkipTwoDayMove = 0.63; StopCapAtr = 0.35; VwapExtensionAtr = 0.10;
				UseOrb60 = true; Orb60TargetR = 0.6; UseVwap60 = true; Vwap60TargetR = 0.6;
				UseOrb30 = true; Orb30TargetR = 0.75; UseOrb15 = true; Orb15TargetR = 0.75;
				UseVwap30 = true; Vwap30TargetR = 0.75;
				UseMseq = true; MseqBars = 5; MseqTargetR = 0.5; MseqStopMult = 1.75; MseqFirst = 1030; MseqLast = 1545;
				EntryStart = 1030; OrbLastEntry = 1300; VwapLastEntry = 1430; FlattenTime = 1555;
				NewsTimes = ""; NewsMinutesBefore = 2; NewsMinutesAfter = 5; PauseFile = "pause_trading.txt";
				ContractsPerModule = 1; MaxOpenModules = 6; MaxRiskPerTrade = 0;
				DailyLossLimit = 0; DailyProfitTarget = 0; MaxTradesPerDay = 12; MaxConsecLosses = 0;
				MaxTrailingDrawdown = 0; DrawdownBuffer = 200;
				ShowDashboard = true; PrintLog = true;
			}
			else if (State == State.Configure)
			{
				AddDataSeries(BarsPeriodType.Minute, 5);
			}
			else if (State == State.DataLoaded)
			{
				rthCloses = new List<double>();
				dashFont = new SimpleFont("Consolas", 12);
				try { etZone = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time"); } catch { etZone = null; }
				newsMinutes = ParseTimes(NewsTimes);
				badTimeframe = !(BarsPeriod.BarsPeriodType == BarsPeriodType.Minute && BarsPeriod.Value == 1);
				if (badTimeframe)
					Print("NQPullbackDayEngine | Needs a 1-MINUTE MNQ chart (CME US Index Futures ETH).");
				mods = new List<Mod>();
				mods.Add(NewMod("ORB60", KindOrb, 60, Orb60TargetR, UseOrb60));
				mods.Add(NewMod("VWP60", KindVwap, 60, Vwap60TargetR, UseVwap60));
				mods.Add(NewMod("ORB30", KindOrb, 30, Orb30TargetR, UseOrb30));
				mods.Add(NewMod("ORB15", KindOrb, 15, Orb15TargetR, UseOrb15));
				mods.Add(NewMod("VWP30", KindVwap, 30, Vwap30TargetR, UseVwap30));
				mseq = NewMod("MSEQ", KindSeq, 0, MseqTargetR, UseMseq);
				mseq.UsePullback = false;
				mods.Add(mseq);
			}
			else if (State == State.Realtime)
			{
				foreach (Mod m in mods) if (m.Entry != null) m.Entry = GetRealtimeOrder(m.Entry);
				isLive = true; liveBaseline = netPnl; livePeak = 0; liveEquity = 0; accountHalted = false;
				Print(string.Format("NQPullbackDayEngine | LIVE {0} on {1} | historical: {2} trades, net ${3:0.00}", Instrument.FullName, Account.Name, totalTrades, netPnl));
			}
			else if (State == State.Terminated)
			{
				if (mods != null && totalTrades == 0 && rthDaysSeen < 25)
					Print(string.Format("NQPullbackDayEngine | 0 trades: only {0} RTH days loaded. It needs ~25 RTH days of warm-up (SMA20 + ATR14). Start the backtest 2+ months earlier.", rthDaysSeen));
			}
		}

		public override string DisplayName { get { return "NQ Pullback-Day Engine"; } }

		private Mod NewMod(string sig, int kind, int range, double r, bool on)
		{
			Mod m = new Mod(); m.Sig = sig; m.Kind = kind; m.Range = range; m.TargetR = r; m.StopCap = StopCapAtr; m.Enabled = on; m.UsePullback = true;
			return m;
		}

		protected override void OnBarUpdate()
		{
			if (badTimeframe || CurrentBars[0] < 2)
				return;
			if (BarsInProgress == 1)
			{
				OnFiveMinute();
				return;
			}

			DateTime etClose = ToEt(Time[0]);
			DateTime etOpen = etClose.AddMinutes(-1);
			int openMin = etOpen.Hour * 60 + etOpen.Minute;
			int closeMin = etClose.Hour * 60 + etClose.Minute;
			int etDate = etOpen.Year * 10000 + etOpen.Month * 100 + etOpen.Day;

			ProcessClosedTrades();

			if (Bars.IsFirstBarOfSession) sessionsSinceRth++;
			bool inRth = openMin >= RthOpen && openMin < RthClose;
			if (inRth && etDate != rthDay)
				StartRthDay(etDate);

			if (inRth && etDate == rthDay)
			{
				if (!dayHasBars) { dayHigh = High[0]; dayLow = Low[0]; dayHasBars = true; }
				else { dayHigh = Math.Max(dayHigh, High[0]); dayLow = Math.Min(dayLow, Low[0]); }
				dayClose = Close[0];
				dayLastOpen = openMin;
				double vol = Volume[0] > 0 ? Volume[0] : 1.0;
				vwapPv += (High[0] + Low[0] + Close[0]) / 3.0 * vol; vwapVol += vol; vwap = vwapPv / vwapVol;
				foreach (Mod m in mods)
				{
					if (m.Kind == KindSeq || openMin >= RthOpen + m.Range) continue;
					if (m.OrBars == 0) { m.OrH = High[0]; m.OrL = Low[0]; } else { m.OrH = Math.Max(m.OrH, High[0]); m.OrL = Math.Min(m.OrL, Low[0]); }
					m.OrBars++;
					if (openMin == RthOpen + m.Range - 1) { m.OrReady = true; if (m.Kind == KindOrb) m.Armed = true; }
				}
			}

			RiskGuards();

			if (FlattenTime > 0 && closeMin >= Hm(FlattenTime) && closeMin < 18 * 60)
			{
				FlattenAll("end of day");
				UpdateDashboard();
				return;
			}

			bool blocked = !CanOpenNew(closeMin);
			if (blocked)
				CancelAllEntries();
			else if (inRth && etDate == rthDay && dayTradable && closeMin >= Hm(EntryStart))
			{
				foreach (Mod m in mods)
				{
					if (!m.Enabled || !m.OrReady || m.Kind == KindSeq) continue;
					if (UsePullbackFilter && m.UsePullback && !pullbackDay) continue;
					if (m.Kind == KindOrb) ManageOrb(m, closeMin);
					else ManageVwap(m, openMin, closeMin);
				}
			}
			UpdateDashboard();
		}

		#region Daily statistics
		private void StartRthDay(int etDate)
		{
			if (dayHasBars)
			{
				double tr = double.IsNaN(atrPrevClose) ? dayHigh - dayLow : Math.Max(dayHigh - dayLow, Math.Max(Math.Abs(dayHigh - atrPrevClose), Math.Abs(dayLow - atrPrevClose)));
				atrCount++;
				int k = Math.Min(atrCount, 14);
				atrDaily = double.IsNaN(atrDaily) ? tr : ((k - 1) * atrDaily + tr) / k;
				atrPrevClose = dayClose;
				prev3RthClose = prev2RthClose; prev2RthClose = prevRthClose; prevRthClose = dayClose;
				full3 = full2; full2 = full1; full1 = dayLastOpen >= RthClose - 1 ? dayClose : double.NaN;
				for (int g = 1; g < sessionsSinceRth; g++) { full3 = full2; full2 = full1; full1 = double.NaN; }	// Globex sessions without RTH (holidays)
				rthCloses.Add(dayClose);
				while (rthCloses.Count > 20) rthCloses.RemoveAt(0);
			}
			rthDaysSeen++; sessionsSinceRth = 0;
			rthDay = etDate; dayHasBars = false; vwapPv = 0; vwapVol = 0; vwap = 0;
			todayAtr = atrDaily; trendDir = 0; dayHalted = false; haltReason = string.Empty; tradesToday = 0; lossStreak = 0; dailyPnl = 0;
			foreach (Mod m in mods) m.NewDay();
			if (rthCloses.Count >= 15 && !double.IsNaN(prevRthClose))
			{
				double s = 0; foreach (double x in rthCloses) s += x;
				double sma = s / rthCloses.Count;
				trendDir = prevRthClose > sma ? 1 : (prevRthClose < sma ? -1 : 0);
			}
			dayTradable = trendDir != 0 && atrCount >= 14 && !double.IsNaN(todayAtr) && todayAtr > 0;
			// Prior-day moves use COMPLETE RTH days only: after a holiday / early close the filter is undefined -> no pullback trades.
			prevRet = (!double.IsNaN(full1) && !double.IsNaN(full2) && dayTradable) ? (full1 - full2) / todayAtr * trendDir : double.NaN;
			prevRet2 = (!double.IsNaN(full1) && !double.IsNaN(full3) && dayTradable) ? (full1 - full3) / todayAtr * trendDir : double.NaN;
			pullbackDay = !double.IsNaN(prevRet) && prevRet < PullbackMaxRet && (SkipTwoDayMove <= 0 || (!double.IsNaN(prevRet2) && prevRet2 <= SkipTwoDayMove));
			if (!dayTradable) dayStatus = atrCount < 14 ? "warming up (" + rthDaysSeen + " RTH days)" : "no trend";
			else dayStatus = (trendDir == 1 ? "trend UP" : "trend DOWN") + (pullbackDay ? " | PULLBACK DAY: all modules" : " | extended day: MSEQ only");
		}
		#endregion

		#region Modules
		private void ManageOrb(Mod m, int closeMin)
		{
			bool window = closeMin < Hm(OrbLastEntry);
			if (!window) { if (Working(m.Entry)) CancelOrder(m.Entry); return; }
			if (!m.Armed && !m.InTrade && !Working(m.Entry) && m.Trades > 0 && m.Trades < 2 && Close[0] < m.OrH && Close[0] > m.OrL)
				m.Armed = true;
			if (!m.Armed || m.InTrade || Working(m.Entry) || m.Trades >= 2)
				return;
			int d = trendDir;
			double entry = d == 1 ? m.OrH + TickSize : m.OrL - TickSize;
			double opp = d == 1 ? m.OrL - TickSize : m.OrH + TickSize;
			int st = Math.Max(8, (int)Math.Round(Math.Min(Math.Abs(entry - opp), m.StopCap * todayAtr) / TickSize));
			m.Armed = false;
			if (!RiskOk(st)) return;
			ArmBracket(m.Sig, st, m.TargetR);
			bool through = d == 1 ? Close[0] >= entry : Close[0] <= entry;
			if (d == 1) { if (through) EnterLong(0, ContractsPerModule, m.Sig); else EnterLongStopMarket(0, true, ContractsPerModule, entry, m.Sig); }
			else { if (through) EnterShort(0, ContractsPerModule, m.Sig); else EnterShortStopMarket(0, true, ContractsPerModule, entry, m.Sig); }
			Log(string.Format("{0} {1} {2} @ {3} | SL {4}t | TP {5:0.##}R", m.Sig, d == 1 ? "BUY" : "SELL", through ? "market" : "stop", Fmt(entry), st, m.TargetR));
		}

		private void ManageVwap(Mod m, int openMin, int closeMin)
		{
			bool window = closeMin < Hm(VwapLastEntry);
			if (Working(m.Entry))
			{
				if (!window) { CancelOrder(m.Entry); m.Done = true; return; }
				double px = Instrument.MasterInstrument.RoundToTickSize(vwap);
				if (Math.Abs(px - m.Entry.LimitPrice) >= TickSize / 2) ChangeOrder(m.Entry, m.Entry.Quantity, px, 0);
				return;
			}
			if (m.Done || m.InTrade || m.Armed || !window || openMin < RthOpen + m.Range)
				return;
			int d = trendDir;
			bool extended = d == 1 ? Close[0] > m.OrH && Close[0] >= vwap + VwapExtensionAtr * todayAtr
								   : Close[0] < m.OrL && Close[0] <= vwap - VwapExtensionAtr * todayAtr;
			if (!extended) return;
			int st = Math.Max(8, (int)Math.Round(m.StopCap * todayAtr / TickSize));
			if (!RiskOk(st)) { m.Done = true; return; }
			ArmBracket(m.Sig, st, m.TargetR);
			double lim = Instrument.MasterInstrument.RoundToTickSize(vwap);
			if (d == 1) EnterLongLimit(0, true, ContractsPerModule, lim, m.Sig); else EnterShortLimit(0, true, ContractsPerModule, lim, m.Sig);
			m.Armed = true;
			Log(string.Format("{0} {1} limit @ VWAP {2} | SL {3}t | TP {4:0.##}R", m.Sig, d == 1 ? "BUY" : "SELL", Fmt(lim), st, m.TargetR));
		}

		private void OnFiveMinute()
		{
			if (mseq == null || !mseq.Enabled || CurrentBars[1] < MseqBars + 2) return;
			DateTime etClose = ToEt(Times[1][0]);
			DateTime etOpen = etClose.AddMinutes(-5);
			int openMin = etOpen.Hour * 60 + etOpen.Minute;
			int closeMin = etClose.Hour * 60 + etClose.Minute;
			int etDate = etOpen.Year * 10000 + etOpen.Month * 100 + etOpen.Day;
			if (etDate != rthDay || !dayTradable || trendDir != 1 || openMin < Hm(MseqFirst) || openMin >= Hm(MseqLast)) return;
			if (mseq.InTrade || Working(mseq.Entry) || !CanOpenNew(closeMin)) return;
			if (FlattenTime > 0 && closeMin >= Hm(FlattenTime)) return;
			int n = MseqBars;
			if (!(Closes[1][n] < Opens[1][n])) return;
			double mainLow = Lows[1][n];
			for (int j = 0; j < n; j++)
			{
				if (Closes[1][j] <= Opens[1][j] || Lows[1][j] <= mainLow) return;
				if (j < n - 1 && Closes[1][j] <= Closes[1][j + 1]) return;
			}
			double c0 = Closes[1][0];
			double dist = (c0 - mainLow) * MseqStopMult;
			if (dist <= 0) return;
			double stop = Instrument.MasterInstrument.RoundDownToTickSize(c0 - dist);
			int st = Math.Max(1, (int)Math.Round((c0 - stop) / TickSize));
			if (!RiskOk(st)) return;
			mseq.PendingStop = stop;
			SetStopLoss(mseq.Sig, CalculationMode.Price, stop, false);
			SetProfitTarget(mseq.Sig, CalculationMode.Ticks, 4000);	// placeholder, replaced on fill
			EnterLong(0, ContractsPerModule, mseq.Sig);
			Log(string.Format("MSEQ BUY market | SL {0} ({1}t) | TP {2:0.##}R", Fmt(stop), st, MseqTargetR));
		}

		private void ArmBracket(string sig, int stopTicks, double r)
		{
			SetStopLoss(sig, CalculationMode.Ticks, stopTicks, false);
			SetProfitTarget(sig, CalculationMode.Ticks, Math.Max(1, (int)Math.Round(stopTicks * r)));
		}
		#endregion

		#region Risk layer
		private int OpenModules() { int c = 0; foreach (Mod m in mods) if (m.InTrade || Working(m.Entry)) c++; return c; }

		private bool RiskOk(int stopTicks)
		{
			if (MaxOpenModules > 0 && OpenModules() >= MaxOpenModules) { dayStatus = "max open modules"; return false; }
			double r = ContractsPerModule * ((stopTicks + 1) * TickSize * Instrument.MasterInstrument.PointValue + 1.0);
			if (MaxRiskPerTrade > 0 && r > MaxRiskPerTrade) { Log(string.Format("skip: risk ${0:0} > max", r)); return false; }
			if (DailyLossLimit > 0 && dailyPnl - r < -DailyLossLimit) { dayStatus = "skip: would breach daily loss"; return false; }
			if (isLive && MaxTrailingDrawdown > 0 && (livePeak - liveEquity) + r > MaxTrailingDrawdown - DrawdownBuffer) { dayStatus = "skip: drawdown headroom"; return false; }
			return true;
		}

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
				dayHalted = true; haltReason = "daily profit target"; CancelAllEntries();
			}
			if (isLive)
			{
				liveEquity = (netPnl - liveBaseline) + unreal;
				livePeak = Math.Max(livePeak, liveEquity);
				if (!accountHalted && MaxTrailingDrawdown > 0 && livePeak - liveEquity >= MaxTrailingDrawdown - DrawdownBuffer)
				{
					accountHalted = true; haltReason = "trailing drawdown guard";
					FlattenAll(haltReason);
					Print("NQPullbackDayEngine | ACCOUNT HALTED: trailing drawdown guard");
				}
			}
		}

		private void FlattenAll(string why)
		{
			CancelAllEntries();
			if (Position.MarketPosition == MarketPosition.Flat || flattenBar == CurrentBars[0]) return;
			flattenBar = CurrentBars[0];
			if (Position.MarketPosition == MarketPosition.Long) ExitLong(); else ExitShort();
			Log("FLATTEN: " + why);
		}

		private void CancelAllEntries() { foreach (Mod m in mods) if (Working(m.Entry)) CancelOrder(m.Entry); }

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

		private Mod BySig(string sig)
		{
			if (mods == null || string.IsNullOrEmpty(sig)) return null;
			foreach (Mod m in mods) if (m.Sig == sig) return m;
			return null;
		}

		protected override void OnOrderUpdate(Order order, double limitPrice, double stopPrice, int quantity, int filled, double averageFillPrice,
			OrderState orderState, DateTime time, ErrorCode error, string nativeError)
		{
			Mod m = BySig(order.Name);
			if (m != null) m.Entry = order;
			if (orderState == OrderState.Rejected)
				Print(string.Format("NQPullbackDayEngine | {0} REJECTED: {1} {2}", order.Name, error, nativeError));
		}

		protected override void OnExecutionUpdate(Execution execution, string executionId, double price, int quantity,
			MarketPosition marketPosition, string orderId, DateTime time)
		{
			if (execution.Order == null) return;
			Mod m = BySig(execution.Order.Name);
			if (m != null)
			{
				if (!m.InTrade)
				{
					m.InTrade = true; m.Trades++; tradesToday++; m.EntryPx = price;
					if (m.Kind == KindVwap) { m.Done = true; m.Armed = false; }
					Log(string.Format("{0} filled @ {1}", m.Sig, Fmt(price)));
				}
				m.OpenQty += quantity;
				if (m.Kind == KindSeq && execution.Order.OrderState == OrderState.Filled)
				{
					double fill = execution.Order.AverageFillPrice;
					if (fill <= m.PendingStop) { ExitLong(0, m.OpenQty, "MSEQ bad fill", m.Sig); return; }
					m.Tgt = Instrument.MasterInstrument.RoundToTickSize(fill + MseqTargetR * (fill - m.PendingStop));
					if (m.Tgt <= fill) m.Tgt = fill + TickSize;
					SetProfitTarget(m.Sig, CalculationMode.Price, m.Tgt);
				}
				return;
			}
			Mod from = BySig(execution.Order.FromEntrySignal);
			if (from != null)
			{
				from.OpenQty = Math.Max(0, from.OpenQty - quantity);
				if (from.OpenQty == 0) from.InTrade = false;
			}
			else if (Position.MarketPosition == MarketPosition.Flat)
				foreach (Mod x in mods) { x.OpenQty = 0; x.InTrade = false; }
		}

		private void ProcessClosedTrades()
		{
			int count = SystemPerformance.AllTrades.Count;
			for (int i = tradesProcessed; i < count; i++)
			{
				double pnl = SystemPerformance.AllTrades[i].ProfitCurrency;
				totalTrades++; netPnl += pnl; dailyPnl += pnl;
				if (pnl > 0) { totalWins++; grossWin += pnl; lossStreak = 0; }
				else { grossLoss -= pnl; lossStreak++; }
				if (MaxConsecLosses > 0 && lossStreak >= MaxConsecLosses && !dayHalted)
				{
					dayHalted = true; haltReason = lossStreak + " consecutive losses"; CancelAllEntries();
				}
			}
			if (count > tradesProcessed)
				Log(string.Format("CLOSED | day ${0:0.00} | net ${1:0.00} | trades {2}", dailyPnl, netPnl, totalTrades));
			tradesProcessed = count;
			if (Position.MarketPosition == MarketPosition.Flat)
				foreach (Mod x in mods) if (x.InTrade) { x.InTrade = false; x.OpenQty = 0; }
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
		private void Log(string m) { if (PrintLog) Print(string.Format("{0} | NQPDE | {1}", Time[0].ToString("yyyy-MM-dd HH:mm", CultureInfo.InvariantCulture), m)); }
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
			sb.AppendLine("NQ PULLBACK-DAY ENGINE");
			sb.AppendLine(string.Format("ATRd {0:0.0} | prev-day move {1} ATR (2d {6}) | trades today {2}/{3}", todayAtr, double.IsNaN(prevRet) ? "-" : prevRet.ToString("0.00"), tradesToday, MaxTradesPerDay, 0, 0, double.IsNaN(prevRet2) ? "-" : prevRet2.ToString("0.00")));
			sb.AppendLine(dayStatus + (dayHalted ? " | HALTED: " + haltReason : ""));
			StringBuilder mm = new StringBuilder();
			foreach (Mod m in mods) if (m.Enabled) mm.Append(m.Sig + (m.InTrade ? "*" : Working(m.Entry) ? "~" : "") + " ");
			sb.AppendLine("Modules: " + mm.ToString() + " (* in trade, ~ order working)");
			sb.AppendLine(string.Format("Day ${0:0.00} | Total {1} tr | WR {2:0.0}% | PF {3:0.00} | ${4:0.00}", dailyPnl, totalTrades, totalTrades > 0 ? 100.0 * totalWins / totalTrades : 0, pf, netPnl));
			if (isLive && MaxTrailingDrawdown > 0) sb.AppendLine(string.Format("Live DD ${0:0.00} / ${1:0}{2}", livePeak - liveEquity, MaxTrailingDrawdown, accountHalted ? " ACCOUNT HALTED" : ""));
			Draw.TextFixed(this, "NQPDE_Dash", sb.ToString(), TextPosition.TopRight, Brushes.White, dashFont, Brushes.Transparent, Brushes.Black, 75);
		}
		#endregion

		#region Properties
		[NinjaScriptProperty][Display(Name = "Use pullback-day filter", Order = 1, GroupName = "01. Edge")] public bool UsePullbackFilter { get; set; }
		[NinjaScriptProperty][Range(-5.0, 5.0)][Display(Name = "Pullback: max prior-day move with trend (x ATRd)", Order = 2, GroupName = "01. Edge")] public double PullbackMaxRet { get; set; }
		[NinjaScriptProperty][Range(0.0, 5.0)][Display(Name = "Skip if 2-day move with trend > (x ATRd, 0 = off)", Order = 5, GroupName = "01. Edge")] public double SkipTwoDayMove { get; set; }
		[NinjaScriptProperty][Range(0.05, 1.0)][Display(Name = "Stop cap ORB/VWAP (x ATRd)", Order = 3, GroupName = "01. Edge")] public double StopCapAtr { get; set; }
		[NinjaScriptProperty][Range(0.0, 1.0)][Display(Name = "VWAP extension (x ATRd)", Order = 4, GroupName = "01. Edge")] public double VwapExtensionAtr { get; set; }

		[NinjaScriptProperty][Display(Name = "ORB60 on", Order = 10, GroupName = "02. Modules")] public bool UseOrb60 { get; set; }
		[NinjaScriptProperty][Range(0.2, 5.0)][Display(Name = "ORB60 target (R)", Order = 11, GroupName = "02. Modules")] public double Orb60TargetR { get; set; }
		[NinjaScriptProperty][Display(Name = "VWAP60 on", Order = 12, GroupName = "02. Modules")] public bool UseVwap60 { get; set; }
		[NinjaScriptProperty][Range(0.2, 5.0)][Display(Name = "VWAP60 target (R)", Order = 13, GroupName = "02. Modules")] public double Vwap60TargetR { get; set; }
		[NinjaScriptProperty][Display(Name = "ORB30 on", Order = 14, GroupName = "02. Modules")] public bool UseOrb30 { get; set; }
		[NinjaScriptProperty][Range(0.2, 5.0)][Display(Name = "ORB30 target (R)", Order = 15, GroupName = "02. Modules")] public double Orb30TargetR { get; set; }
		[NinjaScriptProperty][Display(Name = "ORB15 on", Order = 16, GroupName = "02. Modules")] public bool UseOrb15 { get; set; }
		[NinjaScriptProperty][Range(0.2, 5.0)][Display(Name = "ORB15 target (R)", Order = 17, GroupName = "02. Modules")] public double Orb15TargetR { get; set; }
		[NinjaScriptProperty][Display(Name = "VWAP30 on", Order = 18, GroupName = "02. Modules")] public bool UseVwap30 { get; set; }
		[NinjaScriptProperty][Range(0.2, 5.0)][Display(Name = "VWAP30 target (R)", Order = 19, GroupName = "02. Modules")] public double Vwap30TargetR { get; set; }
		[NinjaScriptProperty][Display(Name = "MSEQ (5-min) on", Order = 20, GroupName = "02. Modules")] public bool UseMseq { get; set; }
		[NinjaScriptProperty][Range(2, 8)][Display(Name = "MSEQ candles (N)", Order = 21, GroupName = "02. Modules")] public int MseqBars { get; set; }
		[NinjaScriptProperty][Range(0.2, 5.0)][Display(Name = "MSEQ target (R)", Order = 22, GroupName = "02. Modules")] public double MseqTargetR { get; set; }
		[NinjaScriptProperty][Range(0.5, 5.0)][Display(Name = "MSEQ stop multiplier", Order = 23, GroupName = "02. Modules")] public double MseqStopMult { get; set; }
		[NinjaScriptProperty][Range(930, 1559)][Display(Name = "MSEQ first signal bar (ET HHmm)", Order = 24, GroupName = "02. Modules")] public int MseqFirst { get; set; }
		[NinjaScriptProperty][Range(930, 1559)][Display(Name = "MSEQ last signal bar (ET HHmm)", Order = 25, GroupName = "02. Modules")] public int MseqLast { get; set; }

		[NinjaScriptProperty][Range(930, 1559)][Display(Name = "Entry start ORB/VWAP (ET HHmm)", Order = 30, GroupName = "03. Hours (ET)")] public int EntryStart { get; set; }
		[NinjaScriptProperty][Range(1000, 1559)][Display(Name = "ORB last entry (ET HHmm)", Order = 31, GroupName = "03. Hours (ET)")] public int OrbLastEntry { get; set; }
		[NinjaScriptProperty][Range(1000, 1559)][Display(Name = "VWAP last entry (ET HHmm)", Order = 32, GroupName = "03. Hours (ET)")] public int VwapLastEntry { get; set; }
		[NinjaScriptProperty][Range(1000, 1659)][Display(Name = "Flatten time (ET HHmm)", Order = 33, GroupName = "03. Hours (ET)")] public int FlattenTime { get; set; }
		[NinjaScriptProperty][Display(Name = "News times (ET HH:mm list)", Order = 34, GroupName = "03. Hours (ET)")] public string NewsTimes { get; set; }
		[NinjaScriptProperty][Range(0, 120)][Display(Name = "News minutes before", Order = 35, GroupName = "03. Hours (ET)")] public int NewsMinutesBefore { get; set; }
		[NinjaScriptProperty][Range(0, 120)][Display(Name = "News minutes after", Order = 36, GroupName = "03. Hours (ET)")] public int NewsMinutesAfter { get; set; }
		[NinjaScriptProperty][Display(Name = "Pause file (create it to pause)", Order = 37, GroupName = "03. Hours (ET)")] public string PauseFile { get; set; }

		[NinjaScriptProperty][Range(1, 50)][Display(Name = "Contracts per module", Order = 40, GroupName = "04. Prop firm")] public int ContractsPerModule { get; set; }
		[NinjaScriptProperty][Range(0, 6)][Display(Name = "Max open modules (0 = no limit)", Order = 41, GroupName = "04. Prop firm")] public int MaxOpenModules { get; set; }
		[NinjaScriptProperty][Range(0.0, double.MaxValue)][Display(Name = "Max $ risk per trade (0 = off)", Order = 42, GroupName = "04. Prop firm")] public double MaxRiskPerTrade { get; set; }
		[NinjaScriptProperty][Range(0.0, double.MaxValue)][Display(Name = "Daily loss limit $ (flattens, 0 = off)", Order = 43, GroupName = "04. Prop firm")] public double DailyLossLimit { get; set; }
		[NinjaScriptProperty][Range(0.0, double.MaxValue)][Display(Name = "Daily profit target $ (0 = off)", Order = 44, GroupName = "04. Prop firm")] public double DailyProfitTarget { get; set; }
		[NinjaScriptProperty][Range(1, 50)][Display(Name = "Max trades per day (hard)", Order = 45, GroupName = "04. Prop firm")] public int MaxTradesPerDay { get; set; }
		[NinjaScriptProperty][Range(0, 20)][Display(Name = "Stop day after N losses (0 = off)", Order = 46, GroupName = "04. Prop firm")] public int MaxConsecLosses { get; set; }
		[NinjaScriptProperty][Range(0.0, double.MaxValue)][Display(Name = "Trailing drawdown $ (live, 0 = off)", Order = 47, GroupName = "04. Prop firm")] public double MaxTrailingDrawdown { get; set; }
		[NinjaScriptProperty][Range(0.0, double.MaxValue)][Display(Name = "Drawdown buffer $", Order = 48, GroupName = "04. Prop firm")] public double DrawdownBuffer { get; set; }

		[Display(Name = "Show dashboard", Order = 50, GroupName = "05. Display")] public bool ShowDashboard { get; set; }
		[Display(Name = "Print log", Order = 51, GroupName = "05. Display")] public bool PrintLog { get; set; }
		#endregion
	}
}
