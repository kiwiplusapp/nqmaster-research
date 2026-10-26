//
// GOLD MASTER - intraday strategy for gold futures (MGC / GC), NinjaTrader 8, single file
// ------------------------------------------------------------------------------------------------
// Run on a 1-MINUTE MGC chart (Trading hours: CME Commodities / Metals ETH, 18:00-17:00 ET). Flat by 16:50 ET.
// Research: research/mine/gold_curated.py (16 years of gold 1-minute data, MGC costs $1.90 RT + 1 tick per side).
// Modules (all in daily-ATR units; ATR = 14-day EWM of RTH 09:30-16:00 true ranges; trend = prior RTH close vs SMA20):
//   OD1030  NY open drive: if 09:30-10:30 moved >= 0.30 ATR with the daily trend, enter at 10:30; stop beyond the drive's
//           opposite extreme (max 0.5 ATR); target 0.5R.
//   ENG0408 London 4H candle (04:00-08:00 ET) closes beyond the 00:00-04:00 candle's extreme -> from 09:30 to 15:00 a stop entry
//           1 tick beyond the London candle, stop beyond its other side, target 0.5R.
//   SVWAP22 22:00 ET: price >= 0.30 ATR away from the session VWAP (from 18:00) -> fade toward it; stop 0.25 ATR, target 0.5R.
//   ENG0610 4H candle 06:00-10:00 engulfs the 02:00-06:00 candle -> 10:00-15:00 stop entry beyond it in its direction,
//           stop at half its range, target 0.5R.
//   ASIA    Asian range 20:00-24:00 ET; first breakout 00:00-06:00, only if it is with the daily trend (stop entry); stop at the other side
//           (max 0.6 ATR); target 1R.
//   ENG0206 4H candle 02:00-06:00 closes beyond the 22:00-02:00 candle's extreme -> 09:30-15:00 stop entry; stop beyond it; 0.5R.
//   LATE    14:30 ET: day move since the prior RTH close >= 0.5 ATR with the daily trend -> continue; stop 1 ATR; target 1R.
// Profiles (1 MGC per module; research, FOMC days skipped; CFD 2020-23 / CFD 2024-26 / real MGC 2024-26):
//   WinRate  (OD1030 + ENG0408 + SVWAP22): WR 64.7 / 68.8 / 70.3%, PF 1.42 / 1.74 / 1.99, 0.29 trades/day;
//            real MGC Feb-2024..Sep-2026: 192 trades, +$6,579, max DD $504.
//   Robust   (WinRate + ASIA + ENG0206)  : WR 59.4 / 61.4 / 61.9%, PF 1.22 / 1.35 / 1.37, 0.88 trades/day; real MGC: 582 trades,
//            +$13,648, max DD $1,684. Also PF 1.20 (2010-14) and 1.08 (2015-19) at today's cost ratio; WinRate was < 1 before 2020.
//   ENG0610 and LATE are Custom-only switches (ENG0610 lost money on real MGC 2024-26).
// Managed orders, one signal per module; an entry is skipped while the strategy holds or works the opposite direction.
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
	public enum GoldMasterProfile { WinRate, Robust, Custom }

	public class GoldMaster : Strategy
	{
		private const int RthOpen = 570, RthClose = 960;
		private static readonly int[] Starts = { 240, 360, 480, 600, 720 };	// session minutes of 22:00, 00:00, 02:00, 04:00, 06:00 ET
		private const string BuiltinFomc = "2024-01-31,2024-03-20,2024-05-01,2024-06-12,2024-07-31,2024-09-18,2024-11-07,2024-12-18,2025-01-29,2025-03-19,2025-05-07,2025-06-18,2025-07-30,2025-09-17,2025-10-29,2025-12-10,2026-01-28,2026-03-18,2026-04-29,2026-06-17,2026-07-29,2026-09-16,2026-10-28,2026-12-09,2027-01-27,2027-03-17,2027-04-28,2027-06-09,2027-07-28,2027-09-15,2027-10-27,2027-12-08,2028-01-26";

		private class Mod
		{
			public string Sig; public bool On; public int MaxHold;
			public bool Done, InTrade; public Order Entry; public int Dir; public int EntryBar = -1; public int ExpireMin = -1;
			public double Sl, Tp;
			public bool Def; public double DPx;		// parked stop setup (blocked by an opposite position / order)
		}
		private Mod od, e0408, svw, e0610, asia, e0206, late;
		private List<Mod> mods;

		#region Fields
		private TimeZoneInfo etZone; private SimpleFont dashFont; private bool badTimeframe; private HashSet<int> fomc;
		private int prevSm = -1; private bool fomcToday; private int sessionDate;
		// RTH statistics
		private bool rthHas; private double rthO, rthH, rthL, rthC; private int rthLastOpen;
		private double atr = double.NaN, prevRthClose = double.NaN, pdc = double.NaN; private List<double> closes = new List<double>(); private int trendDir;
		// session state
		private double svPv, svV;
		private double[] cH = new double[6], cL = new double[6], cO = new double[6], cC = new double[6]; private bool[] cHas = new bool[6];	// 4H candles: 22-02, 00-04, 02-06, 04-08, 06-10 (index by start)
		private double odH, odL; private bool odHas;
		private double asH, asL; private bool asHas, asBroken; private int asFirst, rthDays;
		private Mod pendMod; private int pendBar = -1;
		private int flattenBar = -1; private string status = "waiting";
		private double dayStartPnl, acctDayStart = double.NaN; private bool dayStopped, acctStopped;
		private double evDayStart = double.NaN, evBestDay = double.NaN; private bool targetHit;
		private int tradesProcessed, totalTrades, totalWins; private double grossWin, grossLoss, netPnl;
		#endregion

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Description = "Gold (MGC) intraday strategy: NY open drive, 4H London/Asia candle breakouts, session-VWAP fade, Asian range breakout.";
				Name = "GoldMaster";
				Calculate = Calculate.OnBarClose;
				EntriesPerDirection = 1;
				EntryHandling = EntryHandling.UniqueEntries;
				IsExitOnSessionCloseStrategy = true;
				ExitOnSessionCloseSeconds = 30;
				IsFillLimitOnTouch = false;
				MaximumBarsLookBack = MaximumBarsLookBack.Infinite;
				OrderFillResolution = OrderFillResolution.Standard;
				Slippage = 1;
				StartBehavior = StartBehavior.WaitUntilFlat;
				TimeInForce = TimeInForce.Gtc;
				RealtimeErrorHandling = RealtimeErrorHandling.IgnoreAllErrors;	// rejections handled in OnOrderUpdate
				StopTargetHandling = StopTargetHandling.PerEntryExecution;
				BarsRequiredToTrade = 20;
				IsInstantiatedOnEachOptimizationIteration = true;

				Profile = GoldMasterProfile.WinRate;
				UseOd = true; UseEng0408 = true; UseSvwap = true; UseEng0610 = true; UseAsia = true; UseEng0206 = true; UseLate = false;
				UseEng0610 = false;
				Contracts = 1; FlattenTime = 1651; SkipFomc = true; FomcDates = "";
				DailyLossLimit = 0; AccountDailyStop = 0; AccountProfitStop = 0; EvalTarget = 0; StartBalance = 50000; ConsistencyPct = 50; EvalBestDaySoFar = 0;
				EdgeMonitor = true; EdgeMonitorPause = false; EdgeMonitorStart = "2026-10-05"; PauseFile = "pause_gold.txt"; ShowDashboard = true; PrintLog = true;
			}
			else if (State == State.DataLoaded)
			{
				dashFont = new SimpleFont("Consolas", 11);
				try { etZone = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time"); } catch { etZone = null; }
				badTimeframe = !(BarsPeriod.BarsPeriodType == BarsPeriodType.Minute && BarsPeriod.Value == 1);
				if (badTimeframe) Print("GoldMaster | Needs a 1-MINUTE MGC chart.");
				fomc = new HashSet<int>();
				foreach (string raw in (BuiltinFomc + "," + (FomcDates ?? "")).Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries))
				{
					DateTime d;
					if (DateTime.TryParseExact(raw.Trim(), "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out d)) fomc.Add(d.Year * 10000 + d.Month * 100 + d.Day);
				}
				BuildModules();
			}
			else if (State == State.Realtime)
			{
				// enabled mid-day: the day started at equity now minus what the account already realized today
				try
				{
					double rp = Account.Get(AccountItem.RealizedProfitLoss, Currency.UsDollar);
					acctDayStart = AcctEquity() - rp; evDayStart = Account.Get(AccountItem.CashValue, Currency.UsDollar) - rp;
					if (double.IsNaN(evBestDay)) evBestDay = EvalBestDaySoFar;
				}
				catch { }
				if (rthDays < 60) Print("GoldMaster | WARNING: only " + rthDays + " RTH days loaded - set Days to load >= 120 (ATR / trend warm-up).");
			}
		}

		public override string DisplayName { get { return "GOLD MASTER (" + Profile + ")"; } }

		private void BuildModules()
		{
			bool c = Profile == GoldMasterProfile.Custom, rob = Profile == GoldMasterProfile.Robust;
			mods = new List<Mod>();
			od = NewMod("OD1030", c ? UseOd : UseOd, 400);
			e0408 = NewMod("ENG0408", c ? UseEng0408 : UseEng0408, 400);
			svw = NewMod("SVWAP22", c ? UseSvwap : UseSvwap, 120);
			e0610 = NewMod("ENG0610", c && UseEng0610, 400);
			asia = NewMod("ASIA", c ? UseAsia : (rob && UseAsia), 600);
			e0206 = NewMod("ENG0206", c ? UseEng0206 : (rob && UseEng0206), 400);
			late = NewMod("LATE", c && UseLate, 400);
			StringBuilder sb = new StringBuilder();
			foreach (Mod m in mods) if (m.On) sb.Append(m.Sig + " ");
			Print("GoldMaster | profile " + Profile + " | modules: " + sb.ToString());
		}
		private Mod NewMod(string sig, bool on, int hold) { Mod m = new Mod(); m.Sig = sig; m.On = on; m.MaxHold = hold; mods.Add(m); return m; }

		protected override void OnBarUpdate()
		{
			if (badTimeframe || CurrentBar < 3) return;
			DateTime etClose = ToEt(Time[0]); DateTime etOpen = etClose.AddMinutes(-1);
			int openMin = etOpen.Hour * 60 + etOpen.Minute, closeMin = etClose.Hour * 60 + etClose.Minute;
			int sm = (openMin - 1080 + 1440) % 1440;
			if (openMin >= 17 * 60 && openMin < 18 * 60) return;	// CME maintenance hour

			ProcessClosedTrades();
			if (prevSm < 0 || sm < prevSm) NewSession(etOpen);
			prevSm = sm;

			// ---- RTH statistics (09:30-16:00)
			if (openMin >= RthOpen && openMin < RthClose)
			{
				if (!rthHas) { rthO = Open[0]; rthH = High[0]; rthL = Low[0]; rthHas = true; }
				rthH = Math.Max(rthH, High[0]); rthL = Math.Min(rthL, Low[0]); rthC = Close[0]; rthLastOpen = openMin;
			}
			// ---- session VWAP (from 18:00, typical price x volume)
			double vol = Volume[0] > 0 ? Volume[0] : 1.0;
			svPv += (High[0] + Low[0] + Close[0]) / 3.0 * vol; svV += vol;
			// ---- 4H candles by start hour: 0 = 22:00, 1 = 00:00, 2 = 02:00, 3 = 04:00, 4 = 06:00 (session minutes)
			for (int k = 0; k < 5; k++)
				if (sm >= Starts[k] && sm < Starts[k] + 240)
				{
					if (!cHas[k]) { cO[k] = Open[0]; cH[k] = High[0]; cL[k] = Low[0]; cHas[k] = true; }
					cH[k] = Math.Max(cH[k], High[0]); cL[k] = Math.Min(cL[k], Low[0]); cC[k] = Close[0];
				}
			// ---- NY open drive range (09:30-10:29)
			if (openMin >= RthOpen && openMin < RthOpen + 60)
			{
				if (!odHas) { odH = High[0]; odL = Low[0]; odHas = true; }
				odH = Math.Max(odH, High[0]); odL = Math.Min(odL, Low[0]);
			}
			// ---- Asian range 20:00-23:59
			if (sm >= S(2000) && sm < S(0))
			{
				if (!asHas) { asH = High[0]; asL = Low[0]; asHas = true; }
				asH = Math.Max(asH, High[0]); asL = Math.Min(asL, Low[0]);
			}
			// ---- first Asian-range breakout 00:00-06:00 (research: the first breakout decides; both sides in one bar = no trade)
			if (asHas && asFirst == 0 && sm >= S(0) && sm < S(600))
			{
				bool up = High[0] >= asH + TickSize, dn = Low[0] <= asL - TickSize;
				asFirst = up && dn ? 2 : (up ? 1 : (dn ? -1 : 0));
				if (asFirst == 2 && asia.InTrade) ExitModule(asia, "both Asian sides broken in one bar");
			}

			DailyLossCheck();
			// ---- exits: flatten, time exits, expiries
			if (FlattenTime > 0 && closeMin >= Hm(FlattenTime) && closeMin < 18 * 60) { FlattenAll("end of day"); UpdateDashboard(); return; }
			foreach (Mod m in mods)
			{
				if (m.InTrade && m.EntryBar >= 0 && CurrentBar - m.EntryBar >= m.MaxHold) ExitModule(m, "time exit");
				if (Working(m.Entry) && m.ExpireMin >= 0 && sm >= m.ExpireMin - 1) { CancelOrder(m.Entry); Log(m.Sig + " entry expired"); }
			}
			// the opposite side broke first -> no trade today
			if (asia.On && Working(asia.Entry) && asia.Dir != 0 && asFirst != 0 && asFirst != asia.Dir) { CancelOrder(asia.Entry); asBroken = true; }
			if (!CanTrade()) { CancelAllEntries(); UpdateDashboard(); return; }
			if (pendMod != null)
			{
				Mod pm = pendMod;
				if (CurrentBar - pendBar > 1 || pm.InTrade || OppPos(pm.Dir)) pendMod = null;
				else if (!OppWork(pm.Dir, pm)) { pendMod = null; SendMarket(pm); }
			}
			// parked stop setups: re-arm once no opposite position / order remains; drop if touched meanwhile (research drops a fill
			// against an open opposite position) or expired
			foreach (Mod m in mods)
			{
				if (!m.Def) continue;
				bool hit = m.Dir == 1 ? High[0] >= m.DPx : Low[0] <= m.DPx;
				if (hit || m.InTrade || (m.ExpireMin >= 0 && sm >= m.ExpireMin - 1) || (m == asia && asFirst != 0)) { m.Def = false; continue; }
				if (!OppPos(m.Dir) && !OppWork(m.Dir, m)) { m.Def = false; StopEntry(m, m.Dir, m.DPx, m.Sl, m.Tp, m.ExpireMin); }
			}

			// ---- signals (evaluated at the close of the bar that OPENED at openMin)
			if (od.On && !od.Done && openMin == RthOpen + 59 && odHas) { od.Done = true; OpenDrive(); }
			if (e0408.On && !e0408.Done && openMin == 569 && cHas[1] && cHas[3]) { e0408.Done = true; Engulf(e0408, 1, 3, 2, 2); }
			if (e0206.On && !e0206.Done && openMin == 569 && cHas[0] && cHas[2]) { e0206.Done = true; Engulf(e0206, 0, 2, 2, 2); }
			if (e0610.On && !e0610.Done && openMin == 599 && cHas[2] && cHas[4]) { e0610.Done = true; Engulf(e0610, 2, 4, 0, 1); }
			if (svw.On && !svw.Done && sm >= S(2200) && sm < S(2200) + 15) { svw.Done = true; SvwapFade(); }
			if (asia.On && !asia.Done && asHas && sm >= S(0) - 1 && sm < S(600)) { asia.Done = true; AsiaArm(); }
			if (late.On && !late.Done && openMin == 869) { late.Done = true; Late(); }
			UpdateDashboard();
		}

		#region Session / daily statistics
		private void NewSession(DateTime etOpen)
		{
			EdgeDayClose();
			// finalize the previous RTH day (ATR: EWM 1/14 of RTH true ranges; trend: prior close vs SMA20 of RTH closes)
			if (rthHas)
			{
				double tr = double.IsNaN(prevRthClose) ? rthH - rthL : Math.Max(rthH - rthL, Math.Max(Math.Abs(rthH - prevRthClose), Math.Abs(rthL - prevRthClose)));
				atr = double.IsNaN(atr) ? tr : atr + (tr - atr) / 14.0;
				prevRthClose = rthC; pdc = rthLastOpen >= RthClose - 1 ? rthC : double.NaN;
				closes.Add(rthC); while (closes.Count > 20) closes.RemoveAt(0); rthDays++;
				trendDir = 0;
				if (closes.Count >= 20) { double s = 0; foreach (double x in closes) s += x; s /= closes.Count; trendDir = rthC > s ? 1 : (rthC < s ? -1 : 0); }
			}
			else pdc = double.NaN;
			rthHas = false;
			DateTime tradeDay = etOpen.Hour >= 18 ? etOpen.Date.AddDays(1) : etOpen.Date;
			sessionDate = tradeDay.Year * 10000 + tradeDay.Month * 100 + tradeDay.Day;
			fomcToday = SkipFomc && fomc.Contains(sessionDate);
			svPv = 0; svV = 0; odHas = false; asHas = false; asBroken = false; asFirst = 0; pendMod = null;
			for (int k = 0; k < 6; k++) cHas[k] = false;
			foreach (Mod m in mods) { m.Done = false; m.ExpireMin = -1; m.Dir = 0; m.Def = false; }
			dayStartPnl = netPnl; dayStopped = false; acctStopped = false; acctDayStart = AcctEquity();
			if (State == State.Realtime)
			{
				double eq = Account.Get(AccountItem.CashValue, Currency.UsDollar);
				if (double.IsNaN(evBestDay)) evBestDay = EvalBestDaySoFar;
				if (!double.IsNaN(evDayStart)) evBestDay = Math.Max(evBestDay, eq - evDayStart);
				evDayStart = eq;
			}
		}
		#endregion

		#region Modules
		private bool AtrOk { get { return !double.IsNaN(atr) && atr > 0 && closes.Count >= 15 && rthDays >= 60; } }

		private void OpenDrive()
		{
			if (!AtrOk || trendDir == 0) return;
			double mv = Close[0] - rthO;
			if (Math.Abs(mv) < 0.30 * atr) return;
			int d = mv > 0 ? 1 : -1;
			if (d != trendDir) return;
			double sl = d == 1 ? odL - TickSize : odH + TickSize, risk = (Close[0] - sl) * d;
			if (risk <= 0) return;
			if (risk > 0.5 * atr) { sl = Close[0] - d * 0.5 * atr; risk = 0.5 * atr; }
			MarketEntry(od, d, sl, Close[0] + d * 0.5 * risk);
		}

		// A = earlier 4H candle, B = later one. body 2: B closes beyond A's extreme in B's direction; body 0: B's range engulfs A's,
		// direction = B's colour. stopMode 2: beyond B's other side; 1: half of B's range from the entry level.
		private void Engulf(Mod m, int a, int b, int body, int stopMode)
		{
			if (!AtrOk) return;
			int d = 0;
			if (body == 2) { if (cC[b] > cO[b] && cC[b] > cH[a]) d = 1; else if (cC[b] < cO[b] && cC[b] < cL[a]) d = -1; }
			else { if (cH[b] >= cH[a] && cL[b] <= cL[a]) d = cC[b] > cO[b] ? 1 : (cC[b] < cO[b] ? -1 : 0); }
			if (d == 0) return;
			double px = d == 1 ? cH[b] + TickSize : cL[b] - TickSize;
			if ((d == 1 && Close[0] >= px) || (d == -1 && Close[0] <= px)) return;
			double sl = stopMode == 2 ? (d == 1 ? cL[b] - TickSize : cH[b] + TickSize) : px - d * 0.5 * (cH[b] - cL[b]);
			double risk = (px - sl) * d;
			if (risk <= 0.02 * atr || risk > 0.6 * atr) return;
			StopEntry(m, d, px, sl, px + d * 0.5 * risk, S(1500));
		}

		private void SvwapFade()
		{
			if (!AtrOk || svV <= 0) return;
			double vw = svPv / svV, dist = (Close[0] - vw) / atr;
			if (Math.Abs(dist) < 0.30) return;
			int d = dist > 0 ? -1 : 1;
			MarketEntry(svw, d, Close[0] - d * 0.25 * atr, Close[0] + d * 0.125 * atr);
		}

		private void AsiaArm()
		{
			if (!AtrOk || trendDir == 0 || asBroken || asFirst != 0) return;
			int d = trendDir;
			// if the opposite side is already broken at arming time, the day is lost
			double lvl = d == 1 ? asH + TickSize : asL - TickSize;
			if ((d == 1 && Close[0] >= lvl) || (d == -1 && Close[0] <= lvl)) return;
			double risk = Math.Min(asH - asL + 2 * TickSize, 0.6 * atr);
			StopEntry(asia, d, lvl, lvl - d * risk, lvl + d * 1.0 * risk, S(600));
		}

		private void Late()
		{
			if (!AtrOk || trendDir == 0 || double.IsNaN(pdc)) return;
			double mv = Close[0] - pdc;
			if (Math.Abs(mv) < 0.5 * atr) return;
			int d = mv > 0 ? 1 : -1;
			if (d != trendDir) return;
			MarketEntry(late, d, Close[0] - d * 1.0 * atr, Close[0] + d * 1.0 * atr);
		}
		#endregion


		// ---- edge monitor (research/mine/gold_monitor.py): one-sided CUSUM on z = day P&L per contract / (10 x daily ATR in $ of gold),
		// S = max(0, S + k - z), alarm when S > h. Calibrated on 2020-26 (CFD) with 30 sd: ~1.5-2% false alarms per year, no alarm in
		// 2020-26 nor on real MGC 2024-26; a dead edge is detected after ~14 months (gold edges are small, so it needs time).
		// Replay 2010-19 (old gold regime): WinRate would have alarmed after ~2.6 years; Robust never (it kept a small edge).
		private double edgeS; private int edgeDays; private bool edgeAlarm, edgePaused, edgeDayRth;
		private void EdgeDayClose()
		{
			bool counted = EdgeMonitor && rthHas && AtrOk && sessionDate > 0;
			DateTime st;
			if (counted && DateTime.TryParseExact(EdgeMonitorStart ?? "", "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out st) && sessionDate >= st.Year * 10000 + st.Month * 100 + st.Day)
			{
				double k = Profile == GoldMasterProfile.Robust ? 0.01215 : 0.00523, h = Profile == GoldMasterProfile.Robust ? 8.992 : 3.861;
				double z = fomcToday ? 0.0 : (netPnl - dayStartPnl) / Math.Max(1, Contracts) / (10.0 * atr);
				edgeS = Math.Max(0.0, edgeS + k - z); edgeDays++;
				if (PrintLog) Print(string.Format("{0} | GOLD | EDGE day {1}: z {2:0.000} | CUSUM {3:0.00} / {4:0.00} ({5:0}%)", sessionDate, edgeDays, z, edgeS, h, 100 * edgeS / h));
				if (!edgeAlarm && edgeS > h)
				{
					edgeAlarm = true; edgePaused = EdgeMonitorPause;
					Print(string.Format("GoldMaster | EDGE MONITOR ALARM {0}: live results no longer consistent with the backtested gold edge ({1} days). {2}", sessionDate, edgeDays,
						EdgeMonitorPause ? "New entries paused." : "Alert only (pause is off)."));
				}
			}
		}

		#region Orders
		private bool OppPos(int d) { return Position.MarketPosition == (d == 1 ? MarketPosition.Short : MarketPosition.Long); }
		private bool OppWork(int d, Mod self) { foreach (Mod o in mods) if (o != self && Working(o.Entry) && o.Dir == -d) return true; return false; }
		private void Park(Mod o) { o.Def = true; o.DPx = o.Entry.StopPrice; CancelOrder(o.Entry); Log(o.Sig + " stop order parked (opposite trade)"); }
		private void MarketEntry(Mod m, int d, double sl, double tp)
		{
			if (OppPos(d) || m.InTrade) { Log(m.Sig + " skipped (opposite position)"); return; }
			sl = Instrument.MasterInstrument.RoundToTickSize(sl); tp = Instrument.MasterInstrument.RoundToTickSize(tp);
			m.Dir = d; m.Sl = sl; m.Tp = tp; m.Def = false;
			if (OppWork(d, m))
			{
				// NinjaTrader ignores an entry while an opposite entry order works: park those orders, enter once they are cancelled
				pendMod = m; pendBar = CurrentBar;
				foreach (Mod o in mods) if (o != m && Working(o.Entry) && o.Dir == -d) Park(o);
				return;
			}
			SendMarket(m);
		}
		private void SendMarket(Mod m)
		{
			SetStopLoss(m.Sig, CalculationMode.Price, m.Sl, false);
			SetProfitTarget(m.Sig, CalculationMode.Price, m.Tp);
			if (m.Dir == 1) EnterLong(Contracts, m.Sig); else EnterShort(Contracts, m.Sig);
			Log(string.Format("{0} {1} market | SL {2} TP {3}", m.Sig, m.Dir == 1 ? "BUY" : "SELL", Fmt(m.Sl), Fmt(m.Tp)));
		}
		private void StopEntry(Mod m, int d, double px, double sl, double tp, int expireSm)
		{
			if (m.InTrade) return;
			px = Instrument.MasterInstrument.RoundToTickSize(px); sl = Instrument.MasterInstrument.RoundToTickSize(sl); tp = Instrument.MasterInstrument.RoundToTickSize(tp);
			m.Dir = d; m.Sl = sl; m.Tp = tp; m.ExpireMin = expireSm; m.Def = false;
			if (OppPos(d) || OppWork(d, m)) { m.Def = true; m.DPx = px; Log(m.Sig + " parked (opposite position / order)"); return; }
			if (State == State.Realtime)
			{
				// level already passed (a stop there would be rejected): research fills at the open -> market entry unless the target is passed too
				double mk = double.NaN;
				try { mk = d == 1 ? GetCurrentAsk() : GetCurrentBid(); } catch { }
				if (!double.IsNaN(mk) && (mk - px) * d >= 0) { if ((mk - tp) * d < 0) SendMarket(m); else Log(m.Sig + " skipped (target already passed)"); return; }
			}
			SetStopLoss(m.Sig, CalculationMode.Price, sl, false);
			SetProfitTarget(m.Sig, CalculationMode.Price, tp);
			if (d == 1) EnterLongStopMarket(0, true, Contracts, px, m.Sig); else EnterShortStopMarket(0, true, Contracts, px, m.Sig);
			Log(string.Format("{0} {1} STOP @ {2} | SL {3} TP {4}", m.Sig, d == 1 ? "BUY" : "SELL", Fmt(px), Fmt(sl), Fmt(tp)));
		}
		private void ExitModule(Mod m, string why)
		{
			if (m.Dir == 1) ExitLong(0, Contracts, m.Sig + "X", m.Sig); else if (m.Dir == -1) ExitShort(0, Contracts, m.Sig + "X", m.Sig);
			m.EntryBar = -1; Log(m.Sig + " exit: " + why);
		}
		private void FlattenAll(string why)
		{
			CancelAllEntries();
			if (Position.MarketPosition == MarketPosition.Flat || flattenBar == CurrentBar) return;
			flattenBar = CurrentBar;
			if (Position.MarketPosition == MarketPosition.Long) ExitLong(); else ExitShort();
			Log("FLATTEN: " + why);
		}
		private void CancelAllEntries() { pendMod = null; foreach (Mod m in mods) { m.Def = false; if (Working(m.Entry)) CancelOrder(m.Entry); } }
		private static bool Working(Order o)
		{
			if (o == null) return false;
			OrderState s = o.OrderState;
			return s != OrderState.Filled && s != OrderState.Cancelled && s != OrderState.Rejected && s != OrderState.Unknown;
		}
		private Mod BySig(string sig) { if (mods == null || string.IsNullOrEmpty(sig)) return null; foreach (Mod m in mods) if (m.Sig == sig) return m; return null; }

		protected override void OnOrderUpdate(Order order, double limitPrice, double stopPrice, int quantity, int filled, double averageFillPrice,
			OrderState orderState, DateTime time, ErrorCode error, string nativeError)
		{
			Mod m = BySig(order.Name);
			if (m != null) m.Entry = order;
			if (orderState == OrderState.Rejected)
			{
				Print(string.Format("GoldMaster | {0} REJECTED: {1} {2}", order.Name, error, nativeError));
				Mod f = m == null && (order.Name == "Stop loss" || order.Name == "Profit target") ? BySig(order.FromEntrySignal) : null;
				if (f != null && f.InTrade) ExitModule(f, "protective order rejected");
				else if (m != null && !m.InTrade) { m.Dir = 0; m.ExpireMin = -1; m.Def = false; if (pendMod == m) pendMod = null; }
			}
			// a market entry waiting for an opposite stop order to be cancelled
			if (orderState == OrderState.Cancelled && pendMod != null && !pendMod.InTrade && !OppPos(pendMod.Dir) && !OppWork(pendMod.Dir, pendMod)) { Mod pm = pendMod; pendMod = null; SendMarket(pm); }
		}

		protected override void OnExecutionUpdate(Execution execution, string executionId, double price, int quantity, MarketPosition marketPosition, string orderId, DateTime time)
		{
			if (execution.Order == null) return;
			Mod m = BySig(execution.Order.Name);
			if (m != null)
			{
				if (execution.Order.Filled <= 0) return;
				if (m.InTrade) return;			// further partial fills of the same entry
				m.InTrade = true; m.EntryBar = CurrentBar; m.Def = false;
				double f = execution.Order.AverageFillPrice;
				// research: skip the trade if the fill is already beyond the stop or the target
				if ((m.Dir == 1 && (f <= m.Sl || f >= m.Tp)) || (m.Dir == -1 && (f >= m.Sl || f <= m.Tp))) ExitModule(m, "filled beyond stop/target");
				// cancel opposite working entries
				foreach (Mod o in mods) if (o != m && Working(o.Entry) && o.Dir == -m.Dir) Park(o);
				Log(string.Format("{0} filled @ {1}", m.Sig, Fmt(f)));
				return;
			}
			Mod from = BySig(execution.Order.FromEntrySignal);
			if (from != null && execution.Order.OrderState == OrderState.Filled) { from.InTrade = false; from.EntryBar = -1; }
			if (Position.MarketPosition == MarketPosition.Flat) foreach (Mod x in mods) { x.InTrade = false; x.EntryBar = -1; }
		}
		#endregion

		#region Account layer and helpers
		// account-level daily stop (realtime: whole account incl. NQMaster; historical: this strategy) - prop eval protection
		private double AcctEquity()
		{
			if (State == State.Realtime) return Account.Get(AccountItem.CashValue, Currency.UsDollar) + Account.Get(AccountItem.UnrealizedProfitLoss, Currency.UsDollar);
			return netPnl + (Position.MarketPosition == MarketPosition.Flat ? 0 : Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Close[0]));
		}
		// eval target with Lucid-style consistency (realtime, whole account): stop when profit >= max(target, best day / consistency)
		private void EvalTargetCheck()
		{
			if (EvalTarget <= 0 || State != State.Realtime) return;
			double bal = Account.Get(AccountItem.CashValue, Currency.UsDollar), eq = bal + Account.Get(AccountItem.UnrealizedProfitLoss, Currency.UsDollar);
			if (double.IsNaN(evDayStart)) { evDayStart = bal; if (double.IsNaN(evBestDay)) evBestDay = EvalBestDaySoFar; }
			double need = EvalTarget;
			if (ConsistencyPct > 0) need = Math.Max(need, Math.Max(evBestDay, eq - evDayStart) * 100.0 / ConsistencyPct);
			if (!targetHit && eq - StartBalance >= need) { targetHit = true; FlattenAll("eval target"); Print(string.Format("GoldMaster | EVAL TARGET REACHED (+{0:0}, needed {1:0}) - trading stopped.", eq - StartBalance, need)); }
			else if (targetHit && Position.MarketPosition == MarketPosition.Flat && eq - StartBalance < need)
			{ targetHit = false; Print(string.Format("GoldMaster | eval target not met after closing (+{0:0}, needed {1:0}) - trading resumes.", eq - StartBalance, need)); }
		}
		private void DailyLossCheck()
		{
			EvalTargetCheck();
			if (AccountDailyStop > 0 && !acctStopped && !double.IsNaN(acctDayStart) && AcctEquity() - acctDayStart <= -AccountDailyStop) { acctStopped = true; FlattenAll("account daily stop"); Log("ACCOUNT DAILY STOP reached"); }
			if (AccountProfitStop > 0 && !acctStopped && !double.IsNaN(acctDayStart) && AcctEquity() - acctDayStart >= AccountProfitStop) { acctStopped = true; FlattenAll("account daily profit stop"); Log("ACCOUNT DAILY PROFIT STOP reached (eval consistency)"); }
			if (DailyLossLimit <= 0 || dayStopped) return;
			if (netPnl - dayStartPnl <= -DailyLossLimit) { dayStopped = true; FlattenAll("daily loss limit"); Log("DAILY LOSS LIMIT reached"); }
		}
		private bool CanTrade()
		{
			if (fomcToday) { status = "FOMC day: no trading"; return false; }
			if (dayStopped) { status = "daily loss limit"; return false; }
			if (acctStopped) { status = "account daily stop"; return false; }
			if (targetHit) { status = "eval target reached"; return false; }
			if (edgePaused) { status = "EDGE MONITOR ALARM - review before trading"; return false; }
			if (PauseActive()) { status = "MANUAL PAUSE (file)"; return false; }
			status = AtrOk ? "trading" : "warming up (needs 60 RTH days: Days to load >= 120)";
			return true;
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
			if (Position.MarketPosition == MarketPosition.Flat) foreach (Mod x in mods) { x.InTrade = false; x.EntryBar = -1; }
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
		private static int S(int hhmm) { return ((hhmm / 100) * 60 + hhmm % 100 - 1080 + 1440) % 1440; }
		private static int Hm(int hhmm) { return (hhmm / 100) * 60 + hhmm % 100; }
		private string Fmt(double p) { return Instrument.MasterInstrument.FormatPrice(p); }
		private void Log(string m) { if (PrintLog) Print(string.Format("{0} | GOLD | {1}", Time[0].ToString("yyyy-MM-dd HH:mm", CultureInfo.InvariantCulture), m)); }
		private void UpdateDashboard()
		{
			if (!ShowDashboard || (State == State.Historical && CurrentBar < Count - 2)) return;
			double pf = grossLoss > 0 ? grossWin / grossLoss : 0;
			StringBuilder mm = new StringBuilder();
			foreach (Mod m in mods) if (m.On) mm.Append(m.Sig + (m.InTrade ? "*" : Working(m.Entry) ? "~" : "") + " ");
			string txt = string.Format("GOLD MASTER ({0}) | {1}\ntrend {2} | ATRd {3:0.0}\n{4}\nTotal {5} tr | WR {6:0.0}% | PF {7:0.00} | ${8:0.00}",
				Profile, status, trendDir == 1 ? "UP" : trendDir == -1 ? "DOWN" : "-", atr, mm.ToString(), totalTrades,
				totalTrades > 0 ? 100.0 * totalWins / totalTrades : 0, pf, netPnl);
			if (EdgeMonitor && edgeDays > 0) txt += string.Format("\nEdge monitor: {0:0}% of alarm ({1} days){2}", 100 * edgeS / (Profile == GoldMasterProfile.Robust ? 8.992 : 3.861), edgeDays, edgeAlarm ? " | ALARM" : "");
			Draw.TextFixed(this, "GM_Dash", txt, TextPosition.TopRight, Brushes.White, dashFont, Brushes.Transparent, Brushes.Black, 75);
		}
		#endregion

		#region Properties
		[NinjaScriptProperty][Display(Name = "Profile", Order = 0, GroupName = "00. Profile")] public GoldMasterProfile Profile { get; set; }
		[NinjaScriptProperty][Display(Name = "OD1030 on (NY open drive)", Order = 1, GroupName = "01. Modules (Custom uses all switches)")] public bool UseOd { get; set; }
		[NinjaScriptProperty][Display(Name = "ENG0408 on (London 4H candle)", Order = 2, GroupName = "01. Modules (Custom uses all switches)")] public bool UseEng0408 { get; set; }
		[NinjaScriptProperty][Display(Name = "SVWAP22 on (22:00 session-VWAP fade)", Order = 3, GroupName = "01. Modules (Custom uses all switches)")] public bool UseSvwap { get; set; }
		[NinjaScriptProperty][Display(Name = "ENG0610 on (Custom only)", Order = 4, GroupName = "01. Modules (Custom uses all switches)")] public bool UseEng0610 { get; set; }
		[NinjaScriptProperty][Display(Name = "ASIA on (Robust / Custom)", Order = 5, GroupName = "01. Modules (Custom uses all switches)")] public bool UseAsia { get; set; }
		[NinjaScriptProperty][Display(Name = "ENG0206 on (Robust / Custom)", Order = 6, GroupName = "01. Modules (Custom uses all switches)")] public bool UseEng0206 { get; set; }
		[NinjaScriptProperty][Display(Name = "LATE on (Custom only)", Order = 7, GroupName = "01. Modules (Custom uses all switches)")] public bool UseLate { get; set; }
		[NinjaScriptProperty][Range(1, 50)][Display(Name = "Contracts per module", Order = 1, GroupName = "02. Risk / account")] public int Contracts { get; set; }
		[NinjaScriptProperty][Range(1000, 1659)][Display(Name = "Flatten time (ET HHmm)", Order = 2, GroupName = "02. Risk / account")] public int FlattenTime { get; set; }
		[NinjaScriptProperty][Display(Name = "Skip FOMC days", Order = 3, GroupName = "02. Risk / account")] public bool SkipFomc { get; set; }
		[NinjaScriptProperty][Display(Name = "Extra FOMC dates (yyyy-MM-dd list)", Order = 4, GroupName = "02. Risk / account")] public string FomcDates { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Daily loss limit $ (0 = off)", Order = 5, GroupName = "02. Risk / account")] public double DailyLossLimit { get; set; }
		[NinjaScriptProperty][Display(Name = "Pause file", Order = 6, GroupName = "02. Risk / account")] public string PauseFile { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Account daily stop $ (whole account in realtime; 0 = off)", Order = 7, GroupName = "02. Risk / account")] public double AccountDailyStop { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Eval target $ (realtime, whole account; 0 = off)", Order = 8, GroupName = "02. Risk / account")] public double EvalTarget { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Account daily profit stop $ (eval: 1400 with 2 contracts; 0 = off)", Order = 12, GroupName = "02. Risk / account")] public double AccountProfitStop { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Start balance $", Order = 9, GroupName = "02. Risk / account")] public double StartBalance { get; set; }
		[NinjaScriptProperty][Range(0, 100)][Display(Name = "Eval consistency % (Lucid 50, 0 = off)", Order = 10, GroupName = "02. Risk / account")] public double ConsistencyPct { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Eval: best day so far $ (after a restart)", Order = 11, GroupName = "02. Risk / account")] public double EvalBestDaySoFar { get; set; }
		[Display(Name = "Show dashboard", Order = 1, GroupName = "03. Display")] public bool ShowDashboard { get; set; }
		[NinjaScriptProperty][Display(Name = "Edge monitor on", Order = 1, GroupName = "04. Edge monitor")] public bool EdgeMonitor { get; set; }
		[NinjaScriptProperty][Display(Name = "Pause new entries on alarm", Order = 2, GroupName = "04. Edge monitor")] public bool EdgeMonitorPause { get; set; }
		[NinjaScriptProperty][Display(Name = "Edge monitor start date (yyyy-MM-dd)", Order = 3, GroupName = "04. Edge monitor")] public string EdgeMonitorStart { get; set; }
		[Display(Name = "Print log", Order = 2, GroupName = "03. Display")] public bool PrintLog { get; set; }
		#endregion
	}
}
