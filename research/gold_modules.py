import os, sys, itertools, numpy as np, pandas as pd
TAG = os.environ["NQ_DATA"]
from common import Ctx
import nt_v3_replica as r3
from nt_v2_replica import daily_stats
import wr60, ict, london, crt2, crt
PV = float(os.environ.get("PV", "4"))
def pf(u): return u[u > 0].sum() / -u[u <= 0].sum() if (u <= 0).any() and len(u) > 10 else np.nan
cx = Ctx(); A, T, _ = daily_stats(cx)
PR = {cx.dates[dd]: (cx.prev_close[dd] - cx.prev_close[dd - 1]) / A[dd] * T[dd] for dd in range(2, cx.nd) if A[dd] > 0}
res = []
def add(name, date, pts):
    date = np.asarray(date); u = np.asarray(pts) * PV - 1.0
    for lab, lo, hi in (("2020-23", 20000101, 20231231), ("2024", 20240101, 20241231), ("2025-26", 20250101, 20991231)):
        m = (date >= lo) & (date <= hi)
        if m.sum() > 10: res.append(dict(mod=name, per=lab, n=int(m.sum()), wr=round(100 * (u[m] > 0).mean(), 1), pf=round(pf(u[m]), 2)))
base = dict(contracts=1, t1_frac=1.0, max_consec_losses=0, dll=0)
for cap in (0.25, 0.35):
    for t1 in (0.6, 1.0, 2.0):
        for nm, kw in (("ORB60", dict(use_vwap=False)), ("VWP60", dict(use_orb=False)), ("ORB30", dict(use_vwap=False, range_min=30))):
            df = r3.run(cx, t1_r=t1, orb_cap=cap, vw_stop=cap, **base, **kw)
            pts = (df.usd + 1) / 2
            add(f"{nm} {t1}R cap{cap} all", df.date, pts)
            m = df.date.map(PR) < 0.44
            add(f"{nm} {t1}R cap{cap} pullback", df.date[m], pts[m])
B = wr60.build(5)
for N, R, sk in itertools.product((4, 5), (0.5, 1.0), (1.75, 2.5)):
    out = np.zeros((len(B["c"]) // 3, 4)); k = wr60.sim(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], B["up20"], N, R, sk, 0.0, 0, 630, 945, 955, 0.0, out)
    add(f"MSEQ N{N} {R}R sk{sk}", B["date"][out[:k, 1].astype(int)], out[:k, 0])
for hr in range(2, 15):
    for R in (1.0, 2.0):
        df = crt2.run(60, (hr,), 1, R, 0.0, 0.5, 0.0, 0, 955); add(f"CRT {hr:02d}h {R}R trend", df.date, df.pts)
D = ict.load(TAG); Bl = london.bars(D, 1); _, atl, trl = london.day_levels(D)
for rs, R, bias in itertools.product((1200, 0), (1.0, 2.0), (0, 1)):
    df = london.run(Bl, atl, trl, rs, 180, 360, 480, 1, 2, R, 0.25, 570, bias); add(f"LON rs{rs} {R}R bias{bias}", df.date, df.pts)
Bi = ict.bars(D, 5); L, atr, trend = ict.day_levels(D)
for win, R, bias in itertools.product(((570, 630), (480, 600), (180, 300)), (1.0, 2.0), (0, 1)):
    df = ict.run(Bi, L, atr, trend, np.array([1] * 6, np.bool_), win, 4, 2, R, bias, 0.25); add(f"ICT win{win[0]} {R}R bias{bias}", df.date, df.pts)
g = pd.DataFrame(res).pivot_table(index="mod", columns="per", values=["n", "wr", "pf"])
g.columns = [f"{a}_{b}" for a, b in g.columns]
g.to_csv(f"gold_modules_{TAG.split('.')[0]}.csv"); print(TAG, "done", len(g))
