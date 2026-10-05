import os, numpy as np, pandas as pd
from common import Ctx
import nt_v3_replica as r3
from nt_v2_replica import daily_stats
from wr60 import build, sim as msim
from ict import load, day_levels
import timefill as tfm
import crt2
NQ = os.environ.get("NQ_DATA", "nq_1m.npz")
def pf(s): return s[s > 0].sum() / -s[s <= 0].sum()
cx = Ctx(); A, T, _ = daily_stats(cx)
PR = {}; R2 = {}
for dd in range(3, cx.nd):
    if A[dd] > 0: PR[cx.dates[dd]] = (cx.prev_close[dd] - cx.prev_close[dd - 1]) / A[dd] * T[dd]; R2[cx.dates[dd]] = (cx.prev_close[dd] - cx.prev_close[dd - 2]) / A[dd] * T[dd]
base = dict(contracts=1, t1_frac=1.0, max_consec_losses=0, dll=0, orb_cap=0.35, vw_stop=0.35)
S = {}
for nm, kw in {"ORB60": dict(use_vwap=False, t1_r=0.6), "VWP60": dict(use_orb=False, t1_r=0.6), "ORB30": dict(use_vwap=False, range_min=30, t1_r=0.75),
               "ORB15": dict(use_vwap=False, range_min=15, t1_r=0.75), "VWP30": dict(use_orb=False, range_min=30, t1_r=0.75)}.items():
    df = r3.run(cx, **base, **kw); S[nm] = df[df.date.map(PR) < 0.44][["date", "usd"]]
B = build(5); out = np.zeros((len(B["c"]) // 3, 4))
k = msim(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], B["up20"], 5, 0.5, 1.75, 0.0, 0, 630, 945, 955, 0.0, out)
S["MSEQ"] = pd.DataFrame(dict(date=B["date"][out[:k, 1].astype(int)], usd=out[:k, 0] * 2 - 1))
d = load(NQ); L, atr, trend = day_levels(d)
S["MOM11"] = tfm.run(d, L, atr, trend, 660, 1, 0.25, 0.3, 0)[["date", "usd"]]
S["CRT11"] = crt2.run(60, (11,), 1, 2.0, 0.0, 0.5, 0.0, 0, 955)[["date", "usd"]] if NQ != "mnq_fut.npz" or True else None
lo = 20240201 if NQ == "mnq_fut.npz" else 20200201
days = [x for x in cx.rth_days if x >= lo]
def report(names, label):
    P = pd.concat([S[n].assign(mod=n) for n in names]); P = P[P.date >= lo]
    daily = P.groupby("date").usd.sum().reindex(days, fill_value=0.0)
    eq = daily.cumsum(); dd = (eq.cummax() - eq).max()
    cov = P.groupby("date").size().reindex(days, fill_value=0)
    sh = daily.mean() / daily.std() * np.sqrt(252)
    yrs = " ".join(f"{y}:{pf(g.usd):.2f}" for y, g in P.groupby(P.date // 10000))
    print(f"{label:34s} tr/day {len(P)/len(days):.2f} | days traded {100*(cov>0).mean():.0f}% | WR {100*(P.usd>0).mean():.1f}% | PF {pf(P.usd):.2f} | net/yr ${daily.sum()/len(days)*252:,.0f} | DD ${dd:,.0f} | Sharpe {sh:.2f} | {yrs}")
print("DATA", NQ)
for n in S: report([n], n)
report(["MOM11"] + list(k for k in S if k.startswith(("ORB", "VWP"))), "MOM11 + pullback modules")
report(["MOM11", "MSEQ"] + [k for k in S if k.startswith(("ORB", "VWP"))], "MOM11 + pullback + MSEQ")
report(["MOM11", "MSEQ", "CRT11"] + [k for k in S if k.startswith(("ORB", "VWP"))], "ALL incl CRT11")
report(["MOM11", "ORB60", "VWP60", "MSEQ"], "MOM11+ORB60+VWP60+MSEQ")

report(["MOM11", "ORB60", "VWP60", "MSEQ", "CRT11"], "MOM11+ORB60+VWP60+MSEQ+CRT11")
pd.to_pickle({k: v.assign(mod=k) for k, v in S.items()}, f"streams_{NQ.split('.')[0]}.pkl")
import sys; sys.exit(0)
# eval pass rates on daily P&L (EOD trailing), scale = MNQ per module
from eval_opt import evals
for names, lab in ((["MOM11", "ORB60", "VWP60", "MSEQ"], "core4"), (["MOM11", "ORB60", "VWP60", "MSEQ", "CRT11"], "core5")):
    P = pd.concat([S[n] for n in names]); P = P[P.date >= lo]
    daily = P.groupby("date").usd.sum().reindex(days, fill_value=0.0).to_numpy()
    z = np.zeros_like(daily)
    for acc, tg, ddl in (("25K 1500/1500", 1500, 1500), ("50K 3000/2500", 3000, 2500), ("50K 3000/2000", 3000, 2000)):
        line = f"  {lab} {acc}:"
        for sc in (1, 2, 3, 4):
            x = daily * sc
            p20, b20, d20 = evals(x, np.minimum(x, 0), np.maximum(x, 0), tg, ddl, 20, 0, len(x) - 10)
            p60, b60, _ = evals(x, np.minimum(x, 0), np.maximum(x, 0), tg, ddl, 60, 0, len(x) - 10)
            line += f" | x{sc}: 20d {p20*100:.0f}/{b20*100:.0f} 60d {p60*100:.0f}/{b60*100:.0f}"
        print(line)
