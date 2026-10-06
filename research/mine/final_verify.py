"""Final verification of the candidate profiles (Lucid 50K lifecycle): history, +1 tick per side, 1,000 bootstrap years.
Cost stress uses the number of exits per day counted on each module's realized grid (x $1 MNQ / $2 MGC per contract)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
import prof_grid_lib
from acct_life import CFG
from acct_policy import vec
from acct_lab import Z
from acct_size import life_g
T, D, Q, CAP, FEE = 3000.0, 2000.0, 150.0, 2000.0, 105.2
CAND = {  # name: (eval cfg, eval profit stop $, funded cfgs (SAFE, NOB, FULL), c1, c2, k, X)
    "MEJOR: eval UA+oroR (stop +$1.400) / fondeada UA+oroW / 2c / $4k": ("UA_FULL_GR", 1400.0, ("UA_FULL_GW",) * 3, 0, 0, 2.0, 4000.0),
    "igual sin stop de ganancia": ("UA_FULL_GR", 0.0, ("UA_FULL_GW",) * 3, 0, 0, 2.0, 4000.0),
    "igual, cobro $5k": ("UA_FULL_GR", 1400.0, ("UA_FULL_GW",) * 3, 0, 0, 2.0, 5000.0),
    "EQ2 2c (fondeada con cambio de modo)": ("UA_FULL_GR", 1400.0, ("UA_SAFE_GW", "UA_NOB_GW", "UA_FULL_GW"), 750, 1500, 2.0, 4000.0),
    "1 contrato: eval UA+oroR (stop +$700) / fondeada UA+oroW": ("UA_FULL_GR", 700.0, ("UA_FULL_GW",) * 3, 0, 0, 1.0, 4000.0),
    "Ultra anterior 2c (referencia)": ("ULTRA", 0.0, ("ULTRA",) * 3, 0, 0, 2.0, 4000.0)}
def exits(per, cfg):
    z = Z(per); n = len(z["days"]); out = np.zeros(n)
    for m in CFG[cfg]:
        if m + "|R" not in z.files: continue
        R = z[m + "|R"]; ch = (np.abs(np.diff(R, axis=1)) > 1e-6).sum(1); out += ch * (2.0 if m.startswith("G:") else 1.0)
    return out
rows = []
for per in ("IS", "C24", "REAL"):
    rng = np.random.default_rng(31); nd = len(Z(per)["days"])
    IDX = [np.concatenate([np.arange(s, s + 10) % nd for s in rng.integers(0, nd, 27)])[:253] for _ in range(1000)]
    for nm, (ec, G, fc, c1, c2, k, X) in CAND.items():
        ev = vec(per, ec, 0.0, G / k if G > 0 else 0.0); fv = [vec(per, c, 0.0, 0.0) for c in fc]
        E = [np.array([ev[0]] * 3), np.array([ev[1]] * 3)]; F = [np.array([v[0] for v in fv]), np.array([v[1] for v in fv])]
        for test in ("historia", "costo +1 tick", "Monte Carlo"):
            e0, e1, f0, f1 = E[0], E[1], F[0], F[1]
            if test == "costo +1 tick":
                ce = exits(per, ec); cf = np.array([exits(per, c) for c in fc]); e0, e1, f0, f1 = e0 - ce, e1 - ce, f0 - cf, f1 - cf
            if test != "Monte Carlo":
                out = np.zeros((1000, 6)); m = life_g(np.ascontiguousarray(e0), np.ascontiguousarray(e1), k, 0.0, 0.0, np.ascontiguousarray(f0), np.ascontiguousarray(f1), k, float(c1), float(c2), X, T, D, Q, CAP, FEE, 252, 3, out); L = out[:m]
            else:
                o1 = np.zeros((2, 6)); L = []
                for idx in IDX:
                    life_g(e0[:, idx].copy(), e1[:, idx].copy(), k, 0.0, 0.0, f0[:, idx].copy(), f1[:, idx].copy(), k, float(c1), float(c2), X, T, D, Q, CAP, FEE, 252, 252, o1); L.append(o1[0].copy())
                L = np.array(L)
            rows.append(dict(per=per, cand=nm, test=test, mo=round(L[:, 0].mean() / 12), p10=round(np.percentile(L[:, 0], 10) / 12), ploss=round(100 * (L[:, 0] < 0).mean(), 1),
                             evals=round(L[:, 1].mean(), 1), fbust=round(L[:, 3].mean(), 2), payouts=round(L[:, 4].mean(), 1)))
    print(per, flush=True)
R = pd.DataFrame(rows); R.to_csv("final_verify.csv", index=False); pd.set_option("display.width", 300); pd.set_option("display.max_colwidth", 70)
P = R.pivot_table(index="cand", columns=["per", "test"], values="mo"); print(P.to_string())
print(R.pivot_table(index="cand", columns=["per", "test"], values="p10").to_string())
print(R[R.test == "Monte Carlo"].pivot_table(index="cand", columns="per", values=["ploss", "evals", "fbust", "payouts"]).to_string())
