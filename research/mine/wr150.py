"""High win-rate alternative for the 150K plan: WR70Plus (+ gold) with the night modules vs the recommended Ultra ampliado + night.
Eval 6c / funded 3c; history / +1 tick / 1,000 bootstrap years; also the trade-level WR / PF of each portfolio (REAL). -> wr150.csv"""
import sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, ".")
import prof_grid_lib
import lc_lib as L
from acct_life import CFG
from acct_policy import vec
from acct_bigger import life_q, ACC
from final_verify_lib import exits
NIGHT = ["N:NF05", "N:LF06", "N:LF0430"]
C = {"Ultra ampliado + noche (recomendado)": ("UA_FULL_GR", ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR")),
     "WR70Plus + noche, oro Robust": ("WR_FULL_GR", ("WR_SAFE_GR", "WR_NOB_GR", "WR_FULL_GR")),
     "WR70Plus + noche, oro WinRate": ("WR_FULL_GW", ("WR_SAFE_GW", "WR_NOB_GW", "WR_FULL_GW"))}
cands = {nm: (L.define("W150E_" + str(i), CFG[e] + NIGHT), tuple(L.define("W150F_" + str(i) + x, CFG[x] + NIGHT) for x in f)) for i, (nm, (e, f)) in enumerate(C.items())}
T, D, Q, CAP, FEE = ACC["150K"]; ek, fk = 6, 3; rows = []
for per in ("IS", "C24", "REAL"):
    for nm, (e, f) in cands.items():
        ev = vec(per, e, 0.0, 0.4667 * T / ek); nd = len(ev[0]); ce = exits(per, e); fv = [vec(per, c, 0.0, 0.0) for c in f]; cf = np.array([exits(per, c) for c in f])
        for test in ("historia", "costo +1 tick", "Monte Carlo"):
            cst = test == "costo +1 tick"
            LO = ek * (ev[0] - (ce if cst else 0)); CL = ek * (ev[1] - (ce if cst else 0))
            f0 = fk * (np.array([v[0] for v in fv]) - (cf if cst else 0)); f1 = fk * (np.array([v[1] for v in fv]) - (cf if cst else 0)); args = (1687.5, 3375.0, 6000.0, T, D, Q, CAP, FEE)
            if test != "Monte Carlo":
                out = np.zeros((1000, 6)); m = life_q(LO, CL, f0, f1, *args, 252, 3, out); Lr = out[:m]
            else:
                o1 = np.zeros((2, 6)); Lr = []
                for q in range(1000):
                    idx = np.concatenate([np.arange(s, s + 10) % nd for s in np.random.default_rng(31 + q).integers(0, nd, 27)])[:253]
                    life_q(LO[idx].copy(), CL[idx].copy(), f0[:, idx].copy(), f1[:, idx].copy(), *args, 252, 252, o1); Lr.append(o1[0].copy())
                Lr = np.array(Lr)
            rows.append(dict(per=per, cand=nm, test=test, mo=Lr[:, 0].mean() / 12, ploss=100 * (Lr[:, 0] < 0).mean(), fbust=Lr[:, 3].mean(), evals=Lr[:, 1].mean(), passes=Lr[:, 2].mean()))
R = pd.DataFrame(rows); R.to_csv("wr150.csv", index=False); pd.set_option("display.width", 250)
print(R.pivot_table(index="cand", columns=["per", "test"], values="mo").round(0).to_string())
S = R.groupby("cand").agg(mean9=("mo", "mean"), min9=("mo", "min"), ploss=("ploss", "max"), fbust=("fbust", "mean"), ev=("evals", "sum"), ps=("passes", "sum"))
S["pass_rate"] = 100 * S.ps / S.ev; print(S.drop(columns=["ev", "ps"]).round(1).to_string())
