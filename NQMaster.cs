//
// NQ MASTER - the whole research portfolio in ONE strategy (NinjaTrader 8, single file)
// ------------------------------------------------------------------------------------------------
// Run on a 1-MINUTE MNQ chart (CME US Index Futures ETH). Gold runs in its own strategy (GoldMaster.cs) on an MGC chart.
// A 5-minute series is added internally (MSEQ and ICT modules).
// Profiles (Profile parameter; every module can still be switched on/off below):
//   Ultra     : default. ORB60 0.6R + ORB90 (pullback days), MSEQ, MSEQS, CRT11 2R, ICT x2, MOM11, MOM1030 / MOM13 (only with
//               another module open the same way), ON07, REV06, LON, VW13 wide, VOLB 2R, LATE15, night fades NF05 / LF06 / LF0430;
//               ENG10 / LATEFH off since 2026-10-12. Real NQ futures 2020-23 / 2024-26: WR 66.9 / 65.7%, PF 1.47 / 1.50,
//               Sharpe 3.38 / 3.65, ~4.7 trades/day, $1,700-2,300 per month per contract.
//   UltraQ    : 2026-10-14 quality build = Ultra without ON07, LON, ICT and without the wide VW13 lot (VW13 only at >= 0.30 ATR).
//               Real NQ 2020-23 / 2024-26: WR 70.2 / 68.3% (Ultra 66.9 / 65.7), PF 1.51 / 1.53 (1.47 / 1.50), lower max drawdown,
//               ~3.9 trades/day, ~8% less $; win rate AND profit factor higher in all four periods incl. 2010-14 / 2015-19.
//   CPI09     : (Ultra, UltraQ, WR70Plus) on US CPI days only: at 09:30 fade the 08:30 -> 09:29 move if >= 0.05 ATR, stop 0.35 ATR,
//               0.5R, 60 min. 2010-14 / 2015-19 / 2020-23 / 2024-26 PF 1.58 / 1.13 / 1.94 / 2.62, WR ~78-81% since 2020; the same
//               rule on ordinary days loses (research/mine/cpi_lab.py). ~12 trades a year.
//   WR70Plus  : >= 70% win rate build: ORB60 0.75R, ORB90, MSEQ, MSEQS, CRT11, ICT x2, MOM11, REV06, VW13 wide, VOLB with the
//               trend at 0.5R, LATE15 (+ night fades with NightOnWr70). WR 72.2 / 69.4%, PF 1.57 / 1.48, ~3.3 trades/day.
//   Durable   : the 6 modules that held up on 16 years of real futures (2010-2026): ORB60, ORB90, MSEQS, CRT11, VOLB 2R, NF05.
//               PF 1.63, WR 62%, ~1.4 trades/day, cost-normalised PF 1.18 / 1.23 in 2010-14 / 2015-19. Fallback if the edge
//               monitor alarms or the post-2020 regime fades.
//   Custom    : every module switch and the ORB range / target / pullback settings apply.
// Six-year modules (2026-10-16, Ultra, group 11, default OFF): CA04V, SO04, GD03, RV11, ENG26, ORFAIL, CAM3 + LATEFH. Chosen on real NQ
//   2020-10..2023, checked on 2024-26 (research/mine/six_reselect.py, six_combo2.py, six_life.py), with opposite-position blocking:
//   Ultra Sharpe 3.45 / 3.96 -> 3.76 / 4.09, +$13.8k over 6 years per contract (+9%), max drawdown $4,694 -> $4,406, WR -1.5 pts.
//   MFFU 50K per seat 2024-26: +$67/month (full edge), +$8 (35% less edge, worse worst year). Weak in 2010-19 (post-2020 edge).
// Risk layer (2026-10-12): structure stops >= 0.10 ATR; in prop accounts trades risking > $300 per contract are skipped while
// the cushion is small (fewer lost accounts: MyFundedFutures 2024-26 resampled 1.65 -> 0.70 per year per slot).
// Account layer: FOMC days skipped, shared pause file, eval-target stop and drawdown guard (realtime).
// Managed orders: one signal per module. An entry is skipped if the strategy holds (or is working) the opposite direction.
// FillSeries (2026-10-26, experiment 01): Off = orders on the 1-minute bars (default, unchanged); Tick1 / Second1 = a 1-tick / 1-second
//   series is added and every order is submitted to it (SampleIntrabarBacktest), so Strategy Analyzer fills are intrabar. Backtest only.
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
	public enum NQMasterProfile { Ultra, UltraQ, WR70Plus, Durable, Custom }
	public enum NQMasterPropMode { Off, Eval, Funded }
	public enum NQMasterPropPreset { Manual, Lucid25K, Lucid50K, Mffu50K, LucidPro25K, FundedNext25K, Mffu50KLadder, Lucid150K, LucidPro50K }
	public enum NQMasterSafeSet { Classic, Estable }
	public enum NQMasterFillSeries { Off, Tick1, Second1 }	// experiment 01 (2026-10-26): intrabar fill series for the Strategy Analyzer

	public class NQMaster : Strategy
	{
		private const int RthOpen = 570, RthClose = 960;
		// FOMC decision days always skipped (merged with the FomcDates parameter). Source: federalreserve.gov (2027 schedule, Sep 2025).
		private const string BuiltinFomc = "2024-01-31,2024-03-20,2024-05-01,2024-06-12,2024-07-31,2024-09-18,2024-11-07,2024-12-18,2025-01-29,2025-03-19,2025-05-07,2025-06-18,2025-07-30,2025-09-17,2025-10-29,2025-12-10,2026-01-28,2026-03-18,2026-04-29,2026-06-17,2026-07-29,2026-09-16,2026-10-28,2026-12-09,2027-01-27,2027-03-17,2027-04-28,2027-06-09,2027-07-28,2027-09-15,2027-10-27,2027-12-08,2028-01-26";

		#region Module state
		private class Mod
		{
			public string Sig; public bool On; public double R; public int Kind;	// Kind: 0 ORB, 1 time, 2 other
			public bool InTrade; public Order Entry; public int Dir; public double StopPx; public double EntryPx; public int EntryBar;
			// ORB
			public int Range; public double OrH, OrL; public bool OrReady, Armed; public int Trades; public bool UsePullback;
			// time module
			public int Time; public int Lookback; public bool Reverse; public double StopAtr; public int MaxHold; public bool Trend; public bool Vwap; public bool Done; public double MinDist; public double DoubleDist;
			// target set on fill (price mode)
			public bool PriceTarget;
			public bool BaseOn; public bool FhCheck;
			public bool Retry;
			public bool CpiOnly;	// CPI09: only on US CPI release days
			public int LastFillDay = -1; public bool InactWarned;	// inactivity alarm (tradable-day index of the last fill)
			public int Anchor = -1; public double AnchorPx = double.NaN;	// Lookback -5: open of the bar at the anchor time (ET minutes)
			public bool Parked, ParkLimit, ParkHit; public double ParkPx; public int ParkQty;	// entry cancelled for an opposite trade, re-placed when free
			public Order SeenOrd, CancelOrd; public int SeenBar = -1, CancelBar = -1;	// stale-order watchdog (PurgeStaleEntries)
			public int OfQ0, OfWant; public Order OfChangeOrd, OfNoChange; public int OfChangeBar = -1;	// order-flow boost: size before the boost, last re-size
			public int OpenQty, RejToday;
			public double FixTgt = double.NaN; public bool StructStop, WinHas, Six; public double WinH, WinL, RvolMax;	// six-year modules (2026-10-16)	// lots still open (multi-lot entries close in parts), rejected orders this session
		}
		private List<Mod> mods;
		private Mod orb, orb2, mseq, mseqs, crt, lon, ict, rsi, volb, eng10;
		private double rthFirstClose = double.NaN;
		private double e10aO, e10aH, e10aL, e10aC, e10bO, e10bH, e10bL, e10bC, close10 = double.NaN; private bool e10aHas, e10bHas, eng10Done;
		private double volbUp = double.NaN, volbDn = double.NaN; private bool volbDone, volbTrendOnly, volbTrendBase; private double volbRBase = 2.0; private int volbTrades;
		private List<Order> zombies = new List<Order>(); private int zombieCount;	// entry orders NinjaTrader never processed (PurgeStaleEntries)
		private int orbFirstDir, orbFirstMin = 9999;
		private int m11Dir, onSum, lonDir;	// confluence state (MOM11 direction, overnight modules ON07/REV06/LON)
		private List<Mod> timeMods;
		// six-year modules (2026-10-16): ENG26 (22-02 vs 02-06 4H engulf at 09:30), ORFAIL (failed 15-min ORB), CAM3 (Camarilla L3/H3 fade)
		private Mod eng26, orf, cam3; private List<Mod> sixMods = new List<Mod>();
		private double e26aO, e26aH, e26aL, e26aC; private bool e26aHas;
		private double sVwPv, sVwV;	// session VWAP since 18:00 (CA04V)
		private double rvAcc; private bool rvDone; private List<double> rvHist = new List<double>();	// RTH volume 09:30-10:59 (RV11)
		private double orfH, orfL, orfExt, orfSl, orfTp; private int orfBrk, orfBi, orfSig; private bool orfHas, orfReady, orfDone;
		private double camLev, camExt, camSl, camTp; private int camSide, camBr = -1, camSig; private bool camDone = true;
		#endregion

		#region Fields
		private TimeZoneInfo etZone;
		private SimpleFont dashFont;
		private bool badTimeframe;
		private int fillCfg, fillBip;		// fillCfg = series configured for the orders (0 = 1-minute bars as always, 2 = FillSeries Tick1 / Second1);
													// fillBip = the one in use on this bar: 2 once the fill series has bars (tick history can start years after the minutes), else 0
		private DateTime runStart;			// wall clock at DataLoaded -> run-time line at Terminated (Off vs Tick1 ratio)
		private HashSet<int> fomc, cpiDays; private bool cpiToday;
		// US CPI release days (BLS schedule) for CPI09; add later years with the CpiDates parameter
		private const string BuiltinCpi = "2024-01-11,2024-02-13,2024-03-12,2024-04-10,2024-05-15,2024-06-12,2024-07-11,2024-08-14,2024-09-11,2024-10-10,2024-11-13,2024-12-11," +
			"2025-01-15,2025-02-12,2025-03-12,2025-04-10,2025-05-13,2025-06-11,2025-07-15,2025-08-12,2025-09-11,2025-10-24,2025-12-18," +
			"2026-01-13,2026-02-13,2026-03-11,2026-04-10,2026-05-12,2026-06-10,2026-07-14,2026-08-12,2026-09-11,2026-10-14,2026-11-10,2026-12-10," +
			"2027-01-13,2027-02-11,2027-03-10,2027-04-13,2027-05-12,2027-06-10,2027-07-14,2027-08-11,2027-09-14,2027-10-14,2027-11-10,2027-12-10";
		// Tier-1 news (MyFundedFutures: CPI, Employment Report 08:30 ET, FOMC minutes 14:00 ET; FOMC days are skipped anyway).
		// CPI / NFP from the BLS schedules (2024 - Dec 2027; 2027 schedule published 2026-10-09), minutes = decision + 21 days (released dates to Oct 2026,
		// later ones are Fed-rule estimates), plus FOMC decisions 14:00 from 2026-10-28 (safety net when SkipFomc is off). Checked 2026-10-19: research/mine/calendar_check_2026-10-19.md
		private const string BuiltinNews = "2024-01-03 14:00,2024-01-05 08:30,2024-01-11 08:30,2024-02-02 08:30,2024-02-13 08:30,2024-02-21 14:00,2024-03-08 08:30,2024-03-12 08:30,2024-04-05 08:30,2024-04-10 08:30,2024-04-10 14:00,2024-05-03 08:30,2024-05-15 08:30,2024-05-22 14:00,2024-06-07 08:30,2024-06-12 08:30,2024-07-03 14:00,2024-07-05 08:30,2024-07-11 08:30,2024-08-02 08:30,2024-08-14 08:30,2024-08-21 14:00,2024-09-06 08:30,2024-09-11 08:30,2024-10-04 08:30,2024-10-09 14:00,2024-10-10 08:30,2024-11-01 08:30,2024-11-13 08:30,2024-11-26 14:00,2024-12-06 08:30,2024-12-11 08:30,2025-01-08 14:00,2025-01-10 08:30,2025-01-15 08:30,2025-02-07 08:30,2025-02-12 08:30,2025-02-19 14:00,2025-03-07 08:30,2025-03-12 08:30,2025-04-04 08:30,2025-04-09 14:00,2025-04-10 08:30,2025-05-02 08:30,2025-05-13 08:30,2025-05-28 14:00,2025-06-06 08:30,2025-06-11 08:30,2025-07-03 08:30,2025-07-09 14:00,2025-07-15 08:30,2025-08-01 08:30,2025-08-12 08:30,2025-08-20 14:00,2025-09-05 08:30,2025-09-11 08:30,2025-10-03 08:30,2025-10-08 14:00,2025-10-24 08:30,2025-11-19 14:00,2025-11-20 08:30,2025-12-16 08:30,2025-12-18 08:30,2025-12-30 14:00,2026-01-09 08:30,2026-01-13 08:30,2026-02-11 08:30,2026-02-13 08:30,2026-02-18 14:00,2026-03-06 08:30,2026-03-11 08:30,2026-04-03 08:30,2026-04-08 14:00,2026-04-10 08:30,2026-05-08 08:30,2026-05-12 08:30,2026-05-20 14:00,2026-06-05 08:30,2026-06-10 08:30,2026-07-02 08:30,2026-07-08 14:00,2026-07-14 08:30,2026-08-07 08:30,2026-08-12 08:30,2026-08-19 14:00,2026-09-04 08:30,2026-09-11 08:30,2026-10-07 14:00,2026-10-14 08:30,2026-11-06 08:30,2026-11-10 08:30,2026-11-18 14:00,2026-12-04 08:30,2026-12-10 08:30,2026-12-30 14:00,2027-02-17 14:00,2027-04-07 14:00,2027-05-19 14:00,2027-06-30 14:00,2027-08-18 14:00,2027-10-06 14:00,2027-11-17 14:00,2027-12-29 14:00,2026-10-02 08:30,2027-01-08 08:30,2027-01-13 08:30,2027-02-05 08:30,2027-02-11 08:30,2027-03-05 08:30,2027-03-10 08:30,2027-04-02 08:30,2027-04-13 08:30,2027-05-07 08:30,2027-05-12 08:30,2027-06-04 08:30,2027-06-10 08:30,2027-07-02 08:30,2027-07-14 08:30,2027-08-06 08:30,2027-08-11 08:30,2027-09-03 08:30,2027-09-14 08:30,2027-10-08 08:30,2027-10-14 08:30,2027-11-05 08:30,2027-11-10 08:30,2027-12-03 08:30,2027-12-10 08:30,2026-10-28 14:00,2026-12-09 14:00,2027-01-27 14:00,2027-03-17 14:00,2027-04-28 14:00,2027-06-09 14:00,2027-07-28 14:00,2027-09-15 14:00,2027-10-27 14:00,2027-12-08 14:00,2028-01-26 14:00";
		private List<DateTime> newsEt; private bool profUltra, volbBeSet;

		// completed RTH days
		private int rthDay = -1, rthDaysSeen, atrCount;
		private double dayHigh, dayLow, dayClose, atrDaily = double.NaN, atrPrevClose = double.NaN, prevRthHigh = double.NaN, prevRthLow = double.NaN;
		private double full1 = double.NaN, full2 = double.NaN;
		private bool dayHasBars;
		private int dayLastOpen = -1;
		private List<double> rthCloses;
		private int trendDir;
		private double todayAtr = double.NaN, prevRet = double.NaN;
		private bool pullbackDay, fomcToday;

		// session / intraday
		private double sessOpen = double.NaN, rthOpenPx = double.NaN, vwPv, vwV;
		private double onH, onL, lonH, lonL, postH, postL; private bool onHas, lonHas, postHas;
		private double c1H, c1L, c2H, c2L, c2C; private bool c1Has, c2Has;
		private double rH, rL; private bool rHas; private int lonStage;
		private double[] lvl = new double[6]; private bool[] taken = new bool[6]; private bool levelsReady;
		private bool[] ictAct = new bool[2]; private double[] ictExt = new double[2]; private int[] ictExtBar = new int[2];
		private int ictTrades, ictExpiry; private double ictExtPend;
		private int flattenBar = -1;
		private double rsiUp = double.NaN, rsiDn = double.NaN, rsiVal = 50; private int rsiTrades;
		private string status = "waiting";

		// ---- operations layer (2026-10-12 code audit, research/mine/audit_code_2026-10-12.md) ----
		private SessionIterator sessIt; private int sessEndMin = 17 * 60; private bool shortSession, syncArmed, desyncHalt, rejectHalt, rollHalt;
		private int desyncBars, capLogBar = -1, capCuts; private List<Order> rtZombies = new List<Order>();
		private static int SignedQty(NinjaTrader.Cbi.Position p) { return p == null || p.MarketPosition == MarketPosition.Flat ? 0 : (p.MarketPosition == MarketPosition.Long ? p.Quantity : -p.Quantity); }
		// H1: the firm's auto-close, a manual flatten, a restart with a real position or an overfill leave the account and the strategy
		// apart; an exit sent then opens a reverse, unprotected position. 2 bars apart -> flatten this instrument, alert, stop.
		private void CheckAccountSync()
		{
			if (!AccountSyncGuard || State != State.Realtime || desyncHalt) return;
			int acct, strat;
			try { acct = SignedQty(PositionAccount); strat = SignedQty(Position); } catch { return; }
			if (!syncArmed) { if (strat != 0) return; syncArmed = true; }	// WaitUntilFlat: compare once the simulated history position is closed
			if (acct == strat) { desyncBars = 0; return; }
			if (++desyncBars < 2) return;
			desyncHalt = true;
			try { Account.Flatten(new[] { Instrument }); } catch (Exception ex) { Print("NQMaster | account flatten failed: " + ex.Message); }
			Warn("nqm_desync", string.Format("NQMaster | ACCOUNT / STRATEGY POSITION MISMATCH for 2 bars: account {0}, strategy {1} ({2}). The account position and orders of this instrument were closed and the strategy stops. Check the Positions / Orders tabs, then enable it again.", acct, strat, Instrument.FullName));
			try { SetState(State.Terminated); } catch { }
		}
		// H2: real session end (holidays / half days end at 13:00-13:15 ET; NinjaTrader's trading-hours template knows them)
		private void SessionBounds()
		{
			sessEndMin = 17 * 60; shortSession = false;
			try
			{
				if (sessIt == null) sessIt = new SessionIterator(Bars);
				sessIt.GetNextSession(Time[0], true);
				DateTime se = ToEt(sessIt.ActualSessionEnd);
				sessEndMin = se.Hour * 60 + se.Minute;
				shortSession = sessEndMin >= 9 * 60 && sessEndMin < 16 * 60;
			}
			catch { }
			if (shortSession) Log(string.Format("short session (holiday / half day): the market closes {0:00}:{1:00} ET{2}", sessEndMin / 60, sessEndMin % 60, SkipShortSessions ? " - no new entries this session" : ""));
			rollHalt = State == State.Realtime && RollDue();
			if (rollHalt) Warn("nqm_roll", "NQMaster | ROLL DATE reached for " + Instrument.FullName + ": no new entries. Move the strategy to the next contract (same settings).");
		}
		// ---- account presets (research/mine/smallacct_*.py, real NQ futures 2020-26, 1 contract per module). Applied at start-up when PropMode is Eval or Funded.
		// Eval: profit stop = 0.9 x consistency x target (best day must stay under the consistency limit; the old '700 with 1 contract' cost ~9 points of 22-day pass
		// rate on Lucid 50K), no per-trade risk cap (neutral for passing, it only slows a 25K eval). Funded: per-trade risk cap while the cushion is small.
		private string payoutHint = "";	// dashboard PAYOUT text per firm (round 5, 2026-10-21: the exact rule of research/mine/prop_wf.py fund())
		private string PayoutGeneric() { return string.Format("ganancia >= ${0:0} -> retiro: seguir la regla de la firma (RUNBOOK_OPERACION.md)", FundedPayoutAt); }
		private void PresetPrint(string m) { if (!presetQuiet) Print(m); }
		// ---- retired settings (2026-10-21 cleanup): hidden and forced to the validated values. Each one failed out of sample or was
		// superseded (memory: order-flow boost, adaptive size, late eval size-up, cushion gating, ATR start check, monitor pause, VOLB re-arm,
		// MOM1130 / RSI2 / LF0315 / CA04V / GD03 / ENG26 / ENG10 / LATEFH); the edge parameters keep the values every test used.
		private void ForceRetired()
		{
			EvalMode = false; AdaptiveSize = false; UseOrderFlowBoost = false; EvalCushionFull = 0; FundedCushionSafe = 0; FundedCushionFull = 0; FundedHighFull = true;
			AtrStartMax = 0; EdgeMonitorPause = false; EdgeK = 0; EdgeH = 0; MaxDrawdown = 0; VolbReArm = false;
			UseMom1130 = false; UseRsi2 = false; UseLf0315 = false; UseCa04v = false; UseGd03 = false; UseEng26 = false; UseEng10 = false; UseLateFh = false;
			PullbackMaxRet = 0.44; StopCapAtr = 0.35; OrbPriorCloseAtr = 0.10; VolbBreakEven = true; MomAgreement = true; VolbTrendLastEntry = 1047; MinStopAtr = 0.10;
			UseContextRules = true; UseConfluence = true; IctMultiplier = 2; Vw13Wide = true; Cpi09Multiplier = 4; Mom1030Multiplier = 4;
		}
		private void ApplyPreset()
		{
			payoutHint = "";
			if (PropPreset == NQMasterPropPreset.Manual || PropMode == NQMasterPropMode.Off) { payoutHint = PayoutGeneric(); return; }
			bool ev = PropMode == NQMasterPropMode.Eval;
			// round 5 (2026-10-21) C2: clear leftovers of old templates that no simulated account policy uses (prop_wf.py CUR_EVAL / CUR_FUND);
			// these are the SetDefaults values, so a fresh strategy is unchanged. Mffu50K turns NewsBlackout back on in Funded.
			EvalMode = false; AdaptiveSize = false;
			EvalCushionFull = 0; EvalDailyStop = 0;
			FundedCushionSafe = 0; FundedCushionFull = 0; FundedHighFull = true;
			DailyLossLimit = 0;
			if (PropPreset != NQMasterPropPreset.Mffu50KLadder) { FundedStepUpCushion = 0; FundedLadderStep = 0; DailyLossPerContract = 0; }
			NewsBlackout = false;
			// C2 (c): one cross-account group per prop firm (only when HedgeGroup is empty): an empty group would also pair accounts of other firms on this PC
			if (string.IsNullOrEmpty(HedgeGroup))
			{
				switch (PropPreset)
				{
					case NQMasterPropPreset.Lucid25K: case NQMasterPropPreset.Lucid50K: case NQMasterPropPreset.Lucid150K:
					case NQMasterPropPreset.LucidPro25K: case NQMasterPropPreset.LucidPro50K: HedgeGroup = "LUCID"; break;
					case NQMasterPropPreset.Mffu50K: case NQMasterPropPreset.Mffu50KLadder: HedgeGroup = "MFFU"; break;
					case NQMasterPropPreset.FundedNext25K: HedgeGroup = "FNEXT"; break;
				}
			}
			switch (PropPreset)
			{
				case NQMasterPropPreset.Lucid25K:
					StartBalance = 25000; PropTrailingDD = 1000; ConsistencyPct = 50;
					if (ev) { EvalTarget = 1250; EvalProfitStop = 560; EvalRiskCapCushion = 0; MaxOpenContracts = 20; }
					else { EvalTarget = 0; RiskCapPerContract = 150; FundedRiskCapCushion = 500; FundedPayoutAt = 1500; MaxOpenContracts = 10; FundedProfitStop = 0; }
					payoutHint = string.Format("ganancia >= ${0:0} y 5 d\u00edas >= $100 en el ciclo -> pedir min($1.000, 50% de la ganancia)", FundedPayoutAt);
					break;
				case NQMasterPropPreset.Lucid50K:
					StartBalance = 50000; PropTrailingDD = 2000; ConsistencyPct = 50;
					if (ev) { EvalTarget = 3000; EvalProfitStop = 1350; EvalRiskCapCushion = 0; MaxOpenContracts = 40; EvalHighWrMultiplier = 8; }
					else { EvalTarget = 0; RiskCapPerContract = 300; FundedRiskCapCushion = 1000; FundedPayoutAt = 4000; MaxOpenContracts = 20; FundedProfitStop = 0; }
					payoutHint = string.Format("ganancia >= ${0:0} y 5 d\u00edas >= $150 en el ciclo -> pedir min($2.000, 50% de la ganancia)", FundedPayoutAt);
					break;
				case NQMasterPropPreset.LucidPro25K:
				case NQMasterPropPreset.FundedNext25K:
					// research/mine/month80.py: 25K eval with NO consistency rule, 2 contracts per module, new eval the day after a bust ->
					// funded within ~22 trading days 90% / 92% (2020-23 / 2024-26; 35% less edge: 83% / 89%); funded account at 1 contract.
					StartBalance = 25000; PropTrailingDD = 1000; ConsistencyPct = 0;
					if (ev) { EvalTarget = PropPreset == NQMasterPropPreset.LucidPro25K ? 1250 : 1500; EvalProfitStop = 0; EvalRiskCapCushion = 0; MaxOpenContracts = 20; Contracts = 2; }
					else { EvalTarget = 0; RiskCapPerContract = 150; FundedRiskCapCushion = 500; FundedPayoutAt = PropPreset == NQMasterPropPreset.LucidPro25K ? 2100 : 1500; MaxOpenContracts = 20; FundedProfitStop = 0; Contracts = 1; FundedStepUpCushion = 0; }	// LucidPro25K: buffer 1,100 + first payout 1,000 (research X 1,000)
					if (PropPreset == NQMasterPropPreset.LucidPro25K) payoutHint = "pedir min(tope, ganancia - 1.100) cuando eso sea >= $1.000, con >= 3 d\u00edas en el ciclo, ganancia del ciclo >= $500 y mejor d\u00eda <= 40% del ciclo; tope 1.000 el primero, luego 1.500";
					break;
				case NQMasterPropPreset.LucidPro50K:
					// research/mine/lucidpro_week.py (2026-10-20): Lucid Pro 50K (target 3,000, EOD trailing 2,000, no eval consistency, DLL OFF, 40 micros).
					// Eval 4 contracts per module, flatten at the target, a new eval (or reset) the day after a bust: funded within 5 trading days with up to
					// 3 evals 52% / 66% (2020-23 / 2024-26; 35% less edge 45% / 55%). Funded 1 contract, account daily profit stop 1,000 (keeps the 40% cycle
					// consistency), risk cap 300 below a 1,000 cushion, payout request at 4,100 of profit (buffer 2,100 + cap 2,000): median $1,128 / $1,545 a month.
					StartBalance = 50000; PropTrailingDD = 2000; ConsistencyPct = 0;
					if (ev) { EvalTarget = 3000; EvalProfitStop = 0; EvalRiskCapCushion = 0; MaxOpenContracts = 40; Contracts = 4; EvalHighWrMultiplier = 0; }
					else { EvalTarget = 0; RiskCapPerContract = 300; FundedRiskCapCushion = 1000; FundedPayoutAt = 4100; MaxOpenContracts = 40; FundedProfitStop = 1000; Contracts = 1; FundedStepUpCushion = 0; FundedLadderStep = 0; }
					payoutHint = "pedir min(tope, ganancia - 2.100) cuando eso sea >= $2.000, con >= 3 d\u00edas en el ciclo, ganancia del ciclo >= $500 y mejor d\u00eda <= 40% del ciclo; tope 2.000 el primero, luego 2.500";
					break;
				case NQMasterPropPreset.Lucid150K:
					// research/mine/acct_150k.py + acct_2027.py: Lucid Flex 150K (target 9,000, EOD trailing 4,500, 50% consistency; funded payout days >= $250,
					// cap 3,000, 5 payouts). Eval 6 contracts per module with a daily profit stop of 4,050 (0.9 x 50% x target); funded 3 contracts, risk cap 300
					// below a 1,687 cushion, request the payout at 6,000 of profit. 5 x 150K: median $352-459/day (2020-23 / 2024-26), $189-266 with 35% less edge.
					StartBalance = 150000; PropTrailingDD = 4500; ConsistencyPct = 50;
					if (ev) { EvalTarget = 9000; EvalProfitStop = 4050; EvalRiskCapCushion = 0; MaxOpenContracts = 100; Contracts = 6; EvalHighWrMultiplier = 0; }
					else { EvalTarget = 0; RiskCapPerContract = 300; FundedRiskCapCushion = 1687; FundedPayoutAt = 6000; MaxOpenContracts = 40; FundedProfitStop = 0; Contracts = 3; FundedStepUpCushion = 0; FundedLadderStep = 0; }
					payoutHint = string.Format("ganancia >= ${0:0} y 5 d\u00edas >= $250 en el ciclo -> pedir min($3.000, 50% de la ganancia)", FundedPayoutAt);
					break;
				case NQMasterPropPreset.Mffu50KLadder:
					// research/mine/ladder_plan.py + ladder_stop.py + code review 2026-10-17: the whole MFFU size-ladder recipe in one setting.
					// Funded: 1c (risk cap 300 below a 2,000 cushion) -> 2c at a 3,000 day-start cushion, +1 per further 3,000 up to 4; withdraw only above
					// 11,100 of profit; account daily stop 1,500 per contract. Eval exactly as Mffu50K. GoldMaster: same step-up / ladder values by hand.
					if (!ev) { FundedStepUpCushion = 3000; FundedStepUpContracts = 2; FundedLadderStep = 3000; FundedLadderMax = 4; FundedPayoutAt = 11600; DailyLossPerContract = 1500; Contracts = 1; }
					goto case NQMasterPropPreset.Mffu50K;
				case NQMasterPropPreset.Mffu50K:
					StartBalance = 50000; PropTrailingDD = 2000; ConsistencyPct = 30;
					if (ev) { EvalTarget = 3000; EvalProfitStop = 800; EvalRiskCapCushion = 0; MaxOpenContracts = 30; EvalHighWrMultiplier = 8; }
					else { EvalTarget = 0; RiskCapPerContract = 300; FundedRiskCapCushion = 2000; if (FundedLadderStep <= 0) FundedPayoutAt = FundedStepUpCushion > 0 ? 6600 : 4600; else FundedPayoutAt = Math.Max(FundedPayoutAt, FundedStepUpCushion + (FundedLadderMax - FundedStepUpContracts) * FundedLadderStep + 2600); MaxOpenContracts = 30; FundedProfitStop = 0; }	// ladder on: payout level at least the top of the ladder + 2,600 (11,600 for the K4 / $3,000 recipe; code review 2026-10-17 L1)
					if (!ev) NewsBlackout = true;	// MFFU funded: no trades or orders +-2 min around Tier-1 news (rule). Payout at $4,600 = keep $4,100; the optional step-up (FundedStepUpCushion 4000 -> $6,600) now needs PropPreset Manual (round 5 C2 resets it here): more median $ but 2x size, +6-7 pts P(negative year) at 35% less edge (c4_cushion.py + red team 2026-10-16), so it is NOT a default
					if (!ev) Contracts = 1;	// round 5 C2 (b): the simulated MFFU funded policies are 1 contract (the ladder steps up from 1 by itself)
					else if (Contracts != 1) PresetPrint(string.Format("NQMaster | WARNING: Mffu50K eval simulated at Contracts 1 (x8); Contracts is {0}", Contracts));
					payoutHint = string.Format("ganancia >= ${0:0} -> pedir el retiro y dejar ${1:0} de ganancia en la cuenta (es el colch\u00f3n)", FundedPayoutAt, Math.Max(0, FundedPayoutAt - 500));
					break;
			}
			if (string.IsNullOrEmpty(payoutHint)) payoutHint = PayoutGeneric();	// FundedNext25K (and any preset without its own text)
			if (FundedLadderStep > 0 && !ev && FundedStepUpCushion <= 0) PresetPrint("NQMaster | WARNING: the size ladder needs FundedStepUpCushion > 0 (first step); it is OFF");
			PresetPrint(string.Format("NQMaster | preset {0} ({1}): balance {2:0}, trailing DD {3:0}, eval target {4:0}, profit stop {5:0}, consistency {6:0}%, risk cap {7:0} below cushion {8:0}, max open contracts {9}, MOM1030/CPI09 x{10}",
				PropPreset, PropMode, StartBalance, PropTrailingDD, EvalTarget, EvalProfitStop, ConsistencyPct, RiskCapPerContract, ev ? EvalRiskCapCushion : FundedRiskCapCushion, MaxOpenContracts, HwQty(Mom1030Multiplier)));
			PresetPrint(string.Format("NQMaster | preset {0} ({1}): contracts {2}, payout at {3:0}, step-up cushion {4:0}, ladder step {5:0}, hedge group '{6}', news blackout {7}",
				PropPreset, PropMode, Contracts, FundedPayoutAt, FundedStepUpCushion, FundedLadderStep, HedgeGroup, NewsBlackout ? "on" : "off"));
			// C2 (d): strategy options, not account settings, and not in the account simulations: warn, never override
		}
		private bool RollDue()
		{
			if (!RollGuard) return false;
			try
			{
				if (Instrument.MasterInstrument.InstrumentType != InstrumentType.Future) return false;
				DateTime ex = Instrument.Expiry; if (ex.Year < 2000) return false;
				DateTime first = new DateTime(ex.Year, ex.Month, 1);
				DateTime roll = first.AddDays(((int)DayOfWeek.Friday - (int)first.DayOfWeek + 7) % 7 + 14 - 8);
				return ToEt(Core.Globals.Now).Date >= roll.Date;
			}
			catch { return false; }
		}
		private int FlatMin { get { int f = FlattenTime > 0 ? Hm(FlattenTime) : 24 * 60; return shortSession ? Math.Min(f, sessEndMin - 5) : f; } }
		private bool LateBar(DateTime barTime) { try { return State == State.Realtime && (Core.Globals.Now - barTime).TotalSeconds > 120; } catch { return false; } }
		// H3: open + working contracts (realtime: every instrument of the account, so MNQ and MGC together) never above MaxOpenContracts
		private int OpenAndWorking(object self)
		{
			int n = Position.MarketPosition == MarketPosition.Flat ? 0 : Position.Quantity;
			foreach (Mod m in mods) if ((object)m != self && Working(m.Entry) && !zombies.Contains(m.Entry)) n += Math.Max(0, m.Entry.Quantity - m.Entry.Filled);
			if (State == State.Realtime)
			{
				try { lock (Account.Positions) foreach (NinjaTrader.Cbi.Position p in Account.Positions) if (p.Instrument != Instrument && p.MarketPosition != MarketPosition.Flat) n += p.Quantity; } catch { }
			}
			return n;
		}
		private int CapQty(object self, string who, int q)
		{
			if (MaxOpenContracts <= 0 || q <= 0) return q;
			int room = MaxOpenContracts - OpenAndWorking(self);
			if (q <= room) return q;
			int nq = Math.Max(0, room); capCuts++;
			if (capLogBar != CurrentBars[0]) { capLogBar = CurrentBars[0]; Log(string.Format("{0} size {1} -> {2} (max open contracts {3})", who, q, nq, MaxOpenContracts)); }
			return nq;
		}
		// M2: in realtime an order the watchdog gave up on may still rest at the exchange -> it keeps blocking the opposite direction
		private bool RtZombieOpp(int d)
		{
			foreach (Order z in rtZombies) if (Working(z) && (z.OrderAction == OrderAction.Buy ? 1 : -1) == -d) return true;
			return false;
		}
		private void RejectSeen(string nativeError)
		{
			string ne = (nativeError ?? "").ToLowerInvariant();
			if (!rejectHalt && (ne.Contains("liquidat") || ne.Contains("disabled") || ne.Contains("margin") || ne.Contains("not allowed") || ne.Contains("locked")))
			{ rejectHalt = true; Warn("nqm_rejhalt", "NQMaster | the account refuses orders (" + nativeError + "): no new entries this session."); }
		}
		// M6: important events also go to an alert and to Documents\NinjaTrader 8\nqmaster_logs\<account>_<date>.txt
		private void LogFile(string line)
		{
			if (!LogToFile || State != State.Realtime) return;
			try
			{
				string dir = Path.Combine(Core.Globals.UserDataDir, "nqmaster_logs"); Directory.CreateDirectory(dir);
				File.AppendAllText(Path.Combine(dir, (Account != null ? Account.Name : "acct") + "_" + DateTime.Now.ToString("yyyyMMdd", CultureInfo.InvariantCulture) + ".txt"),
					DateTime.Now.ToString("HH:mm:ss", CultureInfo.InvariantCulture) + " " + line + Environment.NewLine);
			}
			catch { }
		}
		private void Warn(string id, string msg)
		{
			Print(msg);
			if (State != State.Realtime) return;
			LogFile(msg);
			try { Alert(id, Priority.High, msg, NinjaTrader.Core.Globals.InstallDir + @"\sounds\Alert1.wav", 60, Brushes.Red, Brushes.White); } catch { }
		}
		private void NewsListCheck()
		{
			if (!NewsBlackout || newsEt == null) return;
			DateTime last = DateTime.MinValue; foreach (DateTime e in newsEt) if (e.Hour == 8 && e > last) last = e;
			if ((last - ToEt(Core.Globals.Now)).TotalDays < 35) Warn("nqm_news", "NQMaster | NEWS LIST ends " + last.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture) + ": add the next CPI / NFP times (bls.gov) in 'Extra Tier-1 times'.");
		}

		// account layer
		private double highWater = double.NaN; private bool ddTripped, targetHit;
		private int tradesProcessed, totalTrades, totalWins; private double grossWin, grossLoss, netPnl;
		#endregion

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Description = "Whole NQ research portfolio in one strategy: ORB, MSEQ, CRT11, clock-time modules, London FVG, ICT open, risk layer, account guard.";
				Name = "NQMaster";
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

				Profile = NQMasterProfile.Ultra;
				UseOrb = true; OrbRangeMin = 60; OrbTargetR = 0.6; OrbPullbackFilter = true; PullbackMaxRet = 0.44; StopCapAtr = 0.35;
				UseMseq = true; UseCrt = true; UseMom11 = true; UseMom1130 = false; UseRsi2 = false; UseOrb90 = true; UseMseqShort = true; UseMom13 = true; UseMom1030 = true; UseOn07 = true; UseRev06 = true; UseLon = true; UseIct = true;
				Contracts = 1; FlattenTime = 1556; SkipFomc = true;
				AdaptiveSize = false; SizeHigh = 2; SizeLow = 1; SizeDownDrawdown = 600; IctMultiplier = 2; UseConfluence = true; UseContextRules = true; UseVw13 = true; UseVolBreak = true; UseLate15 = true; UseEng10 = false; UseLateFh = false; Vw13Wide = true; UseNf05 = true; UseLf0315 = false; UseLf06 = true; UseLf0430 = true; NightOnWr70 = false; UseCpi09 = true; CpiDates = ""; Cpi09Multiplier = 4; Mom1030Multiplier = 4; EvalHighWrMultiplier = 0;
				SixYearModules = true; UseCa04v = false; UseSo04 = true; UseGd03 = false; UseRv11 = true; UseEng26 = false; UseOrFail = true; UseCam3 = true;	// research/mine/six_oos.py (2026-10-19): only the four that held on 2010-19 (never used to choose them)
				FomcDates = "2024-01-31,2024-03-20,2024-05-01,2024-06-12,2024-07-31,2024-09-18,2024-11-07,2024-12-18,2025-01-29,2025-03-19,2025-05-07,2025-06-18,2025-07-30,2025-09-17,2025-10-29,2025-12-10,2026-01-28,2026-03-18,2026-04-29,2026-06-17,2026-07-29,2026-09-16,2026-10-28,2026-12-09";
				StartBalance = 50000; EvalTarget = 0; MaxDrawdown = 0; DrawdownBuffer = 250; DailyLossLimit = 0; DailyLossPerContract = 0; MinAtrPoints = 150;
				EvalMode = false; EvalStartDate = "2026-10-05"; EvalLateDay = 12; EvalLateGoal = 2000; EvalLateContracts = 3; EvalLateMinCushion = 0;
				PauseFile = "pause_trading.txt"; ShowDashboard = true; PrintLog = true;
				EdgeMonitor = true; EdgeMonitorPause = false; EdgeMonitorStart = "2026-10-05"; EdgeK = 0; EdgeH = 0; EdgeAlarmFallback = true; EdgeFallbackDays = 252; EdgeFallbackOff = "";
				PropMode = NQMasterPropMode.Off; PropTrailingDD = 2000; EvalCushionFull = 0; EvalDailyStop = 0; FundedCushionSafe = 0; FundedPayoutAt = 5000; FundedHighFull = true; FundedCushionFull = 0;
				PropPeakOverride = 0; PropThresholdOverride = 0; AtrStartMax = 0; ConsistencyPct = 50; EvalBestDaySoFar = 0; EvalProfitStop = 1400; EvalSafeSet = NQMasterSafeSet.Estable; FundedProfitStop = 0; FundedStepUpCushion = 0; FundedStepUpContracts = 2; FundedLadderStep = 0; FundedLadderMax = 4;
				OrbPriorCloseAtr = 0.10; VolbBreakEven = true; MomAgreement = true; VolbTrendLastEntry = 1047; VolbReArm = false; NewsBlackout = false; NewsTimes = "";
				MinStopAtr = 0.10; RiskCapPerContract = 300; EvalRiskCapCushion = 1200; FundedRiskCapCushion = 2000;
				WarmupDays = 15;
				PropPreset = NQMasterPropPreset.Manual; CycleSim = true; EvalPrice = 0; ActivationFee = 0;
				AccountSyncGuard = true; SkipShortSessions = true; MaxOpenContracts = 20; RollGuard = true; LogToFile = true; ModuleHealthReport = true; DisableModules = ""; InactivityAlarm = true; CrossAccountGuard = true; HedgeGroup = "";
				UseOrderFlowBoost = false; OrderFlowCvdMin = 0.015; OrderFlowBoost = 2; OrderFlowStack = false;
				FillSeries = NQMasterFillSeries.Off; TraceOrdersLog = false;
			}
			else if (State == State.Configure)
			{
				AddDataSeries(BarsPeriodType.Minute, 5);
				// experiment 01 (docs/PLAN_2026-10-26.md): optional intrabar series (index 2) that receives every order, as in NinjaTrader's
				// SampleIntrabarBacktest. Backtest realism only: the 1-minute logic is untouched, fills happen on ticks / seconds.
				if (FillSeries == NQMasterFillSeries.Tick1) AddDataSeries(BarsPeriodType.Tick, 1);
				else if (FillSeries == NQMasterFillSeries.Second1) AddDataSeries(BarsPeriodType.Second, 1);
				fillCfg = FillSeries == NQMasterFillSeries.Off ? 0 : 2; fillBip = 0;
				TraceOrders = TraceOrdersLog;
			}
			else if (State == State.DataLoaded)
			{
				runStart = DateTime.Now; Print(string.Format("NQMaster | fill series {0} (orders on BarsInProgress {1}), trace orders {2}, run started {3:HH:mm:ss}", FillSeries, fillCfg, TraceOrders ? "on" : "off", runStart));
				rthCloses = new List<double>(); atrHist = new List<double>();
				dashFont = new SimpleFont("Consolas", 11);
				try { etZone = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time"); } catch { etZone = null; }
				badTimeframe = !(BarsPeriod.BarsPeriodType == BarsPeriodType.Minute && BarsPeriod.Value == 1);
				if (badTimeframe) Print("NQMaster | Needs a 1-MINUTE chart (CME US Index Futures ETH).");
				if (etZone == null) { badTimeframe = true; Print("NQMaster | Windows time zone 'Eastern Standard Time' not found: every module uses ET clock times, so the strategy does not trade."); }
				try { sessIt = new SessionIterator(Bars); } catch { sessIt = null; }
				fomc = new HashSet<int>();
				foreach (string raw in (BuiltinFomc + "," + (FomcDates ?? "")).Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries))
				{
					DateTime d;
					if (DateTime.TryParseExact(raw.Trim(), "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out d)) fomc.Add(d.Year * 10000 + d.Month * 100 + d.Day);
					else Print("NQMaster | FOMC dates: cannot read '" + raw.Trim() + "' (format yyyy-MM-dd)");
				}
				cpiDays = new HashSet<int>();
				foreach (string raw in (BuiltinCpi + "," + (CpiDates ?? "")).Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries))
				{
					DateTime d;
					if (DateTime.TryParseExact(raw.Trim(), "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out d)) cpiDays.Add(d.Year * 10000 + d.Month * 100 + d.Day);
					else Print("NQMaster | CPI dates: cannot read '" + raw.Trim() + "' (format yyyy-MM-dd)");
				}
				ForceRetired();
				CycleInit();
				newsEt = new List<DateTime>();
				foreach (string raw in (BuiltinNews + "," + (NewsTimes ?? "")).Split(new[] { ',', ';' }, StringSplitOptions.RemoveEmptyEntries))
				{
					DateTime nt;
					if (DateTime.TryParseExact(raw.Trim(), "yyyy-MM-dd HH:mm", CultureInfo.InvariantCulture, DateTimeStyles.None, out nt)) newsEt.Add(nt);
					else Print("NQMaster | news times: cannot read '" + raw.Trim() + "' (format yyyy-MM-dd HH:mm, 24 h, e.g. 2027-01-08 08:30)");
				}
				BuildModules();
				ApplyDisableList();
				foreach (Mod m in mods) m.BaseOn = m.On;
				EdgeParams();
			}
			else if (State == State.Realtime)
			{
				// an entry still Initialized at the switch was never processed on history (NinjaTrader would send it live now): drop it
				foreach (Mod m in mods)
				{
					if (m.Entry == null) continue;
					if (m.Entry.OrderState == OrderState.Initialized) DropStale(m, "not processed on history", false);
					else m.Entry = GetRealtimeOrder(m.Entry);
				}
				foreach (Order z in zombies) { try { Order r = GetRealtimeOrder(z); if (r != null && Working(r)) CancelOrder(r); } catch { } }
				eqPeak = netPnl;	// adaptive size measures the drawdown from the moment the strategy goes live
				int hq = Math.Max(1, Qty());
				CycleGoLive();
				liveStartPnl = netPnl; liveStartTrades = totalTrades; liveStart = ToEt(Times[0][0]);
				PropGoLive();
				int lq = Math.Max(1, Qty());	// code review 2026-10-17 M1: entries carried over from history keep the backtest size; re-size them to the live cushion's size
				if (lq != hq) foreach (Mod m in mods)
				{
					if (m.Entry == null || !Working(m.Entry) || (m.Entry.OrderType != OrderType.StopMarket && m.Entry.OrderType != OrderType.Limit)) continue;
					int want = Math.Max(1, (int)Math.Round(m.Entry.Quantity * (double)lq / hq));
					if (want != m.Entry.Quantity) { try { ChangeOrder(m.Entry, want, m.Entry.LimitPrice, m.Entry.StopPrice); Log(string.Format("{0} entry re-sized {1} -> {2} at go-live (cushion size {3} -> {4})", m.Sig, m.Entry.Quantity, want, hq, lq)); } catch { } }
				}
				if (lq != hq)	// review 2026-10-21 M2: parked setups and the pending MSEQ / MSEQS retry carry the history size as well
				{
					foreach (Mod m in mods) if (m.Parked) m.ParkQty = Math.Max(1, (int)Math.Round(m.ParkQty * (double)lq / hq));
					if (pend5 != null) pend5Qty = Math.Max(1, (int)Math.Round(pend5Qty * (double)lq / hq));
				}
				edgeDayQty = Qty(); statQty = Qty();	// review L14
				syncArmed = false; desyncBars = 0; NewsListCheck();
				if (atrCount < AtrMin || rthDaysSeen < WarmupDays) Warn("nqm_warmup", string.Format("NQMaster | WARNING: only {0} RTH days loaded, the warm-up needs {1}: modules stay idle until then (set Days to load >= 45).", rthDaysSeen, WarmupDays));
				rollHalt = RollDue(); if (rollHalt) Warn("nqm_roll", "NQMaster | ROLL DATE reached for " + Instrument.FullName + ": no new entries. Move the strategy to the next contract (same settings).");
				Log(string.Format("LIVE on {0} | profile {1} | contracts {2} | prop {3} | max open contracts {4} | account sync guard {5}", Instrument.FullName, Profile, Contracts, PropMode, MaxOpenContracts, AccountSyncGuard ? "on" : "off"));
				wentLive = true; PrintModuleReport("loaded history"); EdgeRestore();
			}
			else if (State == State.Terminated)
			{
				if (presetSnap != null && cy != null) { RestorePreset(presetSnap); PropMode = realMode; }	// review M4: never leave the simulated phase in the properties
				try { if (CrossAccountGuard && PosFile != null && File.Exists(PosFile)) File.Delete(PosFile); } catch { }
				if (zombieCount > 0)
					Print(string.Format("NQMaster | {0} stale entry order(s) were dropped during this run (Output lines 'STALE ORDER'). Before this fix each one blocked a module and the opposite direction for good.", zombieCount));
				if (UseOrderFlowBoost && mods != null)
					Print(ofTicks == 0 ? "NQMaster | ORDER FLOW BOOST was on but NO TICK DATA arrived, so nothing was boosted. Backtests need Tick Replay: Tools > Options > Market data > 'Show Tick Replay', then tick 'Tick Replay' in the Strategy Analyzer data series."
						: string.Format("NQMaster | order flow: {0:N0} trades read, {1} of {2} entries filled with the boost ({3:0.0}%; research Apr-Oct 2026: ~16%).", ofTicks, ofBoosted, ofEntries, ofEntries > 0 ? 100.0 * ofBoosted / ofEntries : 0));
				if (mods != null && !wentLive) PrintModuleReport("end of run");
				if (mods != null && runStart.Year > 2000 && BarsArray != null && BarsArray.Length > fillCfg && BarsArray[0] != null)
					Print(string.Format("NQMaster | RUN TIME fill series {0}: {1:0.0} s wall clock, {2:N0} 1-minute bars{3}", FillSeries, (DateTime.Now - runStart).TotalSeconds, BarsArray[0].Count,
						fillCfg > 0 && BarsArray[fillCfg] != null ? string.Format(", {0:N0} fill-series bars", BarsArray[fillCfg].Count) : ""));
				if (mods != null && totalTrades == 0 && rthDaysSeen < WarmupDays + 2)
					Print(string.Format("NQMaster | 0 trades: only {0} RTH days loaded; needs {1} days of warm-up (property 'Warm-up days'). Start the test earlier or lower it.", rthDaysSeen, WarmupDays));
			}
		}

		public override string DisplayName { get { return "NQ MASTER (" + Profile + ")"; } }

		private void BuildModules()
		{
			bool w7 = Profile == NQMasterProfile.WR70Plus, uq = Profile == NQMasterProfile.UltraQ, ul = Profile == NQMasterProfile.Ultra || uq, du = Profile == NQMasterProfile.Durable, custom = Profile == NQMasterProfile.Custom;
			profUltra = ul;
			mods = new List<Mod>(); timeMods = new List<Mod>(); sixMods = new List<Mod>();
			orb = new Mod(); orb.Sig = "ORB60"; orb.Kind = 0;
			orb.On = UseOrb;
			orb.Range = custom ? OrbRangeMin : 60;
			orb.R = custom ? OrbTargetR : (w7 ? 0.75 : 0.6);
			orb.UsePullback = custom ? OrbPullbackFilter : true;
			mods.Add(orb);
			orb2 = new Mod(); orb2.Sig = "ORB90"; orb2.Kind = 0; orb2.On = (custom ? UseOrb90 : (ul || w7 || du) && UseOrb90); orb2.Range = 90; orb2.R = 0.6; orb2.UsePullback = true;
			mods.Add(orb2);
			mseq = NewMod("MSEQ", (custom ? UseMseq : (ul || w7) && UseMseq), 0.5); mseq.PriceTarget = true;
			mseqs = NewMod("MSEQS", (custom ? UseMseqShort : (ul || w7 || du) && UseMseqShort), 0.75); mseqs.PriceTarget = true;
			crt = NewMod("CRT11", UseCrt, 2.0); crt.PriceTarget = true;
			lon = NewMod("LON", (custom ? UseLon : ul && !uq && UseLon), 2.0); lon.PriceTarget = true;
			ict = NewMod("ICT", (custom ? UseIct : ((ul && !uq) || w7) && UseIct), 1.0); ict.PriceTarget = true;
			AddTime("MOM11", (custom ? UseMom11 : (ul || w7) && UseMom11), 1100, -2, false, 0.25, 0.3, 0, false, true);
			AddTime("MOM13", (custom ? UseMom13 : ul && UseMom13), 1300, -2, false, 0.20, 1.0, 240, true, false);
			AddTime("MOM1030", (custom ? UseMom1030 : ul && UseMom1030), 1030, -2, false, 0.20, 0.3, 60, true, false);
			AddTime("ON07", (custom ? UseOn07 : ul && !uq && UseOn07), 700, 30, false, 0.20, 1.0, 60, true, false);
			AddTime("REV06", (custom ? UseRev06 : (ul || w7) && UseRev06), 600, 30, true, 0.20, 0.3, 240, true, false);
			AddTime("MOM1130", custom && UseMom1130, 1130, -2, false, 0.25, 0.3, 0, false, true);
			Mod vw13 = AddTime("VW13", (custom ? UseVw13 : (ul || w7) && UseVw13), 1301, -3, false, 0.15, 0.5, 120, true, false); bool vwWide = w7 || ((ul || custom) && !uq && Vw13Wide); vw13.MinDist = vwWide ? 0.15 : 0.30; vw13.DoubleDist = vwWide ? 0.30 : 0;
			Mod late15 = AddTime("LATE15", (custom ? UseLate15 : (ul || w7) && UseLate15), 1500, -4, false, 0.30, 0.5, 0, true, false); late15.MinDist = 0.5;
			bool six = Profile == NQMasterProfile.Ultra && SixYearModules;	// six-year modules (group 11, 2026-10-16; durable four by default since 2026-10-19)
			Mod latefh = AddTime("LATEFH", (custom ? UseLateFh : ul && UseLateFh), 1500, -4, false, 0.20, 0.5, 0, false, false); latefh.MinDist = 0.25; latefh.FhCheck = true;
			Mod nf05 = AddTime("NF05", (custom ? UseNf05 : (ul || du || (w7 && NightOnWr70)) && UseNf05), 500, -5, true, 0.20, 2.0, 240, false, false); nf05.MinDist = 0.35; nf05.Anchor = 20 * 60;
			Mod lf0315 = AddTime("LF0315", (custom ? UseLf0315 : ul && UseLf0315), 315, -5, true, 0.20, 2.0, 600, false, false); lf0315.MinDist = 0.10; lf0315.Anchor = 3 * 60;
			Mod lf06 = AddTime("LF06", (custom ? UseLf06 : (ul || (w7 && NightOnWr70)) && UseLf06), 600, -5, true, 0.20, 0.5, 240, false, false); lf06.MinDist = 0.20; lf06.Anchor = 4 * 60;
			Mod lf0430 = AddTime("LF0430", (custom ? UseLf0430 : (ul || (w7 && NightOnWr70)) && UseLf0430), 430, -5, true, 0.35, 0.5, 240, true, false); lf0430.MinDist = 0.10; lf0430.Anchor = 4 * 60;
			// research/mine/cpi_lab.py (2026-10-14): CPI days, fade the 08:30 release move at the 09:30 open (16 years, 4 periods PF > 1)
			Mod cpi09 = AddTime("CPI09", (custom ? UseCpi09 : (ul || w7) && UseCpi09), 930, -5, true, 0.35, 0.5, 60, false, false); cpi09.MinDist = 0.05; cpi09.Anchor = 8 * 60 + 30; cpi09.CpiOnly = true;
			// six-year modules (research/mine/six_combo2.py; real NQ 2020-10..2026, chosen on 2020-23, checked on 2024-26). Ultra only (not UltraQ).
			Mod ca04v = AddTime("CA04V", ((custom ? SixYearModules : six) && UseCa04v), 401, -6, false, 0.15, 1.0, 120, false, false); ca04v.MinDist = 0.20;	// 04:00 momentum vs the session VWAP
			Mod so04 = AddTime("SO04", ((custom ? SixYearModules : six) && UseSo04), 401, -1, false, 0.15, 1.0, 330, true, false); so04.MinDist = 0.35;	// 04:00 momentum vs the 18:00 open, with the trend
			Mod gd03 = AddTime("GD03", ((custom ? SixYearModules : six) && UseGd03), 500, -5, true, 0.20, 2.0, 240, true, false); gd03.MinDist = 0.20; gd03.Anchor = 3 * 60; gd03.StructStop = true;	// 05:00 fade of the move since 03:00, with the trend
			Mod rv11 = AddTime("RV11", ((custom ? SixYearModules : six) && UseRv11), 1100, -7, false, 0.15, 1.0, 400, false, false); rv11.MinDist = 0.25; rv11.RvolMax = 0.8;	// 11:00 low-volume continuation vs the prior close
			eng26 = NewMod("ENG26", ((custom ? SixYearModules : six) && UseEng26), 0.5); eng26.PriceTarget = true; eng26.MaxHold = 400; eng26.Six = true; sixMods.Add(eng26);
			orf = NewMod("ORFAIL", ((custom ? SixYearModules : six) && UseOrFail), 1.0); orf.PriceTarget = true; orf.MaxHold = 240; orf.Six = true; sixMods.Add(orf);
			cam3 = NewMod("CAM3", ((custom ? SixYearModules : six) && UseCam3), 1.0); cam3.PriceTarget = true; cam3.MaxHold = 240; cam3.Six = true; sixMods.Add(cam3);
			eng10 = NewMod("ENG10", (custom ? UseEng10 : ul && UseEng10), 0.5); eng10.PriceTarget = true; eng10.MaxHold = 400;
			volb = NewMod("VOLB", (custom ? UseVolBreak : (ul || w7 || du) && UseVolBreak), w7 ? 0.5 : 2.0); volb.PriceTarget = true; volb.MaxHold = 400; volbTrendOnly = w7; volbTrendBase = volbTrendOnly; volbRBase = volb.R;
			rsi = NewMod("RSI2", custom && UseRsi2, 0.3); rsi.StopAtr = 0.15; rsi.MaxHold = 120;
			StringBuilder sb = new StringBuilder();
			foreach (Mod m in mods) if (m.On) sb.Append(m.Sig + " ");
			Print("NQMaster | profile " + Profile + " | modules: " + sb.ToString());
			if (!custom && (OrbRangeMin != 60 || Math.Abs(OrbTargetR - 0.6) > 1e-9 || !OrbPullbackFilter))
				Print("NQMaster | NOTE: ORB range / target R / pullback filter only apply with Profile = Custom. The profile values are being used.");
		}
		// 'Disable modules' (group 10): switch modules off by name in any profile (the yearly review, research/mine/robust16.py)
		private void ApplyDisableList()
		{
			if (string.IsNullOrEmpty(DisableModules)) return;
			foreach (string raw in DisableModules.Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries))
			{
				string s = raw.Trim(); bool hit = false;
				foreach (Mod m in mods) if (string.Equals(m.Sig, s, StringComparison.OrdinalIgnoreCase)) { hit = true; m.On = false; }
				Print(hit ? "NQMaster | module " + s.ToUpperInvariant() + " switched off by 'Disable modules'" : "NQMaster | 'Disable modules': '" + s + "' is not a module name (names: ORB60 ORB90 MSEQ MSEQS CRT11 LON ICT MOM11 MOM13 MOM1030 ON07 REV06 VW13 LATE15 LATEFH NF05 LF06 LF0430 CPI09 ENG10 VOLB CA04V SO04 GD03 RV11 ENG26 ORFAIL CAM3 ...)");
			}
		}

		// Module health report (group 10): trades / win rate / PF / net per module, whole run and last 365 days, from this strategy's own trades
		private bool wentLive;
		private void PrintModuleReport(string label)
		{
			if (!ModuleHealthReport) return;
			try
			{
				if (SystemPerformance == null || SystemPerformance.AllTrades == null || SystemPerformance.AllTrades.Count == 0) return;
				TradeCollection all = SystemPerformance.AllTrades;
				DateTime last = all[all.Count - 1].Exit.Time, fromTime = last.AddDays(-365);
				Dictionary<string, double[]> st = new Dictionary<string, double[]>(); List<string> order = new List<string>();
				foreach (Trade t in all)
				{
					string k = t.Entry != null && !string.IsNullOrEmpty(t.Entry.Name) ? t.Entry.Name : "?";
					double[] a; if (!st.TryGetValue(k, out a)) { a = new double[8]; st[k] = a; order.Add(k); }
					double p = t.ProfitCurrency; bool yr = t.Exit != null && t.Exit.Time >= fromTime;
					a[0] += 1; if (p > 0) { a[1] += 1; a[2] += p; } else a[3] -= p;
					if (yr) { a[4] += 1; if (p > 0) { a[5] += 1; a[6] += p; } else a[7] -= p; }
				}
				order.Sort();
				Print(string.Format("NQMaster | MODULE HEALTH ({0}; {1} trades, last exit {2:yyyy-MM-dd}; 'last 365 d' ends there)", label, all.Count, last));
				foreach (string k in order)
				{
					double[] a = st[k];
					string line = string.Format("  {0,-8} all: {1,5:0} tr  WR {2,5:0.0}%  PF {3,5}  net {4,9:$#,0;-$#,0}  | last 365 d: {5,4:0} tr  WR {6,5}  PF {7,5}  net {8,9:$#,0;-$#,0}{9}",
						k, a[0], 100.0 * a[1] / a[0], a[3] > 0 ? (a[2] / a[3]).ToString("0.00") : "inf", a[2] - a[3],
						a[4], a[4] > 0 ? (100.0 * a[5] / a[4]).ToString("0.0") + "%" : "-", a[7] > 0 ? (a[6] / a[7]).ToString("0.00") : (a[4] > 0 ? "inf" : "-"), a[6] - a[7],
						a[4] >= 20 && a[5] >= 0.8 * a[4] ? "  <- >= 80% win rate last year" : (a[4] >= 20 && a[7] > 0 && a[6] / a[7] < 1.0 ? "  <- losing last year (review)" : ""));
					Print(line); if (State == State.Realtime) Log("health " + line.Trim());
				}
				Print("NQMaster | research: a >= 80% win-rate year does NOT predict the next trades better than the module's long-run rate (research/mine/sniper_eval.py, wr80_lab.py); use this list for the yearly review, not for sizing.");
			}
			catch (Exception e) { Print("NQMaster | module report skipped: " + e.Message); }
		}

		private Mod NewMod(string sig, bool isOn, double r) { Mod m = new Mod(); m.Sig = sig; m.On = isOn; m.R = r; m.Kind = 2; mods.Add(m); return m; }
		private Mod AddTime(string sig, bool isOn, int t, int lb, bool rev, double sa, double r, int hold, bool trend, bool vwap)
		{
			Mod m = new Mod(); m.Sig = sig; m.On = isOn; m.Kind = 1; m.Time = t; m.Lookback = lb; m.Reverse = rev; m.StopAtr = sa; m.R = r; m.MaxHold = hold; m.Trend = trend; m.Vwap = vwap;
			mods.Add(m); timeMods.Add(m); return m;
		}

		protected override void OnBarUpdate()
		{
			if (BarsInProgress == 2) return;				// fill series (FillSeries Tick1 / Second1): orders only, no logic
			if (badTimeframe || CurrentBars[0] < 3) return;
			if (fillCfg > 0)							// orders go to the fill series only once it has bars; before that (no tick history yet) they go to the 1-minute series as with Off
			{
				int fb = CurrentBars.Length > fillCfg && CurrentBars[fillCfg] >= 1 ? fillCfg : 0;
				if (fb != fillBip) { fillBip = fb; Log(string.Format("FILL SERIES {0}: orders on BarsInProgress {1} from this bar", FillSeries, fillBip)); }
			}
			if (BarsInProgress == 1) { OnFiveMinute(); return; }

			DateTime etClose = ToEt(Time[0]);
			DateTime etOpen = etClose.AddMinutes(-1);
			int openMin = etOpen.Hour * 60 + etOpen.Minute;
			int closeMin = etClose.Hour * 60 + etClose.Minute;
			int etDate = etOpen.Year * 10000 + etOpen.Month * 100 + etOpen.Day;

			ProcessClosedTrades();
			PurgeStaleEntries();
			if (firstBarDate == 0) firstBarDate = etDate;
			CrossAccountPublish();
			CheckAccountSync();
			if (desyncHalt) return;
			CrossAccountCancelOpp();
			if (hedgeFlat) { if (Position.MarketPosition == MarketPosition.Flat) hedgeFlat = false; else FlattenAll("cross-account hedge guard"); }

			if (Bars.IsFirstBarOfSession)
			{
				CancelAllEntries();                                  // nothing from the last session survives (half days: no 15:56 cancel)
				foreach (Order z in rtZombies) { try { if (Working(z)) CancelOrder(z); } catch { } }
				rtZombies.Clear(); rejectHalt = false;
				SessionBounds();
				InactivityDayClose();
				EdgeDayClose(etOpen);
				StatDayClose();
				dayStartPnl = netPnl; dayStopped = false;
				// the session that just ended: finalize its RTH day, or mark it as a session without a complete RTH day
				if (dayHasBars) FinalizeRthDay();
				else if (rthDaysSeen > 0) { full2 = full1; full1 = double.NaN; }
				DateTime tradeDay = etOpen.Hour >= 18 ? etOpen.Date.AddDays(1) : etOpen.Date;
				prevSessDay = curSessDay; curSessDay = tradeDay.Year * 10000 + tradeDay.Month * 100 + tradeDay.Day;
				fomcToday = SkipFomc && fomc.Contains(tradeDay.Year * 10000 + tradeDay.Month * 100 + tradeDay.Day);
				cpiToday = cpiDays != null && cpiDays.Contains(tradeDay.Year * 10000 + tradeDay.Month * 100 + tradeDay.Day);
				EvalSessionStart(tradeDay);
				CycleSessionStart(tradeDay);
				edgeDayQty = Qty(); edgeDayTradable = !fomcToday && !rollHalt && !PauseActive(); edgeDayDate = tradeDay;		// review F9: blocked days are not counted
				NewSession();
				PropSessionStart();
				edgeDayQty = Qty();                                  // after the prop cushion is known (funded step-up)
				statQty = Qty(); statDayHalted = cyOn && cyHalt;
				cyPrevTradable = !fomcToday && !(MinAtrPoints > 0 && !double.IsNaN(todayAtr) && todayAtr < MinAtrPoints) && !(SkipShortSessions && shortSession) && !rollHalt;
				if (cyOn && cyHalt) edgeDayTradable = false;	// review L6
				sessHi = High[0]; sessLo = Low[0];
			}
			sessHi = Math.Max(sessHi, High[0]); sessLo = Math.Min(sessLo, Low[0]);
			if (openMin >= 120 && openMin < 360) { if (!e10aHas) { e10aO = Open[0]; e10aH = High[0]; e10aL = Low[0]; e10aHas = true; } e10aH = Math.Max(e10aH, High[0]); e10aL = Math.Min(e10aL, Low[0]); e10aC = Close[0]; }
			else if (openMin >= 360 && openMin < 600) { if (!e10bHas) { e10bO = Open[0]; e10bH = High[0]; e10bL = Low[0]; e10bHas = true; } e10bH = Math.Max(e10bH, High[0]); e10bL = Math.Min(e10bL, Low[0]); e10bC = Close[0]; }
			if (openMin == 599) close10 = Close[0];
			foreach (Mod m in timeMods) if (m.Anchor >= 0 && double.IsNaN(m.AnchorPx) && openMin >= m.Anchor && openMin <= m.Anchor + 5) m.AnchorPx = Open[0];
			foreach (Mod m in timeMods) if (m.StructStop && !double.IsNaN(m.AnchorPx)) { if (!m.WinHas) { m.WinH = High[0]; m.WinL = Low[0]; m.WinHas = true; } else { m.WinH = Math.Max(m.WinH, High[0]); m.WinL = Math.Min(m.WinL, Low[0]); } }
			{ double sv = Volume[0] > 0 ? Volume[0] : 1.0; sVwPv += (High[0] + Low[0] + Close[0]) / 3.0 * sv; sVwV += sv; }
			if (openMin >= 1320 || openMin < 120) { if (!e26aHas) { e26aO = Open[0]; e26aH = High[0]; e26aL = Low[0]; e26aHas = true; } e26aH = Math.Max(e26aH, High[0]); e26aL = Math.Min(e26aL, Low[0]); e26aC = Close[0]; }
			orfSig = 0; camSig = 0;
			bool inRth = openMin >= RthOpen && openMin < RthClose;
			bool overnight = openMin < RthOpen || openMin >= 18 * 60;
			if (overnight && openMin < RthOpen)
			{
				if (!onHas) { onH = High[0]; onL = Low[0]; onHas = true; } else { onH = Math.Max(onH, High[0]); onL = Math.Min(onL, Low[0]); }
				if (openMin >= 120 && openMin < 300) { if (!lonHas) { lonH = High[0]; lonL = Low[0]; lonHas = true; } else { lonH = Math.Max(lonH, High[0]); lonL = Math.Min(lonL, Low[0]); } }
				else if (openMin >= 300) { if (!postHas) { postH = High[0]; postL = Low[0]; postHas = true; } else { postH = Math.Max(postH, High[0]); postL = Math.Min(postL, Low[0]); } }
			}
			else if (overnight)
			{
				if (!onHas) { onH = High[0]; onL = Low[0]; onHas = true; } else { onH = Math.Max(onH, High[0]); onL = Math.Min(onL, Low[0]); }
			}
			if (inRth)
			{
				edgeDayRth = true;
				if (etDate != rthDay) StartRthDay(etDate);
				if (!dayHasBars) { dayHigh = High[0]; dayLow = Low[0]; dayHasBars = true; rthOpenPx = Open[0]; rthFirstClose = Close[0]; SetupIctLevels();
					double prng = prevRthHigh - prevRthLow; volbUp = double.IsNaN(prng) ? double.NaN : rthOpenPx + 0.45 * prng; volbDn = double.IsNaN(prng) ? double.NaN : rthOpenPx - 0.45 * prng; }
				else { dayHigh = Math.Max(dayHigh, High[0]); dayLow = Math.Min(dayLow, Low[0]); }
				dayClose = Close[0]; dayLastOpen = openMin;
				double vol = Volume[0] > 0 ? Volume[0] : 1.0;
				vwPv += (High[0] + Low[0] + Close[0]) / 3.0 * vol; vwV += vol;
				foreach (Mod o in new Mod[] { orb, orb2 })
					if (o.On && openMin < RthOpen + o.Range)
					{
						if (!o.OrReady && o.OrH == 0 && o.OrL == 0) { o.OrH = High[0]; o.OrL = Low[0]; }
						else { o.OrH = Math.Max(o.OrH, High[0]); o.OrL = Math.Min(o.OrL, Low[0]); }
						if (openMin == RthOpen + o.Range - 1) { o.OrReady = true; o.Armed = true; }
					}
				// CRT candles
				if (openMin >= 600 && openMin < 660) { if (!c1Has) { c1H = High[0]; c1L = Low[0]; c1Has = true; } else { c1H = Math.Max(c1H, High[0]); c1L = Math.Min(c1L, Low[0]); } }
				else if (openMin >= 660 && openMin < 720) { if (!c2Has) { c2H = High[0]; c2L = Low[0]; c2Has = true; } else { c2H = Math.Max(c2H, High[0]); c2L = Math.Min(c2L, Low[0]); } c2C = Close[0]; }
				if (openMin < 660) { rvAcc += Volume[0]; if (openMin == 659) rvDone = true; }
				if (orf.On) OrfTrack(openMin);
			}

			if (cam3.On) Cam3Track(openMin);
			AccountGuard();
			DailyLossCheck();
			PropDailyCheck();
			CycleBar();
			if (NewsBlackout && InNews(etClose, 3)) { FlattenAll("news blackout (Tier-1 release)"); status = "NEWS BLACKOUT"; UpdateDashboard(); return; }

			// exits: module time exits, London exit, flatten
			if (closeMin >= FlatMin && closeMin < 18 * 60) { FlattenAll(shortSession ? "early close (holiday / half day)" : "end of day"); UpdateDashboard(); return; }
			foreach (Mod m in timeMods)
				if (m.InTrade && m.MaxHold > 0 && CurrentBars[0] - m.EntryBar >= m.MaxHold) ExitModule(m, "time exit");
			if (rsi.InTrade && CurrentBars[0] - rsi.EntryBar >= rsi.MaxHold) ExitModule(rsi, "time exit");
			if (volb.InTrade && CurrentBars[0] - volb.EntryBar >= volb.MaxHold) ExitModule(volb, "time exit");
			// research/mine/wrq_exits.py: VOLB 2R (Ultra) stop to entry + 0.10R once the bar reaches +0.75R, from the next bar
			// (VOLB WR 52/51/50% -> 61/62/61%, PF 1.25/1.52/1.50 -> 1.30/1.66/1.57; plateau 0.4-1.0R x 0-0.2R)
			if (VolbBreakEven && volb.InTrade && !volbTrendOnly && !volbBeSet && volb.R >= 1.5)
			{
				double vr = (volb.EntryPx - volb.StopPx) * volb.Dir;
				if (vr > 0 && (volb.Dir == 1 ? High[0] >= volb.EntryPx + 0.75 * vr : Low[0] <= volb.EntryPx - 0.75 * vr))
				{
					double be = Instrument.MasterInstrument.RoundToTickSize(volb.EntryPx + volb.Dir * 0.10 * vr); volbBeSet = true;
					if ((Close[0] - be) * volb.Dir > TickSize) { SetStopLoss(volb.Sig, CalculationMode.Price, be, false); Log("VOLB stop -> entry + 0.1R @ " + Fmt(be)); }
					else ExitModule(volb, "break-even level already crossed");
				}
			}
			if (eng10.InTrade && CurrentBars[0] - eng10.EntryBar >= eng10.MaxHold) ExitModule(eng10, "time exit");
			foreach (Mod m in sixMods) if (m.InTrade && m.MaxHold > 0 && CurrentBars[0] - m.EntryBar >= m.MaxHold) ExitModule(m, "time exit");
			if (lon.InTrade && openMin >= 570 && openMin < 18 * 60) ExitModule(lon, "London exit 09:30");
			if (Working(lon.Entry) && (openMin >= 480 && openMin < 18 * 60)) CancelEntry(lon);

			bool canTrade = CanTrade();
			if (!canTrade) { CancelAllEntries(); UpdateDashboard(); return; }
			if (LateBar(Time[0])) { Log("bar processed late (session break / data gap): no new entries on it"); UpdateDashboard(); return; }
			// MSEQ / MSEQS deferred by an opposite stop/limit order: one retry on the next 1-minute bars (research enters them at market)
			if (pend5 != null)
			{
				if (pend5.InTrade || CurrentBars[0] > pend5Bar + 2 || (pend5Dir == 1 ? Low[0] <= pend5Stop : High[0] >= pend5Stop)) pend5 = null;
				else if (CurrentBars[0] > pend5Bar && DirectionAllowed(pend5Dir))
				{
					ArmPriceBracket(pend5, pend5Dir, pend5Stop); int pq = OfApply(pend5, pend5Qty, pend5Dir); Order po = pq <= 0 ? null : (pend5Dir == 1 ? EnterLong(fillBip, pq, pend5.Sig) : EnterShort(fillBip, pq, pend5.Sig));
					if (po != null) pend5.Entry = po; Log(pend5.Sig + " entered after the deferral"); pend5 = null;
				}
			}
			ManageParked(openMin, closeMin);
			if (UseOrderFlowBoost) OfRefresh();

			// ---- modules on the 1-minute series
			foreach (Mod o in new Mod[] { orb, orb2 })
				if (o.On && inRth && etDate == rthDay && o.OrReady && closeMin >= Math.Max(630, RthOpen + o.Range)) ManageOrb(o, closeMin);
			foreach (Mod m in timeMods)
			{
				if (m.Retry) { m.Retry = false; TimeEntry(m); if (lastDeferred) m.Retry = false; continue; }
				if (m.On && !m.Done && closeMin == Hm(m.Time)) { m.Done = true; TimeEntry(m); if (lastDeferred) m.Retry = true; }
			}
			if (crt.On && inRth && crt.Retry) { crt.Retry = false; crt.Done = false; CrtEntry(); crt.Retry = false; }
			else if (crt.On && inRth && openMin == 719 && c1Has && c2Has) { CrtEntry(); if (lastDeferred) crt.Retry = true; }
			if (lon.On && overnight && openMin < RthOpen) LondonStep(openMin);
			if (volb.On && inRth && etDate == rthDay) ManageVolb(openMin);
			if (eng10.On) ManageEng10(openMin);
			if (eng26.On && openMin == 929) Eng26Entry();
			if (orfSig != 0) { int os = orfSig; orfSig = 0; SixEnter(orf, os, orfSl, orfTp); }
			if (camSig != 0) { int cs = camSig; camSig = 0; SixEnter(cam3, cs, camSl, camTp); }
			UpdateDashboard();
		}

		#region Session / daily statistics
		private void NewSession()
		{
			sessOpen = Open[0]; rthOpenPx = double.NaN; vwPv = 0; vwV = 0;
			onHas = lonHas = postHas = false; c1Has = c2Has = false; rHas = false; lonStage = 0; levelsReady = false;
			ictAct[0] = ictAct[1] = false; ictTrades = 0;
			orb.OrH = 0; orb.OrL = 0; orb.OrReady = false; orb.Armed = false; orb.Trades = 0;
			orb2.OrH = 0; orb2.OrL = 0; orb2.OrReady = false; orb2.Armed = false; orb2.Trades = 0;
			orbFirstDir = 0; orbFirstMin = 9999;
			foreach (Mod m in timeMods) { m.Done = false; m.Retry = false; m.AnchorPx = double.NaN; }
			crt.Done = false; crt.Retry = false;
			rsiTrades = 0;
			volbDone = false; volbUp = double.NaN; volbDn = double.NaN; volbTrades = 0;
			e26aHas = false; sVwPv = 0; sVwV = 0; foreach (Mod m in timeMods) m.WinHas = false;
			orfHas = orfReady = orfDone = false; orfBrk = 0; orfSig = 0;
			// CAM3 levels: prior complete RTH close +- 1.1/4 of the prior RTH range, the side of the daily trend (research PIVOT_FADE CAM3)
			camSig = 0; camBr = -1; camSide = trendDir; camDone = !(cam3 != null && cam3.On) || camSide == 0 || double.IsNaN(full1) || double.IsNaN(prevRthHigh) || double.IsNaN(todayAtr);
			camLev = camDone ? double.NaN : full1 - camSide * (prevRthHigh - prevRthLow) * 1.1 / 4.0;
			e10aHas = false; e10bHas = false; eng10Done = false; eng10Retry = false; close10 = double.NaN; rthFirstClose = double.NaN;
			m11Dir = 0; onSum = 0; lonDir = 0;
			foreach (Mod m in mods) { m.Parked = false; m.RejToday = 0; }
			pend5 = null;
		}

		private void StartRthDay(int etDate)
		{
			FinalizeRthDay();
			rthDay = etDate; dayHasBars = false;
			if (rvDone) { rvHist.Add(rvAcc); while (rvHist.Count > 20) rvHist.RemoveAt(0); }	// RV11: prior days' 09:30-10:59 volume
			rvAcc = 0; rvDone = false;
			todayAtr = atrDaily;
			atrRatio = double.NaN;
			if (atrHist.Count >= 20 && todayAtr > 0) { List<double> srt = new List<double>(atrHist); srt.Sort(); int nn = srt.Count; double med = nn % 2 == 1 ? srt[nn / 2] : 0.5 * (srt[nn / 2 - 1] + srt[nn / 2]); atrRatio = med > 0 ? todayAtr / med : double.NaN; }
			if (!double.IsNaN(todayAtr)) { atrHist.Add(todayAtr); while (atrHist.Count > 100) atrHist.RemoveAt(0); }
			prevRet = (!double.IsNaN(full1) && !double.IsNaN(full2) && todayAtr > 0 && trendDir != 0) ? (full1 - full2) / todayAtr * trendDir : double.NaN;
			pullbackDay = !double.IsNaN(prevRet) && prevRet < PullbackMaxRet;
			rthDaysSeen++;
		}

		private void FinalizeRthDay()
		{
			if (!dayHasBars) { return; }
			double tr = double.IsNaN(atrPrevClose) ? dayHigh - dayLow : Math.Max(dayHigh - dayLow, Math.Max(Math.Abs(dayHigh - atrPrevClose), Math.Abs(dayLow - atrPrevClose)));
			atrCount++;
			int k = Math.Min(atrCount, 14);
			atrDaily = double.IsNaN(atrDaily) ? tr : ((k - 1) * atrDaily + tr) / k;
			atrPrevClose = dayClose; prevRthHigh = dayHigh; prevRthLow = dayLow;
			full2 = full1; full1 = dayLastOpen >= RthClose - 1 ? dayClose : double.NaN;
			rthCloses.Add(dayClose);
			while (rthCloses.Count > 20) rthCloses.RemoveAt(0);
			trendDir = 0;
			if (rthCloses.Count >= TrendMin)
			{
				double s = 0; foreach (double x in rthCloses) s += x;
				trendDir = dayClose > s / rthCloses.Count ? 1 : (dayClose < s / rthCloses.Count ? -1 : 0);
			}
			todayAtr = atrDaily;
			dayHasBars = false;
		}
		#endregion

		#region Modules
		private void ManageOrb(Mod o, int closeMin)
		{
			if (o.UsePullback && !pullbackDay) return;
			if (trendDir == 0 || atrCount < AtrMin || double.IsNaN(todayAtr)) return;
			bool window = closeMin < 780;
			if (!window) { CancelEntry(o); return; }
			if (!o.Parked && !o.Armed && !o.InTrade && !Working(o.Entry) && o.Trades > 0 && o.Trades < 2 && Close[0] < o.OrH && Close[0] > o.OrL) o.Armed = true;
			if (o.Parked || !o.Armed || o.InTrade || Working(o.Entry) || o.Trades >= 2) return;
			if (CurrentBars[0] <= deferUntil && trendDir == -deferDir) return;	// an opposite deferred module enters first
			int d = trendDir;
			double entry = d == 1 ? o.OrH + TickSize : o.OrL - TickSize;
			// research/mine/wrq_combo.py (ORBt): the breakout trigger must clear the prior RTH close by >= 0.10 ATR in the trade direction
			// (ORB60 0.6R PF 1.62/1.60/1.56 -> 1.92/1.81/2.05, ORB90 1.43/1.31/1.38 -> 1.87/1.48/1.75, IS / CFD 24-26 / MNQ 24-26)
			if (OrbPriorCloseAtr > -1 && !double.IsNaN(atrPrevClose) && (entry - atrPrevClose) * d < OrbPriorCloseAtr * todayAtr)
			{ o.Armed = false; o.Trades = 2; Log(o.Sig + " skipped today: breakout level not beyond the prior close by " + OrbPriorCloseAtr.ToString("0.00") + " ATR"); return; }
			double opp = d == 1 ? o.OrL - TickSize : o.OrH + TickSize;
			int st = Math.Max(8, (int)Math.Round(Math.Min(Math.Abs(entry - opp), StopCapAtr * todayAtr) / TickSize));
			o.Armed = false;
			SetStopLoss(o.Sig, CalculationMode.Ticks, st, false);
			SetProfitTarget(o.Sig, CalculationMode.Ticks, Math.Max(1, (int)Math.Round(st * o.R)));
			// 2026-10-12 (research/mine/rules16_check.py): the ORB60 'ATR ratio' and ORB90 'near VWAP' boosts did not hold on 2010-19 nor 2024-26 -> removed
			bool oc = o == orb ? (FeatGap(d) >= 0.3311 || FeatRet5(d) >= 1.8118) : (FeatOpen(d, entry) >= 0.5458);
			int oq = CtxBoost(Qty(), oc, o.Sig);
			if (TooTight(o.Sig, st * TickSize, todayAtr) || TooBig(o.Sig, st * TickSize, oq)) { o.Trades = 2; return; }
			if (!DirectionAllowed(d)) { if (lastDeferred) o.Armed = true; else if (!PastLevel(d, entry)) { o.Dir = d; ParkSetup(o, false, Instrument.MasterInstrument.RoundToTickSize(entry), oq); } return; }
			bool through = PastLevel(d, entry);
			o.Dir = d;
			oq = OfApply(o, oq, d);
			if (oq <= 0) { o.Trades = 2; return; }
			Order r = d == 1 ? (through ? EnterLong(fillBip, oq, o.Sig) : EnterLongStopMarket(fillBip, true, oq, entry, o.Sig)) : (through ? EnterShort(fillBip, oq, o.Sig) : EnterShortStopMarket(fillBip, true, oq, entry, o.Sig));
			if (r != null) o.Entry = r;
			Log(string.Format("{0} {1} @ {2} | SL {3}t | TP {4:0.##}R", o.Sig, d == 1 ? "BUY" : "SELL", Fmt(entry), st, o.R));
		}

		// ---- VOLB: one stop entry per day at RTH open +/- 0.45 x prior RTH range (the side nearer to price is kept working),
		// stop at the RTH open price, target 2R, max 400 min, 09:30-15:00 entries (research/mine/families2.py, VOL_BREAK).
		private void ManageVolb(int openMin)
		{
			if (volbDone || volb.InTrade || double.IsNaN(volbUp) || double.IsNaN(rthOpenPx) || atrCount < AtrMin) return;
			if (openMin >= 899) { CancelEntry(volb); volbDone = true; return; }
			// research/mine/wrq_combo.py (VTSO): trend-only VOLB (WR70Plus / Estable) fills after 10:47 ET lose their edge
			if (volbTrendOnly && VolbTrendLastEntry > 0 && openMin >= Hm(VolbTrendLastEntry)) { CancelEntry(volb); volbDone = true; return; }
			int d = (volbUp - Close[0]) <= (Close[0] - volbDn) ? 1 : -1;
			if (volbTrendOnly)
			{
				if (trendDir == 0 || (trendDir == 1 && Low[0] <= volbDn) || (trendDir == -1 && High[0] >= volbUp)) { CancelEntry(volb); volbDone = true; return; }
				d = trendDir;
			}
			if (CurrentBars[0] <= deferUntil) return;      // another module is waiting for VOLB's order to be cancelled
			if (Working(volb.Entry))
			{
				if (volb.Dir == d) return;
				CancelEntry(volb); return;                    // switch side on the next bar
			}
			double lvl = d == 1 ? Instrument.MasterInstrument.RoundToTickSize(volbUp) : Instrument.MasterInstrument.RoundToTickSize(volbDn);
			if (TooTight(volb.Sig, Math.Abs(lvl - rthOpenPx), todayAtr) || TooBig(volb.Sig, Math.Abs(lvl - rthOpenPx), Qty())) { volbDone = true; return; }
			if (PastLevel(d, lvl))
			{
				// realtime with the ask / bid right at the level (a stop there would be rejected): market entry; further through: no chase
				double mk = double.NaN;
				if (State == State.Realtime) try { mk = d == 1 ? GetCurrentAsk() : GetCurrentBid(); } catch { }
				if (!double.IsNaN(mk) && (mk - lvl) * d <= TickSize && !OppBusy(d, volb))
				{ ArmPriceBracket(volb, d, Instrument.MasterInstrument.RoundToTickSize(rthOpenPx)); int vq = OfApply(volb, Qty(), d); Order vm = vq <= 0 ? null : (d == 1 ? EnterLong(fillBip, vq, volb.Sig) : EnterShort(fillBip, vq, volb.Sig)); if (vm != null) volb.Entry = vm; }
				volbDone = true; return;
			}
			// never cancel other modules' working entries for VOLB: wait while the position or a working order points the other way
			if ((d == 1 && Position.MarketPosition == MarketPosition.Short) || (d == -1 && Position.MarketPosition == MarketPosition.Long)) return;
			foreach (Mod o in mods) if (o != volb && Working(o.Entry) && o.Dir == -d) return;
			if (RtZombieOpp(d)) return;
			if (OtherOpp(d, false)) return;		// round 5 C6 (2): another account of the group holds the opposite position / entry
			ArmPriceBracket(volb, d, Instrument.MasterInstrument.RoundToTickSize(rthOpenPx));
			int vsq = OfApply(volb, Qty(), d);
			if (vsq <= 0) return;
			Order vr = d == 1 ? EnterLongStopMarket(fillBip, true, vsq, lvl, volb.Sig) : EnterShortStopMarket(fillBip, true, vsq, lvl, volb.Sig);
			if (vr != null) volb.Entry = vr;
		}


		// ENG10 (research/mine/ultra_plus.py): 06:00-10:00 4H candle closes beyond the 02:00-06:00 candle in its direction, with the trend.
		private void ManageEng10(int openMin)
		{
			if (eng10Retry && !eng10.InTrade && !eng10.Parked) { if (openMin >= 600 && openMin < 689) Eng10Place(); else eng10Retry = false; return; }
			if (eng10Done || eng10.InTrade)
			{
				if (Working(eng10.Entry) && openMin >= 689 && openMin < 18 * 60) { CancelEntry(eng10); Log("ENG10 entry expired"); }
				return;
			}
			if (openMin != 599) return;
			eng10Done = true;
			if (!e10aHas || !e10bHas || atrCount < AtrMin || double.IsNaN(todayAtr) || todayAtr <= 0 || trendDir == 0) return;
			int d = 0;
			if (e10bC > e10bO && e10bC > e10aH) d = 1; else if (e10bC < e10bO && e10bC < e10aL) d = -1;
			if (d == 0 || d != trendDir) return;
			double px = Instrument.MasterInstrument.RoundToTickSize(d == 1 ? e10bH + TickSize : e10bL - TickSize);
			if ((d == 1 && Close[0] >= px) || (d == -1 && Close[0] <= px)) return;
			double sl = Instrument.MasterInstrument.RoundToTickSize(px - d * 0.5 * (e10bH - e10bL)), risk = (px - sl) * d;
			if (risk <= 0.02 * todayAtr || risk > 0.6 * todayAtr) return;
			if (TooTight(eng10.Sig, risk, todayAtr) || TooBig(eng10.Sig, risk, Qty())) return;
			e10d = d; e10px = px; e10sl = sl; eng10Retry = true; Eng10Place();
		}
		private int e10d; private double e10px, e10sl; private bool eng10Retry;
		private void Eng10Place()
		{
			if (!DirectionAllowed(e10d))
			{
				if (!lastDeferred) { eng10Retry = false; if (!PastLevel(e10d, e10px)) { ArmPriceBracket(eng10, e10d, e10sl); ParkSetup(eng10, false, e10px, Qty()); } }
				return;
			}
			eng10Retry = false;
			ArmPriceBracket(eng10, e10d, e10sl);
			if (PastLevel(e10d, e10px))
			{
				if ((Close[0] - e10px) * e10d > 0.5 * Math.Abs(e10px - e10sl)) { Log("ENG10 skipped (price ran > 0.5R past the level)"); return; }
				int eq = OfApply(eng10, Qty(), e10d);
				Order em = eq <= 0 ? null : (e10d == 1 ? EnterLong(fillBip, eq, eng10.Sig) : EnterShort(fillBip, eq, eng10.Sig));
				if (em != null) eng10.Entry = em;
			}
			else { int esq = OfApply(eng10, Qty(), e10d); Order er = esq <= 0 ? null : (e10d == 1 ? EnterLongStopMarket(fillBip, true, esq, e10px, eng10.Sig) : EnterShortStopMarket(fillBip, true, esq, e10px, eng10.Sig)); if (er != null) eng10.Entry = er; }
			Log(string.Format("ENG10 {0} @ {1} | SL {2}", e10d == 1 ? "BUY" : "SELL", Fmt(e10px), Fmt(e10sl)));
		}
		// price already at/through a stop-entry level? historical: bar close; realtime: current ask / bid (a stop there would be rejected)
		// eval-only multiplier of the ~80% win-rate modules (MOM1030, CPI09): research/mine/sniper_uniform.py, sniper_life.py
		private int HwMult(int normal) { return PropMode == NQMasterPropMode.Eval && EvalHighWrMultiplier > 0 ? EvalHighWrMultiplier : normal; }
		// total lots for MOM1030 / CPI09: normal multiplier x base contracts; in Eval at least EvalHighWrMultiplier lots in total (review F5)
		private int HwQty(int normal) { int b = Math.Max(1, normal) * Qty(); return PropMode == NQMasterPropMode.Eval && EvalHighWrMultiplier > 0 ? Math.Max(b, EvalHighWrMultiplier) : b; }
		private bool PastLevel(int d, double px)
		{
			if (State == State.Realtime) { try { return d == 1 ? GetCurrentAsk() >= px : GetCurrentBid() <= px; } catch { } }
			return d == 1 ? Close[0] >= px : Close[0] <= px;
		}

		// ---- six-year modules (2026-10-16) -----------------------------------------------------------------------------
		private void SixEnter(Mod m, int d, double sl, double tgt)
		{
			lastDeferred = false;
			if (m.InTrade || Working(m.Entry) || atrCount < AtrMin) return;
			int q = Qty();
			if (TooBig(m.Sig, Math.Abs(Close[0] - sl), q) || !DirectionAllowed(d)) return;
			ArmPriceBracket(m, d, sl); m.FixTgt = tgt;
			q = OfApply(m, q, d);
			if (q <= 0) return;
			Order o = d == 1 ? EnterLong(fillBip, q, m.Sig) : EnterShort(fillBip, q, m.Sig);
			if (o != null) m.Entry = o;
			Log(string.Format("{0} {1} | SL {2}{3}", m.Sig, d == 1 ? "BUY" : "SELL", Fmt(sl), double.IsNaN(tgt) ? "" : " | TP " + Fmt(tgt)));
		}
		// ENG26: 4H candle 02:00-06:00 body-engulfs 22:00-02:00 with opposite colours -> trade its way at 09:30 (market), stop beyond the
		// 02-06 candle, 0.5R, 400 min (research ENGULF_4H #25: T1 PF 1.57, T2 1.33)
		private void Eng26Entry()
		{
			if (eng26.InTrade || !e26aHas || !e10aHas || double.IsNaN(todayAtr) || todayAtr <= 0) return;
			int s = 0;
			if (e10aC > e10aO && e26aC < e26aO && e10aC >= e26aO && e10aO <= e26aC) s = 1;
			else if (e10aC < e10aO && e26aC > e26aO && e10aC <= e26aO && e10aO >= e26aC) s = -1;
			if (s == 0) return;
			double sl = s == 1 ? e10aL - TickSize : e10aH + TickSize;
			double risk = (Close[0] - sl) * s;
			if (risk <= 0.02 * todayAtr || risk > 0.6 * todayAtr) return;
			SixEnter(eng26, s, sl, double.NaN);
		}
		// ORFAIL: 15-min opening range; a break of >= 0.1 ATR that closes back inside on a 5-minute close within 30 min (before 14:00)
		// -> trade back the other way with the trend, stop beyond the break extreme, target the opposite range side (research OR_FAIL #142)
		private void OrfTrack(int openMin)
		{
			if (orfDone) return;
			if (openMin >= 570 && openMin < 585) { if (!orfHas) { orfH = High[0]; orfL = Low[0]; orfHas = true; } else { orfH = Math.Max(orfH, High[0]); orfL = Math.Min(orfL, Low[0]); } if (openMin == 584) orfReady = true; return; }
			if (!orfReady || openMin < 585) return;
			if (openMin >= 840 || double.IsNaN(todayAtr) || todayAtr <= 0) { orfDone = true; return; }
			double A = todayAtr;
			if (orfBrk == 0)
			{
				if (High[0] > orfH + 0.1 * A) { orfBrk = 1; orfExt = High[0]; orfBi = CurrentBars[0]; }
				else if (Low[0] < orfL - 0.1 * A) { orfBrk = -1; orfExt = Low[0]; orfBi = CurrentBars[0]; }
				if (orfBrk == 0) return;
			}
			else orfExt = orfBrk == 1 ? Math.Max(orfExt, High[0]) : Math.Min(orfExt, Low[0]);
			if (CurrentBars[0] - orfBi > 30) { orfDone = true; return; }
			if ((openMin - 570) % 5 != 4) return;
			if (orfBrk == 1 ? Close[0] >= orfH : Close[0] <= orfL) return;
			orfDone = true;
			int s = -orfBrk;
			if (s != trendDir) return;
			double sl = orfBrk == 1 ? orfExt + TickSize : orfExt - TickSize;
			double risk = (Close[0] - sl) * s, tp = s == -1 ? orfL : orfH;
			if (risk < 0.03 * A || risk > 0.4 * A || (tp - Close[0]) * s <= TickSize) return;
			orfSig = s; orfSl = sl; orfTp = tp;
		}
		// CAM3: Camarilla L3 (uptrend) / H3 (downtrend) untouched from 18:00 to 10:00; between 10:00 and 15:30 a break of the level
		// that closes back within 10 bars -> fade it, stop 0.02 ATR beyond the break extreme, target the RTH VWAP (research PIVOT_FADE #365)
		private void Cam3Track(int openMin)
		{
			if (camDone || double.IsNaN(camLev)) return;
			if (openMin >= 1080 || openMin < 600) { if (camSide == 1 ? Low[0] < camLev : High[0] > camLev) camDone = true; return; }
			if (openMin >= 930) { camDone = true; return; }
			if (camBr < 0) { if (camSide == 1 ? Low[0] < camLev : High[0] > camLev) { camBr = CurrentBars[0]; camExt = camSide == 1 ? Low[0] : High[0]; } else return; }
			camExt = camSide == 1 ? Math.Min(camExt, Low[0]) : Math.Max(camExt, High[0]);
			if (camSide == 1 ? Close[0] > camLev : Close[0] < camLev)
			{
				camDone = true;
				double A = todayAtr, sl = camExt - camSide * 0.02 * A, risk = (Close[0] - sl) * camSide, vw = vwV > 0 ? vwPv / vwV : double.NaN;
				if (risk > 0 && !double.IsNaN(vw) && (vw - Close[0]) * camSide > 0.25 * risk) { camSig = camSide; camSl = sl; camTp = vw; }
				return;
			}
			if (CurrentBars[0] - camBr >= 10) camDone = true;
		}

		private void TimeEntry(Mod m)
		{
			lastDeferred = false;
			if (atrCount < AtrMin || double.IsNaN(atrDaily) || m.InTrade) return;
			if (m.CpiOnly && !cpiToday) return;
			double reference = double.NaN;
			if (m.Lookback == -1) reference = sessOpen;
			else if (m.Lookback == -2) reference = rthOpenPx;
			else if (m.Lookback == -4) { if (double.IsNaN(full1)) return; reference = rthFirstClose; }
			else if (m.Lookback == -5) reference = m.AnchorPx;
			else if (m.Lookback == -3) reference = vwV > 0 ? vwPv / vwV : double.NaN;
			else if (m.Lookback == -6) reference = sVwV > 0 ? sVwPv / sVwV : double.NaN;	// session VWAP since 18:00
			else if (m.Lookback == -7) reference = full1;	// prior complete RTH close
			else if (m.Lookback > 0 && CurrentBars[0] > m.Lookback) reference = Close[m.Lookback - 1];
			if (double.IsNaN(reference) || Close[0] == reference) return;
			int d = Close[0] > reference ? 1 : -1;
			if (m.Reverse) d = -d;
			if (m.Trend && d != trendDir) return;
			if (m.MinDist > 0 && Math.Abs(Close[0] - reference) < m.MinDist * atrDaily) return;
			if (m.RvolMax > 0)
			{
				if (!rvDone || rvHist.Count < 10) return;
				double rs = 0; foreach (double x in rvHist) rs += x;
				if (rs <= 0 || rvAcc / (rs / rvHist.Count) > m.RvolMax) { Log(m.Sig + " skipped: relative volume above " + m.RvolMax.ToString("0.00")); return; }
			}
			if (m.FhCheck)
			{
				if (double.IsNaN(close10) || double.IsNaN(full1)) return;
				double fh = close10 - full1;
				if ((fh > 0 ? 1 : -1) != (Close[0] > reference ? 1 : -1) || Math.Abs(fh) < m.MinDist * atrDaily) return;
			}
			if (CtxOn && m.Sig == "ON07" && FeatPdRet(d) < -0.3619) { Log("ON07 skipped: prior day moved against (context rule)"); return; }
			if (RulesOn && m.Sig == "REV06" && lonDir == d) { onSum += d; Log("REV06 skipped: LON already in the same direction"); return; }
			if (m.Vwap)
			{
				if (vwV <= 0) return;
				double vw = vwPv / vwV;
				int vd = Close[0] > vw ? 1 : (Close[0] < vw ? -1 : 0);
				if (vd != (Close[0] > reference ? 1 : -1)) return;
			}
			// research/mine/wrq_agree.py: MOM1030 / MOM13 alone lose (IS PF < 1); with another module already open the same way
			// MOM1030 PF 1.08/1.13/1.17 -> 1.34/1.46/1.71, MOM13 1.31/1.17/1.19 -> 1.54/1.45/1.51 (Ultra)
			if (MomAgreement && profUltra && (m.Sig == "MOM1030" || m.Sig == "MOM13"))
			{
				bool agree = false;
				foreach (Mod x in mods) if (x != m && x.InTrade && x.Dir == d) { agree = true; break; }
				if (!agree) { Log(m.Sig + " skipped: no other module open the same way"); return; }
			}
			int st = Math.Max(4, (int)Math.Round(m.StopAtr * atrDaily / TickSize));
			if (m.StructStop)
			{
				// GD03: stop beyond the window's extreme (anchor -> signal bar) + 1 tick, capped at StopAtr x ATR (research G_DRIVE stop=1)
				if (!m.WinHas) return;
				double rk = Math.Min((d == 1 ? Close[0] - m.WinL : m.WinH - Close[0]) + TickSize, m.StopAtr * atrDaily);
				if (rk <= 2 * TickSize) return;
				st = Math.Max(1, (int)Math.Round(rk / TickSize));
			}
			int tq = m.Sig == "MOM13" ? LateQty(d, Hm(m.Time)) : Qty();
			// research/mine/size_q.py + wr80_lab.py (2026-10-15): the two ~80% win-rate modules; x4 raised Sharpe and PF in 2010-14 / 2015-19 / 2020-23 / 2024-26
			bool hw = false;
			if (!noBoost && m.Sig == "CPI09" && HwQty(Cpi09Multiplier) > Qty()) { tq = HwQty(Cpi09Multiplier); hw = true; }
			if (!noBoost && m.Sig == "MOM1030" && HwQty(Mom1030Multiplier) > Qty()) { tq = HwQty(Mom1030Multiplier); hw = true; }
			if (m.DoubleDist > 0 && !noBoost && Math.Abs(Close[0] - reference) >= m.DoubleDist * atrDaily) tq = 2 * Qty();
			if (TooBig(m.Sig, st * TickSize, hw ? Qty() : tq)) return;		// MOM1030 / CPI09: 1-lot risk vs the cap, as in research (review F1)
			if (!DirectionAllowed(d)) return;
			SetStopLoss(m.Sig, CalculationMode.Ticks, st, false);
			SetProfitTarget(m.Sig, CalculationMode.Ticks, Math.Max(1, (int)Math.Round(m.R * st)));
			m.Dir = d; m.EntryBar = CurrentBars[0] + 1;
			tq = OfApply(m, tq, d);
			if (tq <= 0) return;
			Order tr = d == 1 ? EnterLong(fillBip, tq, m.Sig) : EnterShort(fillBip, tq, m.Sig);
			if (tr != null) m.Entry = tr;
			Log(string.Format("{0} {1} | ref {2} | SL {3}t", m.Sig, d == 1 ? "BUY" : "SELL", Fmt(reference), st));
		}

		private void CrtEntry()
		{
			lastDeferred = false;
			if (crt.Done || crt.InTrade) return;
			crt.Done = true;
			if (atrCount < AtrMin || double.IsNaN(todayAtr) || todayAtr <= 0) return;
			int d = 0;
			if (c2H > c1H && c2C < c1H && c2C > c1L && c2L >= c1L) d = -1;
			else if (c2L < c1L && c2C > c1L && c2C < c1H && c2H <= c1H) d = 1;
			if (d == 0 || d != trendDir) return;
			double stop = d == 1 ? c2L - TickSize : c2H + TickSize;
			double risk = (Close[0] + d * TickSize - stop) * d;
			if (risk <= 0 || risk > 0.5 * todayAtr) return;
			int cq = CtxBoost(LateQty(d, 720), FeatTrend(d) >= 1.7456 || FeatGap(d) >= 0.1048 || FeatPdRet(d) >= 0.6155, "CRT11");
			if (TooTight(crt.Sig, risk, todayAtr) || TooBig(crt.Sig, risk, cq) || !DirectionAllowed(d)) return;
			ArmPriceBracket(crt, d, stop);
			cq = OfApply(crt, cq, d);
			if (cq <= 0) return;
			Order cr = d == 1 ? EnterLong(fillBip, cq, crt.Sig) : EnterShort(fillBip, cq, crt.Sig);
			if (cr != null) crt.Entry = cr;
			Log(string.Format("CRT11 {0} | SL {1}", d == 1 ? "BUY" : "SELL", Fmt(stop)));
		}

		private void LondonStep(int openMin)
		{
			if (openMin < 180) { if (!rHas) { rH = High[0]; rL = Low[0]; rHas = true; } else { rH = Math.Max(rH, High[0]); rL = Math.Min(rL, Low[0]); } return; }
			if (!rHas || lonStage >= 3 || lon.InTrade) return;
			if (lonStage == 0)
			{
				if (openMin >= 360) { lonStage = 3; return; }
				if (Close[0] > rH || Close[0] < rL)
				{
					int d = Close[0] > rH ? 1 : -1;
					if (atrCount < AtrMin || double.IsNaN(atrDaily) || d != trendDir) { lonStage = 3; return; }
					lon.Dir = d; lonStage = 1;
				}
				else return;
			}
			if (lonStage == 1)
			{
				if (openMin >= 480) { lonStage = 3; return; }
				bool gap = lon.Dir == 1 ? Low[0] > High[2] : High[0] < Low[2];
				if (!gap) return;
				double lim = lon.Dir == 1 ? Low[0] : High[0];
				double stop = lon.Dir == 1 ? rL : rH;
				double risk = (lim - stop) * lon.Dir;
				lonStage = 2;
				if (risk <= 0 || risk > 0.25 * atrDaily) { lonStage = 3; return; }
				if (TooTight(lon.Sig, risk, atrDaily) || TooBig(lon.Sig, risk, Qty())) { lonStage = 3; return; }
				if (!DirectionAllowed(lon.Dir)) { lonStage = 3; ArmPriceBracket(lon, lon.Dir, stop); ParkSetup(lon, true, lim, Qty()); return; }
				ArmPriceBracket(lon, lon.Dir, stop);
				int lq = OfApply(lon, Qty(), lon.Dir);
				if (lq <= 0) { lonStage = 3; return; }
				Order lr = lon.Dir == 1 ? EnterLongLimit(fillBip, true, lq, lim, lon.Sig) : EnterShortLimit(fillBip, true, lq, lim, lon.Sig);
				if (lr != null) lon.Entry = lr;
				Log(string.Format("LON {0} LIMIT @ {1} | SL {2}", lon.Dir == 1 ? "BUY" : "SELL", Fmt(lim), Fmt(stop)));
			}
		}

		private void SetupIctLevels()
		{
			lvl[0] = prevRthHigh; lvl[1] = onHas ? onH : double.NaN; lvl[2] = lonHas ? lonH : double.NaN;
			lvl[3] = prevRthLow; lvl[4] = onHas ? onL : double.NaN; lvl[5] = lonHas ? lonL : double.NaN;
			for (int q = 0; q < 6; q++) taken[q] = double.IsNaN(lvl[q]);
			if (onHas) { if (!taken[0] && onH > lvl[0]) taken[0] = true; if (!taken[3] && onL < lvl[3]) taken[3] = true; }
			if (postHas) { if (!taken[2] && postH > lvl[2]) taken[2] = true; if (!taken[5] && postL < lvl[5]) taken[5] = true; }
			levelsReady = true;
		}

		private void OnFiveMinute()
		{
			if (CurrentBars[1] < 8) return;
			newsBlock5 = NewsBlackout && InNews(ToEt(Times[1][0]), 8);	// a 5-minute entry would still be open at the news window
			// RSI(2) on the 5-minute closes (Wilder, alpha 0.5), updated on every 5m bar
			double chg = Closes[1][0] - Closes[1][1];
			if (double.IsNaN(rsiUp)) { rsiUp = Math.Max(chg, 0); rsiDn = Math.Max(-chg, 0); }
			else { rsiUp = 0.5 * rsiUp + 0.5 * Math.Max(chg, 0); rsiDn = 0.5 * rsiDn + 0.5 * Math.Max(-chg, 0); }
			rsiVal = rsiDn > 0 ? 100 - 100 / (1 + rsiUp / rsiDn) : 50;
			DateTime etClose = ToEt(Times[1][0]);
			DateTime etOpen = etClose.AddMinutes(-5);
			int openMin = etOpen.Hour * 60 + etOpen.Minute;
			int closeMin = etClose.Hour * 60 + etClose.Minute;
			int etDate = etOpen.Year * 10000 + etOpen.Month * 100 + etOpen.Day;
			if (desyncHalt || etDate != rthDay || !CanTrade() || LateBar(Times[1][0])) return;
			if (closeMin >= FlatMin) return;

			// ---- MSEQ (uptrend days, signal bar opening 10:30-15:45)
			if (mseq.On && !mseq.InTrade && !Working(mseq.Entry) && trendDir == 1 && openMin >= 630 && openMin < 945 && atrCount >= AtrMin)
			{
				int n = 5; bool ok = Closes[1][n] < Opens[1][n];
				double mainLow = Lows[1][n];
				for (int j = 0; ok && j < n; j++)
				{
					if (Closes[1][j] <= Opens[1][j] || Lows[1][j] <= mainLow) ok = false;
					if (j < n - 1 && Closes[1][j] <= Closes[1][j + 1]) ok = false;
				}
				double c0m = Closes[1][0]; double stopm = Instrument.MasterInstrument.RoundDownToTickSize(c0m - (c0m - mainLow) * 1.75);
				if (ok && stopm < c0m)
				{
					int mq = CtxBoost(LateQty(1, closeMin), FeatPos(1, Closes[0][0]) >= 0.9686 || FeatM30(1) >= 0.1728 || FeatRet5(1) >= 2.0674, "MSEQ");
					if (TooTight(mseq.Sig, c0m - stopm, todayAtr) || TooBig(mseq.Sig, c0m - stopm, mq)) { }
					else if (!DirectionAllowed(1, 2)) { if (lastDeferred) { pend5 = mseq; pend5Dir = 1; pend5Stop = stopm; pend5Qty = mq; pend5Bar = CurrentBars[0]; } }
					else { ArmPriceBracket(mseq, 1, stopm); int mq2 = OfApply(mseq, mq, 1); Order mo = mq2 <= 0 ? null : EnterLong(fillBip, mq2, mseq.Sig); if (mo != null) mseq.Entry = mo; Log("MSEQ BUY | SL " + Fmt(stopm)); }
				}
			}

			// ---- MSEQS: mirrored momentum sequence (bullish main candle + 5 falling bearish candles below its high), only on days
			// where ORB60 has already entered SHORT (pullback down-trend day), 5m bar opening at/after that entry, 10:30-15:45
			if (mseqs.On && !mseqs.InTrade && !Working(mseqs.Entry) && orbFirstDir == -1 && openMin >= orbFirstMin && openMin >= 630 && openMin < 945)
			{
				int n = 5; bool ok = Closes[1][n] > Opens[1][n];
				double mainHigh = Highs[1][n];
				for (int j = 0; ok && j < n; j++)
				{
					if (Closes[1][j] >= Opens[1][j] || Highs[1][j] >= mainHigh) ok = false;
					if (j < n - 1 && Closes[1][j] >= Closes[1][j + 1]) ok = false;
				}
				double c0s = Closes[1][0]; double stops = Instrument.MasterInstrument.RoundToTickSize(c0s + (mainHigh - c0s) * 1.75);
				if (ok && stops > c0s)
				{
					int sq = LateQty(-1, closeMin);
					if (TooTight(mseqs.Sig, stops - c0s, todayAtr) || TooBig(mseqs.Sig, stops - c0s, sq)) { }
					else if (!DirectionAllowed(-1, 2)) { if (lastDeferred) { pend5 = mseqs; pend5Dir = -1; pend5Stop = stops; pend5Qty = sq; pend5Bar = CurrentBars[0]; } }
					else { ArmPriceBracket(mseqs, -1, stops); int sq2 = OfApply(mseqs, sq, -1); Order so = sq2 <= 0 ? null : EnterShort(fillBip, sq2, mseqs.Sig); if (so != null) mseqs.Entry = so; Log("MSEQS SELL | SL " + Fmt(stops)); }
				}
			}

			// ---- RSI2 pullback: RSI(2) < 10 (> 90) with the daily trend and the intraday trend (price vs RTH open and VWAP agree)
			if (rsi.On && !rsi.InTrade && !Working(rsi.Entry) && rsiTrades < 3 && closeMin >= 630 && closeMin < 945 && atrCount >= AtrMin && trendDir != 0
				&& !double.IsNaN(rthOpenPx) && vwV > 0 && !double.IsNaN(todayAtr) && todayAtr > 0)
			{
				double c0 = Closes[1][0], vw = vwPv / vwV;
				int it = (c0 > rthOpenPx && c0 > vw) ? 1 : ((c0 < rthOpenPx && c0 < vw) ? -1 : 0);
				int d = 0;
				if (rsiVal < 10 && trendDir == 1 && it == 1) d = 1;
				else if (rsiVal > 90 && trendDir == -1 && it == -1) d = -1;
				int rst = Math.Max(4, (int)Math.Round(rsi.StopAtr * todayAtr / TickSize));
				if (d != 0 && !TooBig(rsi.Sig, rst * TickSize, Qty()) && DirectionAllowed(d))
				{
					int st = rst;
					SetStopLoss(rsi.Sig, CalculationMode.Ticks, st, false);
					SetProfitTarget(rsi.Sig, CalculationMode.Ticks, Math.Max(1, (int)Math.Round(rsi.R * st)));
					rsi.Dir = d; rsiTrades++;
					int rq = OfApply(rsi, Qty(), d);
					Order rr = rq <= 0 ? null : (d == 1 ? EnterLong(fillBip, rq, rsi.Sig) : EnterShort(fillBip, rq, rsi.Sig));
					if (rr != null) rsi.Entry = rr;
					Log(string.Format("RSI2 {0} | RSI {1:0.0} | SL {2}t", d == 1 ? "BUY" : "SELL", rsiVal, st));
				}
			}

			// ---- ICT open (09:30-10:30 bar open)
			if (!ict.On || !levelsReady) return;
			if (Working(ict.Entry))
			{
				bool invalid = (ict.Dir == -1 && Highs[1][0] > ictExtPend) || (ict.Dir == 1 && Lows[1][0] < ictExtPend);
				if (CurrentBars[1] >= ictExpiry || invalid) CancelEntry(ict);
			}
			bool inWin = openMin >= 570 && openMin < 630;
			for (int q = 0; q < 6; q++)
			{
				if (taken[q]) continue;
				bool hit = q < 3 ? Highs[1][0] > lvl[q] : Lows[1][0] < lvl[q];
				if (!hit) continue;
				taken[q] = true;
				if (!inWin) continue;
				int s = q < 3 ? 0 : 1;
				if (s == 0 && (!ictAct[0] || Highs[1][0] > ictExt[0])) { ictAct[0] = true; ictExt[0] = Highs[1][0]; ictExtBar[0] = CurrentBars[1]; }
				if (s == 1 && (!ictAct[1] || Lows[1][0] < ictExt[1])) { ictAct[1] = true; ictExt[1] = Lows[1][0]; ictExtBar[1] = CurrentBars[1]; }
			}
			if (!inWin) { ictAct[0] = ictAct[1] = false; return; }
			for (int s = 0; s < 2; s++)
			{
				if (!ictAct[s]) continue;
				if (s == 0 && Highs[1][0] > ictExt[0]) { ictExt[0] = Highs[1][0]; ictExtBar[0] = CurrentBars[1]; }
				if (s == 1 && Lows[1][0] < ictExt[1]) { ictExt[1] = Lows[1][0]; ictExtBar[1] = CurrentBars[1]; }
				if (CurrentBars[1] - ictExtBar[s] > 4) { ictAct[s] = false; continue; }
				if (CurrentBars[1] == ictExtBar[s]) continue;
				int j = CurrentBars[1] - ictExtBar[s];
				if (s == 0) { if (Closes[1][j] <= Opens[1][j]) j++; while (j + 1 <= CurrentBars[1] && Closes[1][j] > Opens[1][j] && Closes[1][j + 1] > Opens[1][j + 1]) j++; }
				else { if (Closes[1][j] >= Opens[1][j]) j++; while (j + 1 <= CurrentBars[1] && Closes[1][j] < Opens[1][j] && Closes[1][j + 1] < Opens[1][j + 1]) j++; }
				double cisd = Opens[1][j];
				bool trig = s == 0 ? Closes[1][0] < cisd : Closes[1][0] > cisd;
				if (!trig) continue;
				ictAct[s] = false;
				int d = s == 0 ? -1 : 1;
				if (ict.InTrade || Working(ict.Entry) || ict.Parked || ictTrades >= 3 || d != trendDir || atrCount < AtrMin) continue;
				double stop = d == -1 ? ictExt[s] + TickSize : ictExt[s] - TickSize;
				double lim = Instrument.MasterInstrument.RoundToTickSize(cisd);
				if ((d == -1 && lim <= Closes[1][0]) || (d == 1 && lim >= Closes[1][0])) continue;
				double risk = (stop - lim) * (-d);
				if (risk <= 0 || risk > 0.25 * todayAtr) continue;
				int iq = Qty() * (noBoost ? 1 : IctMultiplier);
				if (TooTight(ict.Sig, risk, todayAtr) || TooBig(ict.Sig, risk, iq)) continue;
				if (!DirectionAllowed(d))
				{
					if (lastDeferred) ictAct[s] = true;
					else { ict.Dir = d; ictExtPend = ictExt[s]; ictExpiry = CurrentBars[1] + 20; ArmPriceBracket(ict, d, stop); ParkSetup(ict, true, lim, iq); }
					continue;
				}
				ict.Dir = d; ictExtPend = ictExt[s]; ictExpiry = CurrentBars[1] + 20;
				ArmPriceBracket(ict, d, stop);
				int iqo = OfApply(ict, iq, d);
				Order ir = iqo <= 0 ? null : (d == 1 ? EnterLongLimit(fillBip, true, iqo, lim, ict.Sig) : EnterShortLimit(fillBip, true, iqo, lim, ict.Sig));
				if (ir != null) ict.Entry = ir;
				Log(string.Format("ICT {0} LIMIT @ {1} | SL {2}", d == 1 ? "BUY" : "SELL", Fmt(lim), Fmt(stop)));
			}
		}

		private void ArmPriceBracket(Mod m, int d, double stop)
		{
			m.Dir = d; m.StopPx = stop;
			SetStopLoss(m.Sig, CalculationMode.Price, stop, false);
			SetProfitTarget(m.Sig, CalculationMode.Ticks, 4000);	// replaced on fill
		}
		#endregion

		#region Account layer and helpers
		// ---- position size: fixed Contracts, or adaptive (SizeHigh while the strategy's closed-trade drawdown from its
		// peak is below SizeDownDrawdown, SizeLow otherwise). Research (Apex 50K, real MNQ): 2 -> 1 when DD > $800 gives
		// pass-in-30-days 29% with 5% bust vs fixed 2: 33% pass / 21% bust.
		private double eqPeak;
		// ---- daily loss limit (funded-account mode): once the session's realized P&L of this strategy reaches -DailyLossLimit,
		// flatten and stop for the rest of the session (research/mine/apex50_stats.py: Apex 50K PA busts 42/12/33% -> 29/8/20% with $400).
		private double dayStartPnl; private bool dayStopped;
		private void DailyLossCheck()
		{
			if (DailyLossLimit <= 0 || dayStopped) return;
			if (netPnl - dayStartPnl <= -DailyLossLimit) { dayStopped = true; FlattenAll("daily loss limit"); Log("DAILY LOSS LIMIT reached - no more trades this session"); }
		}
		// ---- evaluation mode (research/mine/evalpol.py): Contracts per module (2 recommended); if on the EvalLateDay-th session
		// (0-based, counted from EvalStartDate) the evaluation profit is still below EvalLateGoal, trade EvalLateContracts until the end.
		// Apex 50K, Ultra: pass within 30 days 39% (3 fixed) -> 50% (2 -> 3 at day 12 if < $2,000, daily loss limit $800).
		private int evalDayIndex = -1; private double evalEqDayStart, evalPnlBase = double.NaN;
		private double EvalEquity()
		{
			if (State == State.Realtime) return AcctCash() - StartBalance;
			return double.IsNaN(evalPnlBase) ? 0 : netPnl - evalPnlBase;
		}
		private void EvalSessionStart(DateTime tradeDay)
		{
			if (!EvalMode) return;
			DateTime st;
			if (!DateTime.TryParseExact(EvalStartDate ?? "", "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out st) || tradeDay < st) return;
			if (double.IsNaN(evalPnlBase)) evalPnlBase = netPnl;
			evalDayIndex++; evalEqDayStart = EvalEquity();
			if (evalDayIndex == EvalLateDay && evalEqDayStart < EvalLateGoal) Log(string.Format("EVAL: day {0}, profit {1:0} < {2:0} -> {3} contracts", evalDayIndex, evalEqDayStart, EvalLateGoal, EvalLateContracts));
		}
		// ---- funded step-up (research/mine/final3y_acct.py, MyFundedFutures Rapid EOD 50K, Ultra + gold Robust, REAL 2024-26): 1 contract
		// until the cushion over the EOD-trailing threshold (day start) is >= FundedStepUpCushion ($3,000 = balance >= start + $3,100 once
		// the threshold has locked at start + $100), then FundedStepUpContracts (2); back to Contracts below. Withdraw down to start + $6,100.
		// $ per account per month (history / +1 tick / resampled): 3,888 / 3,592 / 3,336 vs 2,137 / 1,984 / 2,012 at 1 contract.
		private bool StepUpOn { get { return PropMode == NQMasterPropMode.Funded && FundedStepUpCushion > 0 && !double.IsNaN(propCushion) && propCushion >= FundedStepUpCushion; } }
		// ---- size ladder (research/mine/ladder_plan.py, 2026-10-17, Federico: '$200 per day per account'): above the step-up cushion every further
		// FundedLadderStep of day-start cushion adds one contract per module, up to FundedLadderMax; withdraw only above FundedPayoutAt so the
		// cushion that carries the ladder stays in the account. MFFU 50K, Ultra + six-year modules + gold Robust, step-up 3,000 / step 3,000 / max 4,
		// payout at 11,600 (keep 11,100): $/day per account 119 / 189 (bootstrap median 2020-23 / 2024-26; 1 contract: 45 / 68), P(>= $200/day)
		// 19 / 46%, busts 0.27 / 0.69 per year; with 35% less edge 29 / 42 (1 contract 18 / 28) and P(negative year) 35 / 28% (20 / 14%).
		// The ladder amplifies whatever the edge is: more income if it holds, more negative years if it fades. Opt-in (FundedLadderStep 0 = off).
		private int LadderQty()
		{
			if (FundedLadderStep <= 0) return FundedStepUpContracts;
			int k = FundedStepUpContracts + (int)Math.Floor((propCushion - FundedStepUpCushion) / FundedLadderStep);
			return Math.Min(FundedLadderMax, Math.Max(FundedStepUpContracts, k));
		}
		private int Qty()
		{
			if (EvalMode) return (evalDayIndex >= EvalLateDay && evalEqDayStart < EvalLateGoal
				&& (EvalLateMinCushion <= 0 || double.IsNaN(propCushion) || propCushion >= EvalLateMinCushion)) ? EvalLateContracts : Contracts;
			if (StepUpOn) return LadderQty();
			if (!AdaptiveSize) return Contracts;
			return (eqPeak - netPnl) > SizeDownDrawdown ? SizeLow : SizeHigh;
		}

		// ---- confluence rules (research/improve2.py, chosen on CFD 2020-23, held every year 2020-26 and on real MNQ):
		// A) late modules (CRT11, MOM13, MSEQ, MSEQS entering after 11:00) trade 2x size when they go AGAINST today's MOM11 trade
		//    and WITH the overnight modules (sign of ON07+REV06+LON directions): PF 2.06 / 1.81 / 1.63 vs 1.38 / 1.16 / 1.22.
		// B) REV06 is skipped when LON already entered the same direction today: PF 0.83 / 0.92 / 1.12 vs 1.37 / 1.29 / 1.20.
		private bool RulesOn { get { return UseConfluence; } }

		// ---- context rules (2026-10-02; research/mine/filt_mine.py + filt_holdout.py): thresholds chosen on CFD 2020-23 (tertiles/quintiles),
		// kept only if they also held in 2024-25 on CFD AND real MNQ; 2026 was a clean holdout (PF 1.50 -> 1.58 real, 1.42 -> 1.49 CFD).
		// Boosts double the size (never above 2x the base size), the ON07 rule skips the trade. Features are in daily-ATR units,
		// oriented with the trade direction d.
		private double sessHi, sessLo, atrRatio = double.NaN;
		private List<double> atrHist;
		private bool CtxOn { get { return UseContextRules; } }
		private int CtxBoost(int q, bool cond, string who)
		{
			if (!CtxOn || !cond || noBoost) return q;
			int cap = 2 * Qty();
			if (q >= cap) return q;
			Log(who + " context x2"); return cap;
		}
		// warm-up (property WarmupDays; 15 = validated): RTH days of ATR history and closes needed before the modules trade
		private int AtrMin { get { return Math.Min(14, Math.Max(1, WarmupDays)); } }
		private int TrendMin { get { return Math.Min(15, Math.Max(2, WarmupDays)); } }
		private double LastClose(int back) { int n = rthCloses.Count; return n > back ? rthCloses[n - 1 - back] : double.NaN; }
		private double FeatTrend(int d)
		{
			if (rthCloses.Count < TrendMin || double.IsNaN(todayAtr) || todayAtr <= 0) return double.NaN;
			double sm = 0; foreach (double x in rthCloses) sm += x; sm /= rthCloses.Count;
			return (LastClose(0) - sm) * d / todayAtr;
		}
		private double FeatGap(int d) { return (double.IsNaN(rthOpenPx) || todayAtr <= 0) ? double.NaN : (rthOpenPx - LastClose(0)) * d / todayAtr; }
		private double FeatPdRet(int d) { return (double.IsNaN(full1) || double.IsNaN(full2) || todayAtr <= 0) ? double.NaN : (full1 - full2) * d / todayAtr; }
		private double FeatRet5(int d) { return todayAtr > 0 ? (LastClose(0) - LastClose(5)) * d / todayAtr : double.NaN; }
		private double FeatPos(int d, double px) { return sessHi > sessLo ? (d == 1 ? (px - sessLo) : (sessHi - px)) / (sessHi - sessLo) : double.NaN; }
		private double FeatM30(int d) { return (CurrentBars[0] > 31 && todayAtr > 0) ? (Closes[0][0] - Closes[0][30]) * d / todayAtr : double.NaN; }
		private double FeatVw(int d, double px) { return (vwV > 0 && todayAtr > 0) ? (px - vwPv / vwV) * d / todayAtr : double.NaN; }
		private double FeatOpen(int d, double px) { return (double.IsNaN(rthOpenPx) || todayAtr <= 0) ? double.NaN : (px - rthOpenPx) * d / todayAtr; }
		// ---- trade-level risk rules (2026-10-12; research/mine/robust2_*.py, cand16*.py, real Databento NQ futures 2010-2026)
		// MinStopAtr: structure modules (ORB, VOLB, MSEQ, MSEQS, CRT11, ICT, LON, ENG10) skip a trade whose stop is closer than this many
		// daily ATRs: inside the day's noise (WR +0.4 to +0.8 points in 2010-14, 2015-19, 2020-23 and 2024-26, PF +0.01, $ unchanged).
		// Risk cap: in PropMode Eval / Funded, while the cushion over the liquidation threshold at the session start is below
		// EvalRiskCapCushion / FundedRiskCapCushion, a trade whose stop risks more than RiskCapPerContract $ per base contract is skipped.
		// The big-risk trades are the best ones on average, but a few of them can wipe a small cushion. MyFundedFutures 50K, 1 contract,
		// 1,000 resampled years per period: accounts lost per year per slot 0.56 -> 0.45 (2020-23), 1.65 -> 0.89 (2024-26), income -6%.
		private int riskSkips;
		private bool TooTight(string who, double stopPts, double atr)
		{
			if (MinStopAtr <= 0 || double.IsNaN(atr) || atr <= 0 || stopPts >= MinStopAtr * atr) return false;
			Log(string.Format("{0} skipped: stop {1:0.00} pts is inside the day's noise (< {2:0.00} x ATR {3:0.0})", who, stopPts, MinStopAtr, atr)); return true;
		}
		private bool RiskCapActive { get { return PropMode != NQMasterPropMode.Off && RiskCapPerContract > 0 && !double.IsNaN(propCushion)
			&& propCushion < (PropMode == NQMasterPropMode.Eval ? EvalRiskCapCushion : FundedRiskCapCushion); } }
		private bool TooBig(string who, double stopPts, int qty)
		{
			if (!RiskCapActive || qty <= 0) return false;
			double perBase = stopPts * Instrument.MasterInstrument.PointValue * qty / Math.Max(1, Qty());
			if (perBase <= RiskCapPerContract) return false;
			riskSkips++;
			Log(string.Format("{0} skipped by the risk cap: ${1:0} per base contract > ${2:0} while the cushion is ${3:0}", who, perBase, RiskCapPerContract, propCushion)); return true;
		}
		private int LateQty(int d, int entryMin)
		{
			int q = Qty();
			if (RulesOn && !noBoost && m11Dir == -d && onSum * d > 0 && entryMin > 660) { q *= 2; Log("confluence x2 (against MOM11, with overnight)"); }
			return q;
		}


		// ---- edge monitor (research/mine/robust_monitor.py). Live trading is the final out-of-sample test: this one-sided CUSUM
		// watches the daily P&L per base contract, normalised by the daily ATR (z = day $ / contracts / (2 x ATR points)):
		//   S = max(0, S + k - z); alarm when S > h.  k = half the backtested mean, h calibrated on 2020-26 block bootstrap so that
		// false alarms are rare (Ultra: 1.5%/year, 7% in 3 years) and no alarm fires anywhere in the 2020-26 history.
		// If the edge disappears (mean -> 0) the alarm fires after ~7 months (median), if it turns negative (-50%) after ~4 months.
		// Days that cannot trade (FOMC, low ATR, sessions without RTH) are not counted. Counting starts at EdgeMonitorStart.
		private double edgeS, edgeK = double.NaN, edgeH = double.NaN, edgeHw; private bool edgeWarned; private int edgeDays, edgeDayQty = 1; private bool edgeAlarm, edgePaused, edgeDayRth, edgeDayTradable;
		private DateTime edgeDayDate = DateTime.MinValue;
		// Edge-alarm fallback (research/mine/os_adapt.py): modules that failed the walk-forward review (cost-normalised PF <= 1.05 over the
		// previous 5 years, robust16.py rule) as of January of each year. Update yearly from research (or set EdgeFallbackOff).
		private int edgeFbLeft; private List<string> edgeFbOff;
		private List<string> FallbackList(int year)
		{
			string s = EdgeFallbackOff;
			if (string.IsNullOrEmpty(s))
			{
				if (year <= 2020) s = "LF0430 LF06 MOM11 MOM13 ON07 ORB60 ORB90 REV06 VW13";
				else if (year == 2021) s = "LF0430 LF06 MOM11 MOM13 ON07 VW13";
				else if (year == 2022) s = "LF0430 LF06 ON07 VW13";
				else if (year == 2023) s = "LF06 ON07";
				else if (year == 2024) s = "LF06 VW13";
				else if (year <= 2026) s = "";
				else { s = "REV06"; if (year > 2027) Print("NQMaster | fallback table ends in 2027: re-run research/mine/robust16.py and update FallbackList (using the 2027 list)."); }
			}
			List<string> r = new List<string>();
			foreach (string x in s.Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries)) r.Add(x.Trim().ToUpperInvariant());
			return r;
		}
		private bool FallbackOff(string sig) { return edgeFbLeft > 0 && edgeFbOff != null && edgeFbOff.Contains(sig.ToUpperInvariant()); }
		// ---- inactivity alarm (research/mine/inactivity_thresholds.json, 2026-10-16): 1.5 x the longest gap between entries in 2020-26,
		// counted in tradable days (RTH day, not FOMC, ATR >= MinAtrPoints). Alert only.
		private int tradDays, lastLongDay = -1, lastShortDay = -1; private bool longWarned, shortWarned;
		private int InactLimit(string sig)
		{
			if (Profile != NQMasterProfile.Ultra && Profile != NQMasterProfile.UltraQ) return 0;	// thresholds measured on Ultra
			switch (sig)
			{
				case "VOLB": case "MOM11": return 10;
				case "ON07": return 36; case "MOM13": return 38; case "REV06": return 39; case "ORB90": return 41; case "LON": return 42;
				case "ORB60": return 45; case "LATE15": case "MOM1030": return 47; case "CRT11": return 74; case "LF0430": return 75;
				case "VW13": return 105; case "LF06": case "MSEQ": return 116; case "NF05": return 119; case "ICT": return 122; case "CPI09": return 129;
				case "MSEQS": return 233;
				case "LATEFH": return 26; case "ORFAIL": return 60; case "ENG26": return 69; case "GD03": return 72; case "SO04": return 93;
				case "CA04V": return 105; case "RV11": return 107; case "CAM3": return 117;
				default: return 0;
			}
		}
		private void InactivityDayClose()
		{
			bool tradable = edgeDayRth && edgeDayTradable && edgeDayDate != DateTime.MinValue && !double.IsNaN(todayAtr) && todayAtr > 0
				&& !(MinAtrPoints > 0 && todayAtr < MinAtrPoints) && atrCount >= AtrMin && rthDaysSeen >= WarmupDays;
			if (!tradable || !InactivityAlarm || mods == null) return;
			tradDays++;
			if (lastLongDay < 0) lastLongDay = tradDays; if (lastShortDay < 0) lastShortDay = tradDays;
			int dirLimit = (Profile == NQMasterProfile.Ultra || Profile == NQMasterProfile.UltraQ) ? 12 : 20;
			string dd = edgeDayDate.ToString("yyyy-MM-dd");
			foreach (Mod m in mods)
			{
				if (!m.On || m.LastFillDay < 0) { m.LastFillDay = tradDays; m.InactWarned = false; continue; }	// switched off by profile / gating / fallback: clock restarts
				int lim = InactLimit(m.Sig);
				if (lim > 0 && !m.InactWarned && tradDays - m.LastFillDay > lim)
				{
					m.InactWarned = true;
					string msg = string.Format("NQMaster | INACTIVITY {0}: {1} has not entered for {2} tradable days (normal maximum {3}). Check the Output for 'STALE ORDER' / rejections, the module switches and the data feed.", dd, m.Sig, tradDays - m.LastFillDay, lim * 2 / 3);
					Print(msg); Warn("nqm_inact_" + m.Sig, msg);
				}
			}
			if (!shortWarned && tradDays - lastShortDay > dirLimit) { shortWarned = true; string s = string.Format("NQMaster | INACTIVITY {0}: no SHORT entry for {1} tradable days (2020-26 maximum 8). A stuck order can block one direction: check 'STALE ORDER' lines and Working orders.", dd, tradDays - lastShortDay); Print(s); Warn("nqm_inact_short", s); }
			if (!longWarned && tradDays - lastLongDay > dirLimit) { longWarned = true; string s = string.Format("NQMaster | INACTIVITY {0}: no LONG entry for {1} tradable days (2020-26 maximum 8). A stuck order can block one direction: check 'STALE ORDER' lines and Working orders.", dd, tradDays - lastLongDay); Print(s); Warn("nqm_inact_long", s); }
		}
		private void InactivityFill(Mod m)
		{
			m.LastFillDay = tradDays; m.InactWarned = false;
			if (m.Dir == 1) { lastLongDay = tradDays; longWarned = false; } else if (m.Dir == -1) { lastShortDay = tradDays; shortWarned = false; }
		}

		// ---- cross-account guard (2026-10-16; round 5 C6 2026-10-21): Lucid and MFFU ban opposite positions across your own accounts. Each NQMaster
		// instance writes Documents\NinjaTrader 8\nqmaster_positions\<group>_<account>_NQ.txt = "pos;L;S;utcTicks" (pos = -1/0/1 open position,
		// L / S = 1 when a long / short position OR a working long / short entry order exists) every minute, when an entry order is placed,
		// changes state or fills. Files older than 3 minutes are ignored. Same PC only; one HedgeGroup per firm (the presets fill it).
		//  (2) a new entry of direction d is skipped while another account of the group holds the opposite flag (position or working entry).
		//      A working opposite entry of the other account is ignored only when this account holds a working entry on that same side itself:
		//      it is then the mirror of our own order, which the same signal parks here (DirectionAllowed) and in the other account.
		//  (3) every bar, own working entries opposite to another account's OPEN position are cancelled.
		//  (4) an own entry that fills while another account holds the opposite position is flattened at once (+ Alert + log).
		private int otherDirBar = -1; private bool otherLong, otherShort, otherPosLong, otherPosShort, hedgeFlat;
		private string PosDir { get { try { return Path.Combine(Core.Globals.UserDataDir, "nqmaster_positions"); } catch { return null; } } }
		private string PosFile { get { string d = PosDir; return d == null ? null : Path.Combine(d, (HedgeGroup ?? "") + "_" + (Account != null ? Account.Name : "acct") + "_NQ.txt"); } }
		private void CrossAccountPublish()
		{
			if (!CrossAccountGuard || State != State.Realtime || mods == null) return;
			try
			{
				Directory.CreateDirectory(PosDir);
				int pos = Position.MarketPosition == MarketPosition.Long ? 1 : (Position.MarketPosition == MarketPosition.Short ? -1 : 0);
				foreach (Mod m in mods) if (pos == 0 && m.InTrade && m.Dir != 0) pos = m.Dir;	// fill not yet in Position
				bool l = pos == 1, sh = pos == -1;
				foreach (Mod m in mods)
				{
					if (m.InTrade) { if (m.Dir == 1) l = true; else if (m.Dir == -1) sh = true; }
					if (Working(m.Entry) && !zombies.Contains(m.Entry)) { if (m.Dir == 1) l = true; else if (m.Dir == -1) sh = true; }
				}
				foreach (Order z in rtZombies) if (Working(z)) { if (z.OrderAction == OrderAction.Buy) l = true; else sh = true; }
				string txt = pos.ToString(CultureInfo.InvariantCulture) + ";" + (l ? "1" : "0") + ";" + (sh ? "1" : "0") + ";" + DateTime.UtcNow.Ticks.ToString(CultureInfo.InvariantCulture);
				string f = PosFile, tmp = f.Substring(0, f.Length - 4) + ".tmp";
				try { File.WriteAllText(tmp, txt); if (File.Exists(f)) File.Replace(tmp, f, null); else File.Move(tmp, f); }
				catch { File.WriteAllText(f, txt); }
			}
			catch { }
		}
		private void CrossAccountRead()
		{
			otherLong = otherShort = otherPosLong = otherPosShort = false; otherDirBar = CurrentBars[0];
			if (!CrossAccountGuard || State != State.Realtime) return;
			string[] files;
			try { if (!Directory.Exists(PosDir)) return; files = Directory.GetFiles(PosDir, "*_NQ.txt"); } catch { return; }
			string mine = PosFile; string pre = (HedgeGroup ?? "") + "_";
			foreach (string f in files)
			{
				try
				{
					if (string.Equals(f, mine, StringComparison.OrdinalIgnoreCase) || !Path.GetFileName(f).StartsWith(pre, StringComparison.OrdinalIgnoreCase)) continue;
					string[] p = File.ReadAllText(f).Split(';');
					int pos, l, sh; long t;
					if (p.Length >= 4)
					{
						if (!int.TryParse(p[0], NumberStyles.Integer, CultureInfo.InvariantCulture, out pos) || !int.TryParse(p[1], NumberStyles.Integer, CultureInfo.InvariantCulture, out l)
							|| !int.TryParse(p[2], NumberStyles.Integer, CultureInfo.InvariantCulture, out sh) || !long.TryParse(p[3], NumberStyles.Integer, CultureInfo.InvariantCulture, out t)) continue;
					}
					else if (p.Length == 2)		// file of an older NQMaster: direction;ticks
					{
						if (!int.TryParse(p[0], NumberStyles.Integer, CultureInfo.InvariantCulture, out pos) || !long.TryParse(p[1], NumberStyles.Integer, CultureInfo.InvariantCulture, out t)) continue;
						l = pos == 1 ? 1 : 0; sh = pos == -1 ? 1 : 0;
					}
					else continue;
					if ((DateTime.UtcNow - new DateTime(t, DateTimeKind.Utc)).TotalMinutes > 3) continue;
					if (l == 1) otherLong = true;
					if (sh == 1) otherShort = true;
					if (pos == 1) otherPosLong = true; else if (pos == -1) otherPosShort = true;
				}
				catch { }
			}
		}
		// (2): fresh read at every check (a few small files, realtime only)
		private bool OtherOpp(int d, bool log)
		{
			if (!CrossAccountGuard || State != State.Realtime) return false;
			CrossAccountRead();
			bool posOpp = (d == 1 && otherPosShort) || (d == -1 && otherPosLong);
			bool opp = posOpp || (d == 1 && otherShort) || (d == -1 && otherLong);
			if (opp && !posOpp) foreach (Mod m in mods) if (Working(m.Entry) && !zombies.Contains(m.Entry) && m.Dir == -d) { opp = false; break; }	// mirror of our own working entry
			if (opp && log) { status = "another account holds the opposite NQ position / entry (cross-account guard)"; Log(string.Format("entry skipped: another account of group '{0}' holds an opposite NQ {1} (hedging ban)", HedgeGroup, posOpp ? "position" : "working entry")); }
			return opp;
		}
		private bool OtherAccountOpposite(int d) { return OtherOpp(d, true); }
		// (3): own working entries opposite to another account's open position are cancelled (existing CancelEntry path)
		private void CrossAccountCancelOpp()
		{
			if (!CrossAccountGuard || State != State.Realtime || mods == null) return;
			CrossAccountRead();
			if (!otherPosLong && !otherPosShort) return;
			foreach (Mod m in mods)
			{
				if (!Working(m.Entry) || zombies.Contains(m.Entry)) continue;
				if ((m.Dir == 1 && otherPosShort) || (m.Dir == -1 && otherPosLong))
				{
					bool first = m.CancelOrd != m.Entry;
					m.Parked = false; CancelEntry(m);
					if (first) Log(string.Format("{0} entry cancelled: another account of group '{1}' holds the opposite NQ position (hedging ban)", m.Sig, HedgeGroup));
				}
			}
		}
		// (4): called on an own entry fill
		private void CrossAccountOnFill(Mod m)
		{
			if (!CrossAccountGuard || State != State.Realtime) return;
			CrossAccountRead();
			if (!((m.Dir == 1 && otherPosShort) || (m.Dir == -1 && otherPosLong))) return;
			string msg = string.Format("NQMaster | HEDGE GUARD: {0} filled {1} on {2} while another account of group '{3}' holds the opposite NQ position -> flattened at once", m.Sig, m.Dir == 1 ? "LONG" : "SHORT", Account != null ? Account.Name : "?", HedgeGroup);
			Warn("nqm_hedge", msg); Log(msg);
			hedgeFlat = true;
			if (!desyncHalt)
			{
				int q = Math.Max(1, m.OpenQty);
				if (m.Dir == 1) ExitLong(fillBip, q, m.Sig + "X", m.Sig); else ExitShort(fillBip, q, m.Sig + "X", m.Sig);
			}
		}

		private void EdgeParams()
		{
			double k, h;
			switch (Profile)
			{
				// research/mine/monitor_recal2.py (2026-10-16): recalibrated for MOM1030 / CPI09 x4 and CPI09; hw = warning level (alert only)
				case NQMasterProfile.WR70Plus: k = 0.0634; h = 12.07; edgeHw = 6.86; break;
				case NQMasterProfile.Durable: k = 0.0455; h = 10.35; edgeHw = 6.98; break;
				case NQMasterProfile.UltraQ: k = 0.0773; h = 26.08; edgeHw = 9.04; break;
				default:																// Ultra (Custom uses the Ultra calibration)
					if (Profile == NQMasterProfile.Ultra && SixYearModules && UseSo04 && UseRv11 && UseOrFail && UseCam3 && !UseCa04v && !UseGd03 && !UseEng26)
					{ k = 0.0899; h = 26.93; edgeHw = 9.22; }						// research/mine/monitor_recal3.py: Ultra + durable four (2027 default)
					else { k = 0.0850; h = 24.44; edgeHw = 9.12; }
					break;
			}
			edgeK = EdgeK > 0 ? EdgeK : k; edgeH = EdgeH > 0 ? EdgeH : h;
			if (EdgeK > 0 || EdgeH > 0) edgeHw = edgeH * 0.37;					// manual k / h: warning at the same relative level
		}
		// review F3: edge-monitor state survives restarts (saved in realtime, restored at the switch to realtime if newer than the history rebuild)
		private int edgeLastDate, firstBarDate;
		private int DateKey(DateTime d) { return d.Year * 10000 + d.Month * 100 + d.Day; }
		private string EdgeFile { get { try { return Path.Combine(Core.Globals.UserDataDir, "nqmaster_edge_" + (Account != null ? Account.Name : "acct") + ".txt"); } catch { return null; } } }
		private void EdgeSave()
		{
			if (State != State.Realtime || !EdgeMonitor || EdgeFile == null) return;
			try
			{
				File.WriteAllText(EdgeFile, string.Join(";", new string[] { Profile.ToString(), edgeLastDate.ToString(CultureInfo.InvariantCulture), edgeS.ToString("R", CultureInfo.InvariantCulture),
					edgeDays.ToString(CultureInfo.InvariantCulture), edgeAlarm ? "1" : "0", edgeFbLeft.ToString(CultureInfo.InvariantCulture),
					edgeFbOff == null ? "" : string.Join(" ", edgeFbOff.ToArray()), edgeWarned ? "1" : "0", EdgeMonitorStart ?? "" }));
			}
			catch { }
		}
		private void EdgeRestore()
		{
			if (!EdgeMonitor || EdgeFile == null) return;
			try
			{
				if (!File.Exists(EdgeFile))
				{
					DateTime st;
					if (DateTime.TryParseExact(EdgeMonitorStart ?? "", "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out st) && firstBarDate > DateKey(st))
						Warn("nqm_edge_hist", string.Format("NQMaster | edge monitor: the loaded history starts after the monitor start date ({0}) and no saved state exists, so it only counts {1} days. Load data from the start date or keep NinjaTrader running.", EdgeMonitorStart, edgeDays));
					return;
				}
				string[] p = File.ReadAllText(EdgeFile).Split(';');
				if (p.Length < 9 || p[0] != Profile.ToString() || p[8] != (EdgeMonitorStart ?? "")) { Print("NQMaster | edge monitor: saved state is for another profile or start date - ignored."); return; }
				int d = int.Parse(p[1], CultureInfo.InvariantCulture);
				if (d < edgeLastDate) return;			// the history rebuild is newer
				edgeLastDate = d; edgeS = double.Parse(p[2], CultureInfo.InvariantCulture); edgeDays = int.Parse(p[3], CultureInfo.InvariantCulture);
				edgeAlarm = p[4] == "1"; edgeFbLeft = int.Parse(p[5], CultureInfo.InvariantCulture); edgeWarned = p[7] == "1";
				edgeFbOff = new List<string>(); foreach (string x in p[6].Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries)) edgeFbOff.Add(x);
				if (edgeAlarm && EdgeMonitorPause) edgePaused = true;
				Print(string.Format("NQMaster | edge monitor state restored ({0}): CUSUM {1:0.00}, {2} days{3}", d, edgeS, edgeDays, edgeFbLeft > 0 ? ", fallback " + edgeFbLeft + " days left" : ""));
			}
			catch (Exception e) { Print("NQMaster | edge monitor state not restored: " + e.Message); }
		}
		private void EdgeDayClose(DateTime etNow)
		{
			bool counted = EdgeMonitor && edgeDayRth && edgeDayTradable && edgeDayDate != DateTime.MinValue && !double.IsNaN(todayAtr) && todayAtr > 0
				&& !(MinAtrPoints > 0 && todayAtr < MinAtrPoints);
			DateTime st;
			if (counted && DateTime.TryParseExact(EdgeMonitorStart ?? "", "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out st) && edgeDayDate >= st)
			{
				if (double.IsNaN(edgeK)) EdgeParams();
				if (edgeFbLeft > 0)
				{
					// review-set fallback running: the monitor rests (research/mine/os_adapt.py), then resets and the full profile returns
					edgeFbLeft--; edgeLastDate = DateKey(edgeDayDate); EdgeSave();
					if (edgeFbLeft == 0) { edgeAlarm = false; edgeS = 0; edgeFbOff = null; Warn("nqm_edge_fb", "NQMaster | edge-monitor fallback finished: full profile again, CUSUM reset."); }
					edgeDayRth = false; return;
				}
				double z = (netPnl - dayStartPnl) / Math.Max(1, edgeDayQty) / (2.0 * todayAtr);
				edgeS = Math.Max(0.0, edgeS + edgeK - z); edgeDays++; edgeLastDate = DateKey(edgeDayDate);
				if (edgeS <= 0) edgeWarned = false;
				if (!edgeWarned && !edgeAlarm && edgeHw > 0 && edgeS > edgeHw)
				{
					edgeWarned = true;
					Warn("nqm_edge_w", string.Format("NQMaster | EDGE MONITOR WARNING {0}: results are running below the backtest ({1:0}% of the alarm level). Alert only: nothing changes; ~1 in 4 years gives a warning by chance.",
						edgeDayDate.ToString("yyyy-MM-dd"), 100 * edgeS / edgeH));
				}
				if (PrintLog) Print(string.Format("{0} | NQM | EDGE day {1}: z {2:0.000} | CUSUM {3:0.00} / {4:0.00} ({5:0}%)", edgeDayDate.ToString("yyyy-MM-dd"), edgeDays, z, edgeS, edgeH, 100 * edgeS / edgeH));
				if (!edgeAlarm && edgeS > edgeH)
				{
					edgeAlarm = true; edgePaused = EdgeMonitorPause;
					string act = EdgeMonitorPause ? "New entries paused. Review, then set a new 'Edge monitor start date' to resume." : "Alert only (pause and fallback are off).";
					if (!EdgeMonitorPause && EdgeAlarmFallback && EdgeFallbackDays > 0)
					{
						edgeFbOff = FallbackList(edgeDayDate.Year); edgeFbLeft = EdgeFallbackDays; edgeS = 0;
						act = edgeFbOff.Count == 0 ? string.Format("Fallback: the yearly review keeps every module, so nothing changes for {0} days (alert only)." , EdgeFallbackDays)
							: string.Format("Fallback for {0} trading days: modules off = {1}; then the full profile returns.", EdgeFallbackDays, string.Join(" ", edgeFbOff.ToArray()));
					}
					Warn("nqm_edge", string.Format("NQMaster | EDGE MONITOR ALARM {0}: live results are no longer consistent with the backtested edge ({1} days counted). {2}",
						edgeDayDate.ToString("yyyy-MM-dd"), edgeDays, act));
				}
			}
			if (State == State.Realtime) EdgeSave();
			edgeDayRth = false;
		}


		// ---- prop-account cushion gating (research/mine/acct_final.py; Lucid Flex 50K, 1 contract per module, MNQ + MGC 2024-26)
		// Eval  : FULL while the cushion over the liquidation threshold is >= EvalCushionFull ($900), SAFE below; own daily stop $700.
		//         Pass 88.9% vs 78.0% (busts 11% vs 22%) when evals are also started only with ATR < 1.15 x its 60-day median.
		// Funded: SAFE while cushion < FundedCushionSafe ($1,500), NO-BOOST above; request payouts at >= $6,000 profit.
		// EQUILIBRIO defaults (acct_life2.py / acct_mc.py, 12-month lifecycle): eval = full profile (EvalCushionFull 0, no daily stop) with
		// GoldMaster Robust; funded = SAFE below $750 cushion, FULL above (FundedHighFull), payouts at $5,000 with GoldMaster WinRate.
		// vs today: +$20-200/month per account in history, +1 tick cost stress and 2,000 bootstrap years; fewer funded accounts lost.
		// 2026-10-12 (research/mine/robust2_life.py, cand16_life.py): FundedCushionSafe default 0 - the per-trade risk cap
		// (RiskCapPerContract $300 below FundedRiskCapCushion $2,000) keeps every module on and loses fewer accounts than SAFE gating.
		//         Accounts lost within 12 months 25% vs 44%; cash per account ~$6.8k vs ~$5.6k.
		private enum GateMode { Full, NoBoost, Safe }
		private GateMode gate = GateMode.Full; private bool noBoost, propStopped;
		private double propPeak = double.NaN, propThr = double.NaN, propCushion = double.NaN, propDayStart = double.NaN, atrStartRatio = double.NaN;
		private bool propLive; private double propBestDay = 0, savedPrevDayStart = double.NaN, storedOverride = double.NaN; private int propRestoredDay = -1, prevSessDay, curSessDay;
		private int EvalStartInt() { DateTime st; return DateTime.TryParseExact(EvalStartDate ?? "", "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out st) ? st.Year * 10000 + st.Month * 100 + st.Day : 0; }
		private void PropSave(int tradeDay)
		{
			if (!propLive) return;
			try { File.WriteAllText(PropFile, string.Format(CultureInfo.InvariantCulture, "{0:0.00};{1};{2:0.00};{3:0.00};{4:0.00}", propPeak, tradeDay, propDayStart, propBestDay, PropPeakOverride)); } catch { }
		}
		private string PropFile { get { try { return Path.Combine(Core.Globals.UserDataDir, "nqmaster_prop_" + (Account != null ? Account.Name : "acct") + ".txt"); } catch { return null; } } }
		// 2026-10-21: realtime prop equity comes from the account's cash. On a NinjaTrader simulation / playback account (Sim101 starts at
		// $100,000 and keeps its own history) that cash has nothing to do with the prop account (Federico's chart: Sim at $51,426 -> cushion
		// $26,326 on a 25K preset), so Sim/Playback accounts use the strategy's own account: start balance + its P&L since the simulated
		// account started - simulated payouts (the account-cycle simulation keeps running live there). Real prop accounts are read as is.
		private double simBase = double.NaN;	// review M3: Sim / Playback without the cycle simulation starts a fresh account at go-live
		private bool SimAccount { get { string n = Account != null ? Account.Name ?? "" : ""; return n.StartsWith("Sim") || n.StartsWith("Playback"); } }
		private double AcctCash()
		{
			if (SimAccount) return cyOn ? StartBalance + netPnl - CyOffset() : StartBalance + netPnl - (double.IsNaN(simBase) ? netPnl : simBase);
			return Account.Get(AccountItem.CashValue, Currency.UsDollar);
		}

		private double PropEquity()
		{
			if (State == State.Realtime) return AcctCash();
			return StartBalance + netPnl - CyOffset();
		}
		private void PropGoLive()
		{
			if (PropMode == NQMasterPropMode.Off) return;
			if (SimAccount)	// Sim / Playback: no prop file. With the cycle simulation the simulated seat continues; without it a fresh account starts now
			{
				if (cyOn) return;
				simBase = netPnl; propPeak = StartBalance; propDayStart = double.NaN; propBestDay = EvalBestDaySoFar; targetHit = false;
				PropSessionStart(); return;
			}
			propLive = true; propPeak = StartBalance; propDayStart = double.NaN; propBestDay = EvalBestDaySoFar;
			DateTime et = ToEt(Times[0][0]); DateTime td = et.Hour >= 18 ? et.Date.AddDays(1) : et.Date; int today = td.Year * 10000 + td.Month * 100 + td.Day;
			try
			{
				string f = PropFile;
				if (f != null && File.Exists(f))
				{
					string[] a = File.ReadAllText(f).Trim().Split(';'); double v;
					int fd = 0; double ds, bd, ov;
					bool fresh = a.Length >= 4 && int.TryParse(a[1], out fd) && fd >= EvalStartInt();	// older than EvalStartDate = another eval
					bool stalePeak = PropMode == NQMasterPropMode.Eval && a.Length >= 4 && !fresh;				// a new eval does not inherit an old peak
					if (!stalePeak && a.Length > 0 && double.TryParse(a[0], NumberStyles.Any, CultureInfo.InvariantCulture, out v)) propPeak = Math.Max(propPeak, v);
					if (fresh && double.TryParse(a[2], NumberStyles.Any, CultureInfo.InvariantCulture, out ds))
					{ if (fd == today) propDayStart = ds; else if (fd == prevSessDay) savedPrevDayStart = ds; }
					if (fresh && double.TryParse(a[3], NumberStyles.Any, CultureInfo.InvariantCulture, out bd)) propBestDay = Math.Max(propBestDay, bd);
					if (a.Length >= 5 && double.TryParse(a[4], NumberStyles.Any, CultureInfo.InvariantCulture, out ov)) storedOverride = ov;
				}
			}
			catch { }
			// manual correction (e.g. a stale file after an account reset): applied once; later restarts keep the higher saved peak
			bool newOverride = double.IsNaN(storedOverride) || Math.Abs(PropPeakOverride - storedOverride) > 0.01;
			if (PropPeakOverride > 0) propPeak = newOverride ? PropPeakOverride : Math.Max(propPeak, PropPeakOverride);
			// first start of the day (no saved state): the day started at equity now minus what the account already realized today
			if (double.IsNaN(propDayStart)) { try { propDayStart = PropEquity() - Account.Get(AccountItem.RealizedProfitLoss, Currency.UsDollar); } catch { } }
			// the last session NinjaTrader saw start was not closed by it (shut down before 18:00): its P&L = today's start - its start
			if (!double.IsNaN(savedPrevDayStart) && !double.IsNaN(propDayStart)) { propBestDay = Math.Max(propBestDay, propDayStart - savedPrevDayStart); savedPrevDayStart = double.NaN; }
			if (!double.IsNaN(propDayStart)) { propRestoredDay = today; }
			PropSessionStart();
		}
		private void PropSessionStart()
		{
			gate = GateMode.Full; noBoost = false; propStopped = false;
			if (PropMode != NQMasterPropMode.Off)
			{
				double eq = PropEquity();
				DateTime et0 = ToEt(Times[0][0]); DateTime td0 = et0.Hour >= 18 ? et0.Date.AddDays(1) : et0.Date; int tday = td0.Year * 10000 + td0.Month * 100 + td0.Day;
				bool restored = propRestoredDay == tday && !double.IsNaN(propDayStart);
				if (restored) { }                  // restarted mid-session: keep the saved day start
				else { if (!double.IsNaN(propDayStart)) propBestDay = Math.Max(propBestDay, eq - propDayStart); propDayStart = eq; }
				propRestoredDay = -1;
				if (double.IsNaN(propPeak)) propPeak = Math.Max(StartBalance, PropPeakOverride > 0 ? PropPeakOverride : eq);
				double eqRef = restored ? propDayStart : eq;			// intraday cash is not an end-of-day balance
				if (eqRef > propPeak) propPeak = eqRef;
				PropSave(tday);
				propThr = propPeak >= StartBalance + PropTrailingDD + 100 ? StartBalance + 100 : propPeak - PropTrailingDD;
				if (PropThresholdOverride > 0) propThr = PropThresholdOverride;
				if (CyLive) { propPeak = StartBalance + cy.Pk; propThr = StartBalance + cy.Thr; }	// simulated seat: the audited rules engine
				propCushion = eqRef - propThr;
				if (PropMode == NQMasterPropMode.Eval) gate = propCushion >= EvalCushionFull ? GateMode.Full : GateMode.Safe;
				else if (FundedCushionFull > 0) gate = propCushion < FundedCushionSafe ? GateMode.Safe : (propCushion < FundedCushionFull ? GateMode.NoBoost : GateMode.Full);
				else gate = propCushion >= FundedCushionSafe ? (FundedHighFull ? GateMode.Full : GateMode.NoBoost) : GateMode.Safe;
				noBoost = gate != GateMode.Full;
			}
			// Eval SAFE gear "Estable" (research/mine/gate84.py -> gate_lo.py, gate_final.py): below the cushion only the stable modules trade,
			// no x2, VOLB trend-only at 0.5R. Lucid 50K, 1 contract, Ultra above $1,200 cushion, gold WinRate x2, eval started on an
			// ATR < 1.15 day: pass 92% / 83% / 96% (CFD 2024-26 / MNQ 2024-26 / CFD 2020-23) vs 57-65% / 75-76% / 95% without gating.
			bool estable = PropMode == NQMasterPropMode.Eval && gate == GateMode.Safe && EvalSafeSet == NQMasterSafeSet.Estable;
			foreach (Mod m in mods)
				m.On = m.BaseOn && !FallbackOff(m.Sig) && (estable ? EstableSig(m.Sig)
					: !(gate == GateMode.Safe && (m.Sig == "VOLB" || m.Sig == "LON" || m.Sig == "MOM1030" || m.Sig == "MOM11")));
			if (volb != null) { volbTrendOnly = estable || volbTrendBase; volb.R = estable ? 0.5 : volbRBase; }
			atrStartRatio = double.NaN;
			if (atrHist != null && atrHist.Count >= 20 && !double.IsNaN(todayAtr) && todayAtr > 0)
			{
				List<double> srt = new List<double>(atrHist.Count > 60 ? atrHist.GetRange(atrHist.Count - 60, 60) : atrHist); srt.Sort(); int nn = srt.Count;
				double med = nn % 2 == 1 ? srt[nn / 2] : 0.5 * (srt[nn / 2 - 1] + srt[nn / 2]); atrStartRatio = med > 0 ? todayAtr / med : double.NaN;
			}
			if (PropMode != NQMasterPropMode.Off) Log(string.Format("PROP {0}: equity {1:0} | threshold {2:0} | cushion {3:0} -> {4}{5}", PropMode, PropEquity(), propThr, propCushion, gate,
				StepUpOn ? string.Format(" | STEP-UP {0} contracts", LadderQty()) : ""));
		}
		private static bool EstableSig(string s)
		{
			return s == "CRT11" || s == "ORB90" || s == "MSEQ" || s == "ON07" || s == "REV06" || s == "VOLB" || s == "VW13" || s == "ENG10" || s == "LATEFH";
		}
		private void PropDailyCheck()
		{
			// Funded: optional daily profit stop for LucidPro's 40% per-payout-cycle consistency (research/mine/lucidpro.py: 2 contracts,
			// stop at +$500 for the whole account -> $/month per account +13% vs LucidFlex 2c/2c; no daily loss stop in Funded)
			bool evalMode = PropMode == NQMasterPropMode.Eval;
			// research/mine/ladder_stop.py (2026-10-17): with the funded size ladder, an ACCOUNT daily stop of $1,500 per contract per module (realized + open,
			// size fixed at the day start) cuts funded busts 0.61 -> 0.19 per year (2024-26) and raises the p10 of the steady-state income; neutral at 1 contract.
			double lossStop = evalMode ? EvalDailyStop : (PropMode == NQMasterPropMode.Funded && DailyLossPerContract > 0 ? DailyLossPerContract * Math.Max(1, edgeDayQty) : 0);
			double profitStop = evalMode ? EvalProfitStop : (PropMode == NQMasterPropMode.Funded ? FundedProfitStop : 0);
			if ((lossStop <= 0 && profitStop <= 0) || propStopped || double.IsNaN(propDayStart)) return;
			double now = State == State.Realtime ? AcctCash() + (SimAccount ? (Position.MarketPosition == MarketPosition.Flat ? 0 : Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Closes[0][0])) : Account.Get(AccountItem.UnrealizedProfitLoss, Currency.UsDollar))
				: StartBalance + netPnl - CyOffset() + (Position.MarketPosition == MarketPosition.Flat ? 0 : Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Closes[0][0]));
			if (lossStop > 0 && !evalMode && State != State.Realtime && Position.MarketPosition != MarketPosition.Flat)
			{	// historical: mirror the research (minute low of the day's equity) with the bar's adverse extreme
				try { now = Math.Min(now, StartBalance + netPnl - CyOffset() + Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Position.MarketPosition == MarketPosition.Long ? Lows[0][0] : Highs[0][0])); } catch { }
			}
			if (lossStop > 0 && now - propDayStart <= -lossStop) { propStopped = true; FlattenAll("prop daily stop"); Log(string.Format("PROP DAILY STOP: {0:0} today (limit {1:0})", now - propDayStart, lossStop)); }
			else if (profitStop > 0 && now - propDayStart >= profitStop) { propStopped = true; FlattenAll(evalMode ? "eval daily profit stop" : "funded daily profit stop"); Log(string.Format("{0} DAILY PROFIT STOP: +{1:0} today (Lucid consistency)", evalMode ? "EVAL" : "FUNDED", now - propDayStart)); }
		}

		private bool lastDeferred; private int deferUntil = -1, deferDir;
		private Mod pend5; private int pend5Dir, pend5Qty, pend5Bar; private double pend5Stop;
		// Opposite open position -> skip. Opposite WORKING entry orders (e.g. an ORB stop order) -> cancel them and defer this entry
		// one bar (NinjaTrader's managed rules ignore an entry while an opposite entry order is working).
		private bool DirectionAllowed(int d) { return DirectionAllowed(d, BarsInProgress == 1 ? 5 : 1); }
		private bool DirectionAllowed(int d, int deferBars)
		{
			lastDeferred = false;
			if ((d == 1 && Position.MarketPosition == MarketPosition.Short) || (d == -1 && Position.MarketPosition == MarketPosition.Long)) return false;
			if (RtZombieOpp(d)) return false;
			if (OtherAccountOpposite(d)) return false;
			// an opposite MARKET entry already sent (fills at the next open) counts as an open position: research keeps the first trade
			foreach (Mod m in mods) if (Working(m.Entry) && m.Dir == -d && m.Entry.OrderType == OrderType.Market) return false;
			bool blocked = false;
			foreach (Mod m in mods) if (Working(m.Entry) && m.Dir == -d) { ParkOrder(m); blocked = true; }
			if (blocked) { lastDeferred = true; deferUntil = Math.Max(deferUntil, CurrentBars[0] + deferBars); deferDir = d; return false; }
			return true;
		}

		// true from `before` minutes before a Tier-1 release (bar close times) until 2 minutes after it: with before = 3 the bar closing
		// at 08:27 flattens (flat before 08:28:00) and entries resume with the bar closing at 08:32.
		private bool InNews(DateTime etClose, int before)
		{
			if (newsEt == null) return false;
			foreach (DateTime e in newsEt) { double m = (etClose - e).TotalMinutes; if (m >= -before && m < 2) return true; }
			return false;
		}
		private bool newsBlock5;
		private bool CanTrade()
		{
			if (desyncHalt) { status = "ACCOUNT / STRATEGY POSITION MISMATCH - see Output"; return false; }
			if (rejectHalt) { status = "the account refuses orders - see Output"; return false; }
			if (SkipShortSessions && shortSession) { status = "holiday / half-day session: no trading"; return false; }
			if (rollHalt) { status = "ROLL DATE: move the strategy to the next contract"; return false; }
			if (newsBlock5 && BarsInProgress == 1) { status = "NEWS BLACKOUT"; return false; }
			if (fomcToday) { status = "FOMC day: no trading"; return false; }
			if (cyOn && cyHalt) { status = cyStatus.Length > 0 ? cyStatus : "simulaci\u00f3n de cuenta: sin operar"; return false; }
			if (targetHit) { status = "eval target reached"; return false; }
			if (ddTripped) { status = "drawdown guard"; return false; }
			if (dayStopped) { status = "daily loss limit"; return false; }
			if (propStopped) { status = "prop daily stop"; return false; }
			if (MinAtrPoints > 0 && !double.IsNaN(todayAtr) && todayAtr < MinAtrPoints) { status = "low volatility (ATR " + todayAtr.ToString("0") + " < " + MinAtrPoints.ToString("0") + ")"; return false; }
			if (PauseActive()) { status = "MANUAL PAUSE (file)"; return false; }
			if (edgePaused) { status = "EDGE MONITOR ALARM - review before trading"; return false; }
			status = "trading";
			return true;
		}

		private void AccountGuard()
		{
			if (State != State.Realtime) return;
			double bal = AcctCash();
			if (double.IsNaN(highWater) || bal > highWater) highWater = bal;
			if (EvalTarget > 0 && !targetHit && PropMode != NQMasterPropMode.Funded && !cyOn)
			{
				// Lucid-style consistency: the best day may be at most ConsistencyPct % of the total profit -> the real target can be higher
				double eqNow = bal + Account.Get(AccountItem.UnrealizedProfitLoss, Currency.UsDollar);
				double today = double.IsNaN(propDayStart) ? 0 : eqNow - propDayStart;
				double need = EvalTarget;
				if (ConsistencyPct > 0) need = Math.Max(need, Math.Max(propBestDay, today) * 100.0 / ConsistencyPct);
				if (eqNow >= StartBalance + need) { targetHit = true; FlattenAll("eval target"); Warn("nqm_target", string.Format("NQMaster | EVAL TARGET REACHED (+{0:0}, needed {1:0}) - trading stopped.", bal - StartBalance, need)); }
			}
			if (EvalTarget > 0 && targetHit && Position.MarketPosition == MarketPosition.Flat && Math.Abs(Account.Get(AccountItem.UnrealizedProfitLoss, Currency.UsDollar)) < 0.01)
			{
				double today = double.IsNaN(propDayStart) ? 0 : bal - propDayStart, need = EvalTarget;
				if (ConsistencyPct > 0) need = Math.Max(need, Math.Max(propBestDay, today) * 100.0 / ConsistencyPct);
				if (bal < StartBalance + need) { targetHit = false; Print(string.Format("NQMaster | eval target not met after closing (+{0:0}, needed {1:0}) - trading resumes.", bal - StartBalance, need)); }
			}
			if (MaxDrawdown > 0 && bal <= highWater - MaxDrawdown + DrawdownBuffer && !ddTripped) { ddTripped = true; FlattenAll("drawdown guard"); Warn("nqm_dd", "NQMaster | DRAWDOWN GUARD - trading stopped."); }
		}

		private void ExitModule(Mod m, string why)
		{
			if (desyncHalt) return;
			if (Position.MarketPosition == MarketPosition.Long) ExitLong(fillBip, Math.Max(1, Position.Quantity), m.Sig + "X", m.Sig);
			else if (Position.MarketPosition == MarketPosition.Short) ExitShort(fillBip, Math.Max(1, Position.Quantity), m.Sig + "X", m.Sig);
			Log(m.Sig + " exit: " + why);
		}

		private void FlattenAll(string why)
		{
			CancelAllEntries();
			if (desyncHalt) return;
			if (Position.MarketPosition == MarketPosition.Flat || flattenBar == CurrentBars[0]) return;
			flattenBar = CurrentBars[0];
			// FillSeries Off: the parameterless exit, as always. Tick1 / Second1: the same whole-position market exit (default names 'Sell' /
			// 'Buy to cover', fromEntrySignal empty = every entry) submitted to the fill series, so the exit fills on the next tick.
			if (fillBip == 0) { if (Position.MarketPosition == MarketPosition.Long) ExitLong(); else ExitShort(); }
			else if (Position.MarketPosition == MarketPosition.Long) ExitLong(fillBip, Position.Quantity, "Sell", "");
			else ExitShort(fillBip, Position.Quantity, "Buy to cover", "");
			Log("FLATTEN: " + why);
		}

		private void CancelAllEntries() { foreach (Mod m in mods) { m.Parked = false; CancelEntry(m); } }
		// ---- parking (research/mine/patch_review2.py): research keeps every module's order working and only drops a fill against an open
		// opposite position. NinjaTrader's managed rules cannot hold opposite entry orders at once, so the cancelled one is kept here and
		// re-placed as soon as no opposite position / working order remains. Dropped if its level trades while blocked or its window ends.
		private void ParkOrder(Mod o)
		{
			Order e = o.Entry;
			if (e == null || !Working(e)) return;
			if (o != volb && (e.OrderType == OrderType.StopMarket || e.OrderType == OrderType.Limit))
			{ o.Parked = true; o.ParkHit = false; o.ParkLimit = e.OrderType == OrderType.Limit; o.ParkPx = o.ParkLimit ? e.LimitPrice : e.StopPrice; o.ParkQty = Math.Max(1, UseOrderFlowBoost && o.OfQ0 > 0 ? o.OfQ0 : e.Quantity); Log(o.Sig + " order parked (opposite trade)"); }
			CancelEntry(o);
		}
		// a setup blocked by an opposite POSITION at placement time: kept and placed when free (research drops only a fill against it)
		private void ParkSetup(Mod o, bool limit, double px, int qty)
		{
			o.Parked = true; o.ParkHit = false; o.ParkLimit = limit; o.ParkPx = px; o.ParkQty = Math.Max(1, qty);
			Log(string.Format("{0} setup parked @ {1} (opposite position open)", o.Sig, Fmt(px)));
		}
		private bool OppBusy(int d, Mod self)
		{
			if ((d == 1 && Position.MarketPosition == MarketPosition.Short) || (d == -1 && Position.MarketPosition == MarketPosition.Long)) return true;
			foreach (Mod o in mods) if (o != self && Working(o.Entry) && o.Dir == -d) return true;
			if (OtherOpp(d, false)) return true;	// round 5 C6 (2)
			return RtZombieOpp(d);
		}
		private bool ParkExpired(Mod o, int openMin, int closeMin)
		{
			if (o.Kind == 0) return closeMin >= 780;
			if (o == eng10) return openMin >= 689;
			if (o == lon) return openMin >= 480;
			if (o == ict) return CurrentBars[1] >= ictExpiry || (ict.Dir == -1 && High[0] > ictExtPend) || (ict.Dir == 1 && Low[0] < ictExtPend);
			return true;
		}
		private void ManageParked(int openMin, int closeMin)
		{
			foreach (Mod o in mods)
			{
				if (!o.Parked) continue;
				if (o.ParkLimit ? (o.Dir == 1 ? Low[0] <= o.ParkPx : High[0] >= o.ParkPx) : (o.Dir == 1 ? High[0] >= o.ParkPx : Low[0] <= o.ParkPx)) o.ParkHit = true;	// latched
				if (Working(o.Entry)) continue;									// the cancel is still pending
				if (o.InTrade || o.ParkHit || ParkExpired(o, openMin, closeMin)) { o.Parked = false; Log(o.Sig + " parked order dropped" + (o.ParkHit ? " (level traded while blocked)" : "")); continue; }
				if (CurrentBars[0] <= deferUntil) continue;						// the module that parked it enters first
				if (OppBusy(o.Dir, o)) continue;
				o.Parked = false;
				Order r = null;
				int pkq = OfApply(o, o.ParkQty, o.Dir);
				if (pkq <= 0) { o.Parked = true; continue; }		// no room under the contract cap yet
				if (o.ParkLimit) r = o.Dir == 1 ? EnterLongLimit(fillBip, true, pkq, o.ParkPx, o.Sig) : EnterShortLimit(fillBip, true, pkq, o.ParkPx, o.Sig);
				else if (PastLevel(o.Dir, o.ParkPx)) { Log(o.Sig + " parked order dropped (level passed)"); continue; }
				else r = o.Dir == 1 ? EnterLongStopMarket(fillBip, true, pkq, o.ParkPx, o.Sig) : EnterShortStopMarket(fillBip, true, pkq, o.ParkPx, o.Sig);
				if (r != null) o.Entry = r;
				Log(o.Sig + " parked order re-placed @ " + Fmt(o.ParkPx));
			}
		}

		private static bool Working(Order o)
		{
			if (o == null) return false;
			OrderState s = o.OrderState;
			return s != OrderState.Filled && s != OrderState.Cancelled && s != OrderState.Rejected && s != OrderState.Unknown;
		}
		// every cancel of a module entry goes through here so the watchdog knows when it was asked for
		private void CancelEntry(Mod m)
		{
			Order e = m.Entry;
			if (!Working(e)) return;
			if (m.CancelOrd != e) { m.CancelOrd = e; m.CancelBar = CurrentBars[0]; }
			CancelOrder(e);
		}
		// ---- stale-order watchdog. NinjaTrader can hand back an entry order that it never processes (it stays Initialized) or whose
		// cancel never completes; Working() then reports it as live forever and every opposite entry is deferred. Strategy Analyzer
		// MNQ 2024-26 (Ultra): a VOLB buy stop placed 2025-08-13 09:32 ET never reached the market (price crossed it on 2025-09-15 without
		// a fill) and could not be cancelled -> VOLB never traded again and 0 shorts were taken for 14 months (research: 577 shorts,
		// WR 65.7%, PF 1.53, +$17.6k per contract). Historical orders are processed at once and live ones within seconds, so an entry
		// that is still not accepted 2 bars later, a market entry still unfilled 2 bars later, or a cancel not confirmed 2 bars after it
		// was requested is dead: it is dropped (cancel attempted, reference cleared) and a STALE ORDER line is printed. Every entry is
		// cancelled at FlattenTime, so a dead order is found the same day at the latest.
		private void PurgeStaleEntries()
		{
			foreach (Mod m in mods)
			{
				Order e = m.Entry;
				if (!Working(e)) continue;
				if (e != m.SeenOrd) { m.SeenOrd = e; m.SeenBar = CurrentBars[0]; }
				int age = CurrentBars[0] - m.SeenBar;
				OrderState s = e.OrderState;
				string why = null;
				int lim = State == State.Realtime ? 5 : 2;
				if (m.CancelOrd == e && CurrentBars[0] - m.CancelBar >= lim) why = "cancel never confirmed";
				else if (age >= lim && (s == OrderState.Initialized || s == OrderState.Submitted)) why = "never accepted";
				else if (age >= lim && e.OrderType == OrderType.Market && s != OrderState.PartFilled) why = "market entry never filled";
				else if (m.OfChangeOrd == e && CurrentBars[0] - m.OfChangeBar >= 2 && (s == OrderState.ChangePending || s == OrderState.ChangeSubmitted)) why = "size change never confirmed";
				if (why == null) continue;
				DropStale(m, why, true);
			}
		}
		private void DropStale(Mod m, string why, bool cancel)
		{
			Order e = m.Entry;
			OrderState s = e.OrderState;
			if (cancel) { try { CancelOrder(e); } catch { } }
			zombies.Add(e); zombieCount++;
			if (State == State.Realtime) { rtZombies.Add(e); Warn("nqm_stale", "NQMaster | STALE ORDER in realtime: " + m.Sig + " " + e.OrderAction + " " + e.OrderType + " - check the Orders tab; it keeps blocking the opposite direction while it may be live."); }
			m.Entry = null; m.SeenOrd = null; m.CancelOrd = null;
			Print(string.Format("{0} | NQMaster | STALE ORDER dropped ({1}): {2} {3} {4} x{5} @ {6}, state {7} - the module and the opposite direction trade again",
				Times[0][0].ToString("yyyy-MM-dd HH:mm", CultureInfo.InvariantCulture), why, m.Sig, e.OrderAction, e.OrderType, e.Quantity,
				e.OrderType == OrderType.Market ? "market" : Fmt(e.OrderType == OrderType.Limit ? e.LimitPrice : e.StopPrice), s));
		}
		private Mod BySig(string sig) { if (mods == null || string.IsNullOrEmpty(sig)) return null; foreach (Mod m in mods) if (m.Sig == sig) return m; return null; }

		protected override void OnOrderUpdate(Order order, double limitPrice, double stopPrice, int quantity, int filled, double averageFillPrice,
			OrderState orderState, DateTime time, ErrorCode error, string nativeError)
		{
			Mod m = BySig(order.Name);
			if (m != null && !zombies.Contains(order) && (m.Entry == null || m.Entry == order || !Working(m.Entry))) m.Entry = order;
			if (m != null && (orderState == OrderState.Accepted || orderState == OrderState.Working || orderState == OrderState.Cancelled || orderState == OrderState.Rejected || orderState == OrderState.Filled))
				CrossAccountPublish();	// round 5 C6 (5): entry placed / cancelled / filled -> other accounts see it at once
			if (orderState == OrderState.Rejected)
			{
				Warn("nqm_rej", string.Format("NQMaster | {0} REJECTED: {1} {2}", order.Name, error, nativeError));
				if (m != null && ++m.RejToday == 2) Log(m.Sig + " off for the rest of the session (2 rejected orders)");
				RejectSeen(nativeError);
				// a rejected stop-loss / target leaves that module unprotected -> exit it; any other rejected exit -> flatten; a rejected entry is skipped
				if (m == null && Position.MarketPosition != MarketPosition.Flat)
				{
					Mod f = (order.Name == "Stop loss" || order.Name == "Profit target") ? BySig(order.FromEntrySignal) : null;
					if (f != null) { if (f.InTrade) ExitModule(f, "protective order rejected"); }
					else FlattenAll("exit order rejected");
				}
			}
		}

		protected override void OnExecutionUpdate(Execution execution, string executionId, double price, int quantity,
			MarketPosition marketPosition, string orderId, DateTime time)
		{
			if (execution.Order == null) return;
			Mod m = BySig(execution.Order.Name);
			if (m != null)
			{
				if (execution.Order.Filled <= 0) return;
				bool first = !m.InTrade;
				m.InTrade = true; m.EntryPx = execution.Order.AverageFillPrice; m.OpenQty += quantity;
				if (first)
				{
				if (UseOrderFlowBoost) { ofEntries++; if (m.OfQ0 > 0 && execution.Order.Quantity > m.OfQ0) ofBoosted++; }
				InactivityFill(m); CrossAccountPublish(); CrossAccountOnFill(m);
				if (m == orb) { orb.Trades++; if (orbFirstDir == 0) { orbFirstDir = orb.Dir; DateTime eo = ToEt(FillBarTime()).AddMinutes(-1); orbFirstMin = eo.Hour * 60 + eo.Minute; } }
				if (m == orb2) orb2.Trades++;
				if (m == volb) { volbDone = true; volb.EntryBar = FillBar(); volbBeSet = false; volbTrades++; }
				if (m == eng10) eng10.EntryBar = FillBar();
				if (m.Sig == "MOM11" && m11Dir == 0) m11Dir = m.Dir;
				if (m == lon || m.Sig == "ON07" || m.Sig == "REV06") onSum += m.Dir;
				if (m == lon && lonDir == 0) lonDir = lon.Dir;
				if (m == ict) ictTrades++;
				if (m.Kind == 1 || m == rsi || m.Six) m.EntryBar = FillBar();
				// cancel opposite working entries
				foreach (Mod o in mods) if (o != m && Working(o.Entry) && o.Dir == -m.Dir) ParkOrder(o);
				}
				if (m.PriceTarget)
				{
					double fill = m.EntryPx; double risk = (fill - m.StopPx) * m.Dir;
					if (risk <= 0) { ExitModule(m, "filled beyond stop"); return; }
					double tgt = Instrument.MasterInstrument.RoundToTickSize(double.IsNaN(m.FixTgt) ? fill + m.Dir * m.R * risk : m.FixTgt);
					if ((tgt - fill) * m.Dir <= 0) { ExitModule(m, "filled beyond the target"); return; }
					SetProfitTarget(m.Sig, CalculationMode.Price, tgt);
				}
				Log(string.Format("{0} filled @ {1}", m.Sig, Fmt(m.EntryPx)));
				return;
			}
			Mod exitMod = BySig(execution.Order.FromEntrySignal);
			if (exitMod != null)
			{
				exitMod.OpenQty = Math.Max(0, exitMod.OpenQty - quantity); if (exitMod.OpenQty == 0) exitMod.InTrade = false;
				Log(string.Format("{0} exit fill: {1} x{2} @ {3}{4}", exitMod.Sig, execution.Order.Name, quantity, Fmt(price), State == State.Realtime ? string.Format(" | account cash {0:0}", AcctCash()) : ""));
				// research/mine/reentry_lab.py (2026-10-17): VOLB 2R re-armed once after a stop-out (not after the break-even stop), same levels, either
				// side, before 15:00: 181 trades 2020-26, PF 1.52 / 1.32 (T1 / T2), +$58 per month per contract, Sharpe up in both periods, but max DD +6%
				// (protocol limit +5%) -> opt-in only (VolbReArm)
				if (exitMod == volb && exitMod.OpenQty == 0 && VolbReArm && !volbTrendOnly && volb.R >= 1.5 && !volbBeSet && volbTrades < 2 && !Working(volb.Entry) && execution.Order.Name == "Stop loss")
				{ volbDone = false; Log("VOLB stopped out: re-armed for a second attempt (VolbReArm)"); }
			}
			if (Position.MarketPosition == MarketPosition.Flat) foreach (Mod x in mods) { x.InTrade = false; x.OpenQty = 0; }
		}

		private void ProcessClosedTrades()
		{
			int count = SystemPerformance.AllTrades.Count;
			for (int i = tradesProcessed; i < count; i++)
			{
				double pnl = SystemPerformance.AllTrades[i].ProfitCurrency;
				totalTrades++; netPnl += pnl;
				StatTrade(pnl, SystemPerformance.AllTrades[i].Commission, Times[0][0]);
				if (pnl > 0) { totalWins++; grossWin += pnl; } else grossLoss -= pnl;
				if (netPnl > eqPeak) eqPeak = netPnl;
			}
			tradesProcessed = count;
			if (Position.MarketPosition == MarketPosition.Flat) foreach (Mod x in mods) { x.InTrade = false; x.OpenQty = 0; }
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
		// fill callbacks: index / close time of the 1-minute bar the fill belongs to (fill series: that bar is still forming, so +1 bar / +1 min)
		private int FillBar() { return CurrentBars[0] + (fillBip > 0 && BarsInProgress == fillBip ? 1 : 0); }
		private DateTime FillBarTime() { return fillBip > 0 && BarsInProgress == fillBip ? Times[0][0].AddMinutes(1) : Times[0][0]; }
		private string Fmt(double p) { return Instrument.MasterInstrument.FormatPrice(p); }
		private void Log(string m)
		{
			string line = string.Format("{0} | NQM | {1}", Times[0][0].ToString("yyyy-MM-dd HH:mm", CultureInfo.InvariantCulture), m);
			if (PrintLog) Print(line);
			LogFile(line);
		}
		// <propcycle> ---- prop-account rules engine (2026-10-21). No NinjaTrader types: tools/propcycle_test feeds the same day paths to
		// this class and to the research simulators (research/mine/prop_wf.py race(), acct1c_lib.fu_flex / fu_pro, mffu_rapid.fu_m)
		// and requires identical passes, busts and payouts. All amounts are $ of profit over the start balance.
		public class PropCycle
		{
			public string Firm = "";
			public int Model;                 // funded payout rule: 0 Lucid Flex, 1 Lucid Pro / FundedNext (buffer), 2 MFFU (keep a balance)
			public double T, D, Cons, Lock = 100, Q, Cap1, Cap2, X, Buf, PCons = 0.4, Split = 0.9, Fee, Act;
			public int MinDays = 1, NpMax = 5, CycleMinDays = 3;
			public bool Funded, Alive;
			public double Raw, Withdrawn, Pk, DayStart, Best, CycStart, CycBest = -1e9;
			public int Days, Qd, Nd, Pays;
			public bool Locked;
			public double Bal { get { return Raw - Withdrawn; } }
			public double Thr { get { return (Locked || Pk >= D + Lock) ? Lock : Pk - D; } }
			public double Cushion { get { return Bal - Thr; } }
			public void Start(bool funded)
			{
				Funded = funded; Alive = true; Raw = 0; Withdrawn = 0; Pk = 0; DayStart = 0; Best = -1e9; CycStart = 0; CycBest = -1e9;
				Days = 0; Qd = 0; Nd = 0; Pays = 0; Locked = false;
			}
			// eval target with the consistency rule (best day <= Cons x total profit)
			public bool TargetMet(double prof)
			{
				if (prof < T) return false;
				return Cons <= 0 || Math.Max(Best, prof - DayStart) <= Cons * prof;
			}
			// intraday, every bar: rawLow / rawClose = strategy P&L since the account start incl. the open position at the bar's adverse
			// extreme / close. Returns -1 account lost, 1 eval target reached (flatten), 0 nothing.
			public int Bar(double rawLow, double rawClose)
			{
				if (!Alive) return 0;
				if (rawLow - Withdrawn <= Thr) { Alive = false; return -1; }
				if (!Funded && TargetMet(rawClose - Withdrawn)) { Alive = false; return 1; }
				return 0;
			}
			// end of a trading day (flat): returns the payout requested at this close (0 = none)
			public double DayClose(double rawClose)
			{
				Raw = rawClose; Days++;
				double bal = Bal, c = bal - DayStart, amt = 0;
				if (!Funded)
				{
					if (c > Best) Best = c;
					if (bal > Pk) Pk = bal;
					DayStart = bal; return 0;
				}
				Nd++;
				if (bal > Pk) Pk = bal;
				if (Model == 0)
				{
					if (c >= Q) Qd++;
					if (Qd >= 5 && bal - CycStart > 0 && bal >= X)
					{
						double a = Math.Min(Cap1, 0.5 * bal);
						if (a >= 500) { amt = a; Qd = 0; Locked = true; }
					}
				}
				else if (Model == 1)
				{
					if (c > CycBest) CycBest = c;
					double prof = bal - CycStart, cap = Pays == 0 ? Cap1 : Cap2, a = Math.Min(cap, bal - Buf);
					if (Nd >= CycleMinDays && prof >= 500 && a >= Math.Max(500, Math.Min(X, cap)) && CycBest <= PCons * prof) { amt = a; CycBest = -1e9; Nd = 0; }
				}
				else if (bal - X >= 500) amt = bal - X;
				if (amt > 0) { Withdrawn += amt; Pays++; CycStart = Bal; }
				DayStart = Bal;
				if (amt > 0 && NpMax > 0 && Pays >= NpMax) Alive = false;   // last payout: the account moves on (Lucid: to Live) and the seat restarts
				return amt;
			}
			// what is missing for the next payout (dashboard text)
			public string NextPayout(Func<double, string> usd)
			{
				double bal = Bal;
				if (Model == 0)
				{
					string s = "";
					if (bal < X) s += "faltan " + usd(X - bal) + " de ganancia";
					if (Qd < 5) s += (s.Length > 0 ? " y " : "faltan ") + (5 - Qd) + " días >= " + usd(Q);
					if (bal - CycStart <= 0 && Pays > 0) s += (s.Length > 0 ? " y " : "falta ") + "ganancia en el ciclo";
					return s.Length > 0 ? s : "listo para pedir al cierre";
				}
				if (Model == 1)
				{
					double cap = Pays == 0 ? Cap1 : Cap2, need = Buf + Math.Max(500, Math.Min(X, cap)), prof = bal - CycStart;
					string s = "";
					if (bal < need) s += "faltan " + usd(need - bal) + " de saldo";
					if (prof < 500) s += (s.Length > 0 ? " y " : "faltan ") + usd(500 - prof) + " de ganancia en el ciclo";
					if (Nd < CycleMinDays) s += (s.Length > 0 ? " y " : "faltan ") + (CycleMinDays - Nd) + " días";
					if (prof > 0 && CycBest > PCons * prof) s += (s.Length > 0 ? " y " : "") + "el mejor día supera el " + (PCons * 100).ToString("0") + "% del ciclo";
					return s.Length > 0 ? s : "listo para pedir al cierre";
				}
				return bal >= X + 500 ? "listo para pedir al cierre" : "faltan " + usd(X + 500 - bal) + " de ganancia";
			}
		}
		// </propcycle>
		// ---- account cycle simulation (2026-10-21, Federico: 'calculate payouts, show them, whether it burned, how many burned, buying a new
		// eval the next day'). With a firm preset and PropMode Eval/Funded, the backtest runs the whole seat: buy an eval -> pass (flatten at
		// the target, firm minimum days) or lose it -> next session a new eval (fee) or the funded account (activation) -> payouts at the
		// close with the firm rule -> lost or completed (last payout) -> new eval. Eval and funded sizes and stops are the preset's, switched
		// at each phase change. Rules engine = PropCycle (audited against the research simulators by tools/propcycle_test/run_test.py).
		// Runs on history and, on a Sim/Playback account, live; on a real prop account it stops at go-live (the firm's account is the truth).
		private PropCycle cy; private bool cyOn, cyStarted, cyHalt, cyFrozen, presetQuiet; private NQMasterPropMode realMode = NQMasterPropMode.Off;
		private double cyBase; private int cyNext, cyWait, cyEvalN, cyEvPass, cyEvBust, cyFundN, cyFuBust, cyFuDone, cyPayN; private int cySeat = 1;
		private double cyPayGross, cyPayCash, cyFeeEval, cyFeeAct; private DateTime cyFirst = DateTime.MinValue, cyLastDay = DateTime.MinValue, cyFrozenAt;
		private string cyStatus = ""; private List<string> cyEvents = new List<string>();
		private double[] presetSnap;
		private bool CyLive { get { return cy != null && cyOn && cy.Alive; } }
		private double CyOffset() { return cy != null && cyStarted ? cyBase + cy.Withdrawn : 0; }
		// every account setting ApplyPreset() writes: restored before each phase change so a phase never inherits the other phase's values
		private double[] SnapPreset()
		{
			return new double[] { EvalMode ? 1 : 0, AdaptiveSize ? 1 : 0, EvalCushionFull, EvalDailyStop, FundedCushionSafe, FundedCushionFull, FundedHighFull ? 1 : 0,
				DailyLossLimit, FundedStepUpCushion, FundedLadderStep, DailyLossPerContract, NewsBlackout ? 1 : 0, StartBalance, PropTrailingDD, ConsistencyPct,
				EvalTarget, EvalProfitStop, EvalRiskCapCushion, MaxOpenContracts, EvalHighWrMultiplier, RiskCapPerContract, FundedRiskCapCushion, FundedPayoutAt,
				FundedProfitStop, Contracts, FundedStepUpContracts, FundedLadderMax };
		}
		private void RestorePreset(double[] s)
		{
			int i = 0;
			EvalMode = s[i++] > 0; AdaptiveSize = s[i++] > 0; EvalCushionFull = s[i++]; EvalDailyStop = s[i++]; FundedCushionSafe = s[i++]; FundedCushionFull = s[i++]; FundedHighFull = s[i++] > 0;
			DailyLossLimit = s[i++]; FundedStepUpCushion = s[i++]; FundedLadderStep = s[i++]; DailyLossPerContract = s[i++]; NewsBlackout = s[i++] > 0; StartBalance = s[i++]; PropTrailingDD = s[i++]; ConsistencyPct = s[i++];
			EvalTarget = s[i++]; EvalProfitStop = s[i++]; EvalRiskCapCushion = s[i++]; MaxOpenContracts = (int)s[i++]; EvalHighWrMultiplier = (int)s[i++]; RiskCapPerContract = s[i++]; FundedRiskCapCushion = s[i++]; FundedPayoutAt = s[i++];
			FundedProfitStop = s[i++]; Contracts = (int)s[i++]; FundedStepUpContracts = (int)s[i++]; FundedLadderMax = (int)s[i++];
		}
		private void ApplyPhase(NQMasterPropMode mode, bool quiet)
		{
			PropMode = mode; RestorePreset(presetSnap); presetQuiet = quiet; ApplyPreset(); presetQuiet = false;
		}
		// firm rules per preset (research: acct1c_lib.py / smallacct_life2.py / month80.py / mffu_rapid.py / prop_wf.py FIRMS; list prices)
		private PropCycle FirmRules()
		{
			PropCycle p = new PropCycle();
			switch (PropPreset)
			{
				case NQMasterPropPreset.Lucid25K: p.Firm = "Lucid Flex 25K"; p.Model = 0; p.Q = 100; p.Cap1 = p.Cap2 = 1000; p.Fee = 89; break;
				case NQMasterPropPreset.Lucid50K: p.Firm = "Lucid Flex 50K"; p.Model = 0; p.Q = 150; p.Cap1 = p.Cap2 = 2000; p.Fee = 146; break;
				case NQMasterPropPreset.Lucid150K: p.Firm = "Lucid Flex 150K"; p.Model = 0; p.Q = 250; p.Cap1 = p.Cap2 = 3000; p.Fee = 285; break;
				case NQMasterPropPreset.LucidPro25K: p.Firm = "Lucid Pro 25K"; p.Model = 1; p.Cap1 = 1000; p.Cap2 = 1500; p.Fee = 123; break;
				case NQMasterPropPreset.LucidPro50K: p.Firm = "Lucid Pro 50K"; p.Model = 1; p.Cap1 = 2000; p.Cap2 = 2500; p.Fee = 192; break;
				case NQMasterPropPreset.FundedNext25K: p.Firm = "FundedNext Rapid Pro 25K (aprox.)"; p.Model = 1; p.Cap1 = p.Cap2 = 1200; p.Fee = 80; break;
				case NQMasterPropPreset.Mffu50K: case NQMasterPropPreset.Mffu50KLadder: p.Firm = "MFFU Rapid EOD 50K"; p.Model = 2; p.NpMax = 0; p.MinDays = 4; p.Fee = 157; break;
				default: return null;
			}
			if (EvalPrice > 0) p.Fee = EvalPrice;
			p.Act = ActivationFee;
			return p;
		}
		private void CycleInit()
		{
			realMode = PropMode; presetSnap = SnapPreset(); cy = null; cyOn = false;
			if (!CycleSim || PropMode == NQMasterPropMode.Off || PropPreset == NQMasterPropPreset.Manual || FirmRules() == null) { ApplyPreset(); return; }
			cy = FirmRules();
			ApplyPhase(NQMasterPropMode.Funded, false);			// funded rule values (payout level) for the engine, printed once
			double fundedPayoutAt = FundedPayoutAt;
			cy.D = PropTrailingDD; cy.Buf = PropTrailingDD + 100;
			if (cy.Model == 0) cy.X = FundedPayoutAt;
			else if (cy.Model == 1) cy.X = Math.Max(500, FundedPayoutAt - cy.Buf);
			else cy.X = FundedPayoutAt - 500;                   // MFFU: request at FundedPayoutAt, keep FundedPayoutAt - 500
			ApplyPhase(NQMasterPropMode.Eval, false);
			cy.T = EvalTarget; cy.Cons = ConsistencyPct / 100.0;
			cyOn = true;
			Print(string.Format("NQMaster | CICLO DE CUENTA ({0}): eval ${1:0} objetivo, drawdown ${2:0}, consistencia {3:0}%, precio eval ${4:0}; fondeada: retiro con ganancia >= ${5:0}. La primera eval empieza al terminar el calentamiento.",
				cy.Firm, cy.T, cy.D, ConsistencyPct, cy.Fee, fundedPayoutAt));
		}
		private void CyEvent(DateTime day, string s)
		{
			cyEvents.Add(day.ToString("dd-MM-yy", CultureInfo.InvariantCulture) + "  " + s);
			if (cyEvents.Count > 400) cyEvents.RemoveAt(0);
			Log("CICLO: " + s);
		}
		private void CyStart(bool funded, DateTime day)
		{
			ApplyPhase(funded ? NQMasterPropMode.Funded : NQMasterPropMode.Eval, true);
			cyBase = netPnl; cy.Start(funded); cyStarted = true;
			propPeak = StartBalance; propDayStart = double.NaN; propBestDay = 0; targetHit = false;
			if (funded) { cyFundN++; cyFeeAct += cy.Act; CyEvent(day, string.Format("Fondeada #{0} activada{1}", cyFundN, cy.Act > 0 ? " (" + Usd(cy.Act) + ")" : "")); }
			else { cyEvalN++; cyFeeEval += cy.Fee; CyEvent(day, string.Format("Eval #{0} comprada ({1})", cyEvalN, Usd(cy.Fee))); }
			if (cyFirst == DateTime.MinValue) cyFirst = day;
		}
		// first bar of a session, before PropSessionStart(): close the last day, then start what is pending
		private void CycleSessionStart(DateTime tradeDay)
		{
			if (!cyOn) return;
			cyHalt = false; cyLastDay = tradeDay; cyWaitPrev = cyWaitNow; cyWaitNow = false;
			if (cyStarted && cy.Alive && cyPrevTradable)	// review L7: FOMC / low-ATR / skipped sessions are not account days (research day lists skip them)
			{
				DateTime prev = cyPrevDay == DateTime.MinValue ? tradeDay : cyPrevDay;
				double amt = cy.DayClose(netPnl - cyBase);
				if (amt > 0)
				{
					cyPayN++; cyPayGross += amt; cyPayCash += cy.Split * amt;
					CyEvent(prev, string.Format("RETIRO #{0} de la fondeada #{1}: {2} (cobrás {3})", cy.Pays, cyFundN, Usd(amt), Usd(cy.Split * amt)));
				}
				if (!cy.Alive) { cyFuDone++; cyNext = 1; cyWait = 0; CyEvent(prev, string.Format("Fondeada #{0} COMPLETADA ({1} retiros: pasa a cuenta real); nueva eval", cyFundN, cy.Pays)); }
			}
			if (!cyStarted) { if (rthDaysSeen >= WarmupDays && atrCount >= AtrMin) CyStart(false, tradeDay); else { cyHalt = true; cyStatus = "calentamiento: la primera eval empieza al completarlo"; } }
			else if (!cy.Alive && cyNext != 0)
			{
				if (cyWaitPrev && cyPrevTradable && cyWait > 0) cyWait--;
				if (cyWait > 0) { cyHalt = true; cyWaitNow = true; cyStatus = "eval aprobada: esperando los días mínimos de la firma"; }
				else { bool f = cyNext == 2; cyNext = 0; CyStart(f, tradeDay); }
			}
			cyPrevDay = tradeDay;
		}
		private DateTime cyPrevDay = DateTime.MinValue; private bool cyPrevTradable = true, cyWaitPrev, cyWaitNow;
		// every 1-minute bar: account lost (equity incl. the open position at the bar's adverse extreme <= threshold) or eval target reached
		private void CycleBar()
		{
			if (!CyLive || cyHalt) return;
			double raw = netPnl - cyBase, oc = 0, ol = 0;
			if (Position.MarketPosition != MarketPosition.Flat)
			{
				try
				{
					oc = Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Closes[0][0]);
					ol = Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Position.MarketPosition == MarketPosition.Long ? Lows[0][0] : Highs[0][0]);
				}
				catch { }
			}
			int r = cy.Bar(raw + Math.Min(ol, oc), raw + oc);
			if (r == 0) return;
			cyHalt = true; DateTime day = cyLastDay == DateTime.MinValue ? Times[0][0].Date : cyLastDay;
			if (r == -1)
			{
				FlattenAll("SIM: cuenta perdida");
				if (cy.Funded) { cyFuBust++; CyEvent(day, string.Format("Fondeada #{0} PERDIDA (día {1}, {2} retiros cobrados); mañana se compra otra eval", cyFundN, cy.Days + 1, cy.Pays)); }
				else { cyEvBust++; CyEvent(day, string.Format("Eval #{0} PERDIDA (día {1}); mañana se compra otra", cyEvalN, cy.Days + 1)); }
				cyNext = 1; cyWait = 0; cyStatus = "cuenta perdida: nueva eval en la próxima sesión";
			}
			else
			{
				FlattenAll("SIM: objetivo de la eval");
				cyEvPass++; cyNext = 2; cyWait = Math.Max(0, cy.MinDays - (cy.Days + 1));
				CyEvent(day, string.Format("Eval #{0} APROBADA en {1} días", cyEvalN, cy.Days + 1));
				cyStatus = "eval aprobada: la fondeada empieza en la próxima sesión";
			}
		}
		// go-live: a real prop account is the truth -> freeze the simulation, back to the account's real phase and preset values
		private void CycleGoLive()
		{
			if (!cyOn || SimAccount) return;
			cyOn = false; cyFrozen = true; cyFrozenAt = cyLastDay; cyHalt = false; cyStatus = "";	// review H1: a simulated halt never blocks the real account
			ApplyPhase(realMode, false); targetHit = false;
		}

		// ---- performance statistics for the dashboard (closed trades, as NinjaTrader books them: net of commission when a commission
		// template is set)
		private double statPeak, statMaxDd, statComm, statBestDay = double.NaN, statWorstDay = double.NaN; private int statDays, statGreenDays, statDayTrades0;
		private DateTime statFirst = DateTime.MinValue, statLast = DateTime.MinValue;
		private double liveStartPnl = double.NaN; private int liveStartTrades, liveDays, histDays; private DateTime liveStart;
		private void StatTrade(double pnl, double comm, DateTime t)
		{
			statComm += comm; if (statFirst == DateTime.MinValue) statFirst = t; statLast = t;
			if (netPnl > statPeak) statPeak = netPnl;
			statMaxDd = Math.Max(statMaxDd, statPeak - netPnl);
		}
		private int statQty = 1; private bool statDayHalted; private double histUnitSum, liveExpect;
		// review M5: the live expectation is the history's P&L per base contract per tradable day (simulation halts excluded) x the live size
		private void StatDayClose()
		{
			double d = netPnl - dayStartPnl; bool traded = totalTrades != statDayTrades0; statDayTrades0 = totalTrades;
			if (traded)
			{
				statDays++; if (d > 0) statGreenDays++;
				statBestDay = double.IsNaN(statBestDay) ? d : Math.Max(statBestDay, d); statWorstDay = double.IsNaN(statWorstDay) ? d : Math.Min(statWorstDay, d);
			}
			if (statFirst == DateTime.MinValue || statDayHalted) return;
			if (double.IsNaN(liveStartPnl)) { histUnitSum += d / Math.Max(1, statQty); histDays++; }
			else { liveDays++; liveExpect += (histDays > 0 ? histUnitSum / histDays : 0) * Math.Max(1, statQty); }
		}
		private static string Usd(double v)
		{
			string s = Math.Abs(v).ToString("#,0", CultureInfo.InvariantCulture).Replace(',', '.');
			return (v < -0.5 ? "-$" : "$") + s;
		}
		private static string Pct(double v) { return v.ToString("0.0", CultureInfo.InvariantCulture).Replace('.', ',') + "%"; }
		private static string Dec(double v) { return v.ToString("0.00", CultureInfo.InvariantCulture).Replace('.', ','); }
		private string PhaseName(NQMasterPropMode m) { return m == NQMasterPropMode.Eval ? "Evaluación" : m == NQMasterPropMode.Funded ? "Fondeada" : "Off"; }
		// ---- dashboard (2026-10-21 redesign): top right = system and performance, top left = account (simulated cycle and/or the real
		// account), bottom left = warnings. Spanish, $ with thousands dots. Drawn on the last historical bars and on every live bar.
		private const string DashLine = "────────────────────────────────────────────────";
		private void UpdateDashboard()
		{
			if (!ShowDashboard || (State == State.Historical && CurrentBars[0] < Count - 2)) return;
			Draw.TextFixed(this, "NQM_Dash", DashSystem(), TextPosition.TopRight, Brushes.White, dashFont, Brushes.Transparent, Brushes.Black, 80);
			string acct = DashAccount();
			if (acct.Length > 0) Draw.TextFixed(this, "NQM_Acct", acct, TextPosition.TopLeft, Brushes.White, dashFont, Brushes.Transparent, Brushes.Black, 80);
			string warn = DashWarnings();
			if (warn.Length > 0) Draw.TextFixed(this, "NQM_Warn", warn, TextPosition.BottomLeft, Brushes.Orange, dashFont, Brushes.Transparent, Brushes.Black, 80);
			else RemoveDrawObject("NQM_Warn");
		}
		private string DashSystem()
		{
			StringBuilder b = new StringBuilder();
			double pf = grossLoss > 0 ? grossWin / grossLoss : 0;
			string mode = State == State.Realtime ? (SimAccount ? "EN VIVO (simulación)" : "EN VIVO") : "BACKTEST";
			b.AppendLine(string.Format("NQMASTER  ·  {0}  ·  {1}  ·  {2}", Profile, Instrument != null ? Instrument.FullName : "", mode));
			b.AppendLine("Estado: " + StatusEs());
			b.AppendLine(string.Format("Tendencia {0}  ·  ATR diario {1}  ·  día de pullback: {2}", trendDir == 1 ? "ALCISTA" : trendDir == -1 ? "BAJISTA" : "-",
				double.IsNaN(todayAtr) ? "-" : todayAtr.ToString("0"), pullbackDay ? "sí" : "no"));
			StringBuilder mm = new StringBuilder(); int n = 0;
			foreach (Mod m in mods) if (m.On) { mm.Append(m.Sig + (m.InTrade ? "●" : Working(m.Entry) ? "○" : "") + " "); if (++n % 9 == 0) mm.Append("\n         "); }
			b.AppendLine("Módulos: " + mm.ToString().TrimEnd() + "   (● en posición, ○ orden puesta)");
			b.AppendLine(DashLine);
			b.AppendLine(string.Format("RENDIMIENTO{0}", statFirst != DateTime.MinValue ? "  desde " + statFirst.ToString("dd-MM-yy", CultureInfo.InvariantCulture) : ""));
			if (totalTrades == 0) b.AppendLine("Sin trades todavía" + (rthDaysSeen < WarmupDays ? string.Format(" (calentamiento {0}/{1} días)", rthDaysSeen, WarmupDays) : ""));
			else
			{
				double months = statFirst != DateTime.MinValue ? Math.Max(1.0, (statLast - statFirst).TotalDays / 30.44) : 1;
				b.AppendLine(string.Format("Trades {0}  ·  Ganadoras {1}  ·  Factor de beneficio {2}", totalTrades, Pct(100.0 * totalWins / totalTrades), grossLoss > 0 ? Dec(pf) : "sin pérdidas"));
				b.AppendLine(string.Format("Neto {0}  ·  por trade {1}  ·  por mes {2}", Usd(netPnl), Usd(netPnl / totalTrades), Usd(netPnl / months)));
				b.AppendLine(string.Format("Caída máxima {0}  ·  días positivos {1}", Usd(statMaxDd), statDays > 0 ? Pct(100.0 * statGreenDays / statDays) : "-"));
				if (statDays > 0) b.AppendLine(string.Format("Mejor día {0}  ·  peor día {1}", Usd(statBestDay), Usd(statWorstDay)));
				b.AppendLine(statComm > 0.005 ? string.Format("Comisiones incluidas ({0})  ·  deslizamiento {1} tick", Usd(statComm), Slippage)
					: "SIN comisiones: resultado optimista (cargar $1,90 por contrato ida y vuelta)");
			}
			if (EdgeMonitor && !double.IsNaN(edgeH) && edgeH > 0)
				b.AppendLine(string.Format("Monitor de borde: {0} de la alarma ({1} días){2}", Pct(100 * edgeS / edgeH), edgeDays,
					edgeFbLeft > 0 ? string.Format("  ·  MODO DEFENSIVO {0} días", edgeFbLeft) : edgeAlarm ? "  ·  ALARMA" : 100 * edgeS / edgeH >= 35 ? "  ·  AVISO" : "  ·  OK"));
			if (!double.IsNaN(liveStartPnl))
			{
				int lt = totalTrades - liveStartTrades; double lp = netPnl - liveStartPnl;
				double exp = liveExpect;
				b.AppendLine(DashLine);
				b.AppendLine(string.Format("EN VIVO desde {0}: {1} sesiones, {2} trades, {3}", liveStart.ToString("dd-MM-yy", CultureInfo.InvariantCulture), liveDays, lt, Usd(lp)));
				if (liveDays > 0) b.AppendLine(string.Format("Esperado por el backtest para {0} sesiones: {1}{2}", liveDays, Usd(exp),
					liveDays < 40 ? "  (menos de 40 sesiones: todavía es ruido)" : lp >= 0.5 * exp ? "  ·  rinde" : "  ·  rinde POR DEBAJO"));
			}
			return b.ToString().TrimEnd();
		}
		private string StatusEs()
		{
			switch (status)
			{
				case "trading": return "operando";
				case "waiting": return "esperando datos";
				default: return status;
			}
		}
		private string DashAccount()
		{
			StringBuilder b = new StringBuilder();
			if (cy != null && (cyOn || cyFrozen))
			{
				double months = cyFirst != DateTime.MinValue ? Math.Max(1.0, (cyLastDay - cyFirst).TotalDays / 30.44) : 1;
				double fees = cyFeeEval + cyFeeAct, net = cyPayCash - fees;
				b.AppendLine(string.Format("SIMULACIÓN DE CUENTA  ·  {0}{1}", cy.Firm, cyFrozen ? "  (backtest hasta " + cyFrozenAt.ToString("dd-MM-yy", CultureInfo.InvariantCulture) + ")" : ""));
				b.AppendLine("Regla: si se pierde una cuenta, se compra otra eval al día siguiente");
				b.AppendLine(DashLine);
				b.AppendLine(string.Format("Evals compradas   {0,3}   aprobadas {1,3} ({2})   perdidas {3,3}", cyEvalN, cyEvPass, cyEvalN > 0 ? Pct(100.0 * cyEvPass / Math.Max(1, cyEvPass + cyEvBust)) : "-", cyEvBust));
				b.AppendLine(string.Format("Fondeadas         {0,3}   perdidas  {1,3}          completadas {2}", cyFundN, cyFuBust, cyFuDone));
				b.AppendLine(string.Format("Retiros           {0,3}   pedidos {1}   cobrados {2} ({3:0}%)", cyPayN, Usd(cyPayGross), Usd(cyPayCash), cy.Split * 100));
				b.AppendLine(string.Format("Costos            evals {0}{1}", Usd(cyFeeEval), cyFeeAct > 0 ? "  +  activaciones " + Usd(cyFeeAct) : ""));
				b.AppendLine(string.Format("RESULTADO NETO    {0}   ≈ {1} por mes  ({2} meses)", Usd(net), Usd(net / months), months.ToString("0.0", CultureInfo.InvariantCulture).Replace('.', ',')));
				b.AppendLine(DashLine);
				if (!cyStarted) b.AppendLine(string.Format("La primera eval empieza al terminar el calentamiento ({0}/{1} días)", rthDaysSeen, WarmupDays));
				else if (cyFrozen) b.AppendLine("Simulación congelada al pasar a vivo: la cuenta real se muestra abajo");
				else if (cy.Alive)
				{
					double prof = netPnl - cyBase - cy.Withdrawn, bal = StartBalance + prof;
					if (!cy.Funded)
						b.AppendLine(string.Format("Cuenta actual: EVAL #{0}  ·  día {1}  ·  ganancia {2} de {3}", cyEvalN, cy.Days + 1, Usd(prof), Usd(cy.T)));
					else
						b.AppendLine(string.Format("Cuenta actual: FONDEADA #{0}  ·  día {1}  ·  retiros {2}", cyFundN, cy.Days + 1, cy.Pays));
					b.AppendLine(string.Format("Saldo {0}  ·  límite de pérdida {1}  ·  colchón {2}", Usd(bal), Usd(StartBalance + cy.Thr), Usd(prof - cy.Thr)));
					if (!cy.Funded && cy.Cons > 0 && cy.Bal > 0 && cy.Best > cy.Cons * Math.Max(cy.T, cy.Bal))
						b.AppendLine(string.Format("Consistencia: el mejor día ({0}) obliga a llegar a {1}", Usd(cy.Best), Usd(cy.Best / cy.Cons)));
					if (cy.Funded) b.AppendLine("Próximo retiro: " + cy.NextPayout(Usd));
				}
				else b.AppendLine("Cuenta actual: " + (cyStatus.Length > 0 ? cyStatus : "-"));
				int k = Math.Min(8, cyEvents.Count);
				if (k > 0)
				{
					b.AppendLine("Últimos eventos:");
					for (int i = cyEvents.Count - 1; i >= cyEvents.Count - k; i--) b.AppendLine("  " + cyEvents[i]);
				}
			}
			else if (PropMode != NQMasterPropMode.Off && cy == null && State != State.Realtime)
				b.AppendLine(PropPreset == NQMasterPropPreset.Manual ? "Para simular retiros y cuentas perdidas elegí un preset de firma (Lucid, MFFU...)"
					: "Simulación del ciclo apagada (Backtest: simular el ciclo = false)");
			// the real prop account (live, not a Sim account)
			if (State == State.Realtime && !SimAccount && PropMode != NQMasterPropMode.Off && !double.IsNaN(propThr))
			{
				if (b.Length > 0) b.AppendLine(DashLine);
				double eq = PropEquity();
				b.AppendLine(string.Format("CUENTA REAL  ·  {0}  ·  {1}", Account != null ? Account.Name : "", PhaseName(PropMode)));
				b.AppendLine(string.Format("Saldo {0} ({1})  ·  límite {2}  ·  colchón {3}", Usd(eq), Usd(eq - StartBalance), Usd(propThr), Usd(eq - propThr)));
				if (!double.IsNaN(propDayStart)) b.AppendLine("Hoy: " + Usd(eq - propDayStart));
				if (eq <= propThr) b.AppendLine("ATENCIÓN: el saldo está en el límite: verificá la cuenta en la firma");
				if (PropMode == NQMasterPropMode.Eval && EvalTarget > 0) b.AppendLine(string.Format("Objetivo: {0} de {1}", Usd(eq - StartBalance), Usd(EvalTarget)));
				if (PropMode == NQMasterPropMode.Funded) b.AppendLine((eq - StartBalance >= FundedPayoutAt ? "RETIRO DISPONIBLE: " : "Retiro: ") + payoutHint);
			}
			return b.ToString().TrimEnd();
		}
		private string DashWarnings()
		{
			StringBuilder b = new StringBuilder();
			if (zombieCount > 0) b.AppendLine(string.Format("! {0} órdenes trabadas descartadas (ver Output)", zombieCount));
			if (capCuts > 0) b.AppendLine(string.Format("! Tope de {0} contratos abiertos: {1} entradas recortadas", MaxOpenContracts, capCuts));
			if (shortSession) b.AppendLine(string.Format("! Sesión corta: cierra {0:00}:{1:00} ET", sessEndMin / 60, sessEndMin % 60));
			if (edgeAlarm) b.AppendLine("! ALARMA del monitor de borde: revisar antes de seguir");
			if (State == State.Realtime && (atrCount < AtrMin || rthDaysSeen < WarmupDays)) b.AppendLine(string.Format("! Calentamiento incompleto: {0}/{1} días (cargar 45+ días)", rthDaysSeen, WarmupDays));
			if (State == State.Realtime && SimAccount && PropMode != NQMasterPropMode.Off) b.AppendLine(cyOn ? "Cuenta de simulación con el ciclo corriendo: no guardes el template mientras corre (la fase cambia sola)" : "Cuenta de simulación: el saldo es una cuenta nueva desde que pasó a vivo, no el de Sim101");
			if (RiskCapPerContract > 0 && PropMode != NQMasterPropMode.Off && riskSkips > 0) b.AppendLine(string.Format("Tope de riesgo {0}/contrato: {1} trades salteados con colchón chico", Usd(RiskCapPerContract), riskSkips));
			return b.ToString().TrimEnd();
		}
		#endregion

		#region Order-flow boost
		// ---- order-flow size boost (EXPERIMENTAL, default off). research/mine/of_trades.py + of_boost.py, Databento NQ trades
		// 2026-04-01..10-08 (645 Ultra trades, real NQ futures): session cumulative delta = (aggressor buy - sell volume since 18:00 ET)
		// / session volume, oriented with the trade, measured when the entry fills. Top 20% (>= 0.015): PF 4.81 IS (Apr-Jun) / 3.22 OOS
		// (Jul-Oct) vs 1.83 / 1.13 for the rest; x2 on those (never above 2x the base size): $ +32%, PF 1.43 -> 1.54, max DD +8%.
		// NOT statistically significant (1 of ~30 order-flow cells tested, rank correlation 0.06): treat it as a test, not an edge.
		// FAILED OUT OF SAMPLE (research/mine/of_validate.py, 11 new months of NQ trades 2025-05..2026-03, 1,207 Ultra trades, rule unchanged):
		// boosted trades avg $19.0 / PF 1.49 vs $19.4 / PF 1.42 for the rest, rank correlation -0.02, better in 6 of 11 months; the extra $
		// is only the larger size (PF 1.43 -> 1.45, max DD +9%). MNQ's own flow agreed with NQ's on 70% of the decisions (Sep 2025). KEEP OFF.
		// Aggressor side from the tick stream as OrderFlowRecorder.cs: trade at/above the ask = buy, at/below the bid = sell, otherwise
		// tick rule. Historical runs need Tick Replay; a session joined mid-way (no Tick Replay history) never boosts until the next
		// 18:00 ET start. Market entries use the delta at the bar close before the fill (= research); resting stop / limit entries
		// (ORB, VOLB, ENG10, LON, ICT) are re-sized every 1-minute bar until they fill.
		private double ofBuy, ofSell, ofLastPx = double.NaN, ofBid = double.NaN, ofAsk = double.NaN;
		private int ofLastDir = 1, ofSessDay = -1, ofBoosted, ofEntries; private bool ofSessFull; private long ofMinKey = -1, ofTicks;
		protected override void OnMarketData(MarketDataEventArgs e)
		{
			if (!UseOrderFlowBoost || BarsInProgress != 0) return;
			if (e.MarketDataType == MarketDataType.Bid) { ofBid = e.Price; return; }
			if (e.MarketDataType == MarketDataType.Ask) { ofAsk = e.Price; return; }
			if (e.MarketDataType != MarketDataType.Last) return;
			long mk = e.Time.Ticks / TimeSpan.TicksPerMinute;
			if (mk != ofMinKey)
			{
				ofMinKey = mk;
				DateTime sd = ToEt(e.Time).AddHours(6);					// session date: 18:00 ET starts the next day's session
				int key = sd.Year * 10000 + sd.Month * 100 + sd.Day;
				if (key != ofSessDay) { ofSessFull = ofSessDay > 0; ofSessDay = key; ofBuy = 0; ofSell = 0; }
			}
			double b = e.Bid > 0 ? e.Bid : ofBid, a = e.Ask > 0 ? e.Ask : ofAsk, px = e.Price;
			int dir;
			if (!double.IsNaN(a) && a > 0 && px >= a) dir = 1;
			else if (!double.IsNaN(b) && b > 0 && px <= b) dir = -1;
			else if (!double.IsNaN(ofLastPx) && px > ofLastPx) dir = 1;
			else if (!double.IsNaN(ofLastPx) && px < ofLastPx) dir = -1;
			else dir = ofLastDir;
			ofLastPx = px; ofLastDir = dir; ofTicks++;
			if (dir == 1) ofBuy += e.Volume; else ofSell += e.Volume;
		}
		private double OfCvd() { return (ofSessFull && ofBuy + ofSell > 0) ? (ofBuy - ofSell) / (ofBuy + ofSell) : double.NaN; }
		private bool OfAgrees(int d) { double c = OfCvd(); return !double.IsNaN(c) && d * c >= OrderFlowCvdMin; }
		// size after the boost; q = the module's size before it (already including context / confluence / ICT x2)
		private int OfQty(int q, int d, string who)
		{
			if (!UseOrderFlowBoost || q <= 0 || noBoost || OrderFlowBoost <= 1 || !OfAgrees(d)) return q;
			int nq = OrderFlowStack ? q * OrderFlowBoost : Math.Max(q, Qty() * OrderFlowBoost);
			if (nq != q && who != null) Log(string.Format("{0} order-flow x{1}: session delta {2:+0.000;-0.000} with the trade -> {3} contracts", who, OrderFlowBoost, d * OfCvd(), nq));
			return nq;
		}
		private int OfApply(Mod m, int q, int d)
		{
			m.OfQ0 = q; if (m.RejToday >= 2) return 0;
			int f = CapQty(m, m.Sig, OfQty(q, d, m.Sig));
			if (f != q || q != Qty()) Log(string.Format("SIZE {0} {1}: base {2} -> requested {3} (multipliers / boosts) -> sent {4}{5}", m.Sig, d == 1 ? "BUY" : "SELL", Qty(), q, f,
				f < q ? " (capped: max open contracts / order flow)" : ""));
			return f;
		}
		// resting stop / limit entries follow the delta until they fill (one size change per 1-minute bar at most)
		private void OfRefresh()
		{
			foreach (Mod m in mods)
			{
				Order e = m.Entry;
				if (e == null || m.InTrade || m.OfQ0 <= 0 || e.Filled > 0 || zombies.Contains(e) || m.OfNoChange == e) continue;
				if (e.OrderState != OrderState.Working && e.OrderState != OrderState.Accepted) continue;
				if (m.OfChangeOrd == e && m.OfWant != e.Quantity)
				{
					if (CurrentBars[0] - m.OfChangeBar < 2) continue;		// change still in flight
					m.OfNoChange = e; Log(string.Format("{0} order-flow re-size was not applied by NinjaTrader: this order keeps {1} contracts", m.Sig, e.Quantity)); continue;
				}
				if (e.OrderType != OrderType.StopMarket && e.OrderType != OrderType.Limit) continue;
				int d = e.OrderAction == OrderAction.Buy ? 1 : -1;
				int want = OfQty(m.OfQ0, d, null);
				if (want == e.Quantity) continue;
				int was = e.Quantity;
				try { m.OfChangeOrd = e; m.OfChangeBar = CurrentBars[0]; m.OfWant = want; ChangeOrder(e, want, e.LimitPrice, e.StopPrice); Log(string.Format("{0} resting entry re-sized {1} -> {2} (session delta {3:+0.000;-0.000} with the trade)", m.Sig, was, want, d * OfCvd())); }
				catch (Exception ex) { m.OfNoChange = e; Log(m.Sig + " order-flow re-size failed: " + ex.Message); }
			}
		}
		private string OfStatus()
		{
			if (ofTicks == 0) return "Order flow boost: NO TICK DATA (backtest: enable Tick Replay)";
			if (!ofSessFull) return "Order flow boost: waiting for the next 18:00 ET session (joined mid-session)";
			double c = OfCvd();
			return string.Format("Order flow: session delta {0:+0.000;-0.000} ({1:N0} contracts) | x{2} for {3} >= {4:0.000} | boosted {5}/{6}",
				c, ofBuy + ofSell, OrderFlowBoost, double.IsNaN(c) ? "-" : c >= OrderFlowCvdMin ? "LONGS" : c <= -OrderFlowCvdMin ? "SHORTS" : "none", OrderFlowCvdMin, ofBoosted, ofEntries);
		}
		#endregion

		#region Properties
		[NinjaScriptProperty][Display(Name = "Control: posición de la cuenta = posición de la estrategia", Order = 9, GroupName = "03. Operación y seguridad")] public bool AccountSyncGuard { get; set; }
		[NinjaScriptProperty][Display(Name = "No operar feriados ni medias jornadas", Order = 7, GroupName = "03. Operación y seguridad")] public bool SkipShortSessions { get; set; }
		[NinjaScriptProperty][Range(0, 500)][Display(Name = "Máximo de contratos abiertos en la cuenta (0 = sin tope)", Order = 15, GroupName = "02. Reglas de la cuenta (las completa el preset)")] public int MaxOpenContracts { get; set; }
		[NinjaScriptProperty][Display(Name = "Frenar entradas desde la fecha de roll del contrato", Order = 8, GroupName = "03. Operación y seguridad")] public bool RollGuard { get; set; }
		[NinjaScriptProperty][Display(Name = "Guardar log en archivo (Documentos\\NinjaTrader 8\\nqmaster_logs)", Order = 12, GroupName = "03. Operación y seguridad")] public bool LogToFile { get; set; }
		[NinjaScriptProperty][Display(Name = "Reporte por módulo en Output (ganadoras / PF / neto)", Order = 7, GroupName = "04. Monitor y revisión")] public bool ModuleHealthReport { get; set; }
		[NinjaScriptProperty][Display(Name = "Apagar módulos (lista separada por comas, ej. REV06)", Order = 8, GroupName = "04. Monitor y revisión")] public string DisableModules { get; set; }
		[NinjaScriptProperty][Display(Name = "Alarma si un módulo o una dirección deja de operar", Order = 6, GroupName = "04. Monitor y revisión")] public bool InactivityAlarm { get; set; }
		[NinjaScriptProperty][Display(Name = "Control entre cuentas de la misma firma (prohibido el hedge)", Order = 10, GroupName = "03. Operación y seguridad")] public bool CrossAccountGuard { get; set; }
		[NinjaScriptProperty][Display(Name = "Grupo de cuentas para ese control (uno por firma; vacío = automático)", Order = 11, GroupName = "03. Operación y seguridad")] public string HedgeGroup { get; set; }
		[Browsable(false)] public double MinStopAtr { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Tope de riesgo por trade $ por contrato (activo con colchón chico)", Order = 12, GroupName = "02. Reglas de la cuenta (las completa el preset)")] public double RiskCapPerContract { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Eval: tope de riesgo activo con colchón < $", Order = 13, GroupName = "02. Reglas de la cuenta (las completa el preset)")] public double EvalRiskCapCushion { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Fondeada: tope de riesgo activo con colchón < $", Order = 14, GroupName = "02. Reglas de la cuenta (las completa el preset)")] public double FundedRiskCapCushion { get; set; }
		[NinjaScriptProperty][Display(Name = "Perfil (Ultra = recomendado)", Order = 1, GroupName = "01. Perfil y cuenta")] public NQMasterProfile Profile { get; set; }
		[NinjaScriptProperty][Display(Name = "Backtest: simular el ciclo (eval, fondeada, retiros, cuentas perdidas, recompra al día siguiente)", Order = 4, GroupName = "01. Perfil y cuenta")] public bool CycleSim { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Precio pagado por cada eval $ (0 = precio de lista; poné el precio con cupón)", Order = 5, GroupName = "01. Perfil y cuenta")] public double EvalPrice { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Costo de activación de la fondeada $", Order = 6, GroupName = "01. Perfil y cuenta")] public double ActivationFee { get; set; }
		[NinjaScriptProperty][Display(Name = "ORB60 activo", Order = 1, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseOrb { get; set; }
		[NinjaScriptProperty][Range(15, 120)][Display(Name = "ORB: minutos del rango (Custom)", Order = 2, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public int OrbRangeMin { get; set; }
		[NinjaScriptProperty][Range(0.2, 5.0)][Display(Name = "ORB: objetivo en R (Custom)", Order = 3, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public double OrbTargetR { get; set; }
		[NinjaScriptProperty][Display(Name = "ORB: solo días de pullback (Custom)", Order = 4, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool OrbPullbackFilter { get; set; }
		[NinjaScriptProperty][Display(Name = "MSEQ activo", Order = 6, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseMseq { get; set; }
		[NinjaScriptProperty][Display(Name = "CRT11 activo", Order = 8, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseCrt { get; set; }
		[NinjaScriptProperty][Display(Name = "MOM11 activo", Order = 9, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseMom11 { get; set; }
		[NinjaScriptProperty][Display(Name = "MOM13 activo", Order = 10, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseMom13 { get; set; }
		[NinjaScriptProperty][Display(Name = "MOM1030 activo", Order = 11, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseMom1030 { get; set; }
		[NinjaScriptProperty][Display(Name = "ON07 activo", Order = 12, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseOn07 { get; set; }
		[NinjaScriptProperty][Display(Name = "REV06 activo", Order = 13, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseRev06 { get; set; }
		[NinjaScriptProperty][Display(Name = "LON (Londres) activo", Order = 14, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseLon { get; set; }
		[NinjaScriptProperty][Display(Name = "ICT activo", Order = 15, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseIct { get; set; }
		[Browsable(false)] public bool UseMom1130 { get; set; }
		[Browsable(false)] public bool UseRsi2 { get; set; }
		[NinjaScriptProperty][Display(Name = "ORB90 activo", Order = 5, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseOrb90 { get; set; }
		[NinjaScriptProperty][Display(Name = "MSEQS activo", Order = 7, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseMseqShort { get; set; }
		[NinjaScriptProperty][Display(Name = "LATE15 activo", Order = 18, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseLate15 { get; set; }
		[Browsable(false)] public bool UseEng10 { get; set; }
		[NinjaScriptProperty][Display(Name = "Módulos de 6 años (SO04 RV11 ORFAIL CAM3)", Order = 23, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool SixYearModules { get; set; }
		[Browsable(false)] public bool UseCa04v { get; set; }
		[NinjaScriptProperty][Display(Name = "SO04 activo", Order = 24, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseSo04 { get; set; }
		[Browsable(false)] public bool UseGd03 { get; set; }
		[NinjaScriptProperty][Display(Name = "RV11 activo", Order = 25, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseRv11 { get; set; }
		[Browsable(false)] public bool UseEng26 { get; set; }
		[NinjaScriptProperty][Display(Name = "ORFAIL activo", Order = 26, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseOrFail { get; set; }
		[NinjaScriptProperty][Display(Name = "CAM3 activo", Order = 27, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseCam3 { get; set; }
		[Browsable(false)] public bool UseLateFh { get; set; }
		[Browsable(false)] public bool Vw13Wide { get; set; }
		[NinjaScriptProperty][Display(Name = "NF05 activo", Order = 19, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseNf05 { get; set; }
		[Browsable(false)] public bool UseLf0315 { get; set; }
		[NinjaScriptProperty][Display(Name = "LF06 activo", Order = 20, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseLf06 { get; set; }
		[NinjaScriptProperty][Display(Name = "LF0430 activo", Order = 21, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseLf0430 { get; set; }
		[NinjaScriptProperty][Display(Name = "WR70Plus: incluir los módulos nocturnos NF05 / LF06 / LF0430", Order = 8, GroupName = "01. Perfil y cuenta")] public bool NightOnWr70 { get; set; }
		[NinjaScriptProperty][Display(Name = "CPI09 (días de CPI) activo", Order = 22, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseCpi09 { get; set; }
		[NinjaScriptProperty][Display(Name = "Fechas CPI extra (yyyy-MM-dd)", Order = 2, GroupName = "05. Calendario (fechas extra)")] public string CpiDates { get; set; }
		[Browsable(false)] public int Cpi09Multiplier { get; set; }
		[Browsable(false)] public int Mom1030Multiplier { get; set; }
		[Browsable(false)] public double PullbackMaxRet { get; set; }
		[Browsable(false)] public double StopCapAtr { get; set; }
		[Browsable(false)] public double OrbPriorCloseAtr { get; set; }
		[Browsable(false)] public bool VolbBreakEven { get; set; }
		[Browsable(false)] public bool MomAgreement { get; set; }
		[Browsable(false)] public int VolbTrendLastEntry { get; set; }
		[Browsable(false)] public bool VolbReArm { get; set; }
		[NinjaScriptProperty][Display(Name = "Sin posiciones ni órdenes 2 min alrededor de CPI / NFP / actas FOMC (MFFU fondeada)", Order = 3, GroupName = "03. Operación y seguridad")] public bool NewsBlackout { get; set; }
		[NinjaScriptProperty][Display(Name = "Noticias Tier-1 extra (yyyy-MM-dd HH:mm ET)", Order = 3, GroupName = "05. Calendario (fechas extra)")] public string NewsTimes { get; set; }
		[NinjaScriptProperty][Range(1, 50)][Display(Name = "Contratos por módulo (los presets lo ajustan)", Order = 7, GroupName = "01. Perfil y cuenta")] public int Contracts { get; set; }
		[NinjaScriptProperty][Range(1000, 1659)][Display(Name = "Hora de cierre de todo (ET, HHmm)", Order = 1, GroupName = "03. Operación y seguridad")] public int FlattenTime { get; set; }
		[NinjaScriptProperty][Display(Name = "No operar los días de FOMC", Order = 2, GroupName = "03. Operación y seguridad")] public bool SkipFomc { get; set; }
		[NinjaScriptProperty][Display(Name = "Fechas FOMC extra (yyyy-MM-dd, separadas por comas)", Order = 1, GroupName = "05. Calendario (fechas extra)")] public string FomcDates { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Saldo inicial $", Order = 1, GroupName = "02. Reglas de la cuenta (las completa el preset)")] public double StartBalance { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Eval: objetivo de ganancia $", Order = 3, GroupName = "02. Reglas de la cuenta (las completa el preset)")] public double EvalTarget { get; set; }
		[Browsable(false)] public double MaxDrawdown { get; set; }
		[Browsable(false)] public double DrawdownBuffer { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Cortar el día al perder $ en trades cerrados (0 = no)", Order = 10, GroupName = "02. Reglas de la cuenta (las completa el preset)")] public double DailyLossLimit { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Fondeada: cortar el día al perder $ por contrato, abierto + cerrado (0 = no)", Order = 11, GroupName = "02. Reglas de la cuenta (las completa el preset)")] public double DailyLossPerContract { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "ATR diario mínimo para operar (puntos; 150 = validado)", Order = 4, GroupName = "03. Operación y seguridad")] public double MinAtrPoints { get; set; }
		[NinjaScriptProperty][Range(2, 15)][Display(Name = "Días de calentamiento (15 = validado)", Order = 5, GroupName = "03. Operación y seguridad")] public int WarmupDays { get; set; }
		[Browsable(false)] public bool EvalMode { get; set; }
		[NinjaScriptProperty][Display(Name = "Fecha de inicio de la cuenta real (yyyy-MM-dd)", Order = 1, GroupName = "06. Recuperación (reinicio a mitad de una cuenta real)")] public string EvalStartDate { get; set; }
		[Browsable(false)] public int EvalLateDay { get; set; }
		[Browsable(false)] public double EvalLateGoal { get; set; }
		[Browsable(false)] public int EvalLateContracts { get; set; }
		[Browsable(false)] public double EvalLateMinCushion { get; set; }
		[NinjaScriptProperty][Display(Name = "Archivo de pausa manual (si existe, no abre trades)", Order = 6, GroupName = "03. Operación y seguridad")] public string PauseFile { get; set; }
		[Browsable(false)] public bool UseContextRules { get; set; }
		[NinjaScriptProperty][Display(Name = "VOLB activo", Order = 16, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseVolBreak { get; set; }
		[NinjaScriptProperty][Display(Name = "VW13 activo", Order = 17, GroupName = "08. Avanzado: módulos (perfil Custom o apagar)")] public bool UseVw13 { get; set; }
		[Browsable(false)] public bool UseConfluence { get; set; }
		[Browsable(false)] public int IctMultiplier { get; set; }
		[Browsable(false)] public bool AdaptiveSize { get; set; }
		[Browsable(false)] public int SizeHigh { get; set; }
		[Browsable(false)] public int SizeLow { get; set; }
		[Browsable(false)] public double SizeDownDrawdown { get; set; }
		[Display(Name = "Mostrar el panel", Order = 1, GroupName = "07. Panel")] public bool ShowDashboard { get; set; }
		[Display(Name = "Imprimir el log en Output", Order = 2, GroupName = "07. Panel")] public bool PrintLog { get; set; }
		[NinjaScriptProperty][Display(Name = "Monitor de borde (compara el rendimiento en vivo con el backtest)", Order = 1, GroupName = "04. Monitor y revisión")] public bool EdgeMonitor { get; set; }
		[Browsable(false)] public bool EdgeMonitorPause { get; set; }
		[NinjaScriptProperty][Display(Name = "Monitor: fecha de inicio (yyyy-MM-dd)", Order = 2, GroupName = "04. Monitor y revisión")] public string EdgeMonitorStart { get; set; }
		[Browsable(false)] public double EdgeK { get; set; }
		[Browsable(false)] public double EdgeH { get; set; }
		[NinjaScriptProperty][Display(Name = "Con alarma: modo defensivo (apaga los módulos de la revisión anual)", Order = 3, GroupName = "04. Monitor y revisión")] public bool EdgeAlarmFallback { get; set; }
		[NinjaScriptProperty][Range(1, 1000)][Display(Name = "Duración del modo defensivo (días operables; 252 = 1 año)", Order = 4, GroupName = "04. Monitor y revisión")] public int EdgeFallbackDays { get; set; }
		[NinjaScriptProperty][Display(Name = "Módulos del modo defensivo (vacío = tabla interna)", Order = 5, GroupName = "04. Monitor y revisión")] public string EdgeFallbackOff { get; set; }
		[NinjaScriptProperty][Display(Name = "Fase REAL de la cuenta en vivo (Off = sin reglas de fondeo)", Order = 3, GroupName = "01. Perfil y cuenta")] public NQMasterPropMode PropMode { get; set; }
		[NinjaScriptProperty][Display(Name = "Firma / cuenta (preset): completa saldo, drawdown, objetivo, tamaño y retiros", Order = 2, GroupName = "01. Perfil y cuenta")] public NQMasterPropPreset PropPreset { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Drawdown máximo $ (al cierre; se fija en saldo inicial + 100)", Order = 2, GroupName = "02. Reglas de la cuenta (las completa el preset)")] public double PropTrailingDD { get; set; }
		[Browsable(false)] public double EvalCushionFull { get; set; }
		[Browsable(false)] public NQMasterSafeSet EvalSafeSet { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Eval: cortar el día al perder $ (0 = no)", Order = 6, GroupName = "02. Reglas de la cuenta (las completa el preset)")] public double EvalDailyStop { get; set; }
		[Browsable(false)] public double FundedCushionSafe { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Fondeada: pedir retiro con ganancia >= $", Order = 8, GroupName = "02. Reglas de la cuenta (las completa el preset)")] public double FundedPayoutAt { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Saldo de cierre más alto hasta ahora $ (0 = automático)", Order = 3, GroupName = "06. Recuperación (reinicio a mitad de una cuenta real)")] public double PropPeakOverride { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Límite de liquidación $ (0 = automático)", Order = 4, GroupName = "06. Recuperación (reinicio a mitad de una cuenta real)")] public double PropThresholdOverride { get; set; }
		[Browsable(false)] public double AtrStartMax { get; set; }
		[Browsable(false)] public bool FundedHighFull { get; set; }
		[Browsable(false)] public double FundedCushionFull { get; set; }
		[NinjaScriptProperty][Range(0, 100)][Display(Name = "Eval: consistencia % (mejor día <= % de la ganancia; 0 = sin regla)", Order = 4, GroupName = "02. Reglas de la cuenta (las completa el preset)")] public double ConsistencyPct { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Eval: mejor día hasta ahora $", Order = 2, GroupName = "06. Recuperación (reinicio a mitad de una cuenta real)")] public double EvalBestDaySoFar { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Eval: cortar el día al ganar $ (0 = no)", Order = 5, GroupName = "02. Reglas de la cuenta (las completa el preset)")] public double EvalProfitStop { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Fondeada: cortar el día al ganar $ (0 = no)", Order = 9, GroupName = "02. Reglas de la cuenta (las completa el preset)")] public double FundedProfitStop { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Fondeada: subir de tamaño con colchón >= $ (0 = no)", Order = 16, GroupName = "02. Reglas de la cuenta (las completa el preset)")] public double FundedStepUpCushion { get; set; }
		[NinjaScriptProperty][Range(1, 50)][Display(Name = "Fondeada: contratos al subir", Order = 17, GroupName = "02. Reglas de la cuenta (las completa el preset)")] public int FundedStepUpContracts { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Fondeada: escalera, +1 contrato cada $ de colchón (0 = no)", Order = 18, GroupName = "02. Reglas de la cuenta (las completa el preset)")] public double FundedLadderStep { get; set; }
		[NinjaScriptProperty][Range(1, 50)][Display(Name = "Fondeada: escalera, máximo de contratos", Order = 19, GroupName = "02. Reglas de la cuenta (las completa el preset)")] public int FundedLadderMax { get; set; }
		[NinjaScriptProperty][Range(0, 8)][Display(Name = "Eval: lotes totales de MOM1030 / CPI09 (0 = normal, 4 por contrato)", Order = 7, GroupName = "02. Reglas de la cuenta (las completa el preset)")] public int EvalHighWrMultiplier { get; set; }
		[Browsable(false)] public bool UseOrderFlowBoost { get; set; }
		[Browsable(false)] public double OrderFlowCvdMin { get; set; }
		[Browsable(false)] public int OrderFlowBoost { get; set; }
		[Browsable(false)] public bool OrderFlowStack { get; set; }
		[NinjaScriptProperty][Display(Name = "Serie de llenado (solo backtest: Off = barras de 1 min como siempre; Tick1 / Second1 = agrega una serie intrabar y manda todas las órdenes ahí)", Order = 1, GroupName = "09. Backtest: realismo de ejecución")] public NQMasterFillSeries FillSeries { get; set; }
		[NinjaScriptProperty][Display(Name = "TraceOrders en Output (muestra la serie y el precio de cada orden)", Order = 2, GroupName = "09. Backtest: realismo de ejecución")] public bool TraceOrdersLog { get; set; }
		#endregion
	}
}
