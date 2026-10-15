"""2026-10-16 operations patch (audit of 2026-10-16, research/mine/AUDITORIA_2026-10-16.md). Backup NQMaster_backup_pre_ops16.cs.
1. Edge monitor recalibrated for the current defaults (MOM1030 / CPI09 x4, CPI09 in Ultra / UltraQ / WR70Plus; monitor_recal2.py):
   Ultra k 0.0850 h 24.44 (the old 0.0758 / 18.57 would have fired a false alarm on 2024-03-18 in the 2020-26 history),
   UltraQ 0.0773 / 26.08, WR70Plus 0.0634 / 12.07, Durable unchanged. New WARNING level (alert only, ~23% false warnings per year):
   Ultra 9.12, UltraQ 9.04, WR70Plus 6.86, Durable 6.98.
2. Mffu50K preset, funded: step-up to 2 contracts at a $4,000 cushion and payout requested at $6,600 (keeps $6,100)
   (c4_cushion.py: accepted by the pre-registered rule; $/month 1,316 -> 2,156 (full edge), 716 -> 1,263 (35% less edge),
   accounts lost per year in the 2024-25 blocks unchanged 0.29, summer-2026 60-day funded loss unchanged).
3. Inactivity alarm (group 10, InactivityAlarm, default on, alert only): no entry of a module for more tradable days than 1.5x its
   longest gap in 2020-26 (inactivity_thresholds.json), or no SHORT / no LONG entry of any module for 12 tradable days
   (longest gap 8). The blocked-shorts bug of 2025 lasted 13 months; this would have flagged it after 12 days.
4. Cross-account guard (group 10, CrossAccountGuard, default on, realtime only): every NQMaster instance writes its NQ-family
   position direction to Documents\\NinjaTrader 8\\nqmaster_positions\\; an entry opposite to another account's open position
   (files updated within 3 minutes, same HedgeGroup) is skipped. Lucid and MFFU ban opposite positions across your own accounts.
5. Size log: every entry whose size differs from the base contracts logs why (base -> requested -> sent)."""
import os, shutil
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
F = os.path.join(ROOT, "NQMaster.cs"); src = open(F, encoding="utf-8").read()
bk = os.path.join(ROOT, "NQMaster_backup_pre_ops16.cs")
if not os.path.exists(bk): shutil.copy(F, bk)


def rep(old, new, cnt=1):
    global src
    assert src.count(old) == cnt, (old[:100], src.count(old)); src = src.replace(old, new)


# 1. monitor recalibration + warning level
rep("""				case NQMasterProfile.WR70Plus: k = 0.0577; h = 12.18; break;		// research/mine/monitor_recal.py (2026-10-12, real NQ 2020-26)
				case NQMasterProfile.Durable: k = 0.0458; h = 10.71; break;
				case NQMasterProfile.UltraQ: k = 0.0696; h = 20.87; break;		// research/mine/ultraq_build.py (2026-10-14)
				default: k = 0.0758; h = 18.57; break;			// Ultra (Custom uses the Ultra calibration)
			}
			edgeK = EdgeK > 0 ? EdgeK : k; edgeH = EdgeH > 0 ? EdgeH : h;""",
    """				// research/mine/monitor_recal2.py (2026-10-16): recalibrated for MOM1030 / CPI09 x4 and CPI09; hw = warning level (alert only)
				case NQMasterProfile.WR70Plus: k = 0.0634; h = 12.07; edgeHw = 6.86; break;
				case NQMasterProfile.Durable: k = 0.0458; h = 10.71; edgeHw = 6.98; break;
				case NQMasterProfile.UltraQ: k = 0.0773; h = 26.08; edgeHw = 9.04; break;
				default: k = 0.0850; h = 24.44; edgeHw = 9.12; break;			// Ultra (Custom uses the Ultra calibration)
			}
			edgeK = EdgeK > 0 ? EdgeK : k; edgeH = EdgeH > 0 ? EdgeH : h;
			if (EdgeK > 0 || EdgeH > 0) edgeHw = edgeH * 0.37;					// manual k / h: warning at the same relative level""")
