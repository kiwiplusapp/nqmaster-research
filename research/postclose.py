import itertools, numpy as np, pandas as pd
from ict import load, day_levels
TICK = 0.25
def run(D, X, sig, rev, sk, R, tf, t_in=960, t_out=1015):
    L, atr, trend = X; om, day, o, h, l, c = D["om"], D["dayid"], D["o"], D["h"], D["l"], D["c"]
    df = pd.DataFrame(dict(day=day, om=om, i=np.arange(len(c))))
    ro = df[df.om == 570].groupby("day").i.first(); last = df[df.om == 959].groupby("day").i.first(); m30 = df[df.om == 930].groupby("day").i.first()
    ent = df[df.om == t_in].groupby("day").i.first(); ex_ = df[(df.om >= t_in) & (df.om <= t_out)].groupby("day").i.last()
    out = []
    for d in ent.index:
        if d not in last.index or d not in ro.index or atr[d] <= 0: continue
        ref = o[ro[d]] if sig == "day" else (o[m30[d]] if d in m30.index else np.nan)
        if np.isnan(ref) or c[last[d]] == ref: continue
        dr = 1 if c[last[d]] > ref else -1
        if rev: dr = -dr
        if tf and dr != trend[d]: continue
        s = ent[d]; e = o[s] + dr * TICK; rk = sk * atr[d]; sl = e - dr * rk; tp = e + dr * R * rk; ex = np.nan
        for q in range(s, ex_[d] + 1):
            if (dr == 1 and l[q] <= sl) or (dr == -1 and h[q] >= sl): ex = sl - dr * TICK; break
            if q > s and ((dr == 1 and h[q] >= tp + TICK) or (dr == -1 and l[q] <= tp - TICK)): ex = tp; break
        if np.isnan(ex): ex = c[ex_[d]] - dr * TICK
        out.append((D["date"][s], dr * (ex - e) * 2 - 1.9))
    return pd.DataFrame(out, columns=["date", "usd"])
def pf(u): return round(u[u > 0].sum() / -u[u <= 0].sum(), 2) if (u <= 0).any() and len(u) > 30 else np.nan
S = {n: (load(n),) for n in ("nq_1m.npz", "mnq_fut.npz")}; S = {n: (v[0], day_levels(v[0])) for n, v in S.items()}
rows = []
for sig, rev, sk, R, tf in itertools.product(("day", "30m"), (0, 1), (0.1, 0.2), (0.5, 1.0, 9.0), (0, 1)):
    r = dict(sig=sig, rev=rev, sk=sk, R=R, tf=tf)
    for n, (D, X) in S.items():
        x = run(D, X, sig, rev, sk, R, tf)
        parts = [("IS", x[(x.date >= 20200201) & (x.date < 20240101)]), ("C24", x[x.date >= 20240101])] if n == "nq_1m.npz" else [("REAL", x[x.date >= 20240201])]
        for lab, y in parts: r[lab + "_n"] = len(y); r[lab + "_wr"] = round(100 * (y.usd > 0).mean(), 1); r[lab + "_pf"] = pf(y.usd)
    rows.append(r)
g = pd.DataFrame(rows); print(g.sort_values("IS_pf", ascending=False).head(15).to_string(index=False)); print(g[["IS_pf", "C24_pf", "REAL_pf"]].median())
