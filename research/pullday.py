"""'Pullback-day' trend continuation: daily trend (prev RTH close vs SMA20) + prior day moved AGAINST the trend
(or only slightly with it). Several intraday entry modules traded only on those days. P&L per 1 MNQ."""
import numpy as np, pandas as pd
from common import Ctx
import nt_v3_replica as r3
from nt_v2_replica import daily_stats
cx = Ctx()
A, T, ready = daily_stats(cx)
dmap = {d: i for i, d in enumerate(cx.dates)}
prevret = np.full(cx.nd, np.nan)
for dd in range(2, cx.nd):
    prevret[dd] = (cx.prev_close[dd] - cx.prev_close[dd - 1]) / A[dd] * T[dd]
PR = dict(zip(cx.dates, prevret))

def pf(s): return s[s > 0].sum() / -s[s <= 0].sum() if (s <= 0).any() else 9.9
def summ(df, label):
    u = df.usd; out = [f"{label:28s} n{len(u):5d} /wk {len(u)/350:4.2f}"]
    for nm, m in (("IS", df.date < 20240101), ("OOS", df.date >= 20240101)):
        s = u[m]; out.append(f"{nm} wr{100*(s>0).mean():.1f} pf{pf(s):.2f}")
    out.append("yrs " + " ".join(f"{pf(u[df.date//10000==y]):.2f}" for y in range(2020, 2027)))
    print(" | ".join(out))

streams = {}
base = dict(contracts=1, t1_frac=1.0, max_consec_losses=0, dll=0, orb_cap=0.35, vw_stop=0.35)
for t1 in (0.5, 0.6, 0.75):
    streams[f"orb60_{t1}"] = r3.run(cx, t1_r=t1, use_vwap=False, **base)
    streams[f"vw60_{t1}"] = r3.run(cx, t1_r=t1, use_orb=False, **base)
    streams[f"orb30_{t1}"] = r3.run(cx, t1_r=t1, use_vwap=False, range_min=30, **base)
    streams[f"vw30_{t1}"] = r3.run(cx, t1_r=t1, use_orb=False, range_min=30, **base)
    streams[f"orb15_{t1}"] = r3.run(cx, t1_r=t1, use_vwap=False, range_min=15, **base)
    streams[f"orb60x3_{t1}"] = r3.run(cx, t1_r=t1, use_vwap=False, orb_max=3, **base)
pd.to_pickle(streams, "pullday_streams.pkl")
for th in (0.44, 0.6):
    print(f"\n===== prevret < {th}")
    for k, df in streams.items():
        f = df[df.date.map(PR) < th]
        summ(f, k)
