"""Per-module variants (target size) with timeline + direction, for WR/Sharpe trade-off and conflict analysis."""
import os, sys, numpy as np, pandas as pd
NQ, GOLD = sys.argv[1], sys.argv[2]
os.environ["NQ_DATA"] = NQ
from common import Ctx
import nt_v3_replica as r3
from nt_v2_replica import daily_stats
import wr60, tmom, ict, london, crt2
import crt as crtmod
from ict import load, day_levels
from news import NEWS
def sm(om): return (np.asarray(om) - 1080) % 1440
rows = []
def add(mod, var, date, usd, tin, tout, d):
    rows.append(pd.DataFrame(dict(date=np.asarray(date), mod=mod, var=var, usd=np.asarray(usd, float), tin=np.asarray(tin), tout=np.asarray(tout), d=np.asarray(d))))
cx = Ctx(); A, T, _ = daily_stats(cx)
PR = {cx.dates[dd]: (cx.prev_close[dd] - cx.prev_close[dd - 1]) / A[dd] * T[dd] for dd in range(2, cx.nd) if A[dd] > 0}
base = dict(contracts=1, t1_frac=1.0, max_consec_losses=0, dll=0, orb_cap=0.35, vw_stop=0.35)
for t1 in (0.4, 0.5, 0.6, 0.75):
    df = r3.run(cx, t1_r=t1, use_vwap=False, **base); df = df[df.date.map(PR) < 0.44]
    add("ORB60", t1, df.date, df.usd, sm(cx.om[df.entry_idx]), sm(cx.om[df.exit_idx]) + 1, df.dir)
B = wr60.build(5)
for R in (0.4, 0.5):
    out = np.zeros((len(B["c"]) // 3, 4))
    k = wr60.sim(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], B["up20"], 5, R, 1.75, 0.0, 0, 630, 945, 955, 0.0, out)
    ei = out[:k, 1].astype(int); xi = out[:k, 3].astype(int)
    add("MSEQ", R, B["date"][ei], out[:k, 0] * 2 - 1, sm(B["om"][ei]), sm(B["om"][xi]) + 5, np.ones(k))
for R in (1.0, 1.5, 2.0):
    c = crt2.run(60, (11,), 1, R, 0.0, 0.5, 0.0, 0, 955); add("CRT11", R, c.date, c.usd, sm(720), sm(crtmod.OM[c.xi]) + 1, c.d)
D = load(NQ); X = day_levels(D)
spec = {"MOM13": ((780, -2, 0, 0.2), 240, 1, (0.5, 0.75, 1.0)), "MOM1030": ((630, -2, 0, 0.2), 60, 1, (0.3,)), "ON07": ((420, 30, 0, 0.2), 60, 1, (0.5, 0.75, 1.0)),
        "REV06": ((360, 30, 1, 0.2), 240, 1, (0.3,)), "MOM11": ((660, -2, 0, 0.25), 100000, 0, (0.3,))}
for nm, (p, H, tf, Rs) in spec.items():
    for R in Rs:
        df = tmom.run(D, X, p[0], p[1], p[2], p[3], R, H, tf); add(nm, R, df.date, df.usd, sm(p[0]), sm(D["om"][df.xi]) + 1, df.d)
Bi = ict.bars(D, 5); L, atr, trend = ict.day_levels(D)
for R in (0.75, 1.0):
    df = ict.run(Bi, L, atr, trend, np.array([1] * 6, np.bool_), (570, 630), 4, 2, R, 1, 0.25); add("ICT", R, df.date, df.usd, sm(Bi["om"][df.bi]), sm(Bi["om"][df.xi]) + 5, df.d)
Bl = london.bars(D, 1); _, atl, trl = london.day_levels(D)
for R in (1.0, 1.5, 2.0):
    df = london.run(Bl, atl, trl, 0, 180, 360, 480, 1, 2, R, 0.25, 570, 1); add("LON", R, df.date, df.usd, np.full(len(df), sm(300)), sm(Bl["om"][df.xi]) + 1, df.d)
V = pd.concat(rows, ignore_index=True)
exec(open("mom11_feat.py").read().split("for f in [")[0].replace('for n in ("nq_1m.npz","mnq_fut.npz"):', f'for n in ("{NQ}",):'))
va = out[NQ].set_index("date").vw_agree.astype(float)
V = V[(V["mod"] != "MOM11") | (V.date.map(va) == 1)]
os.environ["NQ_DATA"] = GOLD
import importlib, common; importlib.reload(common); cg = common.Ctx()
for t1 in (1.0, 1.5, 2.0):
    dg = r3.run(cg, contracts=1, t1_frac=1.0, max_consec_losses=0, dll=0, orb_cap=0.35, vw_stop=0.35, t1_r=t1, use_vwap=False, range_min=30)
    V = pd.concat([V, pd.DataFrame(dict(date=dg.date, mod="GOLD", var=t1, usd=((dg.usd + 1) / 2) * 4.0 - 1.0, tin=sm(cg.om[dg.entry_idx]), tout=sm(cg.om[dg.exit_idx]) + 1, d=dg.dir))], ignore_index=True)
V["fomc"] = V.date.isin(NEWS["FOMC"])
V.to_pickle(f"variants_{NQ.split('.')[0]}.pkl"); print(NQ, V.groupby(["mod", "var"]).size().to_dict())
