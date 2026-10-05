"""Day-type regime test. Day features known at 10:30 ET: IB range (09:30-10:30) / ATR, relative volume of the IB vs the
prior 20 sessions' IB volume, |gap|/ATR. For every config of the mean-reversion and momentum families, trades entering after
10:30 are split by IS terciles of each feature; (config, feature, bucket) chosen on IS (PF>=1.3, n>=100) are checked OOS."""
import os, sys, pickle, ast, numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import Data, run_events, S
from families import FAMILIES as F1
from families2 import FAMILIES2
FAM = {**F1, **FAMILIES2}
USE = ["VWAP_BAND", "LEVEL_FADE", "CLOCK_ANCHOR", "VA_80", "PIVOT_FADE", "RSI_DIV", "PATTERN_5M", "VWAP_PULLBACK", "HOD_RETEST", "LEVEL_RETEST", "VOL_BREAK", "RANGE_BREAK", "OPEN_DRIVE"]
G = {}
def dayfeat(D):
    rth_ib = (D.om >= 570) & (D.om < 630)
    df = pd.DataFrame(dict(day=D.day[rth_ib], h=D.h[rth_ib], l=D.l[rth_ib], v=D.v[rth_ib], o=D.o[rth_ib]))
    g = df.groupby("day").agg(h=("h", "max"), l=("l", "min"), v=("v", "sum"), o=("o", "first")).reindex(range(D.nd))
    ib = (g.h - g.l) / pd.Series(D.atr).replace(0, np.nan)
    rv = g.v / g.v.rolling(20, min_periods=10).mean().shift(1)
    gap = (g.o - D.pdc).abs() / pd.Series(D.atr).replace(0, np.nan)
    return pd.DataFrame(dict(ib=ib.values, rvol=rv.values, gap=gap.values), index=D.daydate)
def init():
    for k, nm in (("nq", "nq_1m.npz"), ("mnq", "mnq_fut.npz")):
        D = Data(nm); G[k] = D; G[k + "_f"] = dayfeat(D).groupby(level=0).last()
def task(arg):
    fam, j = arg; gen, grid, md = FAM[fam]; p = grid[j]; out = {}
    for k in ("nq", "mnq"):
        D = G[k]; df = run_events(D, gen(D, p), maxday=md)
        if not len(df): out[k] = None; continue
        df["tin"] = D.sm[df.fi.to_numpy().astype(int)]
        df = df[df.tin >= S(1030)]
        out[k] = df[["date", "usd"]].join(G[k + "_f"], on="date")
    return fam, j, out
if __name__ == "__main__":
    tasks = [(f, j) for f in USE for j in range(len(FAM[f][1]))]
    print("configs", len(tasks), flush=True)
    with Pool(10, initializer=init) as pool: res = pool.map(task, tasks, chunksize=8)
    pickle.dump(res, open("daytype_trades.pkl", "wb")); print("saved", flush=True)
