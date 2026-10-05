"""Patch NQMaster.cs: LATE15 module (15:00 ET continuation when the RTH move is >= 0.5 x daily ATR in the daily-trend direction;
stop 0.30 ATR, target 0.5R, flat 15:55). Research: research/mine/families4.py LATE_MOM j=762, late_port.py."""
p = r"D:\NinjaTrader Strategy\NQMaster.cs"
s = open(p, encoding="utf-8").read()
def rep(a, b, cnt=1):
    global s
    n = s.count(a); assert n == cnt, (n, a[:80]); s = s.replace(a, b)
rep('\t\t\tvolb = NewMod("VOLB",',
    '\t\t\tMod late15 = AddTime("LATE15", (custom ? UseLate15 : (ul || w7 || core) && UseLate15), 1500, -2, false, 0.30, 0.5, 0, true, false); late15.MinDist = 0.5;\n\t\t\tvolb = NewMod("VOLB",')
rep("UseVolBreak = true;", "UseVolBreak = true; UseLate15 = true;")
rep('''		[NinjaScriptProperty][Display(Name = "MSEQS on ", Order = 17, GroupName = "01. Module switches (any profile)")] public bool UseMseqShort { get; set; }''',
    '''		[NinjaScriptProperty][Display(Name = "MSEQS on ", Order = 17, GroupName = "01. Module switches (any profile)")] public bool UseMseqShort { get; set; }
		[NinjaScriptProperty][Display(Name = "LATE15 on (15:00 trend-day continuation; Ultra / WR70Plus / Core)", Order = 18, GroupName = "01. Module switches (any profile)")] public bool UseLate15 { get; set; }''')
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
