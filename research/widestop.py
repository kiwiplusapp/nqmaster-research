import itertools, numpy as np, pandas as pd, tmom, intra
from ict import load, day_levels
from port_add_helpers import vwap_side
def pf(u): return round(u[u > 0].sum() / -u[u <= 0].sum(), 3) if (u <= 0).any() and len(u) >= 30 else np.nan
S = {}
for n in ("nq_1m.npz", "mnq_fut.npz"):
    D = load(n); X = day_levels(D); S[n] = (D, X, {t: vwap_side(D, t) for t in (630, 660, 690)}, intra.prep(D))
MODS = {"MOM11": (660, -2, 0, 100000, 0, True), "MOM1130": (690, -2, 0, 100000, 0, True), "MOM1030": (630, -2, 0, 60, 1, False),
        "REV06": (360, 30, 1, 240, 1, False), "MOM1030v": (630, -2, 0, 100000, 0, True)}
rows = []
for (nm, (t, L, rev, H, tf, vw)), sk, R in itertools.product(MODS.items(), (0.15, 0.2, 0.25, 0.35, 0.5, 0.7), (0.2, 0.3, 0.5)):
    r = dict(mod=nm, sk=sk, R=R)
    for n, (D, X, VW, _) in S.items():
        x = tmom.run(D, X, t, L, rev, sk, R, H, tf)
        if vw: x = x[x.date.map(VW[t]) == True]
        parts = [("IS", x[(x.date >= 20200201) & (x.date < 20240101)]), ("C24", x[x.date >= 20240101])] if n == "nq_1m.npz" else [("REAL", x[x.date >= 20240201])]
        for lab, y in parts: r[lab + "_n"] = len(y); r[lab + "_wr"] = round(100 * (y.usd > 0).mean(), 1); r[lab + "_pf"] = pf(y.usd); r[lab + "_net"] = round(y.usd.sum())
    rows.append(r)
for sk, R, K, H in itertools.product((0.15, 0.25, 0.35, 0.5), (0.2, 0.3, 0.5), (3,), (120, 240)):
    r = dict(mod=f"RSI2_H{H}", sk=sk, R=R)
    for n, (D, X, VW, P) in S.items():
        x = intra.run(P[0], P[1], P[2], "RSI2", 10, 2, sk, R, H, K, 630, 945)
        parts = [("IS", x[(x.date >= 20200201) & (x.date < 20240101)]), ("C24", x[x.date >= 20240101])] if n == "nq_1m.npz" else [("REAL", x[x.date >= 20240201])]
        for lab, y in parts: r[lab + "_n"] = len(y); r[lab + "_wr"] = round(100 * (y.usd > 0).mean(), 1); r[lab + "_pf"] = pf(y.usd); r[lab + "_net"] = round(y.usd.sum())
    rows.append(r)
g = pd.DataFrame(rows); g.to_csv("widestop.csv", index=False)
print(g[["mod", "sk", "R", "IS_n", "IS_wr", "IS_pf", "C24_wr", "C24_pf", "REAL_wr", "REAL_pf", "IS_net", "REAL_net"]].to_string(index=False))
