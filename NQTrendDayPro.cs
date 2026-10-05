//
// NQ Trend Day PRO - MNQ intraday strategy for prop-firm accounts (NinjaTrader 8, single file)
// ------------------------------------------------------------------------------------------------
// EDGE: intraday trend continuation on trend days. The daily bias is the prior RTH close vs the SMA(20) of RTH
// closes; only trades in that direction are allowed.
//   Module ORB  : 60-minute opening range (09:30-10:30 ET). A stop order 1 tick beyond the range, on the bias side
//                 only (10:30 to OrbLastEntry). Re-arms once price closes back inside the range. Max 2 per day.
//   Module VWAP : after 10:30, once a bar closes beyond the range and >= VwapExtensionAtr x daily ATR away from
//                 VWAP, a limit order rests at VWAP (moved every bar) until VwapLastEntry. Max 1 per day.
// EXITS (two legs per trade, separate signal names):
//   Leg 1 (ContractsTp1)   : target Tp1R x risk.
//   Leg 2 (ContractsRunner): target Tp2R x risk. After leg 1 fills, the runner's stop moves to breakeven + offset.
//   Initial stop           : opposite side of the range, capped at StopCapAtr x daily ATR(14). The VWAP module
//                            uses StopCapAtr x ATR directly.
//   Time exit              : everything flat at FlattenTime (ET).
// PROP-FIRM LAYER: max daily loss (flattens and stops for the day), optional daily profit target, max trades per
//   day (hard counter), max consecutive losses per day, max contracts, max $ risk per trade, trailing drawdown
//   guard (live only), trading hours in ET, news blackout times, and a MANUAL PAUSE FILE.
//   Manual pause: create the file named in "Pause file" and the strategy cancels pending entries and opens nothing
//   new. Delete the file to resume. No restart needed.
// NO LOOK-AHEAD: Calculate.OnBarClose. Every decision uses completed bars only. The daily ATR, SMA and bias are
//   built from finished RTH days. Orders placed at a bar close become active from the next bar.
// HISTORICAL vs REALTIME: account-level guards (trailing drawdown) run only in State.Realtime and measure from the
//   moment the strategy goes live. Historical orders are converted with GetRealtimeOrder on the transition.
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
	public class NQTrendDayPro : Strategy
	{
		private const string OrbL1 = "ORB1", OrbL2 = "ORB2", VwpL1 = "VWP1", VwpL2 = "VWP2";
		private const int RthOpen = 570, RthClose = 960;		// 09:30 / 16:00 ET in minutes

		#region Fields
		private TimeZoneInfo etZone;
		private SimpleFont dashFont;
		private bool badTimeframe;

		// RTH daily statistics (from completed RTH days only)
		private int rthDay = -1;
		private double dayHigh, dayLow, dayClose, prevRthClose = double.NaN, atrDaily = double.NaN, atrPrevClose = double.NaN;
		private bool dayHasBars;
		private int atrCount;
		private List<double> rthCloses;

		// day state
		private int trendDir;
		private double todayAtr, orHigh, orLow, vwapPv, vwapVol, vwap;
		private int orBars;
		private bool orReady, dayTradable, dayHalted;
		private string dayStatus = "waiting", haltReason = string.Empty;
		private int tradesToday, lossStreak;
		private double dailyPnl;
		private List<int> newsMinutes;

		// modules
		private Order orb1, orb2, vwp1, vwp2;
		private bool orbArmed, orbInTrade, vwpArmed, vwpDone, vwpInTrade;
		private int orbTrades, orbQty, vwpQty;
		private double orbPnl, vwpPnl, orbRisk, vwpRisk, orbEntry, vwpEntry;

		// accounting / guards
		private int tradesProcessed, totalTrades, totalWins;
		private double grossWin, grossLoss, netPnl;
		private int flattenBar = -1;
		private bool isLive, accountHalted;
		private double liveBaseline, livePeak, liveEquity;
		#endregion

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Description = "MNQ trend-day system: 60-min ORB + VWAP pullback in the daily-trend direction, 2-leg exits (TP1 + BE runner), full prop-firm risk layer.";
				Name = "NQTrendDayPro";
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

				// strategy (few, logical parameters)
				RangeMinutes = 60; StopCapAtr = 0.25; Tp1R = 1.0; Tp2R = 2.0; BreakevenAfterTp1 = true; BreakevenOffsetTicks = 1;
				VwapExtensionAtr = 0.10; UseOrb = true; UseVwap = true;
				// sessions (ET, HHmm)
				OrbLastEntry = 1300; VwapLastEntry = 1430; FlattenTime = 1555;
				NewsTimes = "08:30,10:00,14:00"; NewsMinutesBefore = 2; NewsMinutesAfter = 5;
				// sizing & prop firm
				ContractsTp1 = 1; ContractsRunner = 1; MaxContracts = 4; MaxRiskPerTrade = 500;
				DailyLossLimit = 600; DailyProfitTarget = 0; FlattenOnProfitTarget = false; MaxTradesPerDay = 10; MaxConsecLosses = 2;
				MaxTrailingDrawdown = 2000; DrawdownBuffer = 200;
				PauseFile = "pause_trading.txt";
				ShowDashboard = true; PrintLog = true;
			}
			else if (State == State.DataLoaded)
			{
				rthCloses = new List<double>();
				dashFont = new SimpleFont("Consolas", 12);
				try { etZone = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time"); } catch { etZone = null; }
				newsMinutes = ParseTimes(NewsTimes);
				badTimeframe = !(BarsPeriod.BarsPeriodType == BarsPeriodType.Minute && BarsPeriod.Value == 1);
				if (badTimeframe)
					Print("NQTrendDayPro | Needs a 1-MINUTE MNQ chart (ETH trading hours).");
			}
			else if (State == State.Realtime)
			{
				orb1 = RT(orb1); orb2 = RT(orb2); vwp1 = RT(vwp1); vwp2 = RT(vwp2);
				isLive = true; liveBaseline = netPnl; livePeak = 0; liveEquity = 0; accountHalted = false;
				Print(string.Format("NQTrendDayPro | LIVE {0} on {1} | historical: {2} trades, net ${3:0.00}", Instrument.FullName, Account.Name, totalTrades, netPnl));
			}
		}

		public override string DisplayName { get { return "NQ Trend Day PRO"; } }

		private Order RT(Order o) { return o != null ? GetRealtimeOrder(o) : null; }

		protected override void OnBarUpdate()
		{
			if (BarsInProgress != 0 || CurrentBar < 2 || badTimeframe)
				return;

			DateTime etClose = ToEt(Time[0]);
			DateTime etOpen = etClose.AddMinutes(-1);
			int openMin = etOpen.Hour * 60 + etOpen.Minute;
			int closeMin = etClose.Hour * 60 + etClose.Minute;
			int etDate = etOpen.Year * 10000 + etOpen.Month * 100 + etOpen.Day;

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
				vwapPv += (High[0] + Low[0] + Close[0]) / 3.0 * vol; vwapVol += vol; vwap = vwapPv / vwapVol;
				if (openMin < RthOpen + RangeMinutes)
				{
					if (orBars == 0) { orHigh = High[0]; orLow = Low[0]; } else { orHigh = Math.Max(orHigh, High[0]); orLow = Math.Min(orLow, Low[0]); }
					orBars++;
					if (openMin == RthOpen + RangeMinutes - 1) { orReady = true; orbArmed = true; }
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
			else if (inRth && etDate == rthDay && orReady && dayTradable)
			{
				ManageOrb(closeMin);
				ManageVwap(openMin, closeMin);
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
				atrPrevClose = dayClose; prevRthClose = dayClose;
				rthCloses.Add(dayClose);
				while (rthCloses.Count > 20) rthCloses.RemoveAt(0);
			}
			rthDay = etDate; dayHasBars = false; orBars = 0; orReady = false; vwapPv = 0; vwapVol = 0; vwap = 0;
			todayAtr = atrDaily; trendDir = 0; dayHalted = false; haltReason = string.Empty; tradesToday = 0; lossStreak = 0; dailyPnl = 0;
			orbArmed = false; orbTrades = 0; vwpArmed = false; vwpDone = false;
			if (rthCloses.Count >= 15 && !double.IsNaN(prevRthClose))
			{
				double s = 0; foreach (double x in rthCloses) s += x;
				double sma = s / rthCloses.Count;
				trendDir = prevRthClose > sma ? 1 : (prevRthClose < sma ? -1 : 0);
			}
			dayTradable = trendDir != 0 && atrCount >= 14 && !double.IsNaN(todayAtr);
			dayStatus = dayTradable ? (trendDir == 1 ? "bias LONG" : "bias SHORT") : (atrCount < 14 ? "warming up" : "no bias");
		}
		#endregion

		#region Entry modules
		private void ManageOrb(int closeMin)
		{
			if (!UseOrb)
				return;
			bool window = closeMin < Hm(OrbLastEntry);
			if (!window) { CancelModule(true); return; }
			if (!orbArmed && !orbInTrade && !Working(orb1) && !Working(orb2) && orbTrades > 0 && orbTrades < 2 && Close[0] < orHigh && Close[0] > orLow)
				orbArmed = true;
			if (!orbArmed || orbInTrade || Working(orb1) || Working(orb2) || orbTrades >= 2)
				return;
			int d = trendDir;
			double entry = d == 1 ? orHigh + TickSize : orLow - TickSize;
			double opp = d == 1 ? orLow - TickSize : orHigh + TickSize;
			int stopTicks = Math.Max(8, (int)Math.Round(Math.Min(Math.Abs(entry - opp), StopCapAtr * todayAtr) / TickSize));
			orbArmed = false;
			if (!RiskOk(stopTicks)) return;
			orbRisk = RiskUsd(stopTicks);
			ArmBrackets(OrbL1, OrbL2, stopTicks);
			bool through = d == 1 ? GetCurrentAsk() >= entry : GetCurrentBid() <= entry;
			if (ContractsTp1 > 0) SubmitEntry(OrbL1, d, ContractsTp1, entry, through ? 0 : 1);
			if (ContractsRunner > 0) SubmitEntry(OrbL2, d, ContractsRunner, entry, through ? 0 : 1);
			Log(string.Format("ORB {0} stop-entry @ {1} | SL {2}t | TP1 {3:0.##}R TP2 {4:0.##}R | risk ${5:0}", d == 1 ? "BUY" : "SELL", Fmt(entry), stopTicks, Tp1R, Tp2R, orbRisk));
		}

		private void ManageVwap(int openMin, int closeMin)
		{
			if (!UseVwap)
				return;
			bool window = closeMin < Hm(VwapLastEntry);
			if (Working(vwp1) || Working(vwp2))
			{
				if (!window) { CancelModule(false); vwpDone = true; return; }
				double px = Instrument.MasterInstrument.RoundToTickSize(vwap);
				if (Working(vwp1) && Math.Abs(px - vwp1.LimitPrice) >= TickSize / 2) ChangeOrder(vwp1, vwp1.Quantity, px, 0);
				if (Working(vwp2) && Math.Abs(px - vwp2.LimitPrice) >= TickSize / 2) ChangeOrder(vwp2, vwp2.Quantity, px, 0);
				return;
			}
			if (vwpDone || vwpInTrade || vwpArmed || !window || openMin < RthOpen + RangeMinutes)
				return;
			int d = trendDir;
			bool extended = d == 1 ? Close[0] > orHigh && Close[0] >= vwap + VwapExtensionAtr * todayAtr
								   : Close[0] < orLow && Close[0] <= vwap - VwapExtensionAtr * todayAtr;
			if (!extended)
				return;
			int stopTicks = Math.Max(8, (int)Math.Round(StopCapAtr * todayAtr / TickSize));
			if (!RiskOk(stopTicks)) { vwpDone = true; return; }
			vwpRisk = RiskUsd(stopTicks);
			ArmBrackets(VwpL1, VwpL2, stopTicks);
			double lim = Instrument.MasterInstrument.RoundToTickSize(vwap);
			if (ContractsTp1 > 0) SubmitEntry(VwpL1, d, ContractsTp1, lim, 2);
			if (ContractsRunner > 0) SubmitEntry(VwpL2, d, ContractsRunner, lim, 2);
			vwpArmed = true;
			Log(string.Format("VWAP {0} limit @ {1} (follows VWAP) | SL {2}t | risk ${3:0}", d == 1 ? "BUY" : "SELL", Fmt(lim), stopTicks, vwpRisk));
		}

		// kind: 0 market, 1 stop-market, 2 limit
		private void SubmitEntry(string sig, int d, int qty, double price, int kind)
		{
			if (d == 1)
			{
				if (kind == 0) EnterLong(qty, sig);
				else if (kind == 1) EnterLongStopMarket(0, true, qty, price, sig);
				else EnterLongLimit(0, true, qty, price, sig);
			}
			else
			{
				if (kind == 0) EnterShort(qty, sig);
				else if (kind == 1) EnterShortStopMarket(0, true, qty, price, sig);
				else EnterShortLimit(0, true, qty, price, sig);
			}
		}

		private void ArmBrackets(string s1, string s2, int stopTicks)
		{
			SetStopLoss(s1, CalculationMode.Ticks, stopTicks, false);
			SetProfitTarget(s1, CalculationMode.Ticks, Math.Max(1, (int)Math.Round(stopTicks * Tp1R)));
			SetStopLoss(s2, CalculationMode.Ticks, stopTicks, false);
			SetProfitTarget(s2, CalculationMode.Ticks, Math.Max(1, (int)Math.Round(stopTicks * Tp2R)));
		}
		#endregion

		#region Risk layer
		private double RiskUsd(int stopTicks)
		{
			int q = ContractsTp1 + ContractsRunner;
			return q * ((stopTicks + 1) * TickSize * Instrument.MasterInstrument.PointValue + 1.0);
		}

		private bool RiskOk(int stopTicks)
		{
			if (ContractsTp1 + ContractsRunner > MaxContracts) { dayStatus = "contracts > max"; return false; }
			double r = RiskUsd(stopTicks);
			if (MaxRiskPerTrade > 0 && r > MaxRiskPerTrade) { dayStatus = string.Format("skip: risk ${0:0} > max", r); Log(dayStatus); return false; }
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
				dayHalted = true; haltReason = "daily profit target";
				CancelAllEntries();
				if (FlattenOnProfitTarget) FlattenAll(haltReason);
			}
			if (isLive)
			{
				liveEquity = (netPnl - liveBaseline) + unreal;
				livePeak = Math.Max(livePeak, liveEquity);
				if (!accountHalted && MaxTrailingDrawdown > 0 && livePeak - liveEquity >= MaxTrailingDrawdown - DrawdownBuffer)
				{
					accountHalted = true; haltReason = "trailing drawdown guard";
					FlattenAll(haltReason);
					Print("NQTrendDayPro | ACCOUNT HALTED: trailing drawdown guard");
				}
			}
		}

		private void FlattenAll(string why)
		{
			CancelAllEntries();
			if (Position.MarketPosition == MarketPosition.Flat || flattenBar == CurrentBar) return;
			flattenBar = CurrentBar;
			if (Position.MarketPosition == MarketPosition.Long) ExitLong(); else ExitShort();
			Log("FLATTEN: " + why);
		}

		private void CancelAllEntries() { CancelModule(true); CancelModule(false); }

		private void CancelModule(bool orb)
		{
			if (orb) { if (Working(orb1)) CancelOrder(orb1); if (Working(orb2)) CancelOrder(orb2); }
			else { if (Working(vwp1)) CancelOrder(vwp1); if (Working(vwp2)) CancelOrder(vwp2); }
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
			switch (order.Name)
			{
				case OrbL1: orb1 = order; break;
				case OrbL2: orb2 = order; break;
				case VwpL1: vwp1 = order; break;
				case VwpL2: vwp2 = order; break;
				default: return;
			}
			if (orderState == OrderState.Rejected)
				Print(string.Format("NQTrendDayPro | {0} REJECTED: {1} {2}", order.Name, error, nativeError));
		}

		protected override void OnExecutionUpdate(Execution execution, string executionId, double price, int quantity,
			MarketPosition marketPosition, string orderId, DateTime time)
		{
			if (execution.Order == null) return;
			string name = execution.Order.Name, from = execution.Order.FromEntrySignal;
			bool isOrbEntry = name == OrbL1 || name == OrbL2, isVwpEntry = name == VwpL1 || name == VwpL2;
			if (isOrbEntry)
			{
				if (!orbInTrade) { orbInTrade = true; orbTrades++; tradesToday++; orbEntry = price; Log("ORB filled @ " + Fmt(price)); }
				orbQty += quantity;
			}
			else if (isVwpEntry)
			{
				if (!vwpInTrade) { vwpInTrade = true; vwpDone = true; vwpArmed = false; tradesToday++; vwpEntry = price; Log("VWAP filled @ " + Fmt(price)); }
				vwpQty += quantity;
			}
			else if (from == OrbL1 || from == OrbL2) orbQty = Math.Max(0, orbQty - quantity);
			else if (from == VwpL1 || from == VwpL2) vwpQty = Math.Max(0, vwpQty - quantity);

			// TP1 filled -> runner stop to breakeven
			if (BreakevenAfterTp1 && name == "Profit target" && (from == OrbL1 || from == VwpL1))
			{
				string runner = from == OrbL1 ? OrbL2 : VwpL2;
				double entry = from == OrbL1 ? orbEntry : vwpEntry;
				int d = Position.MarketPosition == MarketPosition.Long ? 1 : -1;
				if (Position.MarketPosition != MarketPosition.Flat)
				{
					SetStopLoss(runner, CalculationMode.Price, entry + d * BreakevenOffsetTicks * TickSize, false);
					Log("TP1 hit -> runner stop to breakeven");
				}
			}
		}

		private void ProcessClosedTrades()
		{
			int count = SystemPerformance.AllTrades.Count;
			for (int i = tradesProcessed; i < count; i++)
			{
				Trade tr = SystemPerformance.AllTrades[i];
				string en = tr.Entry != null && tr.Entry.Order != null ? tr.Entry.Order.Name : string.Empty;
				if (en == VwpL1 || en == VwpL2) vwpPnl += tr.ProfitCurrency; else orbPnl += tr.ProfitCurrency;
			}
			tradesProcessed = count;
			bool flat = Position.MarketPosition == MarketPosition.Flat;
			if (orbInTrade && (orbQty <= 0 || flat)) { Finish("ORB", orbPnl); orbInTrade = false; orbQty = 0; orbPnl = 0; }
			if (vwpInTrade && (vwpQty <= 0 || flat)) { Finish("VWAP", vwpPnl); vwpInTrade = false; vwpQty = 0; vwpPnl = 0; }
		}

		private void Finish(string module, double pnl)
		{
			totalTrades++; netPnl += pnl; dailyPnl += pnl;
			if (pnl > 0) { totalWins++; grossWin += pnl; lossStreak = 0; }
			else { grossLoss -= pnl; lossStreak++; }
			Log(string.Format("CLOSED {0} ${1:0.00} | day ${2:0.00} | net ${3:0.00}", module, pnl, dailyPnl, netPnl));
			if (MaxConsecLosses > 0 && lossStreak >= MaxConsecLosses && !dayHalted)
			{
				dayHalted = true; haltReason = lossStreak + " consecutive losses"; CancelAllEntries();
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
		private void Log(string m) { if (PrintLog) Print(string.Format("{0} | NQTDP | {1}", Time[0].ToString("yyyy-MM-dd HH:mm", CultureInfo.InvariantCulture), m)); }
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
			sb.AppendLine("NQ TREND DAY PRO");
			sb.AppendLine(string.Format("Bias {0} | ATRd {1:0.0} | trades today {2}/{3}", trendDir == 1 ? "LONG" : trendDir == -1 ? "SHORT" : "-", todayAtr, tradesToday, MaxTradesPerDay));
			sb.AppendLine(orReady ? string.Format("Range {0} - {1} | VWAP {2}", Fmt(orLow), Fmt(orHigh), Fmt(vwap)) : "Range building...");
			sb.AppendLine(string.Format("Day ${0:0.00} | {1}{2}", dailyPnl, dayStatus, dayHalted ? " | HALTED: " + haltReason : ""));
			sb.AppendLine(string.Format("Total {0} tr | WR {1:0.0}% | PF {2:0.00} | ${3:0.00}", totalTrades, totalTrades > 0 ? 100.0 * totalWins / totalTrades : 0, pf, netPnl));
			if (isLive) sb.AppendLine(string.Format("Live DD ${0:0.00} / ${1:0}{2}", livePeak - liveEquity, MaxTrailingDrawdown, accountHalted ? " ACCOUNT HALTED" : ""));
			Draw.TextFixed(this, "NQTDP_Dash", sb.ToString(), TextPosition.TopRight, Brushes.White, dashFont, Brushes.Transparent, Brushes.Black, 75);
		}
		#endregion

		#region Properties
		[NinjaScriptProperty][Range(15, 120)][Display(Name = "Opening range (min)", Order = 1, GroupName = "01. Strategy")] public int RangeMinutes { get; set; }
		[NinjaScriptProperty][Range(0.05, 1.0)][Display(Name = "Stop cap (x daily ATR)", Order = 2, GroupName = "01. Strategy")] public double StopCapAtr { get; set; }
		[NinjaScriptProperty][Range(0.25, 5.0)][Display(Name = "TP1 (R)", Order = 3, GroupName = "01. Strategy")] public double Tp1R { get; set; }
		[NinjaScriptProperty][Range(0.25, 10.0)][Display(Name = "TP2 runner (R)", Order = 4, GroupName = "01. Strategy")] public double Tp2R { get; set; }
		[NinjaScriptProperty][Display(Name = "Breakeven after TP1", Order = 5, GroupName = "01. Strategy")] public bool BreakevenAfterTp1 { get; set; }
		[NinjaScriptProperty][Range(0, 20)][Display(Name = "Breakeven offset (ticks)", Order = 6, GroupName = "01. Strategy")] public int BreakevenOffsetTicks { get; set; }
		[NinjaScriptProperty][Range(0.0, 1.0)][Display(Name = "VWAP extension (x daily ATR)", Order = 7, GroupName = "01. Strategy")] public double VwapExtensionAtr { get; set; }
		[NinjaScriptProperty][Display(Name = "Use ORB module", Order = 8, GroupName = "01. Strategy")] public bool UseOrb { get; set; }
		[NinjaScriptProperty][Display(Name = "Use VWAP module", Order = 9, GroupName = "01. Strategy")] public bool UseVwap { get; set; }

		[NinjaScriptProperty][Range(1000, 1559)][Display(Name = "ORB last entry (ET HHmm)", Order = 20, GroupName = "02. Hours (ET)")] public int OrbLastEntry { get; set; }
		[NinjaScriptProperty][Range(1000, 1559)][Display(Name = "VWAP last entry (ET HHmm)", Order = 21, GroupName = "02. Hours (ET)")] public int VwapLastEntry { get; set; }
		[NinjaScriptProperty][Range(1000, 1659)][Display(Name = "Flatten time (ET HHmm)", Order = 22, GroupName = "02. Hours (ET)")] public int FlattenTime { get; set; }
		[NinjaScriptProperty][Display(Name = "News times (ET HH:mm list)", Order = 23, GroupName = "02. Hours (ET)")] public string NewsTimes { get; set; }
		[NinjaScriptProperty][Range(0, 120)][Display(Name = "News minutes before", Order = 24, GroupName = "02. Hours (ET)")] public int NewsMinutesBefore { get; set; }
		[NinjaScriptProperty][Range(0, 120)][Display(Name = "News minutes after", Order = 25, GroupName = "02. Hours (ET)")] public int NewsMinutesAfter { get; set; }
		[NinjaScriptProperty][Display(Name = "Pause file (create it to pause)", Order = 26, GroupName = "02. Hours (ET)")] public string PauseFile { get; set; }

		[NinjaScriptProperty][Range(0, 50)][Display(Name = "Contracts TP1 leg", Order = 30, GroupName = "03. Prop firm")] public int ContractsTp1 { get; set; }
		[NinjaScriptProperty][Range(0, 50)][Display(Name = "Contracts runner leg", Order = 31, GroupName = "03. Prop firm")] public int ContractsRunner { get; set; }
		[NinjaScriptProperty][Range(1, 100)][Display(Name = "Max contracts", Order = 32, GroupName = "03. Prop firm")] public int MaxContracts { get; set; }
		[NinjaScriptProperty][Range(0.0, double.MaxValue)][Display(Name = "Max $ risk per trade (0 = off)", Order = 33, GroupName = "03. Prop firm")] public double MaxRiskPerTrade { get; set; }
		[NinjaScriptProperty][Range(0.0, double.MaxValue)][Display(Name = "Daily loss limit $ (flattens)", Order = 34, GroupName = "03. Prop firm")] public double DailyLossLimit { get; set; }
		[NinjaScriptProperty][Range(0.0, double.MaxValue)][Display(Name = "Daily profit target $ (0 = off)", Order = 35, GroupName = "03. Prop firm")] public double DailyProfitTarget { get; set; }
		[NinjaScriptProperty][Display(Name = "Flatten at daily profit target", Order = 36, GroupName = "03. Prop firm")] public bool FlattenOnProfitTarget { get; set; }
		[NinjaScriptProperty][Range(1, 50)][Display(Name = "Max trades per day (hard)", Order = 37, GroupName = "03. Prop firm")] public int MaxTradesPerDay { get; set; }
		[NinjaScriptProperty][Range(0, 20)][Display(Name = "Stop day after N losses (0 = off)", Order = 38, GroupName = "03. Prop firm")] public int MaxConsecLosses { get; set; }
		[NinjaScriptProperty][Range(0.0, double.MaxValue)][Display(Name = "Trailing drawdown $ (live, 0 = off)", Order = 39, GroupName = "03. Prop firm")] public double MaxTrailingDrawdown { get; set; }
		[NinjaScriptProperty][Range(0.0, double.MaxValue)][Display(Name = "Drawdown buffer $", Order = 40, GroupName = "03. Prop firm")] public double DrawdownBuffer { get; set; }

		[Display(Name = "Show dashboard", Order = 50, GroupName = "04. Display")] public bool ShowDashboard { get; set; }
		[Display(Name = "Print log", Order = 51, GroupName = "04. Display")] public bool PrintLog { get; set; }
		#endregion
	}
}
