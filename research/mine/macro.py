"""Post-release momentum/fade on macro days (CPI, NFP at 08:30 ET; FOMC at 14:00 ET).
Signal = move from the release minute to the end of the window W (5/15/30 min); entry at the next bar; direction momentum or fade;
exit at X (09:29 / 10:00 / 11:00 / 15:55) or stop k*ATR / target R*k*ATR. Protocol: choose on 2020-23 (CFD), check 2024-26 CFD and MNQ real."""
import os, sys, itertools, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
from core import Data, S, ev_from_lists, run_events
from news import NEWS
@njit(cache=True)
def gen(c, sm, ds, de, atr, isday, t0, W, x, fade, k, R, X):
    out = np.zeros((len(ds), 8)); n = 0
    for d in range(len(ds)):
        if not isday[d] or ds[d] < 0 or atr[d] <= 0: continue
        a = -1; b = -1; ex = -1
        for q in range(ds[d], de[d] + 1):
            if a < 0 and sm[q] >= t0: a = q
            if b < 0 and sm[q] >= t0 + W: b = q
            if sm[q] < X: ex = q
        if a < 1 or b < 0 or ex <= b: continue
        mv = c[b - 1] - c[a - 1]
        if abs(mv) < x * atr[d] or mv == 0: continue
        s = 1 if mv > 0 else -1
        if fade: s = -s
        px = c[b - 1]; A = atr[d]
        out[n, 0] = b - 1; out[n, 1] = s; out[n, 2] = 0; out[n, 3] = px; out[n, 4] = px - s * k * A; out[n, 5] = px + s * R * k * A; out[n, 6] = b - 1; out[n, 7] = ex - (b - 1); n += 1
    return out[:n]
DD = {"nq": Data("nq_1m.npz"), "mnq": Data("mnq_fut.npz")}
def pf(u): return round(float(u[u > 0].sum() / -u[u <= 0].sum()), 3) if (u <= 0).any() and len(u) >= 15 else np.nan
rows = []
for ev, t0 in (("CPI", 830), ("NFP", 830), ("CPI+NFP", 830), ("FOMC", 1400)):
    days = set(NEWS["CPI"]) | set(NEWS["NFP"]) if ev == "CPI+NFP" else set(NEWS[ev])
    for W, x, fade, k, R, X in itertools.product((5, 15, 30), (0.0, 0.1), (0, 1), (0.15, 0.3), (1.0, 2.0, 99.0), ((929, 1000, 1100, 1555) if t0 == 830 else (1555,))):
        r = dict(ev=ev, W=W, x=x, fade=fade, k=k, R=R, X=X)
        for key in ("nq", "mnq"):
            D = DD[key]; isday = np.array([dd in days for dd in D.daydate])
            evs = ev_from_lists(gen(D.c, D.sm, D.ds, D.de, D.atr.astype(np.float64), isday, S(t0), W, x, fade, k, R, S(X)).tolist())
            df = run_events(D, evs, flat=955, maxday=1)
            if key == "nq":
                for lab, m in (("IS", (df.date >= 20200101) & (df.date < 20240101)), ("C24", df.date >= 20240101)):
                    r[lab + "_n"] = int(m.sum()); r[lab + "_pf"] = pf(df.usd[m].to_numpy()); r[lab + "_avg"] = round(float(df.usd[m].mean()), 1) if m.any() else np.nan
            else:
                m = df.date >= 20240201; r["REAL_n"] = int(m.sum()); r["REAL_pf"] = pf(df.usd[m].to_numpy()); r["REAL_avg"] = round(float(df.usd[m].mean()), 1) if m.any() else np.nan
        rows.append(r)
R = pd.DataFrame(rows); R.to_csv("macro.csv", index=False); pd.set_option("display.width", 250); pd.set_option("display.max_rows", 100)
for ev, g in R.groupby("ev"):
    print("==", ev, "configs", len(g), "IS PF>1 %.0f%%  C24 PF>1 %.0f%%  REAL PF>1 %.0f%%" % (100 * (g.IS_pf > 1).mean(), 100 * (g.C24_pf > 1).mean(), 100 * (g.REAL_pf > 1).mean()))
    print(g.groupby("fade")[["IS_pf", "C24_pf", "REAL_pf"]].median().round(3).to_string())
    top = g[g.IS_n >= 30].sort_values("IS_pf", ascending=False).head(8)
    print(top[["W", "x", "fade", "k", "R", "X", "IS_n", "IS_pf", "IS_avg", "C24_n", "C24_pf", "REAL_n", "REAL_pf", "REAL_avg"]].to_string(index=False))
