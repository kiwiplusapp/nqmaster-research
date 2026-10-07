"""NQ_DRIVE survivors after nqdrive_check.py (base Ultra + NF05):
  LF06   (NQ_DRIVE 2772): 04:00 -> 06:00 move >= 0.2 ATR -> FADE, any direction, stop 0.2 ATR, target 0.5R, max 240 min (WR ~74%)
  LF0430 (NQ_DRIVE 2613): 04:00 -> 04:30 move >= 0.1 ATR -> FADE, with the daily trend, stop 0.35 ATR, target 0.5R, max 240 min
Trade-level metrics vs Ultra + NF05, dense grids N:LF06 / N:LF0430, lifecycle $/month per account (50K 2c/2c, 150K 6c/3c) with NF05
in every set. -> nqdrive_port.csv, nqdrive_lc.csv"""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, ".")
from families_gold import gen_drive
from gold_port import conflict_filter
from gnq_check import U, trades, D_is, D_re
from nqdrive_check import BASE, per_slice, NF
from dense_build import dense
import lc_lib as L
from acct_life import CFG
from acct_policy import vec
from acct_bigger import life_q, ACC
from final_verify_lib import exits
P = {"LF06": dict(A=400, T=120, x=0.2, mode=-1, tf=0, k=0.2, stop=0, R=0.5, hold=240), "LF0430": dict(A=400, T=30, x=0.1, mode=-1, tf=1, k=0.35, stop=0, R=0.5, hold=240)}
NT = {(per, n): per_slice(trades(D_re if per == "REAL" else D_is, gen_drive, p, 1), per).assign(mod=n) for per in ("IS", "C24", "REAL") for n, p in P.items()}
def metrics(X, days):
    x = X.u * X.w; d = x.groupby(X.date).sum().reindex(days, fill_value=0.0)
    return dict(tpd=round(len(X) / len(days), 2), wr=round(100 * (X.u > 0).mean(), 1), pf=round(x[x > 0].sum() / -x[x <= 0].sum(), 3), sharpe=round(d.mean() / d.std() * 252 ** .5, 2), mo=round(d.mean() * 21))
rows = []
for per in ("IS", "C24", "REAL"):
    Bx, days = BASE[per]
    for nm, add in {"Ultra+NF05": [], "+LF06": ["LF06"], "+LF0430": ["LF0430"], "+LF06+LF0430": ["LF06", "LF0430"]}.items():
        X = conflict_filter(pd.concat([Bx] + [NT[(per, a)] for a in add]).sort_values(["date", "tin"]).reset_index(drop=True)); rows.append(dict(per=per, set=nm, **metrics(X, days)))
M = pd.DataFrame(rows); M.to_csv("nqdrive_port.csv", index=False); pd.set_option("display.width", 250)
print(M.pivot_table(index="set", columns="per", values=["tpd", "wr", "pf", "sharpe", "mo"], aggfunc="first").to_string(), flush=True)
RES = os.path.dirname(os.getcwd()); DN = os.path.join(RES, "tmp", "dense"); meta = pickle.load(open(os.path.join(DN, "meta.pkl"), "rb"))
for per in ("IS", "C24", "REAL"):
    z = dict(np.load(os.path.join(DN, f"{per}.npz")))
    for n in P:
        Lg, Rg = dense(NT[(per, n)], "nq", per, z["days"]); z["N:" + n + "|L"] = Lg; z["N:" + n + "|R"] = Rg
    np.savez(os.path.join(DN, f"{per}.npz"), **z); meta[per] = sorted(set(meta[per]) | {"N:" + n for n in P})
pickle.dump(meta, open(os.path.join(DN, "meta.pkl"), "wb")); print("dense added", flush=True)
E0 = "UA_FULL_GR"; F0 = ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR")
SETS = {"final+NF05": ["N:NF05"], "+LF06": ["N:NF05", "N:LF06"], "+LF0430": ["N:NF05", "N:LF0430"], "+LF06+LF0430": ["N:NF05", "N:LF06", "N:LF0430"]}
cands = {nm: (L.define(E0 + nm, CFG[E0] + ex), tuple(L.define(x + nm, CFG[x] + ex) for x in F0)) for nm, ex in SETS.items()}
R50, _ = L.run({k: (e, f, L.FIXED2) for k, (e, f) in cands.items()}); R50["cuenta"] = "50K 2c/2c"
rows = []; T, D, Q, CAP, FEE = ACC["150K"]; ek, fk = 6, 3
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
R150 = pd.DataFrame(rows); R150["cuenta"] = "150K 6c/3c"
R = pd.concat([R50, R150]); R.to_csv("nqdrive_lc.csv", index=False)
print(R.pivot_table(index=["cuenta", "cand"], columns=["per", "test"], values="mo").round(0).to_string())
print(R.groupby(["cuenta", "cand"]).agg(mean9=("mo", "mean"), min9=("mo", "min"), ploss=("ploss", "max"), fbust=("fbust", "mean")).round(1).to_string())
