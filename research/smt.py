"""SMT divergence (NQ vs ES) on ICT open sweeps. For each ICT trade (NQ, 5m), at the entry bar: did ES also take a comparable
liquidity level (PDH/ONH/LonH for shorts, lows for longs) between 09:30 and the entry? SMT = ES did NOT (divergence)."""
import itertools, numpy as np, pandas as pd
import ict
from ict import load, day_levels
NQ = load("nq_1m.npz"); ES = load("es_hd.npz")
Ln, atr, trend = day_levels(NQ); Le, _, _ = day_levels(ES)
ed = pd.Series(np.arange(int(ES["dayid"].max()) + 1)); edate = pd.Series(ES["date"]).groupby(ES["dayid"]).first()
date2esday = dict(zip(edate.to_numpy(), edate.index))
es = pd.DataFrame(dict(ep=ES["epoch"], day=ES["dayid"], om=ES["om"], h=ES["h"], l=ES["l"]))
es = es[(es.om >= 570) & (es.om < 960)]
es["hi"] = es.groupby("day").h.cummax(); es["lo"] = es.groupby("day").l.cummin(); es = es.set_index("ep")
B5 = ict.bars(NQ, 5); ep5 = (pd.DataFrame(dict(g=NQ["epoch"] // 5, day=NQ["dayid"], ep=NQ["epoch"])).groupby(["day", "g"], sort=True).ep.first().to_numpy())
def pf(u): return round(u[u > 0].sum() / -u[u <= 0].sum(), 2) if (u <= 0).any() and len(u) > 15 else np.nan
rows = []
for K, em, R, bias, mx in itertools.product((3, 4, 5), (0, 2), (1.0, 1.5, 2.0), (0, 1), (0.25, 0.5)):
    df = ict.run(B5, Ln, atr, trend, np.ones(6, np.bool_), (570, 630), K, em, R, bias, mx)
    df = df[df.date >= 20200201]
    smt = []
    for r in df.itertuples():
        e = ep5[r.bi] - 1                               # last closed 1m before entry bar
        sub = es.loc[:e].tail(1) if e in es.index else es.loc[:e].tail(1)
        dd = date2esday.get(r.date)
        if dd is None or not len(sub) or sub.day.iloc[0] != dd: smt.append(np.nan); continue
        if r.d == -1: took = any(sub.hi.iloc[0] > Le[dd, q] for q in range(3) if not np.isnan(Le[dd, q]))
        else: took = any(sub.lo.iloc[0] < Le[dd, q] for q in range(3, 6) if not np.isnan(Le[dd, q]))
        smt.append(0.0 if took else 1.0)
    df["smt"] = smt
    r = dict(K=K, em=em, R=R, bias=bias, mx=mx)
    for lab, x in (("IS", df[df.date < 20240101]), ("C24", df[df.date >= 20240101])):
        for s in (0, 1):
            y = x[x.smt == s]; r[f"{lab}_smt{s}_n"] = len(y); r[f"{lab}_smt{s}_pf"] = pf(y.usd); r[f"{lab}_smt{s}_wr"] = round(100 * (y.usd > 0).mean(), 1)
        r[f"{lab}_all_pf"] = pf(x.usd)
    rows.append(r)
g = pd.DataFrame(rows); g.to_csv("smt.csv", index=False)
cols = [c for c in g.columns if "pf" in c or "_n" in c]
print(g.groupby("bias")[cols].median().round(2).T.to_string())
