"""Portfolio value of TDAY variants on Ultra / WR70Plus (conflict filter), all periods + 2026."""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
exec(open("tday.py", encoding="utf8").read().split("pIS = m.predict_proba")[0])
from final_pkg import conflict_filter
pIS = m.predict_proba(Z(IS))[:, 1]
VARS = {"TDAY q50 k0.45 sin obj": (0.5, 0.45, 0, 99.0), "TDAY q67 k0.45 2R": (0.667, 0.45, 0, 2.0), "TDAY q80 k0.30 2R": (0.8, 0.30, 0, 2.0),
        "TDAY q50 k0.30 2R": (0.5, 0.30, 0, 2.0), "TDAY q67 extremo sin obj": (0.667, 0.2, 1, 99.0)}
def trades(D, Tab, v):
    q, k, sm_, R = v; thr = float(np.quantile(pIS, q))
    df = run_events(D, events(D, Tab, thr, k, sm_, R), flat=955, maxday=1)
    return pd.DataFrame(dict(date=df.date, mod="TDAY", tin=D.sm[df.fi.to_numpy().astype(int)], tout=D.sm[df.xi.to_numpy().astype(int)] + 1, d=df.d, u=df.usd - 0.9, w=1.0))
TT = pickle.load(open("robust_trades.pkl", "rb"))
def met(F, days):
    x = F.u * F.w; d = x.groupby(F.date).sum().reindex(days, fill_value=0.0); eq = d.cumsum()
    return dict(tpd=round(len(F) / len(days), 2), wr=round(100 * (F.u > 0).mean(), 1), pf=round(x[x > 0].sum() / -x[x <= 0].sum(), 3),
                sharpe=round(d.mean() / d.std() * 252 ** .5, 2), mo=round(d.mean() * 21), dd=round((eq.cummax() - eq).max()))
TR = {nm: {"IS": trades(DN, IS, v), "C24": trades(DN, C24, v), "REAL": trades(DM, RE, v)} for nm, v in VARS.items()}
pickle.dump(TR, open("tday_trades.pkl", "wb"))
rows = []
for prof in ("Ultra", "WR70Plus", "Core6"):
    for nm in [None] + list(VARS):
        r = dict(prof=prof, add=nm or "BASE")
        for per in ("IS", "C24", "REAL"):
            F, days = TT[prof][per]; F = F[["date", "mod", "tin", "tout", "d", "u", "w"]]
            if nm: F = conflict_filter(pd.concat([F, TR[nm][per][F.columns]], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True))
            r.update({f"{per}_{k}": v for k, v in met(F, days).items()})
            if per == "REAL": r.update({f"R26_{k}": v for k, v in met(F[F.date >= 20260101], days[days >= 20260101]).items()})
        rows.append(r)
G = pd.DataFrame(rows); G.to_csv("tday_port.csv", index=False); pd.set_option("display.width", 260)
for k in ("tpd", "wr", "pf", "sharpe", "mo", "dd"):
    print(k); print(G[["prof", "add"] + [f"{p}_{k}" for p in ("IS", "C24", "REAL", "R26")]].to_string(index=False))
