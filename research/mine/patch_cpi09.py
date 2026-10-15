"""2026-10-14: NQMaster profile UltraQ (Ultra without ON07 / LON / ICT and without the wide VW13 lot) + CPI09 module
(CPI days: at 09:30 fade the 08:30->09:29 move >= 0.05 ATR, stop 0.35 ATR, 0.5R, 60 min). Research: cpi_lab.py, ultra_q2.py,
ultraq_build.py. Applies to NQMaster.cs (backup NQMaster_backup_pre_cpi09.cs)."""
import sys
P = sys.argv[1] if len(sys.argv) > 1 else "../../NQMaster.cs"
s = open(P, encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a)); s = s.replace(a, b)

rep("public enum NQMasterProfile { Ultra, WR70Plus, Durable, Custom }", "public enum NQMasterProfile { Ultra, UltraQ, WR70Plus, Durable, Custom }")
rep("""//   WR70Plus  : >= 70% win rate build:""", """//   UltraQ    : 2026-10-14 quality build = Ultra without ON07, LON, ICT and without the wide VW13 lot (VW13 only at >= 0.30 ATR).
//               Real NQ 2020-23 / 2024-26: WR 70.2 / 68.3% (Ultra 66.9 / 65.7), PF 1.51 / 1.53 (1.47 / 1.50), lower max drawdown,
//               ~3.9 trades/day, ~8% less $; win rate AND profit factor higher in all four periods incl. 2010-14 / 2015-19.
//   CPI09     : (Ultra, UltraQ, WR70Plus) on US CPI days only: at 09:30 fade the 08:30 -> 09:29 move if >= 0.05 ATR, stop 0.35 ATR,
//               0.5R, 60 min. 2010-14 / 2015-19 / 2020-23 / 2024-26 PF 1.58 / 1.13 / 1.94 / 2.62, WR ~78-81% since 2020; the same
//               rule on ordinary days loses (research/mine/cpi_lab.py). ~12 trades a year.
//   WR70Plus  : >= 70% win rate build:""")
rep("""			public int Anchor = -1; public double AnchorPx = double.NaN;""", """			public bool CpiOnly;	// CPI09: only on US CPI release days
			public int Anchor = -1; public double AnchorPx = double.NaN;""")
rep("""		private HashSet<int> fomc;""", """		private HashSet<int> fomc, cpiDays; private bool cpiToday;
		// US CPI release days (BLS schedule) for CPI09; add later years with the CpiDates parameter
		private const string BuiltinCpi = "2024-01-11,2024-02-13,2024-03-12,2024-04-10,2024-05-15,2024-06-12,2024-07-11,2024-08-14,2024-09-11,2024-10-10,2024-11-13,2024-12-11," +
			"2025-01-15,2025-02-12,2025-03-12,2025-04-10,2025-05-13,2025-06-11,2025-07-15,2025-08-12,2025-09-11,2025-10-24,2025-12-18," +
			"2026-01-13,2026-02-13,2026-03-11,2026-04-10,2026-05-12,2026-06-10,2026-07-14,2026-08-12,2026-09-11,2026-10-14,2026-11-10,2026-12-10," +
			"2027-01-13,2027-02-11,2027-03-10,2027-04-13,2027-05-12,2027-06-10,2027-07-14,2027-08-11,2027-09-14,2027-10-14,2027-11-10,2027-12-10";""")
rep("""UseLf0430 = true; NightOnWr70 = false;""", """UseLf0430 = true; NightOnWr70 = false; UseCpi09 = true; CpiDates = "";""")
rep("""				ApplyPreset();
				newsEt = new List<DateTime>();""", """				cpiDays = new HashSet<int>();
				foreach (string raw in (BuiltinCpi + "," + (CpiDates ?? "")).Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries))
				{
					DateTime d;
					if (DateTime.TryParseExact(raw.Trim(), "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out d)) cpiDays.Add(d.Year * 10000 + d.Month * 100 + d.Day);
					else Print("NQMaster | CPI dates: cannot read '" + raw.Trim() + "' (format yyyy-MM-dd)");
				}
				ApplyPreset();
				newsEt = new List<DateTime>();""")
