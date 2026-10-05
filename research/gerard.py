"""Gerard Garcia style NQ opening-range breakout: range = first N minutes from 09:30; first 1-min close beyond the range
-> enter next open (direction of the break, optionally only with the daily trend). Stop: opposite side of the range
(1 tick beyond). Target: R x risk. Optional scaling-in: add a 2nd unit when price reaches +add_at R, and move the stop of
both units to breakeven. Flat 15:55. Costs: 1 tick slippage entries/stops, $1.90 RT per MNQ."""
import numpy as np, pandas as pd, itertools
from ict import load, day_levels
TICK = 0.25; SLIP = 0.25
def run(d, X, N, R, trend_only, scale, add_at=1.0, max_risk_atr=1.0):
    L, atr, trend = X
    o, h, l, c, om, day, date = d["o"], d["h"], d["l"], d["c"], d["om"], d["dayid"], d["date"]
    starts = np.where(om == 570)[0]; out = []
    for s in starts:
        dd = day[s]; a = atr[dd]
        if a <= 0: continue
        e = s
        while e < len(c) and day[e] == dd and om[e] < 955: e += 1
        rng = slice(s, s + N)
        if s + N >= e: continue
        rh = h[rng].max(); rl = l[rng].min()
        dirn = 0; i = s + N
        while i < e - 1:
            if c[i] > rh: dirn = 1; break
            if c[i] < rl: dirn = -1; break
            i += 1
        if dirn == 0 or (trend_only and dirn != trend[dd]): continue
        ent = o[i + 1] + dirn * SLIP; stop = (rl - TICK) if dirn == 1 else (rh + TICK)
        risk = (ent - stop) * dirn
        if risk <= 0 or risk > max_risk_atr * a: continue
        tp = ent + dirn * R * risk; units = [ent]; addpx = ent + dirn * add_at * risk; pnl = None
        for j in range(i + 1, e):
            if (dirn == 1 and l[j] <= stop) or (dirn == -1 and h[j] >= stop):
                px = stop - dirn * SLIP; pnl = sum(dirn * (px - u) for u in units); break
            if j > i + 1 and ((dirn == 1 and h[j] >= tp + TICK) or (dirn == -1 and l[j] <= tp - TICK)):
                pnl = sum(dirn * (tp - u) for u in units); break
            if scale and len(units) == 1 and ((dirn == 1 and h[j] >= addpx) or (dirn == -1 and l[j] <= addpx)):
                units.append(addpx + dirn * SLIP); stop = ent + dirn * TICK
        if pnl is None: pnl = sum(dirn * (c[e - 1] - dirn * SLIP - u) for u in units)
        out.append((date[s], pnl * 2 - 1.9 * len(units), risk * 2, len(units)))
    return pd.DataFrame(out, columns=["date", "usd", "risk_usd", "units"])
def pf(u): return u[u > 0].sum() / -u[u <= 0].sum()
rows = []
for tag, lo in (("nq_1m.npz", 20200201), ("mnq_fut.npz", 20240201)):
    d = load(tag); X = day_levels(d)
    for N, R, tr, sc in itertools.product((5, 15, 30), (2.0, 3.0), (False, True), (False, True)):
        df = run(d, X, N, R, tr, sc); df = df[df.date >= lo]
        parts = [("IS", df[df.date < 20240101]), ("C24", df[df.date >= 20240101])] if tag == "nq_1m.npz" else [("REAL", df)]
        for p, x in parts:
            rows.append(dict(range_min=N, R=R, trend_only=tr, scaling=sc, per=p, n=len(x), wr=round(100 * (x.usd > 0).mean(), 1), pf=round(pf(x.usd), 2), net=round(x.usd.sum())))
g = pd.DataFrame(rows).pivot_table(index=["range_min", "R", "trend_only", "scaling"], columns="per", values=["n", "wr", "pf"])
g.columns = [f"{a}_{b}" for a, b in g.columns]
print(g[["n_REAL", "wr_IS", "pf_IS", "wr_C24", "pf_C24", "wr_REAL", "pf_REAL"]].to_string())
