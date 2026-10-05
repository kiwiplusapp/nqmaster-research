"""Runner only on predicted trend days: trades entering after 10:30 on days whose 10:30 trend-day probability is in the top
tercile (IS cut) keep a 2nd contract after a winning exit, trailed (rule T k*ATR) until 15:55. Everything else: 2 contracts with the
current exits. Compared with plain 2 contracts. Uses runner_delta.pkl (per-trade runner deltas) and trendday_model.pkl."""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
from core import S
exec(open("trendday_pred.py", encoding="utf8").read().split("# bucket Ultra trades")[0])      # rebuild IS/C24/RE tables + model m
T = pickle.load(open("robust_trades.pkl", "rb")); K = pickle.load(open("runner_delta.pkl", "rb"))
q = np.quantile(m.predict_proba(Z(IS))[:, 1], [1 / 3, 2 / 3])
def met(x, F, days):
    d = pd.Series(x).groupby(F.date.to_numpy()).sum().reindex(days, fill_value=0.0); eq = d.cumsum()
    return dict(pf=round(x[x > 0].sum() / -x[x <= 0].sum(), 3), sharpe=round(d.mean() / d.std() * 252 ** .5, 2), mo=round(d.mean() * 21), dd=round((eq.cummax() - eq).max()))
rows = []
for prof in ("Ultra", "WR70Plus"):
    for rule in ("T0.2", "T0.3", "T0.4", "L0.3", "BE"):
        for cut in ("alto", "medio+alto"):
            r = dict(prof=prof, rule=rule, cut=cut)
            for per, X in (("IS", IS), ("C24", C24), ("REAL", RE)):
                F, days = T[prof][per]; delta = K[(prof, per, rule)]
                pmap = pd.Series(m.predict_proba(Z(X))[:, 1], index=X.date.to_numpy()); p = F.date.map(pmap).to_numpy()
                sel = (F.tin.to_numpy() > S(1030)) & ~np.isnan(p) & (p >= (q[1] if cut == "alto" else q[0]))
                base = (2 * F.u * F.w).to_numpy()
                r.update({f"{per}_base_{k}": v for k, v in met(base, F, days).items()})
                r.update({f"{per}_{k}": v for k, v in met(base + np.where(sel, delta, 0.0), F, days).items()})
            rows.append(r)
G = pd.DataFrame(rows); G.to_csv("runner_td.csv", index=False); pd.set_option("display.width", 260)
for k in ("sharpe", "pf", "mo", "dd"):
    cols = ["prof", "rule", "cut"] + [c for p in ("IS", "C24", "REAL") for c in (f"{p}_base_{k}", f"{p}_{k}")]
    print(k); print(G[cols].to_string(index=False))
