import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
import acct_lab; acct_lab._Z.clear()
from acct_size import life_g, eval_stats
from acct_life import stack, CFG
from acct_policy import GOLD
T, D, Q, CAP, FEE = 3000.0, 2000.0, 150.0, 2000.0, 105.2
ULT = [m for m in CFG["ULTRA"] if m != "U:ICT"] + ["U:ICTF"]; EXT = ["N:LATE15", "N:ENG0610", "N:LATEFH"]; ROB = ["G:ASIA1R", "G:ENG0206"]
sw = lambda l: [("W:VW13b" if m == "U:VW13" else m) for m in l]
CFG["E_old"] = ULT + GOLD + ROB; CFG["E_new"] = sw(ULT) + EXT + GOLD + ROB
for nm in ("SAFE", "NOB", "FULL"):
    b = [("U1:ICTF" if m == "U1:ICT" else ("U:ICTF" if m == "U:ICT" else m)) for m in CFG[nm]]; CFG[nm + "_old"] = b; CFG[nm + "_new"] = sw(b) + [m for m in EXT if m not in b]
rng = np.random.default_rng(7); rows = []
for per in ("IS", "C24", "REAL"):
    for v in ("old", "new"):
        E = stack(per, (f"E_{v}",) * 3, 0.0); F = stack(per, (f"SAFE_{v}", f"NOB_{v}", f"FULL_{v}"), 0.0); nd = E[0].shape[1]
        for k in (1.0, 2.0):
            out = np.zeros((10, 6)); L = []; P = []
            for b in range(2000):
                idx = np.concatenate([np.arange(s, s + 10) % nd for s in rng.integers(0, nd, 27)])[:253]
                e0, e1, f0, f1 = E[0][:, idx].copy(), E[1][:, idx].copy(), F[0][:, idx].copy(), F[1][:, idx].copy()
                life_g(e0, e1, k, 0.0, 0.0, f0, f1, k, 750.0, 1500.0, 4000.0, T, D, Q, CAP, FEE, 252, 252, out); L.append(out[0, 0])
            L = np.array(L)
            rows.append(dict(per=per, ver="ampliado" if v == "new" else "Ultra", k=int(k), mo=round(L.mean() / 12), p10=round(np.percentile(L, 10) / 12), P_loss=round(100 * (L < 0).mean(), 1)))
R = pd.DataFrame(rows); pd.set_option("display.width", 250)
print(R.pivot_table(index=["k", "ver"], columns="per", values=["mo", "p10", "P_loss"], aggfunc="first").to_string()); R.to_csv("ampliado_mc.csv", index=False)
