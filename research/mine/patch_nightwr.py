"""NQMaster: let the night modules (NF05, LF06, LF0430) run in the WR70Plus profile too, with a switch (default off), for the high
win-rate 150K alternative (wr150.py: WR70Plus + night + gold WinRate: WR 69.5%, PF 1.50, $1,903/month per account)."""
p = r"D:\NinjaTrader Strategy\NQMaster.cs"
s = open(p, encoding="utf-8").read()
def rep(a, b):
    global s
    n = s.count(a); assert n == 1, (n, a[:100]); s = s.replace(a, b)
rep("UseLf06 = true; UseLf0430 = true;", "UseLf06 = true; UseLf0430 = true; NightOnWr70 = false;")
rep('AddTime("NF05", (custom ? UseNf05 : ul && UseNf05),', 'AddTime("NF05", (custom ? UseNf05 : (ul || (w7 && NightOnWr70)) && UseNf05),')
rep('AddTime("LF06", (custom ? UseLf06 : ul && UseLf06),', 'AddTime("LF06", (custom ? UseLf06 : (ul || (w7 && NightOnWr70)) && UseLf06),')
rep('AddTime("LF0430", (custom ? UseLf0430 : ul && UseLf0430),', 'AddTime("LF0430", (custom ? UseLf0430 : (ul || (w7 && NightOnWr70)) && UseLf0430),')
rep("public bool UseLf0430 { get; set; }",
    "public bool UseLf0430 { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"Night modules also in WR70Plus (NF05 / LF06 / LF0430)\", Order = 26, GroupName = \"01. Module switches (any profile)\")] public bool NightOnWr70 { get; set; }")
open(p, "w", encoding="utf-8", newline="\n").write(s); print("patched")
