import numpy as np, pandas as pd, tmom
from ict import load, day_levels
def pf(u): return u[u > 0].sum() / -u[u <= 0].sum() if (u <= 0).any() and len(u) > 20 else np.nan
def vwap_side(d, t):
    om, day, h, l, c, v, o = d["om"], d["dayid"], d["h"], d["l"], d["c"], np.maximum(d["v"], 1e-9), d["o"]
    m = (om >= 570) & (om < t)
    df = pd.DataFrame(dict(date=d["date"][m], tp=((h + l + c) / 3 * v)[m], v=v[m], o=o[m], c=c[m]))
    g = df.groupby("date").agg(tp=("tp", "sum"), v=("v", "sum"), o=("o", "first"), c=("c", "last"))
    g["agree"] = np.sign(g.c - g.tp / g.v) == np.sign(g.c - g.o)
    return g.agree
rows = []
for tag, lo in (("nq_1m.npz", 20200201), ("mnq_fut.npz", 20240201)):
    d = load(tag); X = day_levels(d)
    base = tmom.run(d, X, 660, -2, 0, 0.25, 0.3, 100000, 0); base = base[base.date >= lo]
    ag11 = vwap_side(d, 660); b11 = base[base.date.map(ag11) == True].groupby("date").usd.sum()
    for t in (600, 630, 690, 720, 750, 780, 810, 840, 870, 900):
        for R in (0.3, 0.5):
            df = tmom.run(d, X, t, -2, 0, 0.25, R, 100000, 0); df = df[df.date >= lo]
            ag = vwap_side(d, t); df = df[df.date.map(ag) == True]
            daily = df.groupby("date").usd.sum(); j = pd.concat([daily, b11], axis=1).fillna(0)
            corr = np.corrcoef(j.iloc[:, 0], j.iloc[:, 1])[0, 1]
            parts = [("IS", df[df.date < 20240101]), ("C24", df[df.date >= 20240101])] if tag == "nq_1m.npz" else [("REAL", df)]
            for p, x in parts:
                rows.append(dict(t=t, R=R, per=p, n=len(x), wr=round(100 * (x.usd > 0).mean(), 1), pf=round(pf(x.usd), 2), corr=round(corr, 2)))
g = pd.DataFrame(rows).pivot_table(index=["t", "R"], columns="per", values=["n", "wr", "pf", "corr"])
g.columns = [f"{a}_{b}" for a, b in g.columns]
print(g[["n_REAL", "wr_IS", "pf_IS", "wr_C24", "pf_C24", "wr_REAL", "pf_REAL", "corr_REAL"]].to_string())
