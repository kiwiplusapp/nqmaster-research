"""Session-drift family with brackets (all inside one CME Globex session 18:00->17:00, so prop-legal intraday).
Selection on IS 2020-2023, OOS 2024-01 -> 2026-09 reported untouched."""
import itertools, numpy as np, pandas as pd
from common import Ctx
import engine as en
PV, COMM = 2.0, 1.0
cx = Ctx(); o, h, l, c, om, dayid = cx.o, cx.h, cx.l, cx.c, cx.om, cx.dayid
atr = cx.atr_daily()
pc = cx.prev_close
closes = np.full(cx.nd, np.nan)
closes[cx.close_idx >= 0] = c[cx.close_idx[cx.close_idx >= 0]]
s = pd.Series(closes)
def sma(k): return s.rolling(k, min_periods=k).mean().shift(1).to_numpy() if False else pd.Series(closes).ffill().rolling(k).mean().shift(1).to_numpy()
dirs = {}
for k in (10, 20, 50):
    m = sma(k); up = np.nan_to_num(pc - m) > 0; dn = np.nan_to_num(pc - m) < 0
    dirs[f"t{k}"] = np.where(up, 1, np.where(dn, -1, 0)).astype(np.int64)
    dirs[f"up{k}"] = up.astype(np.int64)
dirs["long"] = np.ones(cx.nd, np.int64)
dates = cx.dates
rows = []
wins = [(1081, 480), (1081, 505), (1081, 569), (1200, 569), (0, 569), (120, 569), (180, 569), (240, 569), (0, 505),
        (570, 955), (600, 955), (660, 955), (840, 955)]
for (e, x), dn, sk, tk in itertools.product(wins, dirs, (0.15, 0.2, 0.3, 0.4, 0.5, 0.75), (0.0, 0.05, 0.08, 0.1, 0.15, 0.2, 0.3)):
    if tk and tk >= sk * 1.5: continue
    E, X, D, EP, XP, RK, RS = en.sim_window_hold(o, h, l, c, om, dayid, atr, dirs[dn], e, x, sk, tk, 0)
    u = (XP - EP) * D * PV - COMM; dt = dates[dayid[E]]
    r = dict(entry=e, exit=x, dirf=dn, sk=sk, tk=tk)
    for nm, lo, hi in (("is", 20200101, 20231231), ("oos", 20240101, 20991231), ("26", 20260101, 20991231)):
        mm = (dt >= lo) & (dt <= hi); uu = u[mm]
        w = uu[uu > 0].sum(); ls = -uu[uu <= 0].sum()
        r[f"{nm}_n"] = len(uu); r[f"{nm}_wr"] = round((uu > 0).mean() * 100, 1) if len(uu) else np.nan
        r[f"{nm}_pf"] = round(w / ls, 3) if ls > 0 else np.nan; r[f"{nm}_net"] = round(uu.sum())
    yp = []
    for y in range(2020, 2027):
        mm = (dt // 10000) == y; uu = u[mm]
        yp.append(uu[uu > 0].sum() / max(-uu[uu <= 0].sum(), 1e-9))
    r["minyr"] = round(min(yp), 2); r["yrs"] = " ".join(f"{v:.2f}" for v in yp)
    rows.append(r)
g = pd.DataFrame(rows); g.to_csv("drift_scan.csv", index=False)
sel = g[(g.is_wr >= 60) & (g.is_pf >= 1.2)]
print(len(g), "configs; IS-selected", len(sel))
print(sel.sort_values("is_pf", ascending=False).head(40).to_string(index=False))
