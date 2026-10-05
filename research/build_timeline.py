"""Trade timeline (entry/exit session-minute) for the v7 portfolio on one NQ dataset + one gold dataset."""
import os, sys, numpy as np, pandas as pd
NQ, GOLD = sys.argv[1], sys.argv[2]
os.environ["NQ_DATA"] = NQ
from common import Ctx
import nt_v3_replica as r3
from nt_v2_replica import daily_stats
import wr60, tmom, ict, london, crt2
from ict import load, day_levels
from news import NEWS
def sm(om): return (np.asarray(om) - 1080) % 1440
rows = []
cx = Ctx(); A, T, _ = daily_stats(cx)
PR = {cx.dates[dd]: (cx.prev_close[dd] - cx.prev_close[dd - 1]) / A[dd] * T[dd] for dd in range(2, cx.nd) if A[dd] > 0}
base = dict(contracts=1, t1_frac=1.0, max_consec_losses=0, dll=0, orb_cap=0.35, vw_stop=0.35)
for nm, kw in {"ORB60": dict(use_vwap=False, t1_r=0.6), "VWP60": dict(use_orb=False, t1_r=0.6)}.items():
    df = r3.run(cx, **base, **kw); df = df[df.date.map(PR) < 0.44]
    rows.append(pd.DataFrame(dict(date=df.date, mod=nm, usd=df.usd, tin=sm(cx.om[df.entry_idx]), tout=sm(cx.om[df.exit_idx]) + 1)))
B = wr60.build(5); out = np.zeros((len(B["c"]) // 3, 4))
k = wr60.sim(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], B["up20"], 5, 0.5, 1.75, 0.0, 0, 630, 945, 955, 0.0, out)
ei = out[:k, 1].astype(int); xi = out[:k, 3].astype(int)
rows.append(pd.DataFrame(dict(date=B["date"][ei], mod="MSEQ", usd=out[:k, 0] * 2 - 1, tin=sm(B["om"][ei]), tout=sm(B["om"][xi]) + 5)))
import crt as crtmod
c = crt2.run(60, (11,), 1, 2.0, 0.0, 0.5, 0.0, 0, 955)
rows.append(pd.DataFrame(dict(date=c.date, mod="CRT11", usd=c.usd, tin=sm(720), tout=sm(crtmod.OM[c.xi]) + 1)))
D = load(NQ); X = day_levels(D)
for nm, p in {"MOM13": (780, -2, 0, 0.2, 1.0, 240, 1), "MOM1030": (630, -2, 0, 0.2, 0.3, 60, 1), "ON07": (420, 30, 0, 0.2, 1.0, 60, 1),
              "REV06": (360, 30, 1, 0.2, 0.3, 240, 1), "MOM11": (660, -2, 0, 0.25, 0.3, 100000, 0)}.items():
    df = tmom.run(D, X, *p)
    rows.append(pd.DataFrame(dict(date=df.date, mod=nm, usd=df.usd, tin=sm(p[0]), tout=sm(D["om"][df.xi]) + 1)))
Bi = ict.bars(D, 5); L, atr, trend = ict.day_levels(D)
df = ict.run(Bi, L, atr, trend, np.array([1] * 6, np.bool_), (570, 630), 4, 2, 1.0, 1, 0.25)
rows.append(pd.DataFrame(dict(date=df.date, mod="ICT", usd=df.usd, tin=sm(Bi["om"][df.bi]), tout=sm(Bi["om"][df.xi]) + 5)))
Bl = london.bars(D, 1); _, atl, trl = london.day_levels(D)
df = london.run(Bl, atl, trl, 0, 180, 360, 480, 1, 2, 2.0, 0.25, 570, 1)
rows.append(pd.DataFrame(dict(date=df.date, mod="LON", usd=df.usd, tin=sm(Bl["om"][np.searchsorted(Bl["date"], df.date)] * 0 + 300), tout=sm(Bl["om"][df.xi]) + 1)))
TL = pd.concat(rows, ignore_index=True)
# MOM11 VWAP filter
exec(open("mom11_feat.py").read().split("for f in [")[0].replace('for n in ("nq_1m.npz","mnq_fut.npz"):', f'for n in ("{NQ}",):'))
va = out[NQ].set_index("date").vw_agree.astype(float)
TL = TL[(TL["mod"] != "MOM11") | (TL.date.map(va) == 1)]
# gold ORB30 2R
os.environ["NQ_DATA"] = GOLD
import importlib, prep, common
importlib.reload(common)
cg = common.Ctx()
dg = r3.run(cg, contracts=1, t1_frac=1.0, max_consec_losses=0, dll=0, orb_cap=0.35, vw_stop=0.35, t1_r=2.0, use_vwap=False, range_min=30)
TL = pd.concat([TL, pd.DataFrame(dict(date=dg.date, mod="GC_ORB30", usd=((dg.usd + 1) / 2) * 4.0 - 1.0, tin=sm(cg.om[dg.entry_idx]), tout=sm(cg.om[dg.exit_idx]) + 1))], ignore_index=True)
TL["fomc"] = TL.date.isin(NEWS["FOMC"])
TL = TL.sort_values(["date", "tin"]).reset_index(drop=True)
TL.to_pickle(f"timeline_{NQ.split('.')[0]}.pkl"); print(NQ, len(TL), TL.groupby("mod").size().to_dict())
