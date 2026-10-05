"""Overnight drift on NQ (inside one Globex session, so it is allowed by intraday prop rules: flat before 16:59 ET).
Entry at clock time A (session minute), exit at clock time B, optional wide stop k*ATR, direction: long / long only if daily
trend up / with trend (long or short). Costs: 1 tick + $1.90. Reported for CFD 2020-23, CFD 2024-26, MNQ real 2024-26 and
cost-normalised 2015-19 / 2020-23 / 2024-26 on the long CFD file."""
import os, sys, itertools, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
from core import Data, S
@njit(cache=True)
def sim(o, h, l, c, sm, ds, de, atr, trend, dow, A, B, k, mode, skipmon, out):
    n = 0
    for d in range(len(ds)):
        if ds[d] < 0 or atr[d] <= 0: continue
        if skipmon and dow[d] == 0: continue
        s = 1
        if mode == 1 and trend[d] != 1: continue
        if mode == 2: s = trend[d]
        if s == 0: continue
        a = -1; b = -1
        for q in range(ds[d], de[d] + 1):
            if a < 0 and sm[q] >= A: a = q
            if sm[q] < B: b = q
        if a < 0 or b <= a: continue
        e = o[a] + s * 0.25; stop = e - s * k * atr[d]; x = np.nan
        for q in range(a, b + 1):
            if (s == 1 and l[q] <= stop) or (s == -1 and h[q] >= stop):
                x = (min(o[q], stop) if s == 1 else max(o[q], stop)) - s * 0.25; break
        if np.isnan(x): x = c[b] - s * 0.25
        out[n, 0] = d; out[n, 1] = s * (x - e); out[n, 2] = atr[d]; n += 1
    return n
def run(D, A, B, k, mode, skipmon):
    dates = pd.to_datetime(pd.Series(D.daydate).astype(str), format="%Y%m%d", errors="coerce")
    dow = dates.dt.dayofweek.fillna(-1).astype(int).to_numpy()
    out = np.zeros((D.nd, 3)); n = sim(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr.astype(np.float64), D.trend, dow, S(A), S(B), k, mode, skipmon, out)
    o = out[:n]; return pd.DataFrame(dict(date=D.daydate[o[:, 0].astype(int)], pts=o[:, 1], atr=o[:, 2]))
def pf(x): return round(float(x[x > 0].sum() / -x[x <= 0].sum()), 3) if (x <= 0).any() else np.nan
DN, DM, DL = Data("nq_1m.npz"), Data("mnq_fut.npz"), Data("nqhd_long.npz")
rows = []
for A, B, k, mode, sk in itertools.product((1800, 1900, 2000), (300, 700, 900, 929), (0.5, 9.0), (0, 1, 2), (0, 1)):
    r = dict(A=A, B=B, k=k, mode=["long", "long si tendencia", "con tendencia"][mode], skipmon=sk)
    x = run(DN, A, B, k, mode, sk); u = x.pts * 2 - 1.9
    for lab, m in (("IS", (x.date >= 20200201) & (x.date < 20240101)), ("C24", x.date >= 20240101)):
        r[lab + "_n"] = int(m.sum()); r[lab + "_pf"] = pf(u[m]); r[lab + "_wr"] = round(100 * (u[m] > 0).mean(), 1); r[lab + "_mo"] = round(u[m].sum() / max(1, m.sum()) * 21 * m.sum() / max(1, len(np.unique(DN.daydate[(DN.daydate >= (20200201 if lab == 'IS' else 20240101)) & (DN.daydate < (20240101 if lab == 'IS' else 30000000))]))))
    y = run(DM, A, B, k, mode, sk); uy = y.pts * 2 - 1.9; my = y.date >= 20240201
    r["REAL_n"] = int(my.sum()); r["REAL_pf"] = pf(uy[my]); r["REAL_wr"] = round(100 * (uy[my] > 0).mean(), 1)
    z = run(DL, A, B, k, mode, sk); zn = (z.pts + 0.5 - 0.00345 * z.atr) / z.atr     # cost-normalised: add back the 2 ticks, charge 0.345% ATR
    for lab, lo, hi in (("y1519", 20150101, 20200101), ("y2023", 20200101, 20240101), ("y2426", 20240101, 30000000)):
        m = (z.date >= lo) & (z.date < hi); r[lab + "_pf"] = pf(zn[m])
    rows.append(r)
R = pd.DataFrame(rows); R.to_csv("overnight.csv", index=False); pd.set_option("display.width", 260); pd.set_option("display.max_rows", 300)
R["minpf"] = R[["IS_pf", "C24_pf", "REAL_pf", "y1519_pf", "y2023_pf", "y2426_pf"]].min(axis=1)
print(R.sort_values("minpf", ascending=False).head(30).to_string(index=False))
