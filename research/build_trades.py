"""Trade-level table (all 11 modules) with direction, risk and entry-time features, for one dataset (NQ_DATA env)."""
import os, sys, numpy as np, pandas as pd
TAG = os.environ.get("NQ_DATA", "nq_1m.npz")
from common import Ctx
import nt_v3_replica as r3
from nt_v2_replica import daily_stats
from wr60 import build, sim as msim
import tmom, ict, london, crt2
from ict import load, day_levels
cx = Ctx(); A, T, _ = daily_stats(cx)
PR = {cx.dates[dd]: (cx.prev_close[dd] - cx.prev_close[dd - 1]) / A[dd] * T[dd] for dd in range(2, cx.nd) if A[dd] > 0}
tr = []
base = dict(contracts=1, t1_frac=1.0, max_consec_losses=0, dll=0, orb_cap=0.35, vw_stop=0.35)
for nm, kw in {"ORB60": dict(use_vwap=False, t1_r=0.6), "VWP60": dict(use_orb=False, t1_r=0.6)}.items():
    df = r3.run(cx, **base, **kw); df = df[df.date.map(PR) < 0.44]
    tr.append(pd.DataFrame(dict(date=df.date, mod=nm, pts=(df.usd + 1) / 2, risk=df.risk_pts, d=df.dir, t=cx.om[df.entry_idx.to_numpy()])))
B = build(5); out = np.zeros((len(B["c"]) // 3, 4))
k = msim(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], B["up20"], 5, 0.5, 1.75, 0.0, 0, 630, 945, 955, 0.0, out)
tr.append(pd.DataFrame(dict(date=B["date"][out[:k, 1].astype(int)], mod="MSEQ", pts=out[:k, 0], risk=out[:k, 2], d=1, t=B["om"][out[:k, 1].astype(int)])))
c = crt2.run(60, (11,), 1, 2.0, 0.0, 0.5, 0.0, 0, 955); tr.append(pd.DataFrame(dict(date=c.date, mod="CRT11", pts=c.pts, risk=c.risk, d=c.d, t=720)))
D = load(TAG); X = day_levels(D)
for nm, p in {"MOM13": (780, -2, 0, 0.2, 1.0, 240, 1), "MOM1030": (630, -2, 0, 0.2, 0.3, 60, 1), "ON07": (420, 30, 0, 0.2, 1.0, 60, 1), "REV06": (360, 30, 1, 0.2, 0.3, 240, 1),
              "MOM11": (660, -2, 0, 0.25, 0.3, 100000, 0)}.items():
    df = tmom.run(D, X, *p); tr.append(pd.DataFrame(dict(date=df.date, mod=nm, pts=df.pts, risk=df.risk, d=df.d, t=p[0])))
Bi = ict.bars(D, 5); L, atr, trend = ict.day_levels(D)
df = ict.run(Bi, L, atr, trend, np.array([1] * 6, np.bool_), (570, 630), 4, 2, 1.0, 1, 0.25); tr.append(pd.DataFrame(dict(date=df.date, mod="ICT", pts=df.pts, risk=df.risk, d=df.d, t=600)))
Bl = london.bars(D, 1); _, atl, trl = london.day_levels(D)
df = london.run(Bl, atl, trl, 0, 180, 360, 480, 1, 2, 2.0, 0.25, 570, 1); tr.append(pd.DataFrame(dict(date=df.date, mod="LON", pts=df.pts, risk=df.risk, d=df.d, t=300)))
TR = pd.concat(tr, ignore_index=True); TR = TR[TR.risk > 0].copy()
# ---- features known before/at entry
om, day, h, l, c, o, v = D["om"], D["dayid"], D["h"], D["l"], D["c"], D["o"], D["v"]
nd = int(day.max()) + 1
df1 = pd.DataFrame(dict(day=day, om=om, h=h, l=l, c=c, o=o, v=np.maximum(v, 1e-9), date=D["date"]))
rth = df1[(df1.om >= 570) & (df1.om < 960)]
dly = rth.groupby("day").agg(date=("date", "first"), o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"))
dly = dly.reindex(range(nd))
L_, atrd, trendd = X
F = pd.DataFrame(index=range(nd))
F["date"] = pd.Series(D["date"]).groupby(day).first().reindex(range(nd)).to_numpy()
F["atr"] = atrd; F["trend"] = trendd
F["atr_ratio"] = atrd / pd.Series(atrd).replace(0, np.nan).rolling(60, min_periods=20).mean().to_numpy()
pc = dly.c.shift(1); pc2 = dly.c.shift(2); pc3 = dly.c.shift(3)
F["ret1"] = ((pc - pc2) / atrd).to_numpy(); F["ret2"] = ((pc - pc3) / atrd).to_numpy()
F["prng"] = ((dly.h - dly.l).shift(1) / atrd).to_numpy()
F["gap"] = ((dly.o - pc) / atrd).to_numpy()
on = df1[(df1.om >= 1080) | (df1.om < 570)].groupby("day").agg(h=("h", "max"), l=("l", "min")).reindex(range(nd))
F["onrng"] = ((on.h - on.l) / atrd).to_numpy()
F["dow"] = pd.to_datetime(F.date.astype("Int64").astype(str), format="%Y%m%d", errors="coerce").dt.dayofweek.to_numpy()
F = F.dropna(subset=["date"]); F["date"] = F.date.astype(int)
TR = TR.merge(F, on="date", how="left")
TR["with_trend"] = (TR.d == TR.trend).astype(int)
TR["ret1_d"] = TR.ret1 * TR.d; TR["ret2_d"] = TR.ret2 * TR.d
TR["gap_d"] = np.where(TR.t >= 570, TR.gap * TR.d, np.nan)       # gap only known for entries after 09:30
TR["usd1"] = TR.pts * 2 - 1
TR.to_pickle(f"trades_{TAG.split('.')[0]}.pkl")
print(TAG, TR.groupby("mod").size().to_dict())
