"""Time-based daily filler: at a clock time enter in the direction of (close vs RTH VWAP) or (close vs RTH open),
stop k*ATRd, target R*stop, flat 15:55. Evaluates WR/PF on CFD 2020-23, CFD 2024-26 and real futures."""
import itertools, numpy as np, pandas as pd
from numba import njit
from ict import load, day_levels
TICK, SLIP = 0.25, 0.25

@njit(cache=True)
def sim(o, h, l, c, v, om, day, atr, trend, t_entry, rule, sk, R, tf, out):
    n = len(c); k = 0; i = 0
    while i < n:
        d = day[i]
        # find RTH start and entry bar of this day
        j = i; pv = 0.0; vv = 0.0; ro = np.nan; ei = -1
        while j < n and day[j] == d:
            if om[j] >= 570 and om[j] < 960:
                if np.isnan(ro): ro = o[j]
                if om[j] < t_entry:
                    w = max(v[j], 1e-9); pv += (h[j] + l[j] + c[j]) / 3 * w; vv += w
            if om[j] == t_entry and ei < 0: ei = j
            j += 1
        nxt = j
        a = atr[d]
        if ei > 0 and vv > 0 and a > 0 and not np.isnan(ro):
            ref = pv / vv if rule == 0 else ro
            cl = c[ei - 1]
            dr = 1 if cl > ref else -1
            if rule == 2: dr = trend[d]
            if tf == 1 and trend[d] != 0 and dr != trend[d]: dr = 0
            if dr != 0:
                e = o[ei] + dr * SLIP; rk = sk * a; sl = e - dr * rk; tp = e + dr * R * rk
                ex = np.nan
                for q in range(ei, nxt):
                    if dr == 1:
                        if l[q] <= sl: ex = sl - SLIP; break
                        if q > ei and h[q] >= tp + TICK: ex = tp; break
                    else:
                        if h[q] >= sl: ex = sl + SLIP; break
                        if q > ei and l[q] <= tp - TICK: ex = tp; break
                    if om[q] >= 955: ex = c[q] - dr * SLIP; break
                if not np.isnan(ex):
                    out[k, 0] = dr * (ex - e); out[k, 1] = ei; out[k, 2] = rk; k += 1
        i = nxt
    return k

def run(d, L, atr, trend, t, rule, sk, R, tf):
    out = np.zeros((5000, 3))
    k = sim(d["o"], d["h"], d["l"], d["c"], d["v"], d["om"].astype(np.int64), d["dayid"].astype(np.int64), atr, trend, t, rule, sk, R, tf, out)
    df = pd.DataFrame(dict(pts=out[:k, 0], date=d["date"][out[:k, 1].astype(np.int64)], risk=out[:k, 2]))
    df["usd"] = df.pts * 2 - 1
    return df
def pf(s): return s[s > 0].sum() / -s[s <= 0].sum() if (s <= 0).any() else 9
if __name__ == "__main__":
    D = {n: load(n) for n in ("nq_1m.npz", "mnq_fut.npz")}
    X = {n: day_levels(D[n]) for n in D}
    rows = []
    for t, rule, sk, R, tf in itertools.product((600, 630, 660, 720, 780, 840), (0, 1, 2), (0.1, 0.15, 0.25), (0.3, 0.5, 1.0), (0, 1)):
        r = dict(t=t, rule=rule, sk=sk, R=R, tf=tf)
        for n in D:
            L, atr, trend = X[n]
            df = run(D[n], L, atr, trend, t, rule, sk, R, tf)
            if n == "nq_1m.npz":
                for nm, s in (("is", df[df.date < 20240101]), ("c24", df[df.date >= 20240101])):
                    r[nm + "_n"] = len(s); r[nm + "_wr"] = round(100 * (s.usd > 0).mean(), 1); r[nm + "_pf"] = round(pf(s.usd), 3)
            else:
                s = df[df.date >= 20240201]; r["fut_n"] = len(s); r["fut_wr"] = round(100 * (s.usd > 0).mean(), 1); r["fut_pf"] = round(pf(s.usd), 3)
        rows.append(r)
    g = pd.DataFrame(rows); g.to_csv("timefill.csv", index=False)
    g["m"] = g[["is_pf", "c24_pf", "fut_pf"]].min(axis=1)
    print(g.sort_values("m", ascending=False).head(20).to_string(index=False))
