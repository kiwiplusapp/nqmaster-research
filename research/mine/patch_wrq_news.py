"""Patch NQMaster.cs (2026-10-08): the four trade-quality rules validated in research/mine/wrq_*.py + MFFU Tier-1 news blackout.
  ORB60/ORB90: breakout trigger must be >= 0.10 ATR beyond the prior RTH close in the trade direction (OrbPriorCloseAtr)
  VOLB (2R, Ultra): stop to entry + 0.10R once price reaches +0.75R (VolbBreakEven)
  MOM1030 / MOM13 (Ultra): only when another module is already in a filled position the same way (MomAgreement)
  VOLB trend-only (WR70Plus / Estable gear): no entry after 10:47 ET (VolbTrendLastEntry)
  News blackout (MyFundedFutures Rapid sim funded): flat and no orders from 2 min before to 2 min after CPI / Employment Report
  (08:30 ET) and FOMC minutes (14:00 ET) (NewsBlackout, NewsTimes)."""
import sys, datetime as dt
sys.path.insert(0, "research")
from news import NEWS
P = "NQMaster.cs"; s = open(P, encoding="utf-8").read()
def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (old[:80], s.count(old)); s = s.replace(old, new)

# ---- built-in Tier-1 list: CPI / NFP 2024-01 .. 2026-12 (BLS), FOMC minutes = decision + 21 days (Fed calendar; 2027 tentative)
ev = []
for d in sorted(NEWS["CPI"] | NEWS["NFP"]):
    if d >= 20240101: ev.append((d, "08:30"))
