"""Candidate 'daily' modules so the portfolio trades every day. ORB60/VWAP60 machinery with alternative day directions."""
import os, numpy as np, pandas as pd
from common import Ctx
import nt_v3_replica as r3
import nt_v2_replica as r2
cx = Ctx(); A, T, ready = r2.daily_stats(cx)
def pf(s): return s[s > 0].sum() / -s[s <= 0].sum()
PR = np.full(cx.nd, np.nan)
for dd in range(2, cx.nd):
    if A[dd] > 0: PR[dd] = (cx.prev_close[dd] - cx.prev_close[dd - 1]) / A[dd] * T[dd]
fh = np.zeros(cx.nd, np.int64); gap = np.zeros(cx.nd, np.int64)
for dd in range(cx.nd):
    i0 = cx.open_idx[dd]
    if i0 >= 0 and i0 + 59 < len(cx.c):
        fh[dd] = int(np.sign(cx.c[i0 + 59] - cx.o[i0]))
        if not np.isnan(cx.prev_close[dd]): gap[dd] = int(np.sign(cx.o[i0] - cx.prev_close[dd]))
ext = ~(PR < 0.44)          # extended (or undefined) days = the ones the pullback engine skips
dirs = {"trend_all": T, "counter_ext": np.where(ext, -T, 0), "trend_ext": np.where(ext, T, 0),
        "firsthour": fh, "firsthour_ext": np.where(ext, fh, 0), "gap": gap, "fh_eq_trend_ext": np.where(ext & (fh == T), T, 0),
        "fh_vs_trend_ext": np.where(ext & (fh != T) & (fh != 0), fh, 0)}
orig = r2.daily_stats
base = dict(contracts=1, t1_frac=1.0, max_consec_losses=0, dll=0, orb_cap=0.35, vw_stop=0.35)
tag = os.environ.get("NQ_DATA", "nq_1m.npz")
for dn, D in dirs.items():
    r3.daily_stats = lambda cx_, D=D: (A, D.astype(np.int64), ready)
    for mod, kw in (("orb60", dict(use_vwap=False)), ("vw60", dict(use_orb=False))):
        for t1 in (0.5, 1.0):
            df = r3.run(cx, t1_r=t1, **base, **kw)
            parts = [("all", df)] if tag != "nq_1m.npz" else [("20-23", df[df.date < 20240101]), ("24-26", df[df.date >= 20240101])]
            print(f"{tag[:6]} {dn:16s} {mod} {t1}R | " + " | ".join(f"{nm}: n{len(s)} ({len(s)/max(1,len(set(s.date))):.1f}/d, days {len(set(s.date))}) wr{100*(s.usd>0).mean():.0f}% pf{pf(s.usd):.2f}" for nm, s in parts))
r3.daily_stats = orig
