"""2026-10-27 (experiment 01, S2): regenerate ONLY the trade lists of the four six-year modules in trades_db_old.pkl / trades_db_new.pkl
after the daily-trend fix (research/ict.py: SMA of the RTH closes that exist, >= 15, no 20-session blackout after a Globex session without
RTH bars). Same generator, grid row, data (nqdb.npz), flat time, slippage and cost as run_mine_db.task(); results_db_*.csv are NOT touched
(the family selection of six_reselect / six_oos is a separate decision). Prints old vs new trade counts per key.
Run from research/mine: python3 regen_six_keys.py"""
import os, sys, pickle, time, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); os.chdir(HERE)
import run_mine_db as M
from core import Data, run_events
KEYS = [("CLOCK_ANCHOR", 1527, "SO04"), ("RVOL_DRIVE", 4226, "RV11"), ("OR_FAIL", 142, "ORFAIL"), ("PIVOT_FADE", 365, "CAM3")]

if __name__ == "__main__":
    D = Data(os.environ.get("MINE_DATA", "nqdb.npz"))
    files = {f: pickle.load(open(f, "rb")) for f in ("trades_db_old.pkl", "trades_db_new.pkl")}
    changed = set()
    for fam, j, nm in KEYS:
        where = [f for f, T in files.items() if (fam, j) in T]
        if not where: print(nm, (fam, j), "NOT FOUND in trades_db_*.pkl"); continue
        f = where[0]; old = files[f][(fam, j)]["real"]
        gen, grid, maxday = M.FAMILIES[fam]; p = grid[j]; t0 = time.time()
        ev = gen(D, p)
        r = run_events(D, ev, flat=M.FLAT, maxday=maxday, slip=0.25)
        n = run_events(D, ev, flat=M.FLAT, maxday=maxday, slip=0.0, norm_cost=M.NORM)
        for df in (r, n):
            df["tin"] = D.sm[df.fi.to_numpy().astype(int)] if len(df) else []; df["tout"] = D.sm[df.xi.to_numpy().astype(int)] + 1 if len(df) else []
        new = dict(real=r[["date", "usd", "tin", "tout", "d", "fi", "xi"]], norm=n[["date", "usd", "d", "fi"]])
        ko = set(zip(old.date, old.fi)); kn = set(zip(new["real"].date, new["real"].fi))
        print(f"{nm:7s} {fam}#{j} {p} in {f}: trades {len(old)} -> {len(new['real'])} (+{len(kn - ko)} / -{len(ko - kn)}), 2024-26 {int((old.date >= 20240101).sum())} -> {int((new['real'].date >= 20240101).sum())}, {time.time() - t0:.0f} s")
        files[f][(fam, j)] = new; changed.add(f)
    for f in changed: pickle.dump(files[f], open(f, "wb")); print("written", f)
