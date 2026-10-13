"""2026-10-13 presets LucidPro25K / FundedNext25K (research/mine/month80.py: 2 contracts in the eval, 1 in the funded account)."""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
p = os.path.join(ROOT, "NQMaster.cs"); s = open(p, encoding="utf-8").read()
def sub(a, b):
    global s
    assert s.count(a) == 1, a[:60]; s = s.replace(a, b)
sub("public enum NQMasterPropPreset { Manual, Lucid25K, Lucid50K, Mffu50K }", "public enum NQMasterPropPreset { Manual, Lucid25K, Lucid50K, Mffu50K, LucidPro25K, FundedNext25K }")
sub("\t\t\t\tcase NQMasterPropPreset.Mffu50K:\n", """\t\t\t\tcase NQMasterPropPreset.LucidPro25K:
\t\t\t\tcase NQMasterPropPreset.FundedNext25K:
\t\t\t\t\t// research/mine/month80.py: 25K eval with NO consistency rule, 2 contracts per module, new eval the day after a bust ->
\t\t\t\t\t// funded within ~22 trading days 90% / 92% (2020-23 / 2024-26; 35% less edge: 83% / 89%); funded account at 1 contract.
\t\t\t\t\tStartBalance = 25000; PropTrailingDD = 1000; ConsistencyPct = 0;
\t\t\t\t\tif (ev) { EvalTarget = PropPreset == NQMasterPropPreset.LucidPro25K ? 1250 : 1500; EvalProfitStop = 0; EvalRiskCapCushion = 0; MaxOpenContracts = 20; Contracts = 2; }
\t\t\t\t\telse { RiskCapPerContract = 150; FundedRiskCapCushion = 500; FundedPayoutAt = 1500; MaxOpenContracts = 20; FundedProfitStop = 0; Contracts = 1; FundedStepUpCushion = 0; }
\t\t\t\t\tbreak;
\t\t\t\tcase NQMasterPropPreset.Mffu50K:
""")
sub('Display(Name = "Account preset (Lucid 25K / Lucid 50K / MFFU 50K):', 'Display(Name = "Account preset (Lucid 25K / Lucid 50K / MFFU 50K / LucidPro 25K + FundedNext 25K: eval 2 contracts, funded 1):')
open(p, "w", encoding="utf-8", newline="").write(s); print("patched")
