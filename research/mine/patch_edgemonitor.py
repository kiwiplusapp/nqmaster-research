"""Patch NQMaster.cs: Core profile (11-year robust modules only) + EdgeMonitor (one-sided CUSUM on ATR-normalised daily P&L)."""
p = r"D:\NinjaTrader Strategy\NQMaster.cs"
s = open(p, encoding="utf-8").read()
def rep(a, b, cnt=1):
    global s
    n = s.count(a); assert n == cnt, (n, a[:80]); s = s.replace(a, b)

rep("public enum NQMasterProfile { MaxSharpe, WinRate70, Gold, Custom, MaxTrades, MaxPlus, MaxPlus2, Ultra, WR70Plus }",
    "public enum NQMasterProfile { MaxSharpe, WinRate70, Gold, Custom, MaxTrades, MaxPlus, MaxPlus2, Ultra, WR70Plus, Core }")
rep("wr = Profile == NQMasterProfile.WinRate70, gold = Profile == NQMasterProfile.Gold, custom = Profile == NQMasterProfile.Custom;",
    "wr = Profile == NQMasterProfile.WinRate70, gold = Profile == NQMasterProfile.Gold, custom = Profile == NQMasterProfile.Custom, core = Profile == NQMasterProfile.Core;")
rep('lon = NewMod("LON", (custom ? UseLon : (ms) && UseLon), 2.0);', 'lon = NewMod("LON", (custom ? UseLon : (ms || core) && UseLon), 2.0);')
rep('AddTime("MOM11", (custom ? UseMom11 : (!gold) && UseMom11)', 'AddTime("MOM11", (custom ? UseMom11 : (!gold && !core) && UseMom11)')
rep('AddTime("MOM1030", (custom ? UseMom1030 : (!gold && !w7) && UseMom1030)', 'AddTime("MOM1030", (custom ? UseMom1030 : (!gold && !w7 && !core) && UseMom1030)')
rep('AddTime("ON07", (custom ? UseOn07 : (!gold && !w7) && UseOn07)', 'AddTime("ON07", (custom ? UseOn07 : (!gold && !w7 && !core) && UseOn07)')
rep('AddTime("REV06", (custom ? UseRev06 : (!gold) && UseRev06)', 'AddTime("REV06", (custom ? UseRev06 : (!gold && !core) && UseRev06)')
rep('volb = NewMod("VOLB", (custom ? UseVolBreak : (ul || w7) && UseVolBreak)', 'volb = NewMod("VOLB", (custom ? UseVolBreak : (ul || w7 || core) && UseVolBreak)')
rep("int iq = Qty() * ((Profile == NQMasterProfile.MaxPlus || Profile == NQMasterProfile.MaxPlus2 || Profile == NQMasterProfile.Ultra || Profile == NQMasterProfile.WR70Plus || Profile == NQMasterProfile.Custom) ? IctMultiplier : 1);",
    "int iq = Qty() * ((Profile == NQMasterProfile.MaxPlus || Profile == NQMasterProfile.MaxPlus2 || Profile == NQMasterProfile.Ultra || Profile == NQMasterProfile.WR70Plus || Profile == NQMasterProfile.Core || Profile == NQMasterProfile.Custom) ? IctMultiplier : 1);")

# ---- defaults
rep('PauseFile = "pause_trading.txt"; ShowDashboard = true; PrintLog = true;',
    'PauseFile = "pause_trading.txt"; ShowDashboard = true; PrintLog = true;\n\t\t\t\tEdgeMonitor = true; EdgeMonitorPause = false; EdgeMonitorStart = "2026-10-05"; EdgeK = 0; EdgeH = 0;')
# ---- session hook: close the previous session's monitor day before the daily counters reset
rep("\t\t\t\tdayStartPnl = netPnl; dayStopped = false;\n",
    "\t\t\t\tEdgeDayClose(etOpen);\n\t\t\t\tdayStartPnl = netPnl; dayStopped = false;\n")
rep("\t\t\t\tEvalSessionStart(tradeDay);\n", "\t\t\t\tEvalSessionStart(tradeDay);\n\t\t\t\tedgeDayQty = Qty(); edgeDayTradable = !fomcToday; edgeDayDate = tradeDay;\n")
rep("\t\t\tif (inRth)\n\t\t\t{\n\t\t\t\tif (etDate != rthDay) StartRthDay(etDate);",
    "\t\t\tif (inRth)\n\t\t\t{\n\t\t\t\tedgeDayRth = true;\n\t\t\t\tif (etDate != rthDay) StartRthDay(etDate);")
rep('\t\t\tif (PauseActive()) { status = "MANUAL PAUSE (file)"; return false; }',
    '\t\t\tif (PauseActive()) { status = "MANUAL PAUSE (file)"; return false; }\n\t\t\tif (edgePaused) { status = "EDGE MONITOR ALARM - review before trading"; return false; }')

