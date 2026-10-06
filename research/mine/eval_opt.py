"""Eval-speed optimization by module weights (contracts per module) - the only lever that raises BOTH pass rate and speed is the
daily mean / variance ratio. Weights fitted on IS (2020-23 CFD) only, checked on C24 (2024-26 CFD) and REAL (2024-26 MNQ/MGC).
Steps: per-module daily close/low; IS mean + covariance -> long-only max-Sharpe weights (projected gradient), and a greedy integer
allocation (contracts 0-3 per module) maximizing the IS eval objective; all scored by the Lucid eval simulator. -> eval_opt.csv"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
import prof_grid_lib
from acct_life import CFG
from acct_lab import Z
from acct_policy import day_vectors
from acct_size import eval_stats
T, D = 3000.0, 2000.0
MODS = CFG["UA_FULL_GR"]
def grids(per):
    z = Z(per); return {m: (z[m + "|L"].astype(np.float32), z[m + "|R"].astype(np.float32)) for m in MODS if m + "|L" in z.files}
G = {p: grids(p) for p in ("IS", "C24", "REAL")}
DAY = {p: np.array([G[p][m][1][:, -1] for m in MODS]) for p in G}       # modules x days realized close (1 contract)
def portfolio(per, w, PS=0.0):
    L = np.zeros_like(next(iter(G[per].values()))[0]); R = np.zeros_like(L)
    for m, x in zip(MODS, w):
        if x: L += x * G[per][m][0]; R += x * G[per][m][1]
    return day_vectors(L, R, 0.0, PS)
def ev(per, w, PS=1400.0):
    lo, cl = portfolio(per, w, PS); LO = np.ascontiguousarray(np.array([lo] * 3)); CL = np.ascontiguousarray(np.array([cl] * 3))
    out = np.zeros((len(lo), 2)); m = eval_stats(LO, CL, 1.0, 0.0, 0.0, T, D, out); o = out[:m]; ps = o[:, 0] == 1
    return dict(p_pass=100 * ps.mean(), p15=100 * (ps & (o[:, 1] <= 15)).mean(), p22=100 * (ps & (o[:, 1] <= 22)).mean(),
                med=float(np.median(o[ps, 1])) if ps.any() else np.nan, bust=100 * (o[:, 0] == -1).mean(), mu=cl.mean(), sd=cl.std(), lo5=np.percentile(lo, 5))
# per-module stats on IS
X = DAY["IS"]; mu = X.mean(1); C = np.cov(X)
st = pd.DataFrame(dict(mod=MODS, mu_IS=mu, sd_IS=np.sqrt(np.diag(C)), sh_IS=mu / np.sqrt(np.diag(C)) * np.sqrt(252),
                       mu_C24=DAY["C24"].mean(1), mu_REAL=DAY["REAL"].mean(1)))
print(st.round(2).to_string(index=False))
# long-only max-Sharpe weights on IS (projected gradient on Sharpe)
w = np.ones(len(MODS))
for it in range(4000):
    s2 = w @ C @ w; m_ = w @ mu; g = mu / np.sqrt(s2) - m_ * (C @ w) / s2 ** 1.5
    w = np.maximum(w + 0.5 * g / np.abs(g).max(), 0); w *= len(MODS) / w.sum()
print("max-Sharpe weights (sum = n mods):", dict(zip(MODS, w.round(2))))
rows = []
def score(name, wv, scales=(1.0, 1.5, 2.0, 2.5, 3.0), PS=1400.0):
    for sc in scales:
        for per in ("IS", "C24", "REAL"):
            r = ev(per, sc * np.asarray(wv), PS); rows.append(dict(name=name, scale=sc, per=per, **{k: round(v, 2) for k, v in r.items()}))
score("base (1c each)", np.ones(len(MODS)))
# integer version of the max-Sharpe weights: contracts = round(w / median positive w), capped 0-3
wi = np.clip(np.round(w / np.median(w[w > 0])), 0, 3); print("integer max-Sharpe:", dict(zip(MODS, wi)))
score("max-Sharpe integer", wi, scales=(0.5, 1.0, 1.5, 2.0))
# greedy integer allocation on IS: start 1c each at scale 2; try +-1 contract per module, keep moves that raise IS p22 + 0.5 p_pass
def obj(r): return r["p22"] + 0.5 * r["p_pass"]
cur = 2 * np.ones(len(MODS)); best = obj(ev("IS", cur)); improved = True
while improved:
    improved = False
    for i in range(len(MODS)):
        for dlt in (-1, 1):
            c2 = cur.copy(); c2[i] += dlt
            if c2[i] < 0 or c2[i] > 4: continue
            o = obj(ev("IS", c2))
            if o > best + 0.3: best, cur, improved = o, c2, True
    print("greedy", best, dict(zip(MODS, cur)), flush=True)
score("greedy IS integer", cur, scales=(0.5, 1.0, 1.5))
R = pd.DataFrame(rows); R.to_csv("eval_opt.csv", index=False)
pd.set_option("display.width", 250)
print(R.pivot_table(index=["name", "scale"], columns="per", values=["p_pass", "p22", "med", "bust"]).round(1).to_string())
np.save("eval_opt_w.npy", np.array([w, wi, cur]))
