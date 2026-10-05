import pickle, numpy as np, pandas as pd
exec(open("conflict.py").read().split("for tag, lo, split")[0])
R = {"ORB60": 0.6, "ORB90": 0.6, "MSEQ": 0.5, "CRT11": 2.0, "LON": 2.0, "ICT": 1.0, "MOM11": 0.3, "MOM13": 1.0, "MOM1030": 0.3, "ON07": 1.0, "REV06": 0.3, "MSEQS": 0.75}
VV = pickle.load(open("VV_plus3.pkl", "rb"))
M = {}
for tag, lo in (("nq_1m", 20200201), ("mnq_fut", 20240201)):
    V = VV[tag][VV[tag].date >= lo]
    F = conflict_filter(pick(V, R).reset_index(drop=True)); F["u"] = F.usd - 0.9
    days = np.array(sorted(V.date.unique()))
    P = F.pivot_table(index="date", columns="mod", values="u", aggfunc="sum").reindex(days).fillna(0)
    M[tag] = (P, F)
pickle.dump(M, open("modpnl.pkl", "wb"))
P, F = M["nq_1m"]; IS = P[P.index < 20240101]
def sets(P):
    return {"C24": M["nq_1m"][0][M["nq_1m"][0].index >= 20240101], "REAL": M["mnq_fut"][0]}
def perf(D, w, T):
    d = (D * w).sum(axis=1); eq = d.cumsum(); dd = (eq.cummax() - eq).max()
    tw = T.u * T["mod"].map(w)
    return dict(sharpe=round(d.mean() / d.std() * np.sqrt(252), 2), mo=round(d.mean() * 21), maxdd=round(dd), mo_per_dd=round(d.mean() * 21 / dd, 3),
                pf=round(tw[tw > 0].sum() / -tw[tw <= 0].sum(), 3), worstday=round(d.min()))
mods = list(R); sd = IS.std(); mu = IS.mean()
W = {"equal": pd.Series(1.0, mods),
     "invvol": 1 / sd,
     "sharpe": (mu / sd).clip(lower=0) / sd,
     "sqrt_sharpe": np.sqrt((mu / sd).clip(lower=0)) / sd}
rows = []
for nm, w in W.items():
    w = w / w.mean()                                 # mean weight 1
    wi = w.round().clip(1, 3)                         # integer micro contracts 1-3
    for lab, ww in ((nm, w), (nm + "_int", wi)):
        for per in ("IS", "C24", "REAL"):
            D = IS if per == "IS" else sets(P)[per]
            T = F[F.date < 20240101] if per == "IS" else (F[F.date >= 20240101] if per == "C24" else M["mnq_fut"][1])
            r = perf(D, ww, T); r.update(w=lab, per=per); rows.append(r)
    print(nm, w.round(2).to_dict())
g = pd.DataFrame(rows)
print(g.pivot(index="w", columns="per", values=["sharpe", "pf", "mo_per_dd", "mo"]).to_string())
