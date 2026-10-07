"""Gold anchored drives that survived all 5 periods (results_goldnqdrive.csv, 2010-14 / 2015-19 / 2020-23 / 2024-26 cost-normalised and real
MGC): GF07 = 06:00 -> 07:00 move >= 0.2 ATR -> FADE, stop 0.35 ATR, 0.5R; GD11 = 10:00 -> 11:00 move >= 0.35 ATR -> continuation with the
trend, stop 0.35 ATR, 1R. Dense grids G:GF07 / G:GD11, daily correlation with the gold Robust set, lifecycle 150K 6c/3c (final + night
modules as base) in a fresh process. -> gold_new_port.csv"""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, ".")
from core import Data, run_events
from families_gold import gen_drive
from dense_build import dense
from news import NEWS
FOMC = set(NEWS["FOMC"])
P = {"GF07": dict(A=600, T=60, x=0.2, mode=-1, tf=0, k=0.35, stop=0, R=0.5, hold=240), "GD11": dict(A=1000, T=60, x=0.35, mode=1, tf=1, k=0.35, stop=0, R=1.0, hold=240)}
DL, DR = Data("xau_long.npz"), Data("mgc_fut.npz")
def tr(per, p):
    D = DR if per == "REAL" else DL
    df = run_events(D, gen_drive(D, p), flat=1010, maxday=1, slip=0.25); df["tin"] = D.sm[df.fi.to_numpy().astype(int)]; df["tout"] = D.sm[df.xi.to_numpy().astype(int)] + 1
    lo, hi = (20200201, 20240101) if per == "IS" else ((20240101, 3e7) if per == "C24" else (20240201, 3e7))
    df = df[(df.date >= lo) & (df.date < hi) & ~df.date.isin(FOMC)]
    return pd.DataFrame(dict(date=df.date.to_numpy(), mod="X", tin=df.tin.to_numpy(), tout=df.tout.to_numpy(), d=df.d.to_numpy(), u=df.usd.to_numpy(), w=1.0))
if __name__ == "__main__":
    GC = pickle.load(open("gold_curated_trades.pkl", "rb"))
    RES = os.path.dirname(os.getcwd()); DN = os.path.join(RES, "tmp", "dense"); meta = pickle.load(open(os.path.join(DN, "meta.pkl"), "rb"))
    for per in ("IS", "C24", "REAL"):
        z = dict(np.load(os.path.join(DN, f"{per}.npz"))); days = z["days"]
        rob = pd.concat([GC[m][per] for m in ("OD1030", "ENG0408", "SVWAP22", "ASIA1R", "ENG0206")]); rd = (rob.u * rob.w).groupby(rob.date).sum().reindex(days, fill_value=0.0)
        for n, p in P.items():
            x = tr(per, p); xd = x.groupby("date").u.sum().reindex(days, fill_value=0.0); u = x.u.values
            print(per, n, "trades", len(x), "PF %.2f WR %.1f" % (u[u > 0].sum() / -u[u <= 0].sum(), 100 * (u > 0).mean()), "corr with gold Robust %.3f" % np.corrcoef(xd, rd)[0, 1], flush=True)
            Lg, Rg = dense(x.assign(mod=n), "gold", per, days); z["G:" + n + "|L"] = Lg; z["G:" + n + "|R"] = Rg
        np.savez(os.path.join(DN, f"{per}.npz"), **z); meta[per] = sorted(set(meta[per]) | {"G:" + n for n in P})
    pickle.dump(meta, open(os.path.join(DN, "meta.pkl"), "wb")); print("dense added")
