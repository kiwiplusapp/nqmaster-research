"""Time-of-day momentum / reversal map over the whole Globex day (18:00 -> 15:55 ET).
At clock time t: direction = sign(close[t-1] - close[t-L]) (momentum) or the opposite (reversal); L can be the
session open (18:00) or the RTH open. Bracket: stop k*ATRd, target R*stop, max hold H minutes, flat 15:55 ET.
One trade per day per config. Selection must be made on CFD 2020-23; CFD 2024-26 and REAL MNQ 2024-26 are checks."""
import sys, itertools
import numpy as np, pandas as pd
from numba import njit
from ict import load, day_levels
TICK, SLIP = 0.25, 0.25


@njit(cache=True)
def sim(o, h, l, c, om, day, atr, trend, t_entry, L, rev, sk, R, H, tfil, out):
    n = len(c); k = 0; i = 0
    while i < n:
        d = day[i]; j = i; ei = -1; so = -1; ro = -1
        while j < n and day[j] == d:
            if so < 0: so = j
            if ro < 0 and om[j] >= 570 and om[j] < 960: ro = j
            if ei < 0 and om[j] == t_entry: ei = j
            j += 1
        nxt = j
        a = atr[d]
        if ei > 1 and a > 0:
            ref = np.nan
            if L == -1: ref = o[so]
            elif L == -2:
                if ro >= 0 and ro < ei: ref = o[ro]
            else:
                b = ei - L
                if b >= so: ref = c[b]
            if not np.isnan(ref) and c[ei - 1] != ref:
                dr = 1 if c[ei - 1] > ref else -1
                if rev: dr = -dr
                if tfil == 1 and dr != trend[d]: dr = 0
                if tfil == -1 and dr == trend[d]: dr = 0
                if dr != 0:
                    e = o[ei] + dr * SLIP; rk = sk * a; sl = e - dr * rk; tp = e + dr * R * rk
                    ex = np.nan; q = ei
                    while q < nxt:
                        if dr == 1:
                            if l[q] <= sl: ex = min(o[q], sl) - SLIP if q > ei else sl - SLIP; break
                            if q > ei and h[q] >= tp + TICK: ex = max(o[q], tp); break
                        else:
                            if h[q] >= sl: ex = max(o[q], sl) + SLIP if q > ei else sl + SLIP; break
                            if q > ei and l[q] <= tp - TICK: ex = min(o[q], tp); break
                        if (q - ei >= H) or (om[q] >= 955 and om[q] < 1080):
                            ex = c[q] - dr * SLIP; break
                        q += 1
                    if np.isnan(ex) and nxt - 1 > ei:
                        ex = c[nxt - 1] - dr * SLIP
                    if not np.isnan(ex):
                        out[k, 0] = dr * (ex - e); out[k, 1] = ei; out[k, 2] = rk; out[k, 3] = dr; out[k, 4] = min(q, nxt - 1); k += 1
        i = nxt
    return k


def run(D, X, t, L, rev, sk, R, H, tfil):
    L_, atr, trend = X
    out = np.zeros((6000, 5))
    k = sim(D["o"], D["h"], D["l"], D["c"], D["om"].astype(np.int64), D["dayid"].astype(np.int64), atr, trend, t, L, rev, sk, R, H, tfil, out)
    df = pd.DataFrame(dict(pts=out[:k, 0], date=D["date"][out[:k, 1].astype(np.int64)], bi=out[:k, 1].astype(np.int64), d=out[:k, 3], risk=out[:k, 2], xi=out[:k, 4].astype(np.int64)))
    df["usd"] = df.pts * 2 - 1
    return df


def pf(s):
    return s[s > 0].sum() / -s[s <= 0].sum() if (s <= 0).any() else 9.0


TIMES = [1110, 1170, 1230, 1290, 1350, 1410, 0, 60, 120, 180, 240, 300, 360, 420, 480, 540, 570, 600, 630, 660, 690, 720, 780, 840, 870, 900, 930]

if __name__ == "__main__":
    part = int(sys.argv[1]); nparts = int(sys.argv[2])
    D = {n: load(n) for n in ("nq_1m.npz", "mnq_fut.npz")}
    X = {n: day_levels(D[n]) for n in D}
    grid = list(itertools.product(TIMES, (30, 60, 120, -1, -2), (0, 1), (0.1, 0.2), (0.3, 0.5, 1.0), (60, 240, 100000), (0, 1)))
    rows = []
    for gi, (t, L, rev, sk, R, H, tfil) in enumerate(grid):
        if gi % nparts != part: continue
        if L == -2 and not (570 < t < 960): continue
        r = dict(t=t, L=L, rev=rev, sk=sk, R=R, H=H, tfil=tfil)
        for n in D:
            df = run(D[n], X[n], t, L, rev, sk, R, H, tfil)
            if n == "nq_1m.npz":
                for nm, s in (("is", df[df.date < 20240101]), ("c24", df[df.date >= 20240101])):
                    r[nm + "_n"] = len(s); r[nm + "_wr"] = round(100 * (s.usd > 0).mean(), 1) if len(s) else np.nan; r[nm + "_pf"] = round(pf(s.usd), 3) if len(s) else np.nan
            else:
                s = df[df.date >= 20240201]; r["fut_n"] = len(s); r["fut_wr"] = round(100 * (s.usd > 0).mean(), 1) if len(s) else np.nan; r["fut_pf"] = round(pf(s.usd), 3) if len(s) else np.nan
        rows.append(r)
    pd.DataFrame(rows).to_csv(f"tmom_{part}.csv", index=False)
    print(part, len(rows), "done")
