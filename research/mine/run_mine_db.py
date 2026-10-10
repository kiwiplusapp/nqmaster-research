"""Strategy miner on 16 years of REAL NQ futures (Databento, research/data/nqdb.npz, 2010-06 -> 2026-10), 2026-10-09.
Each config is run twice on the same events:
  real : $ per MNQ contract, $1.90 commission + 1 tick slippage  -> T1 = 2020-23, T2 = 2024-26
  norm : cost 0.345% of the daily ATR, P&L in % of ATR (removes the price-level effect of 2010-19) -> A = 2010-14, B = 2015-19
Selection protocol (applied later in mine_db_select.py, fixed before looking): chosen on T1 only; T2, A and B are out of sample.
Usage: MINE_TAG=db_old python3 run_mine_db.py [FAMILY ...]   (default: every family of run_mine.FAMILIES + families5)"""
import os, sys, time, pickle, numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import Data, run_events
from run_mine import FAMILIES as OLD
try:
    from families5 import FAMILIES5
except ImportError:
    FAMILIES5 = {}
FAMILIES = {**OLD, **FAMILIES5}
FLAT = int(os.environ.get("MINE_FLAT", "955")); NORM = 0.00345
PARTS_R = (("T1", 20200101, 20240101), ("T2", 20240101, 20991231))
PARTS_N = (("A", 20100601, 20150101), ("B", 20150101, 20200101), ("T1n", 20200101, 20240101), ("T2n", 20240101, 20991231))
G = {}


def init():
    G["D"] = Data(os.environ.get("MINE_DATA", "nqdb.npz"))


def stats(df, parts, out):
    for lab, lo, hi in parts:
        u = df.usd[(df.date >= lo) & (df.date < hi)].to_numpy()
        l = -u[u <= 0].sum()
        out[lab + "_n"] = len(u); out[lab + "_wr"] = round(100 * (u > 0).mean(), 1) if len(u) else np.nan
        out[lab + "_pf"] = round(u[u > 0].sum() / l, 3) if l > 0 and len(u) >= 20 else np.nan
        out[lab + "_avg"] = round(float(u.mean()), 3) if len(u) else np.nan


def task(arg):
    fam, j = arg; gen, grid, maxday = FAMILIES[fam]; p = grid[j]; D = G["D"]
    row = dict(fam=fam, j=j, params=repr(p)); keep = None
    try:
        ev = gen(D, p)
        r = run_events(D, ev, flat=FLAT, maxday=maxday, slip=0.25)
        nm = run_events(D, ev, flat=FLAT, maxday=maxday, slip=0.0, norm_cost=NORM)
        stats(r, PARTS_R, row); stats(nm, PARTS_N, row)
        if row["T1_n"] >= 80 and (row["T1_pf"] or 0) >= 1.25:
            for df in (r, nm):
                df["tin"] = D.sm[df.fi.to_numpy().astype(int)] if len(df) else []; df["tout"] = D.sm[df.xi.to_numpy().astype(int)] + 1 if len(df) else []
            keep = dict(real=r[["date", "usd", "tin", "tout", "d", "fi", "xi"]], norm=nm[["date", "usd", "d", "fi"]])
    except Exception as e:
        row["err"] = repr(e)[:200]
    return row, keep


if __name__ == "__main__":
    fams = sys.argv[1:] or list(FAMILIES)
    tasks = [(f, j) for f in fams for j in range(len(FAMILIES[f][1]))]
    if os.environ.get("MINE_LIMIT"): tasks = tasks[: int(os.environ["MINE_LIMIT"])]
    print("configs:", len(tasks), {f: len(FAMILIES[f][1]) for f in fams}, flush=True)
    t0 = time.time(); rows = []; trades = {}; tag = os.environ.get("MINE_TAG", "db")
    with Pool(int(os.environ.get("MINE_PROCS", "4")), initializer=init) as pool:
        for k, (row, keep) in enumerate(pool.imap_unordered(task, tasks, chunksize=2)):
            rows.append(row)
            if keep is not None: trades[(row["fam"], row["j"])] = keep
            if k % 500 == 0: print(k, round(time.time() - t0), "s", flush=True)
    R = pd.DataFrame(rows)
    R.to_csv(f"results_{tag}.csv", index=False); pickle.dump(trades, open(f"trades_{tag}.pkl", "wb"))
    print("done", round(time.time() - t0), "s; errors:", int(R["err"].notna().sum()) if "err" in R else 0, flush=True)
