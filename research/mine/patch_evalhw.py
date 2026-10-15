"""2026-10-15: NQMaster 'Eval: high win-rate multiplier' (group 07). In PropMode Eval the MOM1030 / CPI09 size multiplier becomes
EvalHighWrMultiplier when > 0 (0 = keep the normal Mom1030Multiplier / Cpi09Multiplier = 4). research/mine/sniper_uniform.py (50K evals,
1 contract): x8 raises the single-eval pass within ~20 trading days on Lucid Pro 50K 24.6/35.1 -> 33.5/46.4 % (2020-23 / 2024-26; 35% less
edge 19.3/21.4 -> 24.7/33.1), MFFU 50K 20.0/26.5 -> 28.5/40.9 with the bust rate nearly unchanged; sniper_life.py lifecycle eval x8 ->
funded x4 beats x4/x4 in $/month in all 8 tests. Presets Lucid50K / Mffu50K set 8 in Eval. The walk-forward 'any module >= 80% last year'
version (sniper_eval.py) is NOT used: its trades have PF 1.34 (avg loss 2.9x avg win) and big size there only adds busts.
Backup: NQMaster_backup_pre_evalhw.cs"""
import os, shutil
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
F = os.path.join(ROOT, "NQMaster.cs"); src = open(F, encoding="utf-8").read()
bk = os.path.join(ROOT, "NQMaster_backup_pre_evalhw.cs")
if not os.path.exists(bk): shutil.copy(F, bk)
def rep(old, new, cnt=1):
    global src
    assert src.count(old) == cnt, (old[:90], src.count(old)); src = src.replace(old, new)
rep('if (!noBoost && m.Sig == "CPI09" && Cpi09Multiplier > 1) tq = Cpi09Multiplier * Qty();',
    'if (!noBoost && m.Sig == "CPI09" && HwMult(Cpi09Multiplier) > 1) tq = HwMult(Cpi09Multiplier) * Qty();')
rep('if (!noBoost && m.Sig == "MOM1030" && Mom1030Multiplier > 1) tq = Mom1030Multiplier * Qty();',
    'if (!noBoost && m.Sig == "MOM1030" && HwMult(Mom1030Multiplier) > 1) tq = HwMult(Mom1030Multiplier) * Qty();')
rep("		private bool PastLevel(int d, double px)",
    "		// eval-only multiplier of the ~80% win-rate modules (MOM1030, CPI09): research/mine/sniper_uniform.py, sniper_life.py\n"
    "		private int HwMult(int normal) { return PropMode == NQMasterPropMode.Eval && EvalHighWrMultiplier > 0 ? EvalHighWrMultiplier : normal; }\n"
    "		private bool PastLevel(int d, double px)")
rep("if (ev) { EvalTarget = 3000; EvalProfitStop = 1350; EvalRiskCapCushion = 0; MaxOpenContracts = 40; }",
    "if (ev) { EvalTarget = 3000; EvalProfitStop = 1350; EvalRiskCapCushion = 0; MaxOpenContracts = 40; EvalHighWrMultiplier = 8; }")
rep("if (ev) { EvalTarget = 3000; EvalProfitStop = 800; EvalRiskCapCushion = 0; MaxOpenContracts = 30; }",
    "if (ev) { EvalTarget = 3000; EvalProfitStop = 800; EvalRiskCapCushion = 0; MaxOpenContracts = 30; EvalHighWrMultiplier = 8; }")
rep('Print(string.Format("NQMaster | preset {0} ({1}): balance {2:0}, trailing DD {3:0}, eval target {4:0}, profit stop {5:0}, consistency {6:0}%, risk cap {7:0} below cushion {8:0}, max open contracts {9}",\n'
    '				PropPreset, PropMode, StartBalance, PropTrailingDD, EvalTarget, EvalProfitStop, ConsistencyPct, RiskCapPerContract, ev ? EvalRiskCapCushion : FundedRiskCapCushion, MaxOpenContracts));',
    'Print(string.Format("NQMaster | preset {0} ({1}): balance {2:0}, trailing DD {3:0}, eval target {4:0}, profit stop {5:0}, consistency {6:0}%, risk cap {7:0} below cushion {8:0}, max open contracts {9}, MOM1030/CPI09 x{10}",\n'
    '				PropPreset, PropMode, StartBalance, PropTrailingDD, EvalTarget, EvalProfitStop, ConsistencyPct, RiskCapPerContract, ev ? EvalRiskCapCushion : FundedRiskCapCushion, MaxOpenContracts, HwMult(Mom1030Multiplier)));')
rep("Cpi09Multiplier = 4; Mom1030Multiplier = 4;", "Cpi09Multiplier = 4; Mom1030Multiplier = 4; EvalHighWrMultiplier = 0;")
i = src.index("public int FundedStepUpContracts { get; set; }") + len("public int FundedStepUpContracts { get; set; }")
src = src[:i] + '\n		[NinjaScriptProperty][Range(0, 8)][Display(Name = "Eval: MOM1030 / CPI09 multiplier (0 = normal x4; 8 on 50K evals at 1 contract; presets Lucid50K / Mffu50K set 8)", Order = 21, GroupName = "07. Prop account (cushion gating)")] public int EvalHighWrMultiplier { get; set; }' + src[i:]
open(F, "w", encoding="utf-8").write(src); print("patched")
