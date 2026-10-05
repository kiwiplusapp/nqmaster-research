"""Time-of-day momentum/reversal map on GOLD (MGC real 2024-26; XAU CFD 2020-23 when available)."""
import sys, os, itertools, numpy as np, pandas as pd
import tmom
PV = float(os.environ.get("PV", "4")); COMM = 1.0
sets = [s for s in sys.argv[1].split(",")]
part, nparts = int(sys.argv[2]), int(sys.argv[3])
D = {n: tmom.load(n) for n in sets}; X = {n: tmom.day_levels(D[n]) for n in D}
TIMES = [1110, 1200, 1290, 1380, 0, 60, 120, 180, 240, 300, 360, 420, 480, 500, 540, 570, 600, 630, 660, 720, 780, 840, 900]
grid = list(itertools.product(TIMES, (30, 60, 120, -1, -2), (0, 1), (0.1, 0.2), (0.3, 0.5, 1.0), (60, 240, 100000), (0, 1)))
def pf(u): return u[u > 0].sum() / -u[u <= 0].sum() if (u <= 0).any() and len(u) > 10 else np.nan
rows = []
for gi, (t, L, rev, sk, R, H, tf) in enumerate(grid):
    if gi % nparts != part: continue
    if L == -2 and not (570 < t < 960): continue
    r = dict(t=t, L=L, rev=rev, sk=sk, R=R, H=H, tf=tf)
    for n in sets:
        df = tmom.run(D[n], X[n], t, L, rev, sk, R, H, tf); u = df.pts * PV - COMM
        for lab, lo, hi in (("a", 20000101, 20231231), ("b", 20240101, 20241231), ("c", 20250101, 20991231)):
            m = (df.date >= lo) & (df.date <= hi)
            if m.sum() == 0: continue
            key = n.split(".")[0] + "_" + lab
            r[key + "_n"] = int(m.sum()); r[key + "_wr"] = round(100 * (u[m] > 0).mean(), 1); r[key + "_pf"] = round(pf(u[m]), 3)
    rows.append(r)
pd.DataFrame(rows).to_csv(f"tmap_{sets[0].split(chr(46))[0]}_{part}.csv", index=False); print(part, "done")
