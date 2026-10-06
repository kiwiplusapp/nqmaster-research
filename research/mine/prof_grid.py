"""Best prop profile: eval profile x funded profile x contracts x payout threshold, 12-month lifecycle per Lucid 50K slot.
History + 500 block-bootstrap years per combo. Run per period: python prof_grid.py IS|C24|REAL -> prof_grid_<per>.csv"""
import sys, itertools, numpy as np, pandas as pd
sys.path.insert(0, ".")
from acct_lab import META
from acct_size import life_g
from acct_life import stack, CFG
per = sys.argv[1]
U = [m for m in META["IS"] if m.startswith("U:") and m not in ("U:ICT", "U:VW13", "U:ICTF")]
NEWM = ["N:LATE15", "N:ENG0610", "N:LATEFH"]
CFG["UA_FULL"] = U + ["U:ICTF", "W:VW13b"] + NEWM
CFG["UA_NOB"] = [("U1:" + m[2:]) if ("U1:" + m[2:]) in META["IS"] else m for m in U] + ["U1:ICTF", "W:VW13b"] + NEWM
CFG["UA_SAFE"] = ["U1:ORB60", "U1:ORB90", "U1:MSEQ", "U:MSEQS", "U1:CRT11", "U1:ICTF", "U1:MOM13", "U:VW13", "U:ON07", "U:REV06"] + NEWM
WRm = sorted(m[3:] for m in META["IS"] if m.startswith("WR:"))
CFG["WR_FULL"] = ["WR:" + m for m in WRm]; CFG["WR_NOB"] = ["WR1:" + m for m in WRm]; CFG["WR_SAFE"] = ["WR1:" + m for m in WRm if m not in ("MOM11", "VOLB_tf1")]
C6m = sorted(m[3:] for m in META["IS"] if m.startswith("C6:"))
CFG["C6_FULL"] = ["C6:" + m for m in C6m]; CFG["C6_NOB"] = ["C61:" + m for m in C6m]; CFG["C6_SAFE"] = ["C61:" + m for m in C6m if m not in ("VOLB_tf0", "LON")]
GW = ["G:OD1030", "G:ENG0408", "G:SVWAP22"]; GR = GW + ["G:ASIA1R", "G:ENG0206"]
for b in ("UA", "WR", "C6"):
    for lvl in ("FULL", "NOB", "SAFE"):
        CFG[f"{b}_{lvl}_GW"] = CFG[f"{b}_{lvl}"] + GW; CFG[f"{b}_{lvl}_GR"] = CFG[f"{b}_{lvl}"] + GR
    CFG[f"{b}_FULL_none"] = CFG[f"{b}_FULL"]
EVAL = {"UA+GR": "UA_FULL_GR", "UA+GW": "UA_FULL_GW", "UA": "UA_FULL_none", "WR+GW": "WR_FULL_GW", "WR+GR": "WR_FULL_GR", "C6+GR": "C6_FULL_GR"}
FUND = {f"{b} gating +{g}": ((f"{b}_SAFE_{g}", f"{b}_NOB_{g}", f"{b}_FULL_{g}"), 750.0, 1500.0) for b in ("UA", "WR", "C6") for g in ("GW", "GR") if not (b == "C6" and g == "GR")}
FUND.update({"UA full +GW": (("UA_FULL_GW",) * 3, 0.0, 0.0), "WR full +GW": (("WR_FULL_GW",) * 3, 0.0, 0.0)})
T, D, Q, CAP, FEE = 3000.0, 2000.0, 150.0, 2000.0, 105.2
rng = np.random.default_rng({"IS": 1, "C24": 2, "REAL": 3}[per]); rows = []
EA = {k: stack(per, (v,) * 3, 0.0) for k, v in EVAL.items()}; FA = {k: (stack(per, v[0], 0.0), v[1], v[2]) for k, v in FUND.items()}
nd = next(iter(EA.values()))[0].shape[1]
IDX = [np.concatenate([np.arange(s, s + 10) % nd for s in rng.integers(0, nd, 27)])[:253] for _ in range(500)]
for (en, E), (fn, (F, c1, c2)), k, X in itertools.product(EA.items(), FA.items(), (1.0, 2.0), (4000.0, 5000.0)):
    out = np.zeros((1000, 6)); m = life_g(E[0], E[1], k, 0.0, 0.0, F[0], F[1], k, c1, c2, X, T, D, Q, CAP, FEE, 252, 3, out); L = out[:m]
    mc = []; o1 = np.zeros((2, 6))
    for idx in IDX:
        life_g(E[0][:, idx].copy(), E[1][:, idx].copy(), k, 0.0, 0.0, F[0][:, idx].copy(), F[1][:, idx].copy(), k, c1, c2, X, T, D, Q, CAP, FEE, 252, 252, o1); mc.append(o1[0].copy())
    mc = np.array(mc)
    rows.append(dict(per=per, eval=en, fund=fn, k=int(k), X=X, hist_mo=round(L[:, 0].mean() / 12), hist_p10=round(np.percentile(L[:, 0], 10) / 12),
                     mc_mo=round(mc[:, 0].mean() / 12), mc_p10=round(np.percentile(mc[:, 0], 10) / 12), mc_ploss=round(100 * (mc[:, 0] < 0).mean(), 1),
                     evals=round(mc[:, 1].mean(), 2), passes=round(mc[:, 2].mean(), 2), fbust=round(mc[:, 3].mean(), 2), payouts=round(mc[:, 4].mean(), 2)))
pd.DataFrame(rows).to_csv(f"prof_grid_{per}.csv", index=False); print(per, "done", len(rows))
