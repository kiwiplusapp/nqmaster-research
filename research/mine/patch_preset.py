"""2026-10-13: account presets for NQMaster (Lucid 25K / Lucid 50K / MFFU 50K) from research/mine/smallacct_*.py + corrected eval profit-stop label.
Run from the repo root: python3 research/mine/patch_preset.py"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
p = os.path.join(ROOT, "NQMaster.cs"); s = open(p, encoding="utf-8").read()
def sub(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a)); s = s.replace(a, b)
sub("\tpublic enum NQMasterPropMode { Off, Eval, Funded }\n", "\tpublic enum NQMasterPropMode { Off, Eval, Funded }\n\tpublic enum NQMasterPropPreset { Manual, Lucid25K, Lucid50K, Mffu50K }\n")
sub("\t\t\t\tAccountSyncGuard = true; SkipShortSessions = true;", "\t\t\t\tPropPreset = NQMasterPropPreset.Manual;\n\t\t\t\tAccountSyncGuard = true; SkipShortSessions = true;")
sub("\t\t\t\tnewsEt = new List<DateTime>();\n", "\t\t\t\tApplyPreset();\n\t\t\t\tnewsEt = new List<DateTime>();\n")
sub("\t\tprivate bool RollDue()\n", """\t\t// ---- account presets (research/mine/smallacct_*.py, real NQ futures 2020-26, 1 contract per module). Applied at start-up when PropMode is Eval or Funded.
\t\t// Eval: profit stop = 0.9 x consistency x target (best day must stay under the consistency limit; the old '700 with 1 contract' cost ~9 points of 22-day pass
\t\t// rate on Lucid 50K), no per-trade risk cap (neutral for passing, it only slows a 25K eval). Funded: per-trade risk cap while the cushion is small.
\t\tprivate void ApplyPreset()
\t\t{
\t\t\tif (PropPreset == NQMasterPropPreset.Manual || PropMode == NQMasterPropMode.Off) return;
\t\t\tbool ev = PropMode == NQMasterPropMode.Eval;
\t\t\tswitch (PropPreset)
\t\t\t{
\t\t\t\tcase NQMasterPropPreset.Lucid25K:
\t\t\t\t\tStartBalance = 25000; PropTrailingDD = 1000; ConsistencyPct = 50;
\t\t\t\t\tif (ev) { EvalTarget = 1250; EvalProfitStop = 560; EvalRiskCapCushion = 0; MaxOpenContracts = 20; }
\t\t\t\t\telse { RiskCapPerContract = 150; FundedRiskCapCushion = 500; FundedPayoutAt = 1500; MaxOpenContracts = 10; FundedProfitStop = 0; }
\t\t\t\t\tbreak;
\t\t\t\tcase NQMasterPropPreset.Lucid50K:
\t\t\t\t\tStartBalance = 50000; PropTrailingDD = 2000; ConsistencyPct = 50;
\t\t\t\t\tif (ev) { EvalTarget = 3000; EvalProfitStop = 1350; EvalRiskCapCushion = 0; MaxOpenContracts = 40; }
\t\t\t\t\telse { RiskCapPerContract = 300; FundedRiskCapCushion = 1000; FundedPayoutAt = 4000; MaxOpenContracts = 20; FundedProfitStop = 0; }
\t\t\t\t\tbreak;
\t\t\t\tcase NQMasterPropPreset.Mffu50K:
\t\t\t\t\tStartBalance = 50000; PropTrailingDD = 2000; ConsistencyPct = 30;
\t\t\t\t\tif (ev) { EvalTarget = 3000; EvalProfitStop = 800; EvalRiskCapCushion = 0; MaxOpenContracts = 30; }
\t\t\t\t\telse { RiskCapPerContract = 300; FundedRiskCapCushion = 2000; FundedPayoutAt = 6600; MaxOpenContracts = 30; FundedProfitStop = 0; }
\t\t\t\t\tbreak;
\t\t\t}
\t\t\tPrint(string.Format("NQMaster | preset {0} ({1}): balance {2:0}, trailing DD {3:0}, eval target {4:0}, profit stop {5:0}, consistency {6:0}%, risk cap {7:0} below cushion {8:0}, max open contracts {9}",
\t\t\t\tPropPreset, PropMode, StartBalance, PropTrailingDD, EvalTarget, EvalProfitStop, ConsistencyPct, RiskCapPerContract, ev ? EvalRiskCapCushion : FundedRiskCapCushion, MaxOpenContracts));
\t\t}
\t\tprivate bool RollDue()
""")
sub('Display(Name = "Eval: stop the day at +$ (whole account; 1400 with 2 contracts, 700 with 1; 0 = off)", Order = 14',
    'Display(Name = "Eval: stop the day at +$ (whole account; 0.9 x consistency % x target: Lucid 50K 1350, Lucid 25K 560, MFFU 50K 800; 0 = off)", Order = 14')
sub('\t\t[NinjaScriptProperty][Display(Name = "Prop mode (Off / Eval / Funded)", Order = 1, GroupName = "07. Prop account (cushion gating)")] public NQMasterPropMode PropMode { get; set; }\n',
    '\t\t[NinjaScriptProperty][Display(Name = "Prop mode (Off / Eval / Funded)", Order = 1, GroupName = "07. Prop account (cushion gating)")] public NQMasterPropMode PropMode { get; set; }\n'
    '\t\t[NinjaScriptProperty][Display(Name = "Account preset (Lucid 25K / Lucid 50K / MFFU 50K): fills balance, drawdown, target, profit stop, risk cap and contract cap for the chosen mode", Order = 0, GroupName = "07. Prop account (cushion gating)")] public NQMasterPropPreset PropPreset { get; set; }\n')
open(p, "w", encoding="utf-8", newline="").write(s); print("patched")
