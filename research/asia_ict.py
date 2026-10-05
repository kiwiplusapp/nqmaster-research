"""ICT in the Asia session (the posted setups): liquidity sweep -> CISD/MSS -> entry (market / 1m-5m FVG limit / CISD limit)
-> fixed R, flat 23:59 ET. Window 20:00-23:30 ET. Levels (known before 20:00): prior RTH high/low, Globex 18:00-20:00
high/low, 19:00-20:00 high/low. SMT (ES CFD) split: ES did not take a comparable level before entry."""
import itertools, numpy as np, pandas as pd
import ict
from ict import load, day_levels
from ictx import levels
def pf(u): return round(u[u > 0].sum() / -u[u <= 0].sum(), 2) if (u <= 0).any() and len(u) >= 25 else np.nan
S = {}
for n in ("nq_1m.npz", "mnq_fut.npz"):
    D = load(n); L0, atr, trend = day_levels(D)
    L = levels(D, [(0, 1), (1080, 1200), (1140, 1200)]); L[:, 0] = L0[:, 0]; L[:, 3] = L0[:, 3]
    S[n] = (D, L, atr, trend, {tf: ict.bars(D, tf) for tf in (1, 5)})
ES = load("es_hd.npz"); Le = levels(ES, [(0, 1), (1080, 1200), (1140, 1200)]); Le[:, 0] = day_levels(ES)[0][:, 0]; Le[:, 3] = day_levels(ES)[0][:, 3]
edate = pd.Series(ES["date"]).groupby(ES["dayid"]).first(); d2e = dict(zip(edate.to_numpy(), edate.index))
es = pd.DataFrame(dict(ep=ES["epoch"], day=ES["dayid"], om=ES["om"], h=ES["h"], l=ES["l"])); es = es[es.om >= 1200]
es["hi"] = es.groupby("day").h.cummax(); es["lo"] = es.groupby("day").l.cummin(); es = es.set_index("ep")
EP = {}
for tf in (1, 5):
    Dn = S["nq_1m.npz"][0]; EP[tf] = pd.DataFrame(dict(g=Dn["epoch"] // tf, day=Dn["dayid"], ep=Dn["epoch"])).groupby(["day", "g"], sort=True).ep.first().to_numpy()
def smt_flag(df, tf):
    out = []
    for r in df.itertuples():
        e = EP[tf][r.bi] - 1; sub = es.loc[:e].tail(1); dd = d2e.get(r.date)
        if dd is None or not len(sub) or sub.day.iloc[0] != dd: out.append(np.nan); continue
        took = any(sub.hi.iloc[0] > Le[dd, q] for q in range(3) if not np.isnan(Le[dd, q])) if r.d == -1 else any(sub.lo.iloc[0] < Le[dd, q] for q in range(3, 6) if not np.isnan(Le[dd, q]))
        out.append(0.0 if took else 1.0)
    return out
rows = []
for tf, K, em, R, bias in itertools.product((1, 5), (3, 5), (0, 1, 2), (1.0, 1.5, 2.0, 3.0), (0, 1)):
    r = dict(tf=tf, K=K, em=em, R=R, bias=bias)
    for n, (D, L, atr, trend, BB) in S.items():
        df = ict.run(BB[tf], L, atr, trend, np.ones(6, np.bool_), (1200, 1410), K, em, R, bias, 0.25, M=20, max_day=2, flat=1439)
        if n == "nq_1m.npz":
            df = df[df.date >= 20200201]; df["smt"] = smt_flag(df, tf)
            for lab, x in (("IS", df[df.date < 20240101]), ("C24", df[df.date >= 20240101])):
                r[lab + "_n"] = len(x); r[lab + "_wr"] = round(100 * (x.usd > 0).mean(), 1); r[lab + "_pf"] = pf(x.usd - 0.9)
                y = x[x.smt == 1]; r[lab + "_smt_n"] = len(y); r[lab + "_smt_pf"] = pf(y.usd - 0.9)
        else:
            x = df[df.date >= 20240201]; r["REAL_n"] = len(x); r["REAL_wr"] = round(100 * (x.usd > 0).mean(), 1); r["REAL_pf"] = pf(x.usd - 0.9)
    rows.append(r)
g = pd.DataFrame(rows); g.to_csv("asia_ict.csv", index=False)
print(g.groupby(["tf", "em"])[["IS_n", "IS_wr", "IS_pf", "C24_pf", "REAL_n", "REAL_pf", "IS_smt_n", "IS_smt_pf", "C24_smt_pf"]].median().round(2).to_string())
print(g.sort_values("IS_pf", ascending=False).head(12).to_string(index=False))
