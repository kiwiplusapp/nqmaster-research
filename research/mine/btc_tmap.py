"""Time-of-day momentum / reversal map on Bitcoin (research/data/btc_1m.npz, Binance spot scaled to MBT), like research/tmom.py
and gold_tmom.py: at clock time t (ET minutes) trade sign(close[t-1] - close[t-L]) (or the opposite), stop sk x RTH-ATR,
target R x stop, max hold H minutes, flat 15:55 ET, one trade per day. Periods: A 2017-19 (real $ and cost-normalised),
T1 2020-23, T2 2024-26. $ per MBT: pts x 2 - $3.00 commission (1 tick per side slippage is inside pts).
Usage: python3 btc_tmap.py <part> <nparts>  -> btc_tmap_<part>.csv ; python3 btc_tmap.py merge -> btc_tmap.csv + summary"""
import sys, os, glob, itertools, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
PV, COMM, NORM = 2.0, 3.0, float(os.environ.get("MINE_NORM", "0.0147"))
TIMES = [1080, 1110, 1140, 1200, 1230, 1260, 1320, 1380, 0, 60, 120, 150, 180, 240, 300, 360, 420, 480, 510, 540, 570, 600, 630, 660, 720, 780, 840, 900, 930]
GRID = list(itertools.product(TIMES, (30, 60, 120, 240, -1, -2), (0, 1), (0.15, 0.3), (0.5, 1.0, 2.0), (120, 100000), (0, 1)))
PARTS = (("A", 20170801, 20200101), ("T1", 20200101, 20240101), ("T2", 20240101, 20991231))


def pf(u): return float(u[u > 0].sum() / -u[u <= 0].sum()) if (u <= 0).any() and len(u) > 10 else np.nan


if __name__ == "__main__":
    if sys.argv[1] == "merge":
        R = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(HERE, "btc_tmap_[0-9]*.csv")))], ignore_index=True)
        R.to_csv(os.path.join(HERE, "btc_tmap.csv"), index=False)
        print("configs", len(R))
        for lab in ("A", "T1", "T2", "An"):
            print(lab, "median PF", round(float(R[lab + "_pf"].median()), 3), "| PF>=1.2:", int((R[lab + "_pf"] >= 1.2).sum()), "| PF>=1.3 & n>=100:", int(((R[lab + "_pf"] >= 1.3) & (R[lab.rstrip("n") + "_n"] >= 100)).sum()))
        s1 = (R.T1_n >= 100) & (R.T1_wr >= 55) & (R.T1_pf >= 1.3); s2 = (R.T2_pf >= 1.2) & (R.An_pf >= 1.0)
        print("T1 pass", int(s1.sum()), "| T1&T2&An pass", int((s1 & s2).sum()), "| P(T2&An | T1)", round(float(s2[s1].mean()), 3) if s1.any() else None, "| P(T2&An) all", round(float(s2.mean()), 3))
        print(R[s1].sort_values("T2_pf", ascending=False).head(25).to_string())
        sys.exit()
    import tmom
    part, nparts = int(sys.argv[1]), int(sys.argv[2])
    from core import load
    D = load("btc_1m.npz"); X = tmom.day_levels(D); atr = X[1]
    rows = []
    for gi, (t, L, rev, sk, R, H, tf) in enumerate(GRID):
        if gi % nparts != part: continue
        if L == -2 and not (570 < t < 960): continue
        if t == 1080 and L != -1 and L > 0: continue                       # nothing before the 18:00 open inside the session
        df = tmom.run(D, X, t, L, rev, sk, R, H, tf)
        if len(df) == 0: continue
        u = (df.pts * PV - COMM).to_numpy(); A = atr[D["dayid"][df.bi.to_numpy()]]
        un = np.where(A > 0, (df.pts.to_numpy() + 0.5 - NORM * A) / np.where(A > 0, A, 1) * 100, 0.0)      # slippage added back, norm cost
        r = dict(t=t, L=L, rev=rev, sk=sk, R=R, H=H, tf=tf)
        for lab, lo, hi in PARTS:
            m = ((df.date >= lo) & (df.date < hi)).to_numpy()
            r[lab + "_n"] = int(m.sum()); r[lab + "_wr"] = round(100 * float((u[m] > 0).mean()), 1) if m.any() else np.nan
            r[lab + "_pf"] = round(pf(u[m]), 3); r[lab + "_net"] = round(float(u[m].sum()))
            if lab == "A": r["An_pf"] = round(pf(un[m]), 3); r["An_wr"] = round(100 * float((un[m] > 0).mean()), 1) if m.any() else np.nan
        rows.append(r)
    pd.DataFrame(rows).to_csv(os.path.join(HERE, f"btc_tmap_{part}.csv"), index=False); print(part, "done", len(rows))
