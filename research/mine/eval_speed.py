"""Eval speed (Lucid Flex 50K: +$3,000, $2,000 EOD trailing, 50% consistency): for every start day of history, run the eval until
pass / bust; report P(pass), P(pass <= 15 / 22 trading days), median days, P(bust). Grid: eval profile x contracts x daily profit stop
x daily loss stop, 3 periods, plus +1 tick cost. -> eval_speed.csv"""
import sys, itertools, numpy as np, pandas as pd
sys.path.insert(0, ".")
import prof_grid_lib
from acct_life import CFG
from acct_policy import vec
from acct_size import eval_stats
from final_verify_lib import exits
T, D = 3000.0, 2000.0
PROF = ["UA_FULL_GR", "UA_FULL_GW", "UA_FULL_none", "WR_FULL_GW", "WR_FULL_GR", "C6_FULL_GR", "ULTRA"]
rows = []
for per in ("IS", "C24", "REAL"):
    for cfg in PROF:
        ce = exits(per, cfg)
        for k, G, DL in itertools.product((1.0, 2.0, 3.0, 4.0), (0.0, 1000.0, 1200.0, 1400.0, 1500.0, 1800.0), (0.0, 600.0, 900.0)):
            v = vec(per, cfg, DL / k if DL > 0 else 0.0, G / k if G > 0 else 0.0)
            for cost in (0, 1):
                lo, cl = (v[0], v[1]) if cost == 0 else (v[0] - ce, v[1] - ce)
                LO = np.ascontiguousarray(np.array([lo] * 3)); CL = np.ascontiguousarray(np.array([cl] * 3))
                out = np.zeros((len(lo), 2)); m = eval_stats(LO, CL, k, 0.0, 0.0, T, D, out); o = out[:m]
                ps = o[:, 0] == 1; days = o[ps, 1]
                rows.append(dict(per=per, cfg=cfg, k=int(k), G=G, DL=DL, cost=cost, p_pass=round(100 * ps.mean(), 1), p15=round(100 * (ps & (o[:, 1] <= 15)).mean(), 1),
                                 p22=round(100 * (ps & (o[:, 1] <= 22)).mean(), 1), med_days=float(np.median(days)) if len(days) else np.nan,
                                 p_bust=round(100 * (o[:, 0] == -1).mean(), 1)))
    print(per, flush=True)
R = pd.DataFrame(rows); R.to_csv("eval_speed.csv", index=False)
A = R.groupby(["cfg", "k", "G", "DL", "cost"])[["p_pass", "p15", "p22", "med_days", "p_bust"]].agg(["mean", "min"])
A.columns = [a + "_" + b for a, b in A.columns]; A = A.reset_index()
pd.set_option("display.width", 250)
for c in (0, 1):
    print("cost", c); print(A[A.cost == c].sort_values("p22_mean", ascending=False).head(25).to_string(index=False))
