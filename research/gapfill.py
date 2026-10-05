"""RTH-open gap fade toward the prior RTH close. Entry at 09:30 open (+1 tick) against the gap if gap/ATRd in [gmin,gmax];
target = fraction f of the gap (f=1 full fill), stop = k x gap beyond entry (min 0.05 ATR), exit by time T. Optional trend filter."""
import itertools, numpy as np, pandas as pd
from ict import load, day_levels
TICK = 0.25
def run(D, X, gmin, gmax, f, k, T, tf):
    L, atr, trend = X
    om, day, o, h, l, c = D["om"], D["dayid"], D["o"], D["h"], D["l"], D["c"]
    df = pd.DataFrame(dict(day=day, om=om, i=np.arange(len(c))))
    r = df[(df.om >= 570) & (df.om < 960)].groupby("day").agg(s=("i", "first"), e=("i", "last"), fo=("om", "first"))
    closes = pd.Series(c[r.e.to_numpy()], index=r.index); full = pd.Series(om[r.e.to_numpy()] >= 959, index=r.index)
    pc = closes.where(full).shift(1)
    out = []
    for d, row in r.iterrows():
        if row.fo != 570 or np.isnan(pc.get(d, np.nan)) or atr[d] <= 0: continue
        s = row.s; gap = o[s] - pc[d]; a = atr[d]
        if not (gmin <= abs(gap) / a < gmax): continue
        dr = -1 if gap > 0 else 1
        if tf == 1 and dr != trend[d]: continue
        if tf == -1 and dr == trend[d]: continue
        e = o[s] + dr * TICK; tp = e + dr * f * abs(gap); sl = e - dr * max(k * abs(gap), 0.05 * a)
        ex = np.nan
        for q in range(s, row.e + 1):
            if (dr == 1 and l[q] <= sl) or (dr == -1 and h[q] >= sl): ex = sl - dr * TICK; break
            if q > s and ((dr == 1 and h[q] >= tp + TICK) or (dr == -1 and l[q] <= tp - TICK)): ex = tp; break
            if om[q] >= T: ex = c[q] - dr * TICK; break
        if np.isnan(ex): ex = c[row.e] - dr * TICK
        out.append((D["date"][s], dr * (ex - e) * 2 - 1))
    return pd.DataFrame(out, columns=["date", "usd"])
def pf(u): return round(u[u > 0].sum() / -u[u <= 0].sum(), 3) if (u <= 0).any() and len(u) >= 30 else np.nan
if __name__ == "__main__":
    S = {n: (load(n),) for n in ("nq_1m.npz", "mnq_fut.npz")}
    S = {n: (v[0], day_levels(v[0])) for n, v in S.items()}
    rows = []
    for (gmin, gmax), f, k, T, tf in itertools.product(((0.05, 0.25), (0.1, 0.4), (0.25, 0.6), (0.05, 0.6)), (0.5, 1.0), (1.0, 2.0), (630, 720), (0, 1, -1)):
        r = dict(g=f"{gmin}-{gmax}", f=f, k=k, T=T, tf=tf)
        for n, (D, X) in S.items():
            x = run(D, X, gmin, gmax, f, k, T, tf)
            parts = [("IS", x[(x.date >= 20200201) & (x.date < 20240101)]), ("C24", x[x.date >= 20240101])] if n == "nq_1m.npz" else [("REAL", x[x.date >= 20240201])]
            for lab, y in parts: r[lab + "_n"] = len(y); r[lab + "_wr"] = round(100 * (y.usd > 0).mean(), 1); r[lab + "_pf"] = pf(y.usd)
        rows.append(r)
    g = pd.DataFrame(rows); g.to_csv("gapfill.csv", index=False)
    print(g.groupby(["g", "tf"])[["IS_n", "IS_wr", "IS_pf", "C24_pf", "REAL_pf"]].median().round(2).to_string())
    print(g.sort_values("IS_pf", ascending=False).head(15).to_string(index=False))
