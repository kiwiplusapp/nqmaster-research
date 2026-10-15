"""2026-10-15: edge-monitor alarm action = REVIEW-SET FALLBACK (research/mine/os_adapt.py). On an alarm (and pause off), for
EdgeFallbackDays (252) monitored trading days NQMaster switches off the modules that failed the walk-forward review (cost-normalised
PF <= 1.05 over the previous 5 years; built-in yearly table, or EdgeFallbackOff), the CUSUM is not updated meanwhile, then it resets
and the full profile resumes. 2013-19 (out of sample for the monitor calibration, weak-edge era): Sharpe 0.88 -> 1.05 with the yearly
table (1.15 with the exact-date set), max DD $1,519 -> $1,338, losing years 3 -> 2; pausing on alarm instead LOWERS Sharpe to
0.69-0.86. 2020-26: no alarm, no change. Backup: NQMaster_backup_pre_fallback.cs"""
import os, shutil
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
F = os.path.join(ROOT, "NQMaster.cs"); src = open(F, encoding="utf-8").read()
bk = os.path.join(ROOT, "NQMaster_backup_pre_fallback.cs")
if not os.path.exists(bk): shutil.copy(F, bk)
def rep(old, new, cnt=1):
    global src
    assert src.count(old) == cnt, (old[:90], src.count(old)); src = src.replace(old, new)
rep("EdgeMonitor = true; EdgeMonitorPause = false; EdgeMonitorStart = \"2026-10-05\"; EdgeK = 0; EdgeH = 0;",
    "EdgeMonitor = true; EdgeMonitorPause = false; EdgeMonitorStart = \"2026-10-05\"; EdgeK = 0; EdgeH = 0; EdgeAlarmFallback = true; EdgeFallbackDays = 252; EdgeFallbackOff = \"\";")
rep("""				if (double.IsNaN(edgeK)) EdgeParams();
				double z = (netPnl - dayStartPnl) / Math.Max(1, edgeDayQty) / (2.0 * todayAtr);""",
    """				if (double.IsNaN(edgeK)) EdgeParams();
				if (edgeFbLeft > 0)
				{
					// review-set fallback running: the monitor rests (research/mine/os_adapt.py), then resets and the full profile returns
					edgeFbLeft--;
					if (edgeFbLeft == 0) { edgeAlarm = false; edgeS = 0; edgeFbOff = null; Warn("nqm_edge_fb", "NQMaster | edge-monitor fallback finished: full profile again, CUSUM reset."); }
					edgeDayRth = false; return;
				}
				double z = (netPnl - dayStartPnl) / Math.Max(1, edgeDayQty) / (2.0 * todayAtr);""")
rep("""					edgeAlarm = true; edgePaused = EdgeMonitorPause;
					Warn("nqm_edge", string.Format("NQMaster | EDGE MONITOR ALARM {0}: live results are no longer consistent with the backtested edge ({1} days counted). {2}",
						edgeDayDate.ToString("yyyy-MM-dd"), edgeDays, EdgeMonitorPause ? "New entries paused. Review, then set a new 'Edge monitor start date' to resume." : "Alert only (pause is off)."));""",
    """					edgeAlarm = true; edgePaused = EdgeMonitorPause;
					string act = EdgeMonitorPause ? "New entries paused. Review, then set a new 'Edge monitor start date' to resume." : "Alert only (pause and fallback are off).";
					if (!EdgeMonitorPause && EdgeAlarmFallback && EdgeFallbackDays > 0)
					{
						edgeFbOff = FallbackList(edgeDayDate.Year); edgeFbLeft = EdgeFallbackDays; edgeS = 0;
						act = edgeFbOff.Count == 0 ? string.Format("Fallback: the yearly review keeps every module, so nothing changes for {0} days (alert only)." , EdgeFallbackDays)
							: string.Format("Fallback for {0} trading days: modules off = {1}; then the full profile returns.", EdgeFallbackDays, string.Join(" ", edgeFbOff.ToArray()));
					}
					Warn("nqm_edge", string.Format("NQMaster | EDGE MONITOR ALARM {0}: live results are no longer consistent with the backtested edge ({1} days counted). {2}",
						edgeDayDate.ToString("yyyy-MM-dd"), edgeDays, act));""")
rep("""		private DateTime edgeDayDate = DateTime.MinValue;
		private void EdgeParams()""",
    """		private DateTime edgeDayDate = DateTime.MinValue;
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
				else s = "REV06";				// 2027 (research data through 2026-10); later years: re-run research/mine/robust16.py
			}
			List<string> r = new List<string>();
			foreach (string x in s.Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries)) r.Add(x.Trim().ToUpperInvariant());
			return r;
		}
		private bool FallbackOff(string sig) { return edgeFbLeft > 0 && edgeFbOff != null && edgeFbOff.Contains(sig.ToUpperInvariant()); }
		private void EdgeParams()""")
rep("""				m.On = m.BaseOn && (estable ? EstableSig(m.Sig)""", """				m.On = m.BaseOn && !FallbackOff(m.Sig) && (estable ? EstableSig(m.Sig)""")
rep("""edgeAlarm ? " | ALARM" : "");""", """edgeFbLeft > 0 ? string.Format(" | FALLBACK {0} days left", edgeFbLeft) : (edgeAlarm ? " | ALARM" : ""));""")
i = src.index("public double EdgeH { get; set; }") + len("public double EdgeH { get; set; }")
src = src[:i] + """
		[NinjaScriptProperty][Display(Name = "On alarm: switch off the modules that failed the yearly review (pause must be off)", Order = 6, GroupName = "06. Edge monitor")] public bool EdgeAlarmFallback { get; set; }
		[NinjaScriptProperty][Range(1, 1000)][Display(Name = "Fallback length (monitored trading days; 252 = 1 year)", Order = 7, GroupName = "06. Edge monitor")] public int EdgeFallbackDays { get; set; }
		[NinjaScriptProperty][Display(Name = "Fallback modules off (empty = built-in yearly review table)", Order = 8, GroupName = "06. Edge monitor")] public string EdgeFallbackOff { get; set; }""" + src[i:]
open(F, "w", encoding="utf-8").write(src); print("patched")
