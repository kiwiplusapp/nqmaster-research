"""2026-10-15: size multipliers for the two modules whose x2 raised Sharpe in all four periods (size_q.py): CPI09 x2, MOM1030 x2."""
import sys
P = sys.argv[1] if len(sys.argv) > 1 else "../../NQMaster.cs"
s = open(P, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]; s = s.replace(a, b)
rep('''			int tq = m.Sig == "MOM13" ? LateQty(d, Hm(m.Time)) : Qty();''',
    '''			int tq = m.Sig == "MOM13" ? LateQty(d, Hm(m.Time)) : Qty();
			// research/mine/size_q.py (2026-10-15): x2 raised Sharpe in 2010-14 / 2015-19 / 2020-23 / 2024-26 for these two only
			if (!noBoost && m.Sig == "CPI09" && Cpi09Multiplier > 1) tq = Cpi09Multiplier * Qty();
			if (!noBoost && m.Sig == "MOM1030" && Mom1030Multiplier > 1) tq = Mom1030Multiplier * Qty();''')
rep('''UseCpi09 = true; CpiDates = "";''', '''UseCpi09 = true; CpiDates = ""; Cpi09Multiplier = 2; Mom1030Multiplier = 2;''')
rep('''		[NinjaScriptProperty][Display(Name = "Extra CPI release dates (yyyy-MM-dd list; built in 2024-2027)", Order = 28, GroupName = "01. Module switches (any profile)")] public string CpiDates { get; set; }''',
    '''		[NinjaScriptProperty][Display(Name = "Extra CPI release dates (yyyy-MM-dd list; built in 2024-2027)", Order = 28, GroupName = "01. Module switches (any profile)")] public string CpiDates { get; set; }
		[NinjaScriptProperty][Range(1, 3)][Display(Name = "CPI09 size multiplier (2 = validated)", Order = 29, GroupName = "01. Module switches (any profile)")] public int Cpi09Multiplier { get; set; }
		[NinjaScriptProperty][Range(1, 3)][Display(Name = "MOM1030 size multiplier (2 = validated)", Order = 30, GroupName = "01. Module switches (any profile)")] public int Mom1030Multiplier { get; set; }''')
open(P, "w", encoding="utf-8").write(s); print("patched")
