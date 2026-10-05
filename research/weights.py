import itertools, numpy as np, pandas as pd
from common import Ctx
def daily_matrix(tag, lo):
    S = pd.read_pickle(f"streams_{tag}.pkl")
    import os; os.environ["NQ_DATA"] = tag + ".npz"
    return S
def mat(S, days):
    M = pd.DataFrame({k: v.groupby("date").usd.sum().reindex(days, fill_value=0.0) for k, v in S.items()})
    return M
import os
os.environ["NQ_DATA"] = "nq_1m.npz"; cx = Ctx(); dC = np.array(cx.rth_days)
os.environ["NQ_DATA"] = "mnq_fut.npz"; cx2 = Ctx(); dF = np.array([d for d in cx2.rth_days if d >= 20240201])
SC = pd.read_pickle("streams_nq_1m.pkl"); SF = pd.read_pickle("streams_mnq_fut.pkl")
# MOM11 split by VWAP agreement using mom11_feat outputs
exec(open("mom11_feat.py").read().split("for f in [")[0])
for tag, S in (("nq_1m.npz", SC), ("mnq_fut.npz", SF)):
    x = out[tag]; S["MOM11a"] = x[x.vw_agree.astype(bool)][["date", "usd"]]; S["MOM11d"] = x[~x.vw_agree.astype(bool)][["date", "usd"]]
mods = ["MOM11a", "MOM11d", "ORB60", "VWP60", "MSEQ", "CRT11", "ORB30", "ORB15", "VWP30"]
MC = mat({k: SC[k] for k in mods}, dC); MF = mat({k: SF[k] for k in mods}, dF)
IS = MC.index < 20240101
print("daily corr (real):"); print(MF.corr().round(2))
def sh(x): return x.mean() / x.std() * np.sqrt(252)
best = []
for w in itertools.product((1,), (0, 1), (0, 1, 2, 3), (0, 1, 2), (0, 1, 2), (0, 1, 2, 3), (0, 1), (0, 1), (0, 1)):
    w = np.array(w, float)
    a = MC[IS].to_numpy() @ w
    best.append((sh(a), tuple(w)))
best.sort(reverse=True)
print("\nTop weights by IS Sharpe (CFD 2020-23), then CFD 24-26 and REAL 24-26:")
for s, w in best[:12]:
    w = np.array(w); b = MC[~IS].to_numpy() @ w; f = MF.to_numpy() @ w
    print(dict(zip(mods, w.astype(int))), f"IS {s:.2f} | C24 {sh(b):.2f} | REAL {sh(f):.2f}")
base = np.array([1, 1, 1, 1, 1, 1, 0, 0, 0], float)
print("\nbase core5:", f"IS {sh(MC[IS].to_numpy()@base):.2f} C24 {sh(MC[~IS].to_numpy()@base):.2f} REAL {sh(MF.to_numpy()@base):.2f}")
pd.to_pickle((MC, MF, mods), "daily_mats.pkl")
