"""ORB variants (range 15/30/45/60/90) on pullback days / all days, with the daily trend, as extra modules next to ORB60."""
import os, sys, itertools, pickle, numpy as np, pandas as pd
os.environ["NQ_DATA"] = sys.argv[1]
from common import Ctx
import nt_v3_replica as r3
from nt_v2_replica import daily_stats
cx = Ctx(); A, T, _ = daily_stats(cx)
PR = {cx.dates[dd]: (cx.prev_close[dd] - cx.prev_close[dd - 1]) / A[dd] * T[dd] for dd in range(2, cx.nd) if A[dd] > 0}
base = dict(contracts=1, t1_frac=1.0, max_consec_losses=0, dll=0, vw_stop=0.35, use_vwap=False)
res = {}
for rm, t1, cap, last in itertools.product((15, 30, 45, 60, 90), (0.5, 0.6, 0.75, 1.0), (0.25, 0.35), (780, 870)):
    df = r3.run(cx, t1_r=t1, orb_cap=cap, range_min=rm, entry_start=570 + rm, orb_last=last, **base)
    df = df.assign(pr=df.date.map(PR), tin=cx.om[df.entry_idx], tout=cx.om[df.exit_idx])
    res[(rm, t1, cap, last)] = df[["date", "usd", "dir", "pr", "tin", "tout"]]
pickle.dump(res, open(f"orbx_{sys.argv[1].split('.')[0]}.pkl", "wb")); print("done", len(res))
