"""2026-10-16 fixes from the code review research/mine/audit_code_2026-10-16.md. Backup NQMaster_backup_pre_review16.cs.
F1 risk cap: MOM1030 / CPI09 are judged on their 1-lot risk (as research sniper_life.py / c4_cushion.py); before, x4 always exceeded
   the $300 cap, so both modules never traded while the cap was active.
F2 the eval-target stop no longer runs in PropMode Funded, and every funded preset sets EvalTarget 0.
F3 edge-monitor state (CUSUM, days, alarm, warning, running fallback) is saved to Documents\\NinjaTrader 8\\nqmaster_edge_<account>.txt
   in realtime and restored at the switch to realtime when it is newer than what the loaded history rebuilt; warning when the loaded
   history starts after EdgeMonitorStart and there is no saved state.
F5 eval multiplier = total lots for the module (max(normal x base, EvalHighWrMultiplier)): x8 at 1 contract, 2 x 4 = 8 at 2 contracts
   (sniper_uniform.py: at 2 contracts x4 beats x8: Lucid Flex 50K pass 45.3% vs 39.8%, busts 47.5% vs 57%).
F6 years after the built-in fallback table print a reminder.
F8 the end-of-backtest health report no longer calls Log() (reads Times at Terminated).
F9 days blocked by the roll guard or the pause file are not counted by the edge monitor (zero-P&L days pushed the CUSUM up)."""
import os, shutil
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
F = os.path.join(ROOT, "NQMaster.cs"); src = open(F, encoding="utf-8").read()
bk = os.path.join(ROOT, "NQMaster_backup_pre_review16.cs")
if not os.path.exists(bk): shutil.copy(F, bk)


def rep(old, new, cnt=1):
    global src
    assert src.count(old) == cnt, (old[:100], src.count(old)); src = src.replace(old, new)


# F1 + F5
rep("""			if (!noBoost && m.Sig == "CPI09" && HwMult(Cpi09Multiplier) > 1) tq = HwMult(Cpi09Multiplier) * Qty();
			if (!noBoost && m.Sig == "MOM1030" && HwMult(Mom1030Multiplier) > 1) tq = HwMult(Mom1030Multiplier) * Qty();
			if (m.DoubleDist > 0 && !noBoost && Math.Abs(Close[0] - reference) >= m.DoubleDist * atrDaily) tq = 2 * Qty();
			if (TooBig(m.Sig, st * TickSize, tq)) return;""",
    """			bool hw = false;
			if (!noBoost && m.Sig == "CPI09" && HwQty(Cpi09Multiplier) > Qty()) { tq = HwQty(Cpi09Multiplier); hw = true; }
			if (!noBoost && m.Sig == "MOM1030" && HwQty(Mom1030Multiplier) > Qty()) { tq = HwQty(Mom1030Multiplier); hw = true; }
			if (m.DoubleDist > 0 && !noBoost && Math.Abs(Close[0] - reference) >= m.DoubleDist * atrDaily) tq = 2 * Qty();
			if (TooBig(m.Sig, st * TickSize, hw ? Qty() : tq)) return;		// MOM1030 / CPI09: 1-lot risk vs the cap, as in research (review F1)""")
rep("""		private int HwMult(int normal) { return PropMode == NQMasterPropMode.Eval && EvalHighWrMultiplier > 0 ? EvalHighWrMultiplier : normal; }""",
    """		private int HwMult(int normal) { return PropMode == NQMasterPropMode.Eval && EvalHighWrMultiplier > 0 ? EvalHighWrMultiplier : normal; }
		// total lots for MOM1030 / CPI09: normal multiplier x base contracts; in Eval at least EvalHighWrMultiplier lots in total (review F5)
		private int HwQty(int normal) { int b = Math.Max(1, normal) * Qty(); return PropMode == NQMasterPropMode.Eval && EvalHighWrMultiplier > 0 ? Math.Max(b, EvalHighWrMultiplier) : b; }""")
rep("MaxOpenContracts, HwMult(Mom1030Multiplier)));", "MaxOpenContracts, HwQty(Mom1030Multiplier)));")
# F2
assert src.count("else { RiskCapPerContract") == 4
src = src.replace("else { RiskCapPerContract", "else { EvalTarget = 0; RiskCapPerContract")
rep("			if (EvalTarget > 0 && !targetHit)\n", "			if (EvalTarget > 0 && !targetHit && PropMode != NQMasterPropMode.Funded)\n")
# F6
rep("""				else s = "REV06";				// 2027 (research data through 2026-10); later years: re-run research/mine/robust16.py""",
    """				else { s = "REV06"; if (year > 2027) Print("NQMaster | fallback table ends in 2027: re-run research/mine/robust16.py and update FallbackList (using the 2027 list)."); }""")
# F8
rep('Print(line); Log("health " + line.Trim());', 'Print(line); if (State == State.Realtime) Log("health " + line.Trim());')
# F9
rep("edgeDayQty = Qty(); edgeDayTradable = !fomcToday; edgeDayDate = tradeDay;",
    "edgeDayQty = Qty(); edgeDayTradable = !fomcToday && !rollHalt && !PauseActive(); edgeDayDate = tradeDay;		// review F9: blocked days are not counted")
# F3 persistence
rep("""			ProcessClosedTrades();
			PurgeStaleEntries();
""", """			ProcessClosedTrades();
			PurgeStaleEntries();
			if (firstBarDate == 0) firstBarDate = etDate;
""")

rep("""				double z = (netPnl - dayStartPnl) / Math.Max(1, edgeDayQty) / (2.0 * todayAtr);
				edgeS = Math.Max(0.0, edgeS + edgeK - z); edgeDays++;""",
    """				double z = (netPnl - dayStartPnl) / Math.Max(1, edgeDayQty) / (2.0 * todayAtr);
				edgeS = Math.Max(0.0, edgeS + edgeK - z); edgeDays++; edgeLastDate = DateKey(edgeDayDate);""")
rep("""					edgeFbLeft--;
					if (edgeFbLeft == 0)""", """					edgeFbLeft--; edgeLastDate = DateKey(edgeDayDate); EdgeSave();
					if (edgeFbLeft == 0)""")
rep("""		private void EdgeDayClose(DateTime etNow)
		{""", """		// review F3: edge-monitor state survives restarts (saved in realtime, restored at the switch to realtime if newer than the history rebuild)
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
		{""")
# save after each counted day (end of the counted block): after the alarm block we save at the end of the method
rep("""			edgeDayRth = false;
		}


		// ---- prop-account cushion gating""", """			if (State == State.Realtime) EdgeSave();
			edgeDayRth = false;
		}


		// ---- prop-account cushion gating""")
rep("				wentLive = true; PrintModuleReport(\"loaded history\");", "				wentLive = true; PrintModuleReport(\"loaded history\"); EdgeRestore();")
open(F, "w", encoding="utf-8").write(src); print("patched")
