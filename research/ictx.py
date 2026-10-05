"""ICT sweep + CISD on other windows with window-appropriate levels (levels fixed before the window opens)."""
import itertools, numpy as np, pandas as pd
import ict
from ict import load, day_levels
def levels(D, spans):
    om, day, h, l = D["om"], D["dayid"], D["h"], D["l"]; nd = int(day.max()) + 1
    df = pd.DataFrame(dict(day=day, om=om, h=h, l=l))
    L = np.full((nd, 6), np.nan)
    for j, (a, b) in enumerate(spans):
        m = ((df.om >= a) & (df.om < b)) if a < b else ((df.om >= a) | (df.om < b))
        g = df[m].groupby("day").agg(h=("h", "max"), l=("l", "min")).reindex(range(nd))
        L[:, j] = g.h.to_numpy(); L[:, 3 + j] = g.l.to_numpy()
    return L
def pf(u): return round(u[u > 0].sum() / -u[u <= 0].sum(), 3) if (u <= 0).any() and len(u) >= 30 else np.nan
SETS = {"IB->10:30-12:00": ([(570, 630), (1080, 570), (570, 600)], (630, 720)),
        "IB->10:30-15:00": ([(570, 630), (1080, 570), (570, 600)], (630, 900)),
        "AM->12:00-15:00": ([(570, 720), (630, 720), (570, 630)], (720, 900)),
        "Asia->London 02-05": ([(1080, 120), (1260, 120), (0, 120)], (120, 300)),
        "Asia->London 02-08": ([(1080, 120), (1260, 120), (0, 120)], (120, 480)),
        "ON->premkt 08-09:30": ([(1080, 480), (120, 300), (300, 480)], (480, 570)),
        "BASE 09:30-10:30": (None, (570, 630))}
rows = []
S = {}
for n in ("nq_1m.npz", "mnq_fut.npz"):
    D = load(n); L0, atr, trend = day_levels(D); S[n] = (D, L0, atr, trend, {tf: ict.bars(D, tf) for tf in (1, 5)})
for (nm, (spans, win)), tf, K, em, R, bias in itertools.product(SETS.items(), (1, 5), (3, 5), (0, 2), (1.0, 1.5, 2.0), (0, 1)):
    r = dict(set=nm, tf=tf, K=K, em=em, R=R, bias=bias)
    for n, (D, L0, atr, trend, BB) in S.items():
        L = L0 if spans is None else levels(D, spans)
        df = ict.run(BB[tf], L, atr, trend, np.ones(6, np.bool_), win, K, em, R, bias, 0.25)
        parts = [("IS", df[(df.date >= 20200201) & (df.date < 20240101)]), ("C24", df[df.date >= 20240101])] if n == "nq_1m.npz" else [("REAL", df[df.date >= 20240201])]
        for lab, x in parts:
            r[lab + "_n"] = len(x); r[lab + "_wr"] = round(100 * (x.usd > 0).mean(), 1) if len(x) else np.nan; r[lab + "_pf"] = pf(x.usd)
    rows.append(r)
g = pd.DataFrame(rows); g.to_csv("ictx.csv", index=False)
print(g.groupby(["set", "bias"])[["IS_n", "IS_wr", "IS_pf", "C24_pf", "REAL_n", "REAL_pf"]].median().round(2).to_string())
print(g[g.IS_pf >= 1.3].sort_values("IS_pf", ascending=False).head(30).to_string(index=False))
