import pickle, numpy as np, pandas as pd, sys, os
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
from final_pkg import conflict_filter
TT = pickle.load(open("robust_trades.pkl", "rb")); TR = pickle.load(open("tday_trades.pkl", "rb")); L = None
def met(F, days):
    x = F.u * F.w; d = x.groupby(F.date).sum().reindex(days, fill_value=0.0); eq = d.cumsum()
    return dict(tpd=round(len(F) / len(days), 2), pf=round(x[x > 0].sum() / -x[x <= 0].sum(), 3), sharpe=round(d.mean() / d.std() * 252 ** .5, 2), mo=round(d.mean() * 21), dd=round((eq.cummax() - eq).max()))
rows = []
for prof in ("Ultra",):
    for drop in ([], ["MOM1030"], ["MOM1030", "MOM11"]):
        for nm in [None, "TDAY q80 k0.30 2R", "TDAY q67 k0.45 2R", "TDAY q67 extremo sin obj"]:
            r = dict(drop="+".join(drop) or "-", add=nm or "-")
            for per in ("IS", "C24", "REAL"):
                F, days = TT[prof][per]; F = F[~F["mod"].isin(drop)][["date", "mod", "tin", "tout", "d", "u", "w"]]
                if nm: F = conflict_filter(pd.concat([F, TR[nm][per][F.columns]], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True))
                r.update({f"{per}_{k}": v for k, v in met(F, days).items()})
            rows.append(r)
G = pd.DataFrame(rows); pd.set_option("display.width", 250)
for k in ("sharpe", "pf", "mo", "dd"):
    print(k); print(G[["drop", "add"] + [f"{p}_{k}" for p in ("IS", "C24", "REAL")]].to_string(index=False))
