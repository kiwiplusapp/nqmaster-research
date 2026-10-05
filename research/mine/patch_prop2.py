"""Patch NQMaster.cs to the EQUILIBRIO protocol (research/mine/acct_life2.py, acct_mc.py):
eval = full profile (no gating, no daily stop) + consistency-aware eval target; funded = SAFE below $750 of cushion, FULL above,
payout reminder at $5,000. ATR start rule off by default (waiting for it costs more lifecycle income than it saves)."""
p = r"D:\NinjaTrader Strategy\NQMaster.cs"
s = open(p, encoding="utf-8").read()
def rep(a, b, cnt=1):
    global s
    n = s.count(a); assert n == cnt, (n, a[:90]); s = s.replace(a, b)
rep("PropMode = NQMasterPropMode.Off; PropTrailingDD = 2000; EvalCushionFull = 900; EvalDailyStop = 700; FundedCushionSafe = 1500; FundedPayoutAt = 6000;\n\t\t\t\tPropPeakOverride = 0; PropThresholdOverride = 0; AtrStartMax = 1.15;",
    "PropMode = NQMasterPropMode.Off; PropTrailingDD = 2000; EvalCushionFull = 0; EvalDailyStop = 0; FundedCushionSafe = 750; FundedPayoutAt = 5000; FundedHighFull = true;\n\t\t\t\tPropPeakOverride = 0; PropThresholdOverride = 0; AtrStartMax = 0; ConsistencyPct = 50;")
rep("\t\t\t\telse gate = propCushion >= FundedCushionSafe ? GateMode.NoBoost : GateMode.Safe;",
    "\t\t\t\telse gate = propCushion >= FundedCushionSafe ? (FundedHighFull ? GateMode.Full : GateMode.NoBoost) : GateMode.Safe;")
# consistency-aware eval target: track the best closed day of the eval
rep("\t\t\t\tdouble eq = PropEquity(); propDayStart = eq;",
    "\t\t\t\tdouble eq = PropEquity();\n\t\t\t\tif (!double.IsNaN(propDayStart)) propBestDay = Math.Max(propBestDay, eq - propDayStart);\n\t\t\t\tpropDayStart = eq;")
rep("\t\tprivate bool propLive;\n", "\t\tprivate bool propLive; private double propBestDay = 0;\n")
rep("\t\t\tif (EvalTarget > 0 && bal >= StartBalance + EvalTarget && !targetHit) { targetHit = true; FlattenAll(\"eval target\"); Print(\"NQMaster | EVAL TARGET REACHED - trading stopped.\"); }",
    "\t\t\tif (EvalTarget > 0 && !targetHit)\n\t\t\t{\n\t\t\t\t// Lucid-style consistency: the best day may be at most ConsistencyPct % of the total profit -> the real target can be higher\n\t\t\t\tdouble today = double.IsNaN(propDayStart) ? 0 : bal - propDayStart;\n\t\t\t\tdouble need = EvalTarget;\n\t\t\t\tif (ConsistencyPct > 0) need = Math.Max(need, Math.Max(propBestDay, today) * 100.0 / ConsistencyPct);\n\t\t\t\tif (bal >= StartBalance + need) { targetHit = true; FlattenAll(\"eval target\"); Print(string.Format(\"NQMaster | EVAL TARGET REACHED (+{0:0}, needed {1:0}) - trading stopped.\", bal - StartBalance, need)); }\n\t\t\t}")
rep("\t\t\tif (!double.IsNaN(atrStartRatio)) txt += string.Format(", "\t\t\tif (AtrStartMax > 0 && !double.IsNaN(atrStartRatio)) txt += string.Format(")
rep("// Funded: SAFE while cushion < FundedCushionSafe ($1,500), NO-BOOST above; request payouts at >= $6,000 profit.",
    "// Funded: SAFE while cushion < FundedCushionSafe ($1,500), NO-BOOST above; request payouts at >= $6,000 profit.\n\t\t// EQUILIBRIO defaults (acct_life2.py / acct_mc.py, 12-month lifecycle): eval = full profile (EvalCushionFull 0, no daily stop) with\n\t\t// GoldMaster Robust; funded = SAFE below $750 cushion, FULL above (FundedHighFull), payouts at $5,000 with GoldMaster WinRate.\n\t\t// vs today: +$20-200/month per account in history, +1 tick cost stress and 2,000 bootstrap years; fewer funded accounts lost.")
rep('''		[NinjaScriptProperty][Range(0, 10)][Display(Name = "Start new evals only when ATR / 60-day median <", Order = 9, GroupName = "07. Prop account (cushion gating)")] public double AtrStartMax { get; set; }''',
    '''		[NinjaScriptProperty][Range(0, 10)][Display(Name = "Show eval-start ATR check: ATR / 60-day median < (0 = off)", Order = 9, GroupName = "07. Prop account (cushion gating)")] public double AtrStartMax { get; set; }
		[NinjaScriptProperty][Display(Name = "Funded: full profile above the safe cushion (off = no x2)", Order = 10, GroupName = "07. Prop account (cushion gating)")] public bool FundedHighFull { get; set; }
		[NinjaScriptProperty][Range(0, 100)][Display(Name = "Eval consistency % (best day <= % of profit; Lucid 50, 0 = off)", Order = 11, GroupName = "07. Prop account (cushion gating)")] public double ConsistencyPct { get; set; }''')
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
