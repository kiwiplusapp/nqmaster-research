"""150K eval contracts vs pass rate / days / money (final + night modules, funded 3c): eval 4, 5, 6 contracts. -> eval150_easy.csv"""
import sys, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
import prof_grid_lib
import lc_lib as L
from acct_life import CFG
from acct_policy import vec
from acct_bigger import life_q, ev_q, ACC
from final_verify_lib import exits
@njit(cache=True)
def estats(LO, CL, T, D, out):
    nd = LO.shape[0]; r = 0
    for s in range(nd - 60):
        res, j = ev_q(LO, CL, s, nd, T, D); out[r, 0] = res; out[r, 1] = j - s + 1; r += 1
    return r
NIGHT = ["N:NF05", "N:LF06", "N:LF0430"]
E = L.define("EZ_E", CFG["UA_FULL_GR"] + NIGHT); F = tuple(L.define("EZ_" + x, CFG[x] + NIGHT) for x in ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR"))
T, D, Q, CAP, FEE = ACC["150K"]; fk = 3; rows = []; erows = []
for per in ("IS", "C24", "REAL"):
    ce = exits(per, E); fv = [vec(per, c, 0.0, 0.0) for c in F]; cf = np.array([exits(per, c) for c in F])
    for ek in (4, 5, 6):
        ev = vec(per, E, 0.0, 0.4667 * T / ek); nd = len(ev[0])
        o = np.zeros((nd, 2)); m = estats(ek * ev[0], ek * ev[1], T, D, o); o = o[:m]; ps = o[:, 0] == 1
        erows.append(dict(per=per, ek=ek, pasa=100 * ps.mean(), p22=100 * (ps & (o[:, 1] <= 22)).mean(), mediana=np.median(o[ps, 1]), quema=100 * (o[:, 0] == -1).mean()))
        for test in ("historia", "costo +1 tick", "Monte Carlo"):
            cst = test == "costo +1 tick"
            LO = ek * (ev[0] - (ce if cst else 0)); CL = ek * (ev[1] - (ce if cst else 0))
            f0 = fk * (np.array([v[0] for v in fv]) - (cf if cst else 0)); f1 = fk * (np.array([v[1] for v in fv]) - (cf if cst else 0)); args = (1687.5, 3375.0, 6000.0, T, D, Q, CAP, FEE)
            if test != "Monte Carlo":
                out = np.zeros((1000, 6)); mm = life_q(LO, CL, f0, f1, *args, 252, 3, out); Lr = out[:mm]
            else:
                o1 = np.zeros((2, 6)); Lr = []
                for q in range(1000):
                    idx = np.concatenate([np.arange(s, s + 10) % nd for s in np.random.default_rng(31 + q).integers(0, nd, 27)])[:253]
                    life_q(LO[idx].copy(), CL[idx].copy(), f0[:, idx].copy(), f1[:, idx].copy(), *args, 252, 252, o1); Lr.append(o1[0].copy())
                Lr = np.array(Lr)
            rows.append(dict(per=per, ek=ek, test=test, mo=Lr[:, 0].mean() / 12, ploss=100 * (Lr[:, 0] < 0).mean(), evals=Lr[:, 1].mean()))
R = pd.DataFrame(rows); ER = pd.DataFrame(erows); R.to_csv("eval150_easy.csv", index=False); pd.set_option("display.width", 200)
S = R.groupby("ek").agg(mean9=("mo", "mean"), min9=("mo", "min"), ploss=("ploss", "max"), evals=("evals", "mean")).round(1)
S = S.join(ER.groupby("ek")[["pasa", "p22", "mediana", "quema"]].mean().round(1)); print(S.to_string())