rep("""				double z = (netPnl - dayStartPnl) / Math.Max(1, edgeDayQty) / (2.0 * todayAtr);
				edgeS = Math.Max(0.0, edgeS + edgeK - z); edgeDays++;""",
    """				double z = (netPnl - dayStartPnl) / Math.Max(1, edgeDayQty) / (2.0 * todayAtr);
				edgeS = Math.Max(0.0, edgeS + edgeK - z); edgeDays++;
				if (edgeS <= 0) edgeWarned = false;
				if (!edgeWarned && !edgeAlarm && edgeHw > 0 && edgeS > edgeHw)
				{
					edgeWarned = true;
					Warn("nqm_edge_w", string.Format("NQMaster | EDGE MONITOR WARNING {0}: results are running below the backtest ({1:0}% of the alarm level). Alert only: nothing changes; ~1 in 4 years gives a warning by chance.",
						edgeDayDate.ToString("yyyy-MM-dd"), 100 * edgeS / edgeH));
				}""")
rep("private double edgeS, edgeK = double.NaN, edgeH = double.NaN;", "private double edgeS, edgeK = double.NaN, edgeH = double.NaN, edgeHw; private bool edgeWarned;")

# 2. Mffu50K preset funded: step-up 4000, payout 6600
rep("else { RiskCapPerContract = 300; FundedRiskCapCushion = 2000; FundedPayoutAt = FundedStepUpCushion > 0 ? 6600 : 4600; MaxOpenContracts = 30; FundedProfitStop = 0; }",
    "else { RiskCapPerContract = 300; FundedRiskCapCushion = 2000; FundedStepUpCushion = 4000; FundedStepUpContracts = 2; FundedPayoutAt = 6600; MaxOpenContracts = 30; FundedProfitStop = 0; }")
rep("// MFFU funded: no trades +-2 min around Tier-1 news (rule); payout 4,600 = keep $4,100 at 1 contract (smallacct_cushion.py), 6,600 with step-up",
    "// MFFU funded: no trades or orders +-2 min around Tier-1 news (rule). Step-up 2 contracts at a $4,000 cushion, payout at $6,600 = keep $6,100 (c4_cushion.py, 2026-10-16)")

# 3. inactivity alarm + 4. cross-account guard + 5. size log
rep("			public bool CpiOnly;	// CPI09: only on US CPI release days",
    "			public bool CpiOnly;	// CPI09: only on US CPI release days\n			public int LastFillDay = -1; public bool InactWarned;	// inactivity alarm (tradable-day index of the last fill)")
rep("""		private void EdgeParams()""",
    """		// ---- inactivity alarm (research/mine/inactivity_thresholds.json, 2026-10-16): 1.5 x the longest gap between entries in 2020-26,
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

		// ---- cross-account guard (2026-10-16): Lucid and MFFU ban opposite positions across your own accounts. Each NQMaster instance writes
		// its NQ-family direction to Documents\\NinjaTrader 8\\nqmaster_positions\\<group>_<account>.txt every minute in realtime; an entry
		// opposite to another account's open position (file younger than 3 minutes) is skipped. Same PC only.
		private int otherDirBar = -1; private bool otherLong, otherShort;
		private string PosDir { get { try { return Path.Combine(Core.Globals.UserDataDir, "nqmaster_positions"); } catch { return null; } } }
		private string PosFile { get { string d = PosDir; return d == null ? null : Path.Combine(d, (HedgeGroup ?? "") + "_" + (Account != null ? Account.Name : "acct") + "_NQ.txt"); } }
		private void CrossAccountPublish()
		{
			if (!CrossAccountGuard || State != State.Realtime) return;
			try
			{
				Directory.CreateDirectory(PosDir);
				int d = Position.MarketPosition == MarketPosition.Long ? 1 : (Position.MarketPosition == MarketPosition.Short ? -1 : 0);
				foreach (Mod m in mods) if (d == 0 && Working(m.Entry) && m.Entry.OrderType == OrderType.Market) d = m.Dir;	// market entry in flight
				File.WriteAllText(PosFile, d.ToString(CultureInfo.InvariantCulture) + ";" + DateTime.UtcNow.Ticks.ToString(CultureInfo.InvariantCulture));
			}
			catch { }
		}
		private void CrossAccountRead()
		{
			otherLong = otherShort = false; otherDirBar = CurrentBars[0];
			if (!CrossAccountGuard || State != State.Realtime) return;
			try
			{
				string mine = PosFile; string pre = (HedgeGroup ?? "") + "_";
				foreach (string f in Directory.GetFiles(PosDir, "*_NQ.txt"))
				{
					if (string.Equals(f, mine, StringComparison.OrdinalIgnoreCase) || !Path.GetFileName(f).StartsWith(pre, StringComparison.OrdinalIgnoreCase)) continue;
					string[] p = File.ReadAllText(f).Split(';'); if (p.Length < 2) continue;
					long t; int d;
					if (!long.TryParse(p[1], NumberStyles.Integer, CultureInfo.InvariantCulture, out t) || !int.TryParse(p[0], NumberStyles.Integer, CultureInfo.InvariantCulture, out d)) continue;
					if ((DateTime.UtcNow - new DateTime(t, DateTimeKind.Utc)).TotalMinutes > 3) continue;
					if (d == 1) otherLong = true; else if (d == -1) otherShort = true;
				}
			}
			catch { }
		}
		private bool OtherAccountOpposite(int d)
		{
			if (!CrossAccountGuard || State != State.Realtime) return false;
			if (otherDirBar != CurrentBars[0]) CrossAccountRead();
			bool opp = (d == 1 && otherShort) || (d == -1 && otherLong);
			if (opp) { status = "another account holds the opposite NQ position (cross-account guard)"; Log("entry skipped: another account holds the opposite NQ position (hedging ban)"); }
			return opp;
		}

		private void EdgeParams()""")
