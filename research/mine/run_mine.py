"""Run every family x parameter grid on CFD NQ 2020-26 (IS 2020-23 / C24 2024-26) and real MNQ 2024-26 (REAL).
Parallel over configs; each worker loads both datasets once."""
import os, sys, time, pickle, numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import Data, run_events, split_stats
from families import FAMILIES as F1
from families2 import FAMILIES2
from families3 import FAMILIES3
from families4 import FAMILIES4
FAMILIES = {**F1, **FAMILIES2, **FAMILIES3, **FAMILIES4}
G = {}
def init():
    G["nq"] = Data(os.environ.get("MINE_DATA", "nq_1m.npz")); G["mnq"] = Data("mnq_fut.npz")
def task(arg):
    fam, j = arg; gen, grid, maxday = FAMILIES[fam]; p = grid[j]
    row = dict(fam=fam, j=j, params=repr(p)); keep = {}
    try:
        for key in ("nq", "mnq"):
            D = G[key]; nc = float(os.environ['NORM_COST']) if (os.environ.get('NORM_COST') and key == 'nq') else None
            df = run_events(D, gen(D, p), flat=955, maxday=maxday, slip=(0.0 if nc is not None else 0.25), norm_cost=nc)
            df["tin"] = D.sm[df.fi.to_numpy().astype(int)] if len(df) else []; df["tout"] = D.sm[df.xi.to_numpy().astype(int)] + 1 if len(df) else []
            row.update(split_stats(D.name, df)); keep[key] = df[["date", "usd", "tin", "tout", "d"]]
    except Exception as e:
        row["err"] = repr(e)[:200]; return row, None
    good = ((row.get("IS_n", 0) >= 80) and (row.get("IS_pf", 0) or 0) >= 1.15) or ((row.get("TR_n", 0) >= 100) and (row.get("TR_pf", 0) or 0) >= 1.15)
    return row, (keep if good else None)
if __name__ == "__main__":
    fams = sys.argv[1:] or list(FAMILIES)
    tasks = [(f, j) for f in fams for j in range(len(FAMILIES[f][1]))]
    print("configs:", len(tasks), {f: len(FAMILIES[f][1]) for f in fams}, flush=True)
    t0 = time.time(); rows = []; trades = {}
    with Pool(10, initializer=init) as pool:
        for k, (row, keep) in enumerate(pool.imap_unordered(task, tasks, chunksize=4)):
            rows.append(row)
            if keep is not None: trades[(row["fam"], row["j"])] = keep
            if k % 200 == 0: print(k, round(time.time() - t0), "s", flush=True)
    R = pd.DataFrame(rows); tag = os.environ.get("MINE_TAG", "all")
    R.to_csv(f"results_{tag}.csv", index=False); pickle.dump(trades, open(f"trades_{tag}.pkl", "wb"))
    print("done", round(time.time() - t0), "s; errors:", R.get("err", pd.Series(dtype=str)).notna().sum())
