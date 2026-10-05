import numpy as np, pandas as pd
from common import Ctx
import nt_v3_replica as r3
from nt_v2_replica import daily_stats
cx = Ctx()
A, T, ready = daily_stats(cx)
df = r3.run(cx, contracts=1, t1_r=0.6, t1_frac=1.0, orb_cap=0.35, vw_stop=0.35, max_consec_losses=0, dll=0)
dmap = {d: i for i, d in enumerate(cx.dates)}
dd = df.date.map(dmap).to_numpy()
i0 = cx.open_idx[dd]
orh = np.array([cx.h[a:a+60].max() for a in i0]); orl = np.array([cx.l[a:a+60].min() for a in i0])
atr = A[dd]
atr_s = pd.Series(A).rolling(50, min_periods=20).median().to_numpy()[dd]
df["orw"] = (orh - orl) / atr
df["gap"] = (cx.o[i0] - cx.prev_close[dd]) / atr * T[dd]
df["volreg"] = atr / atr_s
df["dow"] = cx.d["dow"][i0]
df["hour"] = cx.om[df.entry_idx.to_numpy()] // 60
df["open_pos"] = ((cx.c[i0 + 59] - cx.o[i0]) / atr) * T[dd]   # first-hour move in trend dir
df["prevret"] = (cx.prev_close[dd] - cx.prev_close[np.maximum(dd - 1, 0)]) / atr * T[dd]
df.to_pickle("orb06_trades.pkl")
IS = df.date < 20240101
def pf(s): return s[s > 0].sum() / -s[s <= 0].sum()
for f in ("orw", "gap", "volreg", "open_pos", "prevret"):
    q = df.loc[IS, f].quantile([0, .2, .4, .6, .8, 1]).to_numpy()
    b = np.digitize(df[f], q[1:-1])
    t = df.assign(b=b).groupby(["b", IS.map({True: "IS", False: "OOS"})]).usd.agg(["size", pf, lambda s: (s > 0).mean() * 100]).unstack().round(2)
    print("\n", f, np.round(q, 2)); print(t.to_string())
for f in ("dow", "hour", "mod"):
    t = df.groupby([f, IS.map({True: "IS", False: "OOS"})]).usd.agg(["size", pf, lambda s: (s > 0).mean() * 100]).unstack().round(2)
    print("\n", f); print(t.to_string())
