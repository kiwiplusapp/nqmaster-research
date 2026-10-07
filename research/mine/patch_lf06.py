"""NQMaster: two London-morning fades from the NQ_DRIVE mining (nqdrive_check.py, nqdrive_port.py, nqdrive_lc.py), ON in Ultra:
  LF06   : at 06:00 ET, move since the 04:00 bar open >= 0.20 x daily ATR -> FADE, any direction, stop 0.2 ATR, target 0.5R, max 240 min.
           PF 1.49 / 1.40 / 1.45 (IS / C24 / REAL), WR ~74%, 2015-19 cost-normalised 1.20, +4 ticks/side 1.32.
  LF0430 : at 04:30 ET, move since the 04:00 bar open >= 0.10 ATR -> FADE, only with the daily trend, stop 0.35 ATR, target 0.5R, max 240 min.
           PF 1.52 / 1.46 / 1.43, 2015-19 1.10, +4 ticks 1.36.
  Both on top of Ultra + NF05: Sharpe 3.21/3.38/3.62 -> 3.31/3.47/3.71; Lucid 150K 6c/3c $2,069 -> $2,168 / month per account
  (9 of 9 tests better, worst test $1,815 -> $1,981); 50K 2c/2c $1,362 -> $1,393."""
p = r"D:\NinjaTrader Strategy\NQMaster.cs"
s = open(p, encoding="utf-8").read()
def rep(a, b):
    global s
    n = s.count(a); assert n == 1, (n, a[:100]); s = s.replace(a, b)
rep("UseNf05 = true; UseLf0315 = false;", "UseNf05 = true; UseLf0315 = false; UseLf06 = true; UseLf0430 = true;")
rep("lf0315.MinDist = 0.10; lf0315.Anchor = 3 * 60;\n",
    "lf0315.MinDist = 0.10; lf0315.Anchor = 3 * 60;\n"
    "\t\t\tMod lf06 = AddTime(\"LF06\", (custom ? UseLf06 : ul && UseLf06), 600, -5, true, 0.20, 0.5, 240, false, false); lf06.MinDist = 0.20; lf06.Anchor = 4 * 60;\n"
    "\t\t\tMod lf0430 = AddTime(\"LF0430\", (custom ? UseLf0430 : ul && UseLf0430), 430, -5, true, 0.35, 0.5, 240, true, false); lf0430.MinDist = 0.10; lf0430.Anchor = 4 * 60;\n")
rep("public bool UseLf0315 { get; set; }",
    "public bool UseLf0315 { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"LF06 on (06:00 fade of the move since 04:00; Ultra)\", Order = 24, GroupName = \"01. Module switches (any profile)\")] public bool UseLf06 { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"LF0430 on (04:30 fade with the trend of the move since 04:00; Ultra)\", Order = 25, GroupName = \"01. Module switches (any profile)\")] public bool UseLf0430 { get; set; }")
open(p, "w", encoding="utf-8", newline="\n").write(s); print("patched")
