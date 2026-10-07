"""Reusable 150K (eval 6c / funded 3c) lifecycle comparison: python lc150.py "<name>=<extra keys comma separated>" ...
Base = final profile + night modules (N:NF05, N:LF06, N:LF0430). Each argument adds keys to eval and funded tiers. Fresh process (dense
read once). History / +1 tick / 1,000 bootstrap years on IS / C24 / REAL. Prints 9-test table, mean, min, and wins vs base."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
import prof_grid_lib
import lc_lib as L
from acct_life import CFG
from acct_lab import Z
from acct_policy import vec
from acct_bigger import life_q, ACC
from final_verify_lib import exits
NIGHT = ["N:NF05", "N:LF06", "N:LF0430"]
E0 = "UA_FULL_GR"; F0 = ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR")
SETS = {"base (final + nocturnos)": []}
for a in sys.argv[1:]:
    nm, keys = a.split("="); SETS[nm] = [k for k in keys.split(",") if k]
for keys in SETS.values():
    for per in ("IS", "C24", "REAL"):
        for k in keys: assert k + "|L" in Z(per).files, (per, k)
cands = {nm: (L.define("E150_" + nm, CFG[E0] + NIGHT + ex), tuple(L.define(x + "_150_" + nm, CFG[x] + NIGHT + ex) for x in F0)) for nm, ex in SETS.items()}
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
            rows.append(dict(per=per, cand=nm, test=test, mo=Lr[:, 0].mean() / 12, ploss=100 * (Lr[:, 0] < 0).mean(), fbust=Lr[:, 3].mean()))
R = pd.DataFrame(rows); pd.set_option("display.width", 250)
P = R.pivot_table(index="cand", columns=["per", "test"], values="mo"); print(P.round(0).to_string())
b = P.loc["base (final + nocturnos)"]
S = R.groupby("cand").agg(mean9=("mo", "mean"), min9=("mo", "min"), ploss=("ploss", "max"), fbust=("fbust", "mean")); S["gana_vs_base"] = [(P.loc[c] > b).sum() for c in S.index]
print(S.round(1).to_string()); R.to_csv("lc150_last.csv", index=False)