for d in (20261014, 20261106, 20261110, 20261204, 20261210): ev.append((d, "08:30"))
fomc = sorted(NEWS["FOMC"]) + [20261028, 20261209, 20270127, 20270317, 20270428, 20270609, 20270728, 20270915, 20271027, 20271208]
for f in fomc:
    if f < 20231201: continue
    m = dt.date(f // 10000, f // 100 % 100, f % 100) + dt.timedelta(days=21); ev.append((int(m.strftime("%Y%m%d")), "14:00"))
ev = sorted(set(ev)); txt = ",".join(f"{d // 10000:04d}-{d // 100 % 100:02d}-{d % 100:02d} {t}" for d, t in ev)
rep('		private HashSet<int> fomc;',
    '		private HashSet<int> fomc;\n'
    '		// Tier-1 news (MyFundedFutures: CPI, Employment Report 08:30 ET, FOMC minutes 14:00 ET; FOMC days are skipped anyway).\n'
    '		// CPI / NFP from the BLS schedules (2024 - Dec 2026; 2027 not published yet: add them in NewsTimes), minutes = decision + 21 days.\n'
    f'		private const string BuiltinNews = "{txt}";\n'
    '		private List<DateTime> newsEt; private bool profUltra, volbBeSet;')
# ---- defaults
rep('FundedProfitStop = 0;', 'FundedProfitStop = 0;\n				OrbPriorCloseAtr = 0.10; VolbBreakEven = true; MomAgreement = true; VolbTrendLastEntry = 1047; NewsBlackout = false; NewsTimes = "";')
# ---- parse news list with the FOMC list
rep('				BuildModules();\n				foreach (Mod m in mods) m.BaseOn = m.On;',
    '				newsEt = new List<DateTime>();\n'
    '				foreach (string raw in (BuiltinNews + "," + (NewsTimes ?? "")).Split(new[] { \',\', \';\' }, StringSplitOptions.RemoveEmptyEntries))\n'
    '				{\n'
    '					DateTime nt;\n'
    '					if (DateTime.TryParseExact(raw.Trim(), "yyyy-MM-dd HH:mm", CultureInfo.InvariantCulture, DateTimeStyles.None, out nt)) newsEt.Add(nt);\n'
    '				}\n'
    '				BuildModules();\n				foreach (Mod m in mods) m.BaseOn = m.On;')
# ---- profile flag
i = s.index("bool w7 = Profile == NQMasterProfile.WR70Plus"); j = s.index("\n", i)
s = s[:j + 1] + "			profUltra = ul;\n" + s[j + 1:]
# ---- news window on the 1-minute series (after the prop checks, before exits / entries)
rep('			PropDailyCheck();\n\n			// exits: module time exits, London exit, flatten',
    '			PropDailyCheck();\n'
    '			if (NewsBlackout && InNews(etClose, 3)) { FlattenAll("news blackout (Tier-1 release)"); status = "NEWS BLACKOUT"; UpdateDashboard(); return; }\n\n'
    '			// exits: module time exits, London exit, flatten')
rep('		private void OnFiveMinute()\n		{\n			if (CurrentBars[1] < 8) return;',
    '		private void OnFiveMinute()\n		{\n			if (CurrentBars[1] < 8) return;\n'
    '			bool news5 = NewsBlackout && InNews(ToEt(Times[1][0]), 8);	// a 5-minute entry would still be open at the news window')
# the 5-minute series also updates indicators: only block its entries -> guard the entry calls via CanTrade-like flag
rep('		private bool CanTrade()\n		{',
    '		// true from `before` minutes before a Tier-1 release (bar close times) until 2 minutes after it: with before = 3 the bar closing\n'
    '		// at 08:27 flattens (flat before 08:28:00) and entries resume with the bar closing at 08:32.\n'
    '		private bool InNews(DateTime etClose, int before)\n'
    '		{\n'
    '			if (newsEt == null) return false;\n'
    '			foreach (DateTime e in newsEt) { double m = (etClose - e).TotalMinutes; if (m >= -before && m < 2) return true; }\n'
    '			return false;\n'
    '		}\n'
    '		private bool newsBlock5;\n'
    '		private bool CanTrade()\n		{\n'
    '			if (newsBlock5 && BarsInProgress == 1) { status = "NEWS BLACKOUT"; return false; }')
rep('			bool news5 = NewsBlackout && InNews(ToEt(Times[1][0]), 8);	// a 5-minute entry would still be open at the news window',
    '			newsBlock5 = NewsBlackout && InNews(ToEt(Times[1][0]), 8);	// a 5-minute entry would still be open at the news window')
# ---- ORB prior-close rule
rep('			double opp = d == 1 ? o.OrL - TickSize : o.OrH + TickSize;',
    '			// research/mine/wrq_combo.py (ORBt): the breakout trigger must clear the prior RTH close by >= 0.10 ATR in the trade direction\n'
    '			// (ORB60 0.6R PF 1.62/1.60/1.56 -> 1.92/1.81/2.05, ORB90 1.43/1.31/1.38 -> 1.87/1.48/1.75, IS / CFD 24-26 / MNQ 24-26)\n'
    '			if (OrbPriorCloseAtr > -1 && !double.IsNaN(atrPrevClose) && (entry - atrPrevClose) * d < OrbPriorCloseAtr * todayAtr)\n'
    '			{ o.Armed = false; o.Trades = 2; Log(o.Sig + " skipped today: breakout level not beyond the prior close by " + OrbPriorCloseAtr.ToString("0.00") + " ATR"); return; }\n'
    '			double opp = d == 1 ? o.OrL - TickSize : o.OrH + TickSize;')
# ---- VOLB trend-only last entry
rep('			if (openMin >= 899) { CancelEntry(volb); volbDone = true; return; }',
    '			if (openMin >= 899) { CancelEntry(volb); volbDone = true; return; }\n'
    '			// research/mine/wrq_combo.py (VTSO): trend-only VOLB (WR70Plus / Estable) fills after 10:47 ET lose their edge\n'
    '			if (volbTrendOnly && VolbTrendLastEntry > 0 && openMin >= Hm(VolbTrendLastEntry)) { CancelEntry(volb); volbDone = true; return; }')
# ---- VOLB break-even
rep('			if (volb.InTrade && CurrentBars[0] - volb.EntryBar >= volb.MaxHold) ExitModule(volb, "time exit");',
    '			if (volb.InTrade && CurrentBars[0] - volb.EntryBar >= volb.MaxHold) ExitModule(volb, "time exit");\n'
    '			// research/mine/wrq_exits.py: VOLB 2R (Ultra) stop to entry + 0.10R once the bar reaches +0.75R, from the next bar\n'
    '			// (VOLB WR 52/51/50% -> 61/62/61%, PF 1.25/1.52/1.50 -> 1.30/1.66/1.57; plateau 0.4-1.0R x 0-0.2R)\n'
    '			if (VolbBreakEven && volb.InTrade && !volbTrendOnly && !volbBeSet && volb.R >= 1.5)\n'
    '			{\n'
    '				double vr = (volb.EntryPx - volb.StopPx) * volb.Dir;\n'
    '				if (vr > 0 && (volb.Dir == 1 ? High[0] >= volb.EntryPx + 0.75 * vr : Low[0] <= volb.EntryPx - 0.75 * vr))\n'
    '				{\n'
    '					double be = Instrument.MasterInstrument.RoundToTickSize(volb.EntryPx + volb.Dir * 0.10 * vr); volbBeSet = true;\n'
    '					if ((Close[0] - be) * volb.Dir > TickSize) { SetStopLoss(volb.Sig, CalculationMode.Price, be, false); Log("VOLB stop -> entry + 0.1R @ " + Fmt(be)); }\n'
    '					else ExitModule(volb, "break-even level already crossed");\n'
    '				}\n'
    '			}')
rep('				if (m == volb) { volbDone = true; volb.EntryBar = CurrentBars[0]; }',
    '				if (m == volb) { volbDone = true; volb.EntryBar = CurrentBars[0]; volbBeSet = false; }')
# ---- agreement rule
rep('			if (!DirectionAllowed(d)) return;\n			int st = Math.Max(4, (int)Math.Round(m.StopAtr * atrDaily / TickSize));',
    '			// research/mine/wrq_agree.py: MOM1030 / MOM13 alone lose (IS PF < 1); with another module already open the same way\n'
    '			// MOM1030 PF 1.08/1.13/1.17 -> 1.34/1.46/1.71, MOM13 1.31/1.17/1.19 -> 1.54/1.45/1.51 (Ultra)\n'
    '			if (MomAgreement && profUltra && (m.Sig == "MOM1030" || m.Sig == "MOM13"))\n'
    '			{\n'
    '				bool agree = false;\n'
    '				foreach (Mod x in mods) if (x != m && x.InTrade && x.Dir == d) { agree = true; break; }\n'
    '				if (!agree) { Log(m.Sig + " skipped: no other module open the same way"); return; }\n'
    '			}\n'
    '			if (!DirectionAllowed(d)) return;\n			int st = Math.Max(4, (int)Math.Round(m.StopAtr * atrDaily / TickSize));')
# ---- properties
rep('		[NinjaScriptProperty][Range(0.05, 1.0)][Display(Name = "ORB stop cap (x ATRd)", Order = 21, GroupName = "02. Edge")] public double StopCapAtr { get; set; }',
    '		[NinjaScriptProperty][Range(0.05, 1.0)][Display(Name = "ORB stop cap (x ATRd)", Order = 21, GroupName = "02. Edge")] public double StopCapAtr { get; set; }\n'
    '		[NinjaScriptProperty][Range(-1.0, 2.0)][Display(Name = "ORB: breakout must clear the prior close by x ATR (0.10; -1 = off)", Order = 22, GroupName = "02. Edge")] public double OrbPriorCloseAtr { get; set; }\n'
    '		[NinjaScriptProperty][Display(Name = "VOLB 2R (Ultra): stop to entry + 0.1R after +0.75R", Order = 23, GroupName = "02. Edge")] public bool VolbBreakEven { get; set; }\n'
    '		[NinjaScriptProperty][Display(Name = "MOM1030 / MOM13 (Ultra): only with another module open the same way", Order = 24, GroupName = "02. Edge")] public bool MomAgreement { get; set; }\n'
    '		[NinjaScriptProperty][Range(0, 2359)][Display(Name = "VOLB trend-only (WR70Plus / Estable): last entry HHMM ET (1047; 0 = off)", Order = 25, GroupName = "02. Edge")] public int VolbTrendLastEntry { get; set; }\n'
    '		[NinjaScriptProperty][Display(Name = "News blackout: flat, no orders 2 min around CPI / NFP / FOMC minutes (MFFU funded)", Order = 1, GroupName = "08. News blackout")] public bool NewsBlackout { get; set; }\n'
    '		[NinjaScriptProperty][Display(Name = "Extra Tier-1 times ET (yyyy-MM-dd HH:mm, comma list; 2027 CPI / NFP)", Order = 2, GroupName = "08. News blackout")] public string NewsTimes { get; set; }')
open(P, "w", encoding="utf-8").write(s)
print("patched; built-in news events:", len(ev), "last", ev[-1])
