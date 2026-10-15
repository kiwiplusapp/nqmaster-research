"""2026-10-15: NQMaster module health report + 'Disable modules' list (group 10).
- ModuleHealthReport (default on): per module, from the strategy's own trades (SystemPerformance.AllTrades): trades, win rate, PF, net $
  for the whole run and for the last 365 days, marking modules at >= 80% win rate over the last year; printed when the strategy goes live
  (historical trades of the loaded days) and at the end of a backtest; also written to the log file in realtime.
- DisableModules (default empty): comma list of module names to switch off in any profile (yearly review, e.g. 'REV06' for 2027).
Backup: NQMaster_backup_pre_report.cs"""
import os, shutil
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
F = os.path.join(ROOT, "NQMaster.cs")
src = open(F, encoding="utf-8").read()
bk = os.path.join(ROOT, "NQMaster_backup_pre_report.cs")
if not os.path.exists(bk): shutil.copy(F, bk)


def rep(old, new, cnt=1):
    global src
    assert src.count(old) == cnt, (old[:80], src.count(old))
    src = src.replace(old, new)


rep("AccountSyncGuard = true; SkipShortSessions = true; MaxOpenContracts = 20; RollGuard = true; LogToFile = true;",
    "AccountSyncGuard = true; SkipShortSessions = true; MaxOpenContracts = 20; RollGuard = true; LogToFile = true; ModuleHealthReport = true; DisableModules = \"\";")
rep("""				BuildModules();
				foreach (Mod m in mods) m.BaseOn = m.On;""",
    """				BuildModules();
				ApplyDisableList();
				foreach (Mod m in mods) m.BaseOn = m.On;""")
rep("""				Log(string.Format("LIVE on {0} | profile {1} | contracts {2} | prop {3} | max open contracts {4} | account sync guard {5}", Instrument.FullName, Profile, Contracts, PropMode, MaxOpenContracts, AccountSyncGuard ? "on" : "off"));
			}""",
    """				Log(string.Format("LIVE on {0} | profile {1} | contracts {2} | prop {3} | max open contracts {4} | account sync guard {5}", Instrument.FullName, Profile, Contracts, PropMode, MaxOpenContracts, AccountSyncGuard ? "on" : "off"));
				PrintModuleReport("loaded history");
			}""")
rep("""				if (mods != null && totalTrades == 0 && rthDaysSeen < WarmupDays + 2)""",
    """				if (mods != null && !wentLive) PrintModuleReport("end of run");
				if (mods != null && totalTrades == 0 && rthDaysSeen < WarmupDays + 2)""")
rep("""				PrintModuleReport("loaded history");""", """				wentLive = true; PrintModuleReport("loaded history");""")
rep("""		private Mod NewMod(string sig, bool on, double r)""",
    """		// 'Disable modules' (group 10): switch modules off by name in any profile (the yearly review, research/mine/robust16.py)
		private void ApplyDisableList()
		{
			if (string.IsNullOrEmpty(DisableModules)) return;
			foreach (string raw in DisableModules.Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries))
			{
				string s = raw.Trim(); bool hit = false;
				foreach (Mod m in mods) if (string.Equals(m.Sig, s, StringComparison.OrdinalIgnoreCase)) { hit = true; m.On = false; }
				Print(hit ? "NQMaster | module " + s.ToUpperInvariant() + " switched off by 'Disable modules'" : "NQMaster | 'Disable modules': '" + s + "' is not a module name (names: ORB60 ORB90 MSEQ MSEQS CRT11 LON ICT MOM11 MOM13 MOM1030 ON07 REV06 VW13 LATE15 LATEFH NF05 LF06 LF0430 CPI09 ENG10 VOLB ...)");
			}
		}

		// Module health report (group 10): trades / win rate / PF / net per module, whole run and last 365 days, from this strategy's own trades
		private bool wentLive;
		private void PrintModuleReport(string when)
		{
			if (!ModuleHealthReport) return;
			try
			{
				if (SystemPerformance == null || SystemPerformance.AllTrades == null || SystemPerformance.AllTrades.Count == 0) return;
				TradeCollection all = SystemPerformance.AllTrades;
				DateTime last = all[all.Count - 1].Exit.Time, from = last.AddDays(-365);
				Dictionary<string, double[]> st = new Dictionary<string, double[]>(); List<string> order = new List<string>();
				foreach (Trade t in all)
				{
					string k = t.Entry != null && !string.IsNullOrEmpty(t.Entry.Name) ? t.Entry.Name : "?";
					double[] a; if (!st.TryGetValue(k, out a)) { a = new double[8]; st[k] = a; order.Add(k); }
					double p = t.ProfitCurrency; bool yr = t.Exit != null && t.Exit.Time >= from;
					a[0] += 1; if (p > 0) { a[1] += 1; a[2] += p; } else a[3] -= p;
					if (yr) { a[4] += 1; if (p > 0) { a[5] += 1; a[6] += p; } else a[7] -= p; }
				}
				order.Sort();
				Print(string.Format("NQMaster | MODULE HEALTH ({0}; {1} trades, last exit {2:yyyy-MM-dd}; 'last 365 d' ends there)", when, all.Count, last));
				foreach (string k in order)
				{
					double[] a = st[k];
					string line = string.Format("  {0,-8} all: {1,5:0} tr  WR {2,5:0.0}%  PF {3,5}  net {4,9:$#,0;-$#,0}  | last 365 d: {5,4:0} tr  WR {6,5}  PF {7,5}  net {8,9:$#,0;-$#,0}{9}",
						k, a[0], 100.0 * a[1] / a[0], a[3] > 0 ? (a[2] / a[3]).ToString("0.00") : "inf", a[2] - a[3],
						a[4], a[4] > 0 ? (100.0 * a[5] / a[4]).ToString("0.0") + "%" : "-", a[7] > 0 ? (a[6] / a[7]).ToString("0.00") : (a[4] > 0 ? "inf" : "-"), a[6] - a[7],
						a[4] >= 20 && a[5] >= 0.8 * a[4] ? "  <- >= 80% win rate last year" : (a[4] >= 20 && a[7] > 0 && a[6] / a[7] < 1.0 ? "  <- losing last year (review)" : ""));
					Print(line); Log("health " + line.Trim());
				}
				Print("NQMaster | research: a >= 80% win-rate year does NOT predict the next trades better than the module's long-run rate (research/mine/sniper_eval.py, wr80_lab.py); use this list for the yearly review, not for sizing.");
			}
			catch (Exception e) { Print("NQMaster | module report skipped: " + e.Message); }
		}

		private Mod NewMod(string sig, bool on, double r)""")
rep("""		[NinjaScriptProperty][Display(Name = "Log file (Documents\\\\NinjaTrader 8\\\\nqmaster_logs, realtime)", Order = 5, GroupName = "10. Operations (safety)")] public bool LogToFile { get; set; }""",
    """		[NinjaScriptProperty][Display(Name = "Log file (Documents\\\\NinjaTrader 8\\\\nqmaster_logs, realtime)", Order = 5, GroupName = "10. Operations (safety)")] public bool LogToFile { get; set; }
		[NinjaScriptProperty][Display(Name = "Module health report (Output window: win rate / PF per module, all + last 365 days)", Order = 6, GroupName = "10. Operations (safety)")] public bool ModuleHealthReport { get; set; }
		[NinjaScriptProperty][Display(Name = "Disable modules (comma list, any profile; yearly review, e.g. REV06)", Order = 7, GroupName = "10. Operations (safety)")] public string DisableModules { get; set; }""")
open(F, "w", encoding="utf-8").write(src)
print("patched", F)
