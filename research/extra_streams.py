import numpy as np, pandas as pd, os
import tmom, ict
from common import Ctx
MC, MF, mods = pd.read_pickle("daily_mats.pkl")
ADD = {"MOM13": (780, -2, 0, 0.2, 1.0, 240, 1), "MOM1030": (630, -2, 0, 0.2, 0.3, 60, 1), "ON07": (420, 30, 0, 0.2, 1.0, 60, 1), "REV06": (360, 30, 1, 0.2, 0.3, 240, 1)}
res = {}
for tag, M in (("nq_1m.npz", MC), ("mnq_fut.npz", MF)):
    D = tmom.load(tag); X = tmom.day_levels(D)
    for k, p in ADD.items():
        df = tmom.run(D, X, *p); M[k] = df.groupby("date").usd.sum().reindex(M.index, fill_value=0.0)
    B = ict.bars(D, 5); L, atr, trend = ict.day_levels(D)
    df = ict.run(B, L, atr, trend, np.array([1, 1, 1, 1, 1, 1], np.bool_), (570, 630), 4, 2, 1.0, 1, 0.25)
    M["ICT_OPEN"] = df.groupby("date").usd.sum().reindex(M.index, fill_value=0.0)
    res[tag] = M
def sh(x): return x.mean() / x.std() * np.sqrt(252)
MC, MF = res["nq_1m.npz"], res["mnq_fut.npz"]
IS = MC.index < 20240101
print("single-stream Sharpe  IS | C24 | REAL")
for k in MC.columns:
    print(f"  {k:9s} {sh(MC[k][IS]):5.2f} | {sh(MC[k][~IS]):5.2f} | {sh(MF[k]):5.2f}")
core = ["MOM11a", "MOM11d", "ORB60", "VWP60", "MSEQ", "CRT11"]
for name, cols in (("core5", core), ("core5+ICT", core + ["ICT_OPEN"]), ("core5+ICT+MOM13", core + ["ICT_OPEN", "MOM13"]),
                   ("core5+ICT+MOM13+ON07", core + ["ICT_OPEN", "MOM13", "ON07"]), ("all", core + ["ICT_OPEN", "MOM13", "ON07", "REV06", "MOM1030"])):
    a = MC[cols].sum(axis=1); f = MF[cols].sum(axis=1)
    print(f"{name:24s} Sharpe IS {sh(a[IS]):.2f} | C24 {sh(a[~IS]):.2f} | REAL {sh(f):.2f} | real corr to core5 {np.corrcoef(f, MF[core].sum(axis=1))[0,1]:.2f}")
pd.to_pickle((MC, MF), "daily_mats2.pkl")