rep("""				EdgeDayClose(etOpen);""", """				InactivityDayClose();
				EdgeDayClose(etOpen);""")
rep("""			if ((d == 1 && Position.MarketPosition == MarketPosition.Short) || (d == -1 && Position.MarketPosition == MarketPosition.Long)) return false;
			if (RtZombieOpp(d)) return false;""",
    """			if ((d == 1 && Position.MarketPosition == MarketPosition.Short) || (d == -1 && Position.MarketPosition == MarketPosition.Long)) return false;
			if (RtZombieOpp(d)) return false;
			if (OtherAccountOpposite(d)) return false;""")
rep("""				if (m == orb) { orb.Trades++; if (orbFirstDir == 0)""", """				InactivityFill(m); CrossAccountPublish();
				if (m == orb) { orb.Trades++; if (orbFirstDir == 0)""")
rep("""			ProcessClosedTrades();
			PurgeStaleEntries();""", """			ProcessClosedTrades();
			PurgeStaleEntries();
			CrossAccountPublish();""")
rep("""		private int OfApply(Mod m, int q, int d) { m.OfQ0 = q; if (m.RejToday >= 2) return 0; return CapQty(m, m.Sig, OfQty(q, d, m.Sig)); }""",
    """		private int OfApply(Mod m, int q, int d)
		{
			m.OfQ0 = q; if (m.RejToday >= 2) return 0;
			int f = CapQty(m, m.Sig, OfQty(q, d, m.Sig));
			if (f != q || q != Qty()) Log(string.Format("SIZE {0} {1}: base {2} -> requested {3} (multipliers / boosts) -> sent {4}{5}", m.Sig, d == 1 ? "BUY" : "SELL", Qty(), q, f,
				f < q ? " (capped: max open contracts / order flow)" : ""));
			return f;
		}""")
rep("""				if (zombieCount > 0)""", """				try { if (CrossAccountGuard && PosFile != null && File.Exists(PosFile)) File.Delete(PosFile); } catch { }
				if (zombieCount > 0)""")
rep("ModuleHealthReport = true; DisableModules = \"\";", "ModuleHealthReport = true; DisableModules = \"\"; InactivityAlarm = true; CrossAccountGuard = true; HedgeGroup = \"\";")
i = src.index("public string DisableModules { get; set; }") + len("public string DisableModules { get; set; }")
src = src[:i] + """
		[NinjaScriptProperty][Display(Name = "Inactivity alarm (a module or a direction stops trading for longer than ever in 2020-26)", Order = 8, GroupName = "10. Operations (safety)")] public bool InactivityAlarm { get; set; }
		[NinjaScriptProperty][Display(Name = "Cross-account guard: skip entries opposite to another account's NQ position (Lucid / MFFU hedging ban)", Order = 9, GroupName = "10. Operations (safety)")] public bool CrossAccountGuard { get; set; }
		[NinjaScriptProperty][Display(Name = "Cross-account group (accounts with the same text check each other; one per prop firm)", Order = 10, GroupName = "10. Operations (safety)")] public string HedgeGroup { get; set; }""" + src[i:]
open(F, "w", encoding="utf-8").write(src); print("patched")
