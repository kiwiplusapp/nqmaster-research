"""150K funded daily loss stop (strategy-level, account $; Lucid has none): DL in {0, 1000, 1500, 2000, 2500} on the funded tiers (3c),
eval unchanged (6c, profit stop 4200). Final profile + night modules. History / +1 tick / 1,000 bootstrap years. -> fdll150.csv"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
import prof_grid_lib
import lc_lib as L
from acct_life import CFG
from acct_policy import vec
from acct_bigger import life_q, ACC
from final_verify_lib import exits
NIGHT = ["N:NF05", "N:LF06", "N:LF0430"]
E = L.define("FD_E", CFG["UA_FULL_GR"] + NIGHT); F = tuple(L.define("FD_" + x, CFG[x] + NIGHT) for x in ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR"))
T, D, Q, CAP, FEE = ACC["150K"]; ek, fk = 6, 3; rows = []
for per in ("IS", "C24", "REAL"):
    ev = vec(per, E, 0.0, 0.4667 * T / ek); nd = len(ev[0]); ce = exits(per, E); cf = np.array([exits(per, c) for c in F])
    for DL in (0.0, 1000.0, 1500.0, 2000.0, 2500.0):
        fv = [vec(per, c, DL / fk if DL > 0 else 0.0, 0.0) for c in F]
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
            rows.append(dict(per=per, DL=DL, test=test, mo=Lr[:, 0].mean() / 12, ploss=100 * (Lr[:, 0] < 0).mean(), fbust=Lr[:, 3].mean()))
    print(per, flush=True)
R = pd.DataFrame(rows); R.to_csv("fdll150.csv", index=False); pd.set_option("display.width", 250)
P = R.pivot_table(index="DL", columns=["per", "test"], values="mo"); print(P.round(0).to_string())
S = R.groupby("DL").agg(mean9=("mo", "mean"), min9=("mo", "min"), ploss=("ploss", "max"), fbust=("fbust", "mean")); S["gana_vs_0"] = [(P.loc[d] > P.loc[0.0]).sum() for d in S.index]
print(S.round(2).to_string())
