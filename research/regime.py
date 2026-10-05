import pickle, numpy as np, pandas as pd
from ict import load, day_levels
T = pickle.load(open("feat_trades2.pkl", "rb"))
def atr_ratio(tag):
    D = load(tag + ".npz"); L, atr, trend = day_levels(D)
    dd = pd.Series(D["date"]).groupby(D["dayid"]).last()        # session date per dayid
    s = pd.Series(atr, index=range(len(atr))).replace(0, np.nan)
    ratio = s / s.rolling(100, min_periods=40).median()
    gap = {}
    return pd.Series(ratio.reindex(dd.index).to_numpy(), index=dd.to_numpy()).groupby(level=0).last()
def pf(u): return round(u[u > 0].sum() / -u[u <= 0].sum(), 2) if (u <= 0).any() and len(u) >= 15 else np.nan
R = {"IS": atr_ratio("nq_1m"), "REAL": atr_ratio("mnq_fut")}; R["C24"] = R["IS"]
for p, (F, days) in T.items(): F["ar"] = F.date.map(R[p])
q1, q2 = np.nanpercentile(T["IS"][0].drop_duplicates("date").ar, [33.3, 66.7]); print("IS terciles", round(q1, 3), round(q2, 3))
for m in sorted(T["IS"][0]["mod"].unique()) + ["ALL"]:
    s = []
    for p, (F, days) in T.items():
        G = F if m == "ALL" else F[F["mod"] == m]
        s.append(f"{p}: " + " ".join(f"{pf(G.u[b])}" for b in (G.ar < q1, (G.ar >= q1) & (G.ar < q2), G.ar >= q2)))
    print(f"{m:8s} low/mid/high vol PF -> " + " | ".join(s))
pickle.dump(T, open("feat_trades2.pkl", "wb"))
