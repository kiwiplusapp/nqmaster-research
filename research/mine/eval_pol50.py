"""Lucid Flex 50K eval sizing policies aimed at 'pass within 15-22 trading days'. Size (contracts on NQMaster AND GoldMaster) per day:
  cushion (equity - EOD-trailing threshold) < c1 -> kdd;  else if day >= dsw and profit < goal -> klate;  else k0.
Daily $ vectors per size k come from the eval profile (Ultra ampliado + gold Robust) with the account profit stop G (G/k per contract).
All start days of history, 3 periods; objective = P(pass <= 22 d), also P(pass), P(<= 15 d), median days. -> eval_pol50.csv"""
import sys, itertools, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
import prof_grid_lib
from acct_policy import vec
T, D, G = 3000.0, 2000.0, 1400.0
@njit(cache=True)
def run(LO, CL, k0, kdd, c1, dsw, kl, goal, out):
    nd = LO.shape[1]; r = 0
    for s in range(nd - 60):
        eq = 0.0; pk = 0.0; best = -1e9; d = s; res = 0
        while d < nd:
            thr = 100.0 if pk >= D + 100.0 else pk - D
            k = k0
            if eq - thr < c1: k = kdd
            elif d - s >= dsw and eq < goal: k = kl
            if eq + LO[k, d] <= thr: res = -1; break
            c = CL[k, d]; eq += c
            if c > best: best = c
            if eq > pk: pk = eq
            if eq >= T and best <= 0.5 * eq: res = 1; break
            d += 1
        out[r, 0] = res; out[r, 1] = d - s + 1; r += 1
    return r
rows = []
for per in ("IS", "C24", "REAL"):
    LO = np.zeros((4, 0)); CL = None
    vs = {k: vec(per, "UA_FULL_GR", 0.0, G / k) for k in (1, 2, 3)}
    nd = len(vs[1][0]); LO = np.zeros((4, nd)); CL = np.zeros((4, nd))
    for k in (1, 2, 3): LO[k] = k * vs[k][0]; CL[k] = k * vs[k][1]
    out = np.zeros((nd, 2))
    for k0, kdd, c1, dsw, kl, goal in itertools.product((1, 2, 3), (1, 2), (0.0, 1000.0, 1250.0, 1500.0, 1750.0), (5, 8, 12, 999), (1, 2, 3), (1500.0, 2100.0)):
        if kdd > k0 or (dsw == 999 and (kl != k0 or goal != 1500.0)) or (c1 == 0.0 and kdd != 1): continue
        m = run(LO, CL, k0, kdd, c1, dsw, kl, goal, out); o = out[:m]; ps = o[:, 0] == 1
        rows.append(dict(per=per, k0=k0, kdd=kdd, c1=c1, dsw=dsw, kl=kl, goal=goal, p_pass=100 * ps.mean(), p15=100 * (ps & (o[:, 1] <= 15)).mean(),
                         p22=100 * (ps & (o[:, 1] <= 22)).mean(), med=np.median(o[ps, 1]) if ps.any() else np.nan, bust=100 * (o[:, 0] == -1).mean()))
    print(per, flush=True)
R = pd.DataFrame(rows); R.to_csv("eval_pol50.csv", index=False)
K = ["k0", "kdd", "c1", "dsw", "kl", "goal"]
A = R.groupby(K).agg(p22=("p22", "mean"), p22_min=("p22", "min"), p15=("p15", "mean"), p_pass=("p_pass", "mean"), pass_min=("p_pass", "min"), med=("med", "mean"), bust=("bust", "mean")).reset_index()
pd.set_option("display.width", 250)
print("fixed sizes:"); print(A[(A.c1 == 0) & (A.dsw == 999)].round(1).to_string(index=False))
print("best by P(pass<=22d):"); print(A.sort_values("p22", ascending=False).head(15).round(1).to_string(index=False))
print("best by P(pass) with P(<=22d) >= 40:"); print(A[A.p22 >= 40].sort_values("p_pass", ascending=False).head(15).round(1).to_string(index=False))
