"""Marginal value of LATE15 (15:00 continuation when the RTH move >= 0.5 ATR with the daily trend) on Ultra and WR70Plus.
Also re-tests ENGULF_4H#411 and combos. Same conflict filter / metrics as the rest of the research."""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
import final_pkg
from final_pkg import cand_trades, conflict_filter
from core import Data, run_events
from families3 import FAMILIES3
from families4 import FAMILIES4
from news import NEWS
T = pickle.load(open("robust_trades.pkl", "rb"))
def gtr(fams, fam, j):
    gen, G, md = fams[fam]; out = {}
    for key, nm in (("nq", "nq_1m.npz"), ("mnq", "mnq_fut.npz")):
        D = final_pkg._D.get(key) or Data(nm); final_pkg._D[key] = D
        df = run_events(D, gen(D, G[j]), flat=955, maxday=md); df["tin"] = D.sm[df.fi.to_numpy().astype(int)]; df["tout"] = D.sm[df.xi.to_numpy().astype(int)] + 1
        out[key] = df[["date", "usd", "tin", "tout", "d"]]
    return out
C = {"LATE15#762": gtr(FAMILIES4, "LATE_MOM", 762), "LATE15#759": gtr(FAMILIES4, "LATE_MOM", 759), "LATE15#765": gtr(FAMILIES4, "LATE_MOM", 765),
     "LATE1430#190": gtr(FAMILIES4, "LATE_MOM", 190), "ENGULF#411": gtr(FAMILIES3, "ENGULF_4H", 411)}
def met(F, days):
    x = F.u * F.w; d = x.groupby(F.date).sum().reindex(days, fill_value=0.0)
    eq = d.cumsum()
    return dict(tpd=round(len(F) / len(days), 2), wr=round(100 * (F.u > 0).mean(), 1), pf=round(x[x > 0].sum() / -x[x <= 0].sum(), 3),
                sharpe=round(d.mean() / d.std() * 252 ** .5, 2), mo=round(d.mean() * 21), dd=round((eq.cummax() - eq).max()))
rows = []
for prof in ("Ultra", "WR70Plus"):
    for add in ([], ["LATE15#762"], ["LATE15#759"], ["LATE15#765"], ["LATE1430#190"], ["LATE15#762", "ENGULF#411"], ["LATE15#762", "LATE1430#190"]):
        r = dict(prof=prof, add="+".join(add) or "BASE")
        for per in ("IS", "C24", "REAL"):
            F, days = T[prof][per]
            parts = [F[["date", "mod", "tin", "tout", "d", "u", "w"]]] + [cand_trades(C[a], per, a, 1.0)[["date", "mod", "tin", "tout", "d", "u", "w"]] for a in add]
            X = conflict_filter(pd.concat(parts, ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True)) if add else parts[0]
            m = met(X, days); r.update({f"{per}_{k}": v for k, v in m.items()})
            if per == "REAL":
                m26 = met(X[X.date >= 20260101], days[days >= 20260101]); r.update({f"R26_{k}": v for k, v in m26.items()})
        rows.append(r); print(r["prof"], r["add"], flush=True)
G = pd.DataFrame(rows); G.to_csv("late_port.csv", index=False); pd.set_option("display.width", 260)
for k in ("tpd", "wr", "pf", "sharpe", "mo", "dd"):
    print(k); print(G[["prof", "add"] + [f"{p}_{k}" for p in ("IS", "C24", "REAL", "R26")]].to_string(index=False))
