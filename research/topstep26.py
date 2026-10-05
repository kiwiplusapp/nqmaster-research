"""Trade-level portfolio on REAL MNQ with risk-based sizing (0.5% of 50K = $250 per trade), Topstep 50K rules."""
import os, numpy as np, pandas as pd
os.environ["NQ_DATA"] = "mnq_fut.npz"
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
    tr.append(pd.DataFrame(dict(date=df.date, mod=nm, pts=(df.usd + 1) / 2, risk=df.risk_pts, t=cx.om[df.entry_idx.to_numpy()])))
B = build(5); out = np.zeros((len(B["c"]) // 3, 4))
k = msim(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], B["up20"], 5, 0.5, 1.75, 0.0, 0, 630, 945, 955, 0.0, out)
tr.append(pd.DataFrame(dict(date=B["date"][out[:k, 1].astype(int)], mod="MSEQ", pts=out[:k, 0], risk=out[:k, 2], t=B["om"][out[:k, 1].astype(int)])))
c = crt2.run(60, (11,), 1, 2.0, 0.0, 0.5, 0.0, 0, 955); tr.append(pd.DataFrame(dict(date=c.date, mod="CRT11", pts=c.pts, risk=c.risk, t=720)))
D = load("mnq_fut.npz"); X = day_levels(D)
for nm, p in {"MOM13": (780, -2, 0, 0.2, 1.0, 240, 1), "MOM1030": (630, -2, 0, 0.2, 0.3, 60, 1), "ON07": (420, 30, 0, 0.2, 1.0, 60, 1), "REV06": (360, 30, 1, 0.2, 0.3, 240, 1)}.items():
    df = tmom.run(D, X, *p); tr.append(pd.DataFrame(dict(date=df.date, mod=nm, pts=df.pts, risk=df.risk, t=p[0])))
# MOM11 with VWAP agreement
exec(open("mom11_feat.py").read().split("for f in [")[0].replace('for n in ("nq_1m.npz","mnq_fut.npz"):', 'for n in ("mnq_fut.npz",):'))
x = out["mnq_fut.npz"]; x = x[x.vw_agree.astype(bool)]
tr.append(pd.DataFrame(dict(date=x.date, mod="MOM11", pts=x.pts, risk=x.risk, t=660)))
Bi = ict.bars(D, 5); L, atr, trend = ict.day_levels(D)
df = ict.run(Bi, L, atr, trend, np.array([1] * 6, np.bool_), (570, 630), 4, 2, 1.0, 1, 0.25); tr.append(pd.DataFrame(dict(date=df.date, mod="ICT", pts=df.pts, risk=df.risk, t=600)))
Bl = london.bars(D, 1); _, atl, trl = london.day_levels(D)
df = london.run(Bl, atl, trl, 0, 180, 360, 480, 1, 2, 2.0, 0.25, 570, 1); tr.append(pd.DataFrame(dict(date=df.date, mod="LON", pts=df.pts, risk=df.risk, t=300)))
TR = pd.concat(tr, ignore_index=True)
TR = TR[TR.risk > 0].copy()
TR.to_pickle("trades_real_all.pkl")
print(TR.groupby("mod").size())
