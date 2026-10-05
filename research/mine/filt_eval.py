"""Honest test of the filter miner: rules chosen on IS only (drop bucket if IS PF_in<1.0 & PF_out>1.2; boost x2 if IS PF_in>1.9;
n>=40), lookahead-prone features excluded (gap for pre-RTH modules; LON excluded: its stored entry time is fixed at 05:00).
Then the WHOLE rule set is applied to C24 and REAL."""
import pickle, numpy as np, pandas as pd, sys
B = pickle.load(open("base_feats.pkl", "rb")); R = pd.read_csv("filt_mine.csv")
PRE = {"ON07", "REV06", "LON"}
ok = ~R["mod"].isin(["LON"]) & ~(R["mod"].isin(PRE) & R.feat.isin(["gap", "open", "rng", "vw"]))
drop_r = R[ok & (R.IS_n >= 40) & (R.IS_pf_in < 1.0) & (R.IS_pf_out > 1.2)]
boost_r = R[ok & (R.IS_n >= 40) & (R.IS_pf_in > 1.9)]
def mask(G, r):
    x = G[r.feat]
    if r.bucket.startswith("low"): return x < r.hi
    return x >= r.lo
def apply(F, drops, boosts):
    w = F.w.copy(); keep = pd.Series(True, index=F.index); b = pd.Series(1.0, index=F.index)
    for r in drops.itertuples():
        m = (F["mod"] == r.mod) & mask(F, r); keep &= ~m.fillna(False)
    for r in boosts.itertuples():
        m = (F["mod"] == r.mod) & mask(F, r); b[m.fillna(False)] = 2.0
    return F[keep].assign(w=w[keep] * b[keep])
def metrics(F, days):
    x = F.u * F.w; d = x.groupby(F.date).sum().reindex(days, fill_value=0); eq = d.cumsum()
    return dict(n=len(F), wr=round(100 * (F.u > 0).mean(), 2), pf=round(x[x > 0].sum() / -x[x <= 0].sum(), 3), sharpe=round(d.mean() / d.std() * np.sqrt(252), 2),
                mo=round(d.mean() * 21), maxdd=round((eq.cummax() - eq).max()))
print("rules: drop", len(drop_r), "boost", len(boost_r))
rows = []
for per in ("IS", "C24", "REAL"):
    F, days = B[per]
    for nm, dr, bo in (("base", drop_r.iloc[0:0], boost_r.iloc[0:0]), ("drops only", drop_r, boost_r.iloc[0:0]), ("boosts only", drop_r.iloc[0:0], boost_r), ("drops+boosts", drop_r, boost_r)):
        r = metrics(apply(F, dr, bo), days); r.update(per=per, set=nm); rows.append(r)
g = pd.DataFrame(rows)
for c in ("wr", "pf", "sharpe", "mo", "maxdd", "n"):
    print(c); print(g.pivot(index="set", columns="per", values=c)[["IS", "C24", "REAL"]].to_string())
pickle.dump((drop_r, boost_r), open("filt_rules_is.pkl", "wb"))
