p = r"D:\NinjaTrader Strategy\NQMaster.cs"; s = open(p, encoding="utf-8").read()
def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (a[:110], s.count(a)); s = s.replace(a, b)
rep("Custom, MaxTrades, MaxPlus, MaxPlus2, Ultra }", "Custom, MaxTrades, MaxPlus, MaxPlus2, Ultra, WR70Plus }")
rep("//   Ultra     : MaxPlus2 + VOLB", "//   WR70Plus  : >=70% win rate build (research/mine/wr70_*.py): ORB60 0.75R, ORB90, MSEQ, MSEQS, CRT11, ICT x2, MOM11, REV06, VW13\n//               (>=0.15 ATR, 2 lots when >=0.30), VOLB with the trend at 0.5R; LON/ON07/MOM13/MOM1030 off; confluence + context rules.\n//               Real MNQ 2024-26: WR 71.5%, PF 1.50, 2.9 trades/day (1 lot base).\n//   Ultra     : MaxPlus2 + VOLB")
rep("bool mt = Profile == NQMasterProfile.MaxTrades, ul = Profile == NQMasterProfile.Ultra,",
    "bool w7 = Profile == NQMasterProfile.WR70Plus, mt = Profile == NQMasterProfile.MaxTrades, ul = Profile == NQMasterProfile.Ultra,")
rep("orb.R = custom ? OrbTargetR : (gold ? 2.0 : (wr ? 0.75 : 0.6));", "orb.R = custom ? OrbTargetR : (gold ? 2.0 : ((wr || w7) ? 0.75 : 0.6));")
rep('orb2.On = (custom ? UseOrb90 : (mp) && UseOrb90);', 'orb2.On = (custom ? UseOrb90 : (mp || w7) && UseOrb90);')
rep('mseqs = NewMod("MSEQS", (custom ? UseMseqShort : (mp) && UseMseqShort), 0.75);', 'mseqs = NewMod("MSEQS", (custom ? UseMseqShort : (mp || w7) && UseMseqShort), 0.75);')
rep('AddTime("MOM1030", (custom ? UseMom1030 : (!gold) && UseMom1030),', 'AddTime("MOM1030", (custom ? UseMom1030 : (!gold && !w7) && UseMom1030),')
rep('AddTime("ON07", (custom ? UseOn07 : (!gold) && UseOn07),', 'AddTime("ON07", (custom ? UseOn07 : (!gold && !w7) && UseOn07),')
rep('AddTime("VW13", (custom ? UseVw13 : (mp2) && UseVw13), 1301, -3, false, 0.15, 0.5, 120, true, false).MinDist = 0.30;',
    'Mod vw13 = AddTime("VW13", (custom ? UseVw13 : (mp2 || w7) && UseVw13), 1301, -3, false, 0.15, 0.5, 120, true, false); vw13.MinDist = w7 ? 0.15 : 0.30; vw13.DoubleDist = w7 ? 0.30 : 0;')
rep('volb = NewMod("VOLB", (custom ? UseVolBreak : (ul) && UseVolBreak), 2.0); volb.PriceTarget = true; volb.MaxHold = 400;',
    'volb = NewMod("VOLB", (custom ? UseVolBreak : (ul || w7) && UseVolBreak), w7 ? 0.5 : 2.0); volb.PriceTarget = true; volb.MaxHold = 400; volbTrendOnly = w7;')
rep("public bool Done; public double MinDist;", "public bool Done; public double MinDist; public double DoubleDist;")
rep("private double volbUp = double.NaN, volbDn = double.NaN; private bool volbDone;", "private double volbUp = double.NaN, volbDn = double.NaN; private bool volbDone, volbTrendOnly;")
# VOLB trend-only variant: only the trend side; a breach of the counter-trend level first ends the day for VOLB
rep("			int d = (volbUp - Close[0]) <= (Close[0] - volbDn) ? 1 : -1;\n",
    "			int d = (volbUp - Close[0]) <= (Close[0] - volbDn) ? 1 : -1;\n			if (volbTrendOnly)\n			{\n				if (trendDir == 0 || (trendDir == 1 && Low[0] <= volbDn) || (trendDir == -1 && High[0] >= volbUp)) { if (Working(volb.Entry)) CancelOrder(volb.Entry); volbDone = true; return; }\n				d = trendDir;\n			}\n")
# VW13 two lots when far from VWAP (WR70Plus)
rep('			int tq = m.Sig == "MOM13" ? LateQty(d, Hm(m.Time)) : Qty();\n',
    '			int tq = m.Sig == "MOM13" ? LateQty(d, Hm(m.Time)) : Qty();\n			if (m.DoubleDist > 0 && Math.Abs(Close[0] - reference) >= m.DoubleDist * atrDaily) tq = 2 * Qty();\n')
rep("(Profile == NQMasterProfile.MaxPlus || Profile == NQMasterProfile.MaxPlus2 || Profile == NQMasterProfile.Ultra || Profile == NQMasterProfile.Custom)",
    "(Profile == NQMasterProfile.MaxPlus || Profile == NQMasterProfile.MaxPlus2 || Profile == NQMasterProfile.Ultra || Profile == NQMasterProfile.WR70Plus || Profile == NQMasterProfile.Custom)", cnt=2)
rep("UseContextRules && (Profile == NQMasterProfile.MaxPlus2 || Profile == NQMasterProfile.Ultra || Profile == NQMasterProfile.Custom)",
    "UseContextRules && (Profile == NQMasterProfile.MaxPlus2 || Profile == NQMasterProfile.Ultra || Profile == NQMasterProfile.WR70Plus || Profile == NQMasterProfile.Custom)")
open(p, "w", encoding="utf-8", newline="").write(s); print("patched")
