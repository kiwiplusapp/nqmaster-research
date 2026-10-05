//
// NQ Account Guard - account-level rules for the whole portfolio (NinjaTrader 8, single file)
// ------------------------------------------------------------------------------------------------
// Runs on any chart (e.g. MNQ 1 minute) on the SAME account as the portfolio strategies. It controls the shared
// pause file that every portfolio strategy checks before opening a trade:
//   * FOMC days: pause for the whole Globex session of each FOMC decision date (list below, editable).
//     Research: skipping FOMC days raised Sharpe 3.21 -> 3.30 (real MNQ) and the 25K pass rate 78% -> 83%.
//   * Evaluation target reached (account balance >= StartBalance + EvalTarget): pause, so nothing trades after passing.
//   * Drawdown guard: if the balance falls to (high-water - MaxDrawdown + Buffer): pause and flatten the account.
// It only removes the pause file if it created it (file content starts with "AUTO"); a manual pause is never removed.
// ------------------------------------------------------------------------------------------------
#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Globalization;
using System.IO;
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
	public class NQAccountGuard : Strategy
	{
		private TimeZoneInfo etZone;
		private SimpleFont dashFont;
		private HashSet<int> fomc;
		private double highWater = double.NaN;
		private bool ddTripped, targetHit;
		private string status = "";

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Description = "Portfolio guard: pauses all portfolio strategies on FOMC days, after the eval target and on the drawdown guard (shared pause file).";
				Name = "NQAccountGuard";
				Calculate = Calculate.OnBarClose;
				IsExitOnSessionCloseStrategy = false;
				BarsRequiredToTrade = 1;
				FomcDates = "2026-01-28,2026-03-18,2026-04-29,2026-06-17,2026-07-29,2026-09-16,2026-10-28,2026-12-09";
				SkipFomc = true; StartBalance = 50000; EvalTarget = 0; MaxDrawdown = 0; Buffer = 250;
				PauseFile = "pause_trading.txt"; ShowDashboard = true;
			}
			else if (State == State.DataLoaded)
			{
				dashFont = new SimpleFont("Consolas", 11);
				try { etZone = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time"); } catch { etZone = null; }
				fomc = new HashSet<int>();
				foreach (string raw in (FomcDates ?? "").Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries))
				{
					DateTime d;
					if (DateTime.TryParseExact(raw.Trim(), "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out d))
						fomc.Add(d.Year * 10000 + d.Month * 100 + d.Day);
				}
			}
		}

		public override string DisplayName { get { return "NQ Account Guard"; } }

		protected override void OnBarUpdate()
		{
			if (CurrentBar < 1) return;
			DateTime et = ToEt(Time[0]);
			DateTime tradeDay = et.Hour >= 18 ? et.Date.AddDays(1) : et.Date;		// Globex trading date
			int td = tradeDay.Year * 10000 + tradeDay.Month * 100 + tradeDay.Day;
			bool pauseFomc = SkipFomc && fomc.Contains(td);
			if (State == State.Realtime)
			{
				double bal = Account.Get(AccountItem.CashValue, Currency.UsDollar);
				if (double.IsNaN(highWater) || bal > highWater) highWater = bal;
				if (EvalTarget > 0 && bal >= StartBalance + EvalTarget) targetHit = true;
				if (MaxDrawdown > 0 && bal <= highWater - MaxDrawdown + Buffer && !ddTripped)
				{
					ddTripped = true;
					try
					{
						List<Instrument> inst = new List<Instrument>();
						foreach (Position p in Account.Positions) if (p.MarketPosition != MarketPosition.Flat) inst.Add(p.Instrument);
						if (inst.Count > 0) Account.Flatten(inst);
					}
					catch (Exception ex) { Print("NQAccountGuard | flatten failed: " + ex.Message); }
					Print("NQAccountGuard | DRAWDOWN GUARD tripped: account flattened and paused.");
				}
				status = string.Format("balance ${0:0} | high ${1:0}{2}{3}", bal, highWater, targetHit ? " | TARGET HIT" : "", ddTripped ? " | DD GUARD" : "");
			}
			bool wantPause = pauseFomc || targetHit || ddTripped;
			SetPause(wantPause, pauseFomc ? "FOMC day" : targetHit ? "eval target reached" : ddTripped ? "drawdown guard" : "");
			if (ShowDashboard && (State == State.Realtime || CurrentBar >= Count - 2))
				Draw.TextFixed(this, "GUARD_Dash", "ACCOUNT GUARD: " + (wantPause ? "PAUSED (" + (pauseFomc ? "FOMC" : targetHit ? "target" : "drawdown") + ")" : "trading allowed") + "\n" + status,
					TextPosition.BottomRight, Brushes.White, dashFont, Brushes.Transparent, Brushes.Black, 75);
		}

		private void SetPause(bool on, string why)
		{
			if (State != State.Realtime) return;		// never touch the file during historical processing
			try
			{
				string path = Path.IsPathRooted(PauseFile) ? PauseFile : Path.Combine(Core.Globals.UserDataDir, PauseFile);
				bool exists = File.Exists(path);
				if (on && !exists) { File.WriteAllText(path, "AUTO " + why); Print("NQAccountGuard | PAUSE ON: " + why); }
				else if (!on && exists)
				{
					string txt = File.ReadAllText(path);
					if (txt.StartsWith("AUTO")) { File.Delete(path); Print("NQAccountGuard | PAUSE OFF"); }
				}
			}
			catch (Exception ex) { Print("NQAccountGuard | pause file error: " + ex.Message); }
		}

		private DateTime ToEt(DateTime t)
		{
			if (etZone == null) return t;
			try { return TimeZoneInfo.ConvertTime(DateTime.SpecifyKind(t, DateTimeKind.Unspecified), Core.Globals.GeneralOptions.TimeZoneInfo, etZone); }
			catch { return t; }
		}

		#region Properties
		[NinjaScriptProperty][Display(Name = "FOMC decision dates (yyyy-MM-dd list)", Order = 1, GroupName = "01. Guard")] public string FomcDates { get; set; }
		[NinjaScriptProperty][Display(Name = "Pause on FOMC days", Order = 2, GroupName = "01. Guard")] public bool SkipFomc { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Start balance $", Order = 3, GroupName = "01. Guard")] public double StartBalance { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Eval target $ (0 = off)", Order = 4, GroupName = "01. Guard")] public double EvalTarget { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Max drawdown $ (0 = off)", Order = 5, GroupName = "01. Guard")] public double MaxDrawdown { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Drawdown buffer $", Order = 6, GroupName = "01. Guard")] public double Buffer { get; set; }
		[NinjaScriptProperty][Display(Name = "Pause file", Order = 7, GroupName = "01. Guard")] public string PauseFile { get; set; }
		[Display(Name = "Show dashboard", Order = 8, GroupName = "02. Display")] public bool ShowDashboard { get; set; }
		#endregion
	}
}
