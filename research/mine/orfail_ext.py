"""OR_FAIL plateau check (2026-10-09): the 16-year survivor needs bk = 0.10 (edge of the mined grid 0 / 0.05 / 0.10). Extended grid
bk 0.08-0.30, OR 15 / 30 min, 1m / 5m closes, targets R0.5 / mid / opp, with the trend, entries until 12:00 / 14:00.
Same executor and periods as run_mine_db.py. -> orfail_ext.csv"""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import Data, run_events
from families import grid
from families5 import gen_orfail
from run_mine_db import stats, PARTS_R, PARTS_N, NORM

if __name__ == "__main__":
    D = Data("nqdb.npz"); rows = []
    for p in grid(T=(15, 30), bk=(0.08, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30), tfb=(1, 5), tg=("R0.5", "mid", "opp"), tf=(1,), w1=(1200, 1400)):
        ev = gen_orfail(D, p); row = dict(p)
        stats(run_events(D, ev, maxday=1, slip=0.25), PARTS_R, row); stats(run_events(D, ev, maxday=1, slip=0.0, norm_cost=NORM), PARTS_N, row)
        rows.append(row)
    R = pd.DataFrame(rows); R.to_csv("orfail_ext.csv", index=False)
    for tg in ("R0.5", "mid", "opp"):
        s = R[(R.tg == tg) & (R["T"] == 15) & (R.tfb == 5) & (R.w1 == 1200)]
        print(f"\nT15 5m w1 1200 tg {tg}"); print(s[["bk", "T1_n", "A_wr", "A_pf", "B_wr", "B_pf", "T1_wr", "T1_pf", "T2_wr", "T2_pf"]].to_string(index=False))
    a4 = (R[["A_pf", "B_pf", "T1_pf", "T2_pf"]] >= 1.1).all(axis=1)
    print("\nconfigs with PF >= 1.1 in all four:", int(a4.sum()), "of", len(R))
    print(R[a4].groupby(["T", "tfb", "tg"]).size().to_string())
