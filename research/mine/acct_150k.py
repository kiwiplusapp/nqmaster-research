"""Refine the 150K LucidFlex sizing (acct_bigger.py found 150K > 100K > 50K per account): eval k 4-7 x funded k 3-5, plus funded
cushion tiers x payout threshold for the best pair. -> acct_150k.csv"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
from acct_bigger import life_q, ACC
from acct_policy import vec
from final_verify_lib import exits
T, D, Q, CAP, FEE = ACC["150K"]; G = 0.4667 * T
CANDS = [(ek, fk, 1687.5, 3375.0, 6000.0) for ek in (4, 5, 6, 7) for fk in (3, 4, 5)]
CANDS += [(6, 4, c1, c2, X) for c1, c2 in ((1000.0, 2500.0), (2500.0, 4500.0)) for X in (6000.0,)] + [(6, 4, 1687.5, 3375.0, X) for X in (7000.0, 9000.0)]
rows = []
for per in ("IS", "C24", "REAL"):
    ce = exits(per, "UA_FULL_GR"); FC = ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR"); fv = [vec(per, c, 0.0, 0.0) for c in FC]; cf = np.array([exits(per, c) for c in FC])
    evs = {}
    for ek, fk, c1, c2, X in CANDS:
        if ek not in evs: evs[ek] = vec(per, "UA_FULL_GR", 0.0, G / ek)
        ev = evs[ek]; nd = len(ev[0])
        for test in ("historia", "costo +1 tick", "Monte Carlo"):
            cst = test == "costo +1 tick"
            LO = ek * (ev[0] - (ce if cst else 0)); CL = ek * (ev[1] - (ce if cst else 0))
            f0 = fk * (np.array([v[0] for v in fv]) - (cf if cst else 0)); f1 = fk * (np.array([v[1] for v in fv]) - (cf if cst else 0))
            args = (c1, c2, X, T, D, Q, CAP, FEE)
            if test != "Monte Carlo":
                out = np.zeros((1000, 6)); m = life_q(LO, CL, f0, f1, *args, 252, 3, out); Lr = out[:m]
            else:
                o1 = np.zeros((2, 6)); Lr = []
                for q in range(1000):
                    idx = np.concatenate([np.arange(s, s + 10) % nd for s in np.random.default_rng(31 + q).integers(0, nd, 27)])[:253]
                    life_q(LO[idx].copy(), CL[idx].copy(), f0[:, idx].copy(), f1[:, idx].copy(), *args, 252, 252, o1); Lr.append(o1[0].copy())
                Lr = np.array(Lr)
            rows.append(dict(per=per, k_eval=ek, k_fondeada=fk, c1=c1, c2=c2, X=X, test=test, mo=Lr[:, 0].mean() / 12, ploss=100 * (Lr[:, 0] < 0).mean(),
                             evals=Lr[:, 1].mean(), passes=Lr[:, 2].mean(), fbust=Lr[:, 3].mean(), payouts=Lr[:, 4].mean(), dtp=Lr[:, 5].mean()))
    print(per, flush=True)
R = pd.DataFrame(rows); R.to_csv("acct_150k.csv", index=False); pd.set_option("display.width", 250)
K = ["k_eval", "k_fondeada", "c1", "c2", "X"]
S = R.groupby(K).agg(mean9=("mo", "mean"), min9=("mo", "min"), ploss=("ploss", "max"), evals=("evals", "mean"), fbust=("fbust", "mean"), payouts=("payouts", "mean"), dias_eval=("dtp", "mean")).reset_index()
S["pass_rate"] = (100 * R.groupby(K).passes.sum() / R.groupby(K).evals.sum()).values
print(S.round(1).sort_values("mean9", ascending=False).to_string(index=False))
