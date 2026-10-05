"""Trade table for the pullback-day engine with risk and day features, for eval-oriented optimisation."""
import numpy as np, pandas as pd
exec(open("pullday.py").read().split("streams = {}")[0])
import nt_v3_replica as r3
base = dict(contracts=1, t1_frac=1.0, max_consec_losses=0, dll=0)
rows = []
cfg = {"orb60": dict(use_vwap=False, range_min=60), "vw60": dict(use_orb=False, range_min=60), "orb30": dict(use_vwap=False, range_min=30),
       "orb15": dict(use_vwap=False, range_min=15), "vw30": dict(use_orb=False, range_min=30)}
for name, kw in cfg.items():
    for t1 in (0.5, 0.6, 0.75, 1.0):
        for cap in (0.25, 0.35):
            df = r3.run(cx, t1_r=t1, orb_cap=cap, vw_stop=cap, **base, **kw)
            df["mod"] = name; df["t1"] = t1; df["cap"] = cap
            df["t_in"] = cx.om[df.entry_idx.to_numpy()]; df["t_out"] = cx.om[df.exit_idx.to_numpy()] + 1
            rows.append(df[["date", "mod", "t1", "cap", "usd", "risk_pts", "t_in", "t_out", "dir"]])
T_ = pd.concat(rows)
m = pd.read_pickle("mseq_times.pkl")
# risk for mseq: rebuild from wr60 sim
from wr60 import build, sim
B = build(5); out = np.zeros((len(B["c"]) // 3, 4))
k = sim(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], B["up20"], 5, 0.5, 1.75, 0.0, 0, 630, 945, 955, 0.0, out)
m["risk_pts"] = out[:k, 2]; m["mod"] = "mseq"; m["t1"] = 0.5; m["cap"] = 0; m["dir"] = 1
T_ = pd.concat([T_, m[["date", "mod", "t1", "cap", "usd", "risk_pts", "t_in", "t_out", "dir"]]])
T_["prevret"] = T_.date.map(PR)
T_["atr"] = T_.date.map(dict(zip(cx.dates, A)))
T_.to_pickle("eval_trades.pkl"); print(len(T_))
