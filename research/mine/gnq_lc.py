"""Lifecycle $/month per account with the overnight NQ modules (gnq_port.py dense keys N:NF05, N:LF0315, N:NM22) added to the eval
profile (UA+GR) and to the funded gating tiers (UA SAFE/NOB/FULL + GR). 50K eval 2c / funded 2c (lc_lib) and 150K eval 6c / funded 3c
(acct_bigger.life_q), history / +1 tick / 1,000 bootstrap years. -> gnq_lc.csv"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
import lc_lib as L
from acct_life import CFG
from acct_policy import vec
from acct_bigger import life_q, ACC
from final_verify_lib import exits
E0 = "UA_FULL_GR"; F0 = ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR")
SETS = {"final": []}
SETS["+NF05+LF0315"] = ["N:NF05", "N:LF0315"]; SETS["+NF05+LF0315+NM22"] = ["N:NF05", "N:LF0315", "N:NM22"]; SETS["+NF05"] = ["N:NF05"]
cands = {}
for nm, extra in SETS.items():
    e = L.define(E0 + nm, CFG[E0] + extra) if extra else E0
    f = tuple(L.define(x + nm, CFG[x] + extra) for x in F0) if extra else F0
    cands[nm] = (e, f)
R50, S50 = L.run({k: (e, f, L.FIXED2) for k, (e, f) in cands.items()})
R50["cuenta"] = "50K 2c/2c"
rows = []
T, D, Q, CAP, FEE = ACC["150K"]; ek, fk = 6, 3
for per in ("IS", "C24", "REAL"):
    for nm, (e, f) in cands.items():
        ev = vec(per, e, 0.0, 0.4667 * T / ek); nd = len(ev[0]); ce = exits(per, e)
        fv = [vec(per, c, 0.0, 0.0) for c in f]; cf = np.array([exits(per, c) for c in f])
        for test in ("historia", "costo +1 tick", "Monte Carlo"):
            cst = test == "costo +1 tick"
            LO = ek * (ev[0] - (ce if cst else 0)); CL = ek * (ev[1] - (ce if cst else 0))
            f0 = fk * (np.array([v[0] for v in fv]) - (cf if cst else 0)); f1 = fk * (np.array([v[1] for v in fv]) - (cf if cst else 0))
            args = (1687.5, 3375.0, 6000.0, T, D, Q, CAP, FEE)
            if test != "Monte Carlo":
                out = np.zeros((1000, 6)); m = life_q(LO, CL, f0, f1, *args, 252, 3, out); Lr = out[:m]
            else:
                o1 = np.zeros((2, 6)); Lr = []
                for q in range(1000):
                    idx = np.concatenate([np.arange(s, s + 10) % nd for s in np.random.default_rng(31 + q).integers(0, nd, 27)])[:253]
                    life_q(LO[idx].copy(), CL[idx].copy(), f0[:, idx].copy(), f1[:, idx].copy(), *args, 252, 252, o1); Lr.append(o1[0].copy())
                Lr = np.array(Lr)
            rows.append(dict(per=per, cand=nm, test=test, mo=Lr[:, 0].mean() / 12, ploss=100 * (Lr[:, 0] < 0).mean(), fbust=Lr[:, 3].mean(), evals=Lr[:, 1].mean(), passes=Lr[:, 2].mean()))
R150 = pd.DataFrame(rows); R150["cuenta"] = "150K 6c/3c"
R = pd.concat([R50, R150]); R.to_csv("gnq_lc.csv", index=False); pd.set_option("display.width", 250)
print(R.pivot_table(index=["cuenta", "cand"], columns=["per", "test"], values="mo").round(0).to_string())
print(R.groupby(["cuenta", "cand"]).agg(mean9=("mo", "mean"), min9=("mo", "min"), ploss=("ploss", "max"), fbust=("fbust", "mean")).round(1).to_string())