monitor = r'''
		// ---- edge monitor (research/mine/robust_monitor.py). Live trading is the final out-of-sample test: this one-sided CUSUM
		// watches the daily P&L per base contract, normalised by the daily ATR (z = day $ / contracts / (2 x ATR points)):
		//   S = max(0, S + k - z); alarm when S > h.  k = half the backtested mean, h calibrated on 2020-26 block bootstrap so that
		// false alarms are rare (Ultra: 1.5%/year, 7% in 3 years) and no alarm fires anywhere in the 2020-26 history.
		// If the edge disappears (mean -> 0) the alarm fires after ~7 months (median), if it turns negative (-50%) after ~4 months.
		// Days that cannot trade (FOMC, low ATR, sessions without RTH) are not counted. Counting starts at EdgeMonitorStart.
		private double edgeS, edgeK = double.NaN, edgeH = double.NaN; private int edgeDays, edgeDayQty = 1; private bool edgeAlarm, edgePaused, edgeDayRth, edgeDayTradable;
		private DateTime edgeDayDate = DateTime.MinValue;
		private void EdgeParams()
		{
			double k, h;
			switch (Profile)
			{
				case NQMasterProfile.WR70Plus: case NQMasterProfile.WinRate70: k = 0.0559; h = 15.05; break;
				case NQMasterProfile.Core: k = 0.0397; h = 9.98; break;
				default: k = 0.0755; h = 16.21; break;			// Ultra (MaxSharpe / MaxPlus / MaxPlus2 / MaxTrades / Custom use the Ultra calibration)
			}
			edgeK = EdgeK > 0 ? EdgeK : k; edgeH = EdgeH > 0 ? EdgeH : h;
		}
		private void EdgeDayClose(DateTime etNow)
		{
			bool counted = EdgeMonitor && Profile != NQMasterProfile.Gold && edgeDayRth && edgeDayTradable && edgeDayDate != DateTime.MinValue && !double.IsNaN(todayAtr) && todayAtr > 0
				&& !(MinAtrPoints > 0 && todayAtr < MinAtrPoints);
			DateTime st;
			if (counted && DateTime.TryParseExact(EdgeMonitorStart ?? "", "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out st) && edgeDayDate >= st)
			{
				if (double.IsNaN(edgeK)) EdgeParams();
				double z = (netPnl - dayStartPnl) / Math.Max(1, edgeDayQty) / (2.0 * todayAtr);
				edgeS = Math.Max(0.0, edgeS + edgeK - z); edgeDays++;
				if (PrintLog) Print(string.Format("{0} | NQM | EDGE day {1}: z {2:0.000} | CUSUM {3:0.00} / {4:0.00} ({5:0}%)", edgeDayDate.ToString("yyyy-MM-dd"), edgeDays, z, edgeS, edgeH, 100 * edgeS / edgeH));
				if (!edgeAlarm && edgeS > edgeH)
				{
					edgeAlarm = true; edgePaused = EdgeMonitorPause;
					Print(string.Format("NQMaster | EDGE MONITOR ALARM {0}: live results are no longer consistent with the backtested edge ({1} days counted). {2}",
						edgeDayDate.ToString("yyyy-MM-dd"), edgeDays, EdgeMonitorPause ? "New entries paused. Review, then set a new 'Edge monitor start date' to resume." : "Alert only (pause is off)."));
				}
			}
			edgeDayRth = false;
		}
'''
rep("\t\tprivate bool lastDeferred;\n", monitor + "\n\t\tprivate bool lastDeferred;\n")
# ---- dashboard line
rep('''				totalTrades, totalTrades > 0 ? 100.0 * totalWins / totalTrades : 0, pf, netPnl);''',
    '''				totalTrades, totalTrades > 0 ? 100.0 * totalWins / totalTrades : 0, pf, netPnl);
			if (EdgeMonitor && !double.IsNaN(edgeH) && edgeH > 0) txt += string.Format("\\nEdge monitor: {0:0}% of alarm ({1} days){2}", 100 * edgeS / edgeH, edgeDays, edgeAlarm ? " | ALARM" : "");''')
# ---- properties
rep('''		[Display(Name = "Print log", Order = 51, GroupName = "04. Display")] public bool PrintLog { get; set; }''',
    '''		[Display(Name = "Print log", Order = 51, GroupName = "04. Display")] public bool PrintLog { get; set; }
		[NinjaScriptProperty][Display(Name = "Edge monitor on (CUSUM of live vs backtested edge)", Order = 1, GroupName = "06. Edge monitor")] public bool EdgeMonitor { get; set; }
		[NinjaScriptProperty][Display(Name = "Pause new entries on alarm", Order = 2, GroupName = "06. Edge monitor")] public bool EdgeMonitorPause { get; set; }
		[NinjaScriptProperty][Display(Name = "Edge monitor start date (yyyy-MM-dd)", Order = 3, GroupName = "06. Edge monitor")] public string EdgeMonitorStart { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "k (0 = profile calibration)", Order = 4, GroupName = "06. Edge monitor")] public double EdgeK { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "h (0 = profile calibration)", Order = 5, GroupName = "06. Edge monitor")] public double EdgeH { get; set; }''')
# ---- calibrate once data is loaded so the dashboard shows it from the start
rep("\t\t\t\tBuildModules();\n\t\t\t}", "\t\t\t\tBuildModules();\n\t\t\t\tEdgeParams();\n\t\t\t}")
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched")