rep("""				fomcToday = SkipFomc && fomc.Contains(tradeDay.Year * 10000 + tradeDay.Month * 100 + tradeDay.Day);""",
    """				fomcToday = SkipFomc && fomc.Contains(tradeDay.Year * 10000 + tradeDay.Month * 100 + tradeDay.Day);
				cpiToday = cpiDays != null && cpiDays.Contains(tradeDay.Year * 10000 + tradeDay.Month * 100 + tradeDay.Day);""")
rep("""			bool w7 = Profile == NQMasterProfile.WR70Plus, ul = Profile == NQMasterProfile.Ultra, du = Profile == NQMasterProfile.Durable, custom = Profile == NQMasterProfile.Custom;
			profUltra = ul;""", """			bool w7 = Profile == NQMasterProfile.WR70Plus, uq = Profile == NQMasterProfile.UltraQ, ul = Profile == NQMasterProfile.Ultra || uq, du = Profile == NQMasterProfile.Durable, custom = Profile == NQMasterProfile.Custom;
			profUltra = ul;""")
rep("""			lon = NewMod("LON", (custom ? UseLon : ul && UseLon), 2.0); lon.PriceTarget = true;
			ict = NewMod("ICT", (custom ? UseIct : (ul || w7) && UseIct), 1.0); ict.PriceTarget = true;""",
    """			lon = NewMod("LON", (custom ? UseLon : ul && !uq && UseLon), 2.0); lon.PriceTarget = true;
			ict = NewMod("ICT", (custom ? UseIct : ((ul && !uq) || w7) && UseIct), 1.0); ict.PriceTarget = true;""")
rep("""			AddTime("ON07", (custom ? UseOn07 : ul && UseOn07), 700, 30, false, 0.20, 1.0, 60, true, false);""",
    """			AddTime("ON07", (custom ? UseOn07 : ul && !uq && UseOn07), 700, 30, false, 0.20, 1.0, 60, true, false);""")
rep("""bool vwWide = w7 || ((ul || custom) && Vw13Wide);""", """bool vwWide = w7 || ((ul || custom) && !uq && Vw13Wide);""")
rep("""			eng10 = NewMod("ENG10",""", """			// research/mine/cpi_lab.py (2026-10-14): CPI days, fade the 08:30 release move at the 09:30 open (16 years, 4 periods PF > 1)
			Mod cpi09 = AddTime("CPI09", (custom ? UseCpi09 : (ul || w7) && UseCpi09), 930, -5, true, 0.35, 0.5, 60, false, false); cpi09.MinDist = 0.05; cpi09.Anchor = 8 * 60 + 30; cpi09.CpiOnly = true;
			eng10 = NewMod("ENG10",""")
rep("""			if (atrCount < AtrMin || double.IsNaN(atrDaily) || m.InTrade) return;
			double reference = double.NaN;""", """			if (atrCount < AtrMin || double.IsNaN(atrDaily) || m.InTrade) return;
			if (m.CpiOnly && !cpiToday) return;
			double reference = double.NaN;""")
rep("""				case NQMasterProfile.Durable: k = 0.0458; h = 10.71; break;""", """				case NQMasterProfile.Durable: k = 0.0458; h = 10.71; break;
				case NQMasterProfile.UltraQ: k = 0.0696; h = 20.87; break;		// research/mine/ultraq_build.py (2026-10-14)""")
rep("""		[NinjaScriptProperty][Display(Name = "Night modules also in WR70Plus (NF05 / LF06 / LF0430)", Order = 26, GroupName = "01. Module switches (any profile)")] public bool NightOnWr70 { get; set; }""",
    """		[NinjaScriptProperty][Display(Name = "Night modules also in WR70Plus (NF05 / LF06 / LF0430)", Order = 26, GroupName = "01. Module switches (any profile)")] public bool NightOnWr70 { get; set; }
		[NinjaScriptProperty][Display(Name = "CPI09 on (CPI days: 09:30 fade of the 08:30 release move; Ultra / UltraQ / WR70Plus)", Order = 27, GroupName = "01. Module switches (any profile)")] public bool UseCpi09 { get; set; }
		[NinjaScriptProperty][Display(Name = "Extra CPI release dates (yyyy-MM-dd list; built in 2024-2027)", Order = 28, GroupName = "01. Module switches (any profile)")] public string CpiDates { get; set; }""")
open(P, "w", encoding="utf-8").write(s); print("patched", P)
