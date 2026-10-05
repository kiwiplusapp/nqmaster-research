"""Time modules with a LIMIT entry: signal at clock time t (as tmom), limit at open[t] - dir*x*ATRd, valid M minutes
(fill needs a 1-tick trade-through); bracket from the fill: stop sk*ATRd, target R*stop, max hold H from fill, flat 15:55."""
import numpy as np, pandas as pd
from numba import njit
from ict import load, day_levels
from port_add_helpers import vwap_side
TICK, SLIP = 0.25, 0.25
@njit(cache=True)
def sim(o, h, l, c, om, day, atr, trend, t_entry, L, rev, sk, R, H, tfil, x, M, out):
    n = len(c); k = 0; i = 0
    while i < n:
        d = day[i]; j = i; ei = -1; so = -1; ro = -1
        while j < n and day[j] == d:
            if so < 0: so = j
            if ro < 0 and om[j] >= 570 and om[j] < 960: ro = j
            if ei < 0 and om[j] == t_entry: ei = j
            j += 1
        nxt = j; a = atr[d]
        if ei > 1 and a > 0:
            ref = np.nan
            if L == -2:
                if ro >= 0 and ro < ei: ref = o[ro]
            else:
                b = ei - L
                if b >= so: ref = c[b]
            if not np.isnan(ref) and c[ei - 1] != ref:
                dr = 1 if c[ei - 1] > ref else -1
                if rev: dr = -dr
                if tfil == 1 and dr != trend[d]: dr = 0
                if dr != 0:
                    e = -1.0; fi = -1
                    if x <= 0:
                        e = o[ei] + dr * SLIP; fi = ei
                    else:
                        lim = o[ei] - dr * x * a
                        for q in range(ei, min(ei + M, nxt)):
                            if om[q] >= 955 and om[q] < 1080: break
                            if (dr == 1 and l[q] <= lim - TICK) or (dr == -1 and h[q] >= lim + TICK):
                                e = min(lim, o[q]) if dr == 1 else max(lim, o[q]); fi = q; break
                    if fi >= 0:
                        rk = sk * a; sl = e - dr * rk; tp = e + dr * R * rk; ex = np.nan; q = fi
                        while q < nxt:
                            if dr == 1:
                                if l[q] <= sl: ex = min(o[q], sl) - SLIP if q > fi else sl - SLIP; break
                                if q > fi and h[q] >= tp + TICK: ex = max(o[q], tp); break
                            else:
                                if h[q] >= sl: ex = max(o[q], sl) + SLIP if q > fi else sl + SLIP; break
                                if q > fi and l[q] <= tp - TICK: ex = min(o[q], tp); break
                            if (q - fi >= H) or (om[q] >= 955 and om[q] < 1080):
                                ex = c[q] - dr * SLIP; break
                            q += 1
                        if np.isnan(ex) and nxt - 1 > fi: ex = c[nxt - 1] - dr * SLIP
                        if not np.isnan(ex):
                            out[k, 0] = dr * (ex - e); out[k, 1] = ei; k += 1
        i = nxt
    return k
def run(D, X, t, L, rev, sk, R, H, tfil, x, M):
    _, atr, trend = X; out = np.zeros((6000, 2))
    k = sim(D["o"], D["h"], D["l"], D["c"], D["om"].astype(np.int64), D["dayid"].astype(np.int64), atr, trend, t, L, rev, sk, R, H, tfil, x, M, out)
    return pd.DataFrame(dict(date=D["date"][out[:k, 1].astype(np.int64)], usd=out[:k, 0] * 2 - 1.9))
def pf(u): return round(u[u > 0].sum() / -u[u <= 0].sum(), 3) if (u <= 0).any() and len(u) > 30 else np.nan
MODS = {"MOM11": (660, -2, 0, 0.25, 0.3, 100000, 0, True), "MOM1030": (630, -2, 0, 0.2, 0.3, 60, 1, False), "REV06": (360, 30, 1, 0.2, 0.3, 240, 1, False),
        "ON07": (420, 30, 0, 0.2, 1.0, 60, 1, False), "MOM13": (780, -2, 0, 0.2, 1.0, 240, 1, False)}
if __name__ == "__main__":
    S = {}
    for n in ("nq_1m.npz", "mnq_fut.npz"):
        D = load(n); S[n] = (D, day_levels(D), {t: vwap_side(D, t) for t in (660,)})
    rows = []
    for nm, (t, L, rev, sk, R, H, tf, vw) in MODS.items():
        for x, M in ((0, 0), (0.02, 5), (0.02, 15), (0.05, 5), (0.05, 15), (0.05, 30), (0.1, 30), (0.1, 60)):
            r = dict(mod=nm, x=x, M=M)
            for n, (D, X, VW) in S.items():
                df = run(D, X, t, L, rev, sk, R, H, tf, x, M)
                if vw: df = df[df.date.map(VW[t]) == True]
                parts = [("IS", df[(df.date >= 20200201) & (df.date < 20240101)]), ("C24", df[df.date >= 20240101])] if n == "nq_1m.npz" else [("REAL", df[df.date >= 20240201])]
                for lab, y in parts: r[lab + "_n"] = len(y); r[lab + "_wr"] = round(100 * (y.usd > 0).mean(), 1); r[lab + "_pf"] = pf(y.usd); r[lab + "_net"] = round(y.usd.sum())
            rows.append(r)
    g = pd.DataFrame(rows); g.to_csv("limitentry.csv", index=False)
    print(g[["mod", "x", "M", "IS_n", "IS_wr", "IS_pf", "IS_net", "C24_pf", "C24_net", "REAL_n", "REAL_wr", "REAL_pf", "REAL_net"]].to_string(index=False))
