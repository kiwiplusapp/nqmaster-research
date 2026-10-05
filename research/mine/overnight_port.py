"""Portfolio value of ONDRIFT (long at the 18:00 Globex open, exit 07:00 ET, optional stop k*ATR) added to Ultra / WR70Plus,
first-come conflict filter (overnight modules LON/REV06/ON07 cannot go short while ONDRIFT is long). Trades use the session's
trading day as 'date' (same convention as the other modules: date of the RTH day the session belongs to)."""
import os, sys, pickle, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
from core import Data, S
from final_pkg import conflict_filter
from news import NEWS
T = pickle.load(open("robust_trades.pkl", "rb"))
@njit(cache=True)
def sim(o, h, l, c, sm, ds, de, atr, trend, A, B, k, mode, out):
    n = 0
    for d in range(len(ds)):
        if ds[d] < 0 or atr[d] <= 0: continue
        s = 1
        if mode == 1 and trend[d] != 1: continue
        a = -1; b = -1
        for q in range(ds[d], de[d] + 1):
            if a < 0 and sm[q] >= A: a = q
            if sm[q] < B: b = q
        if a < 0 or b <= a: continue
        e = o[a] + s * 0.25; stop = e - s * k * atr[d]; x = np.nan; xi = b
        for q in range(a, b + 1):
            if (s == 1 and l[q] <= stop) or (s == -1 and h[q] >= stop):
                x = (min(o[q], stop) if s == 1 else max(o[q], stop)) - s * 0.25; xi = q; break
        if np.isnan(x): x = c[b] - s * 0.25
        out[n, 0] = d; out[n, 1] = s * (x - e); out[n, 2] = a; out[n, 3] = xi; out[n, 4] = s; n += 1
    return n
def ondrift(D, k, mode=0, A=1800, B=700):
    out = np.zeros((D.nd, 5)); n = sim(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr.astype(np.float64), D.trend, S(A), S(B), k, mode, out); o = out[:n]
    a = o[:, 2].astype(int); x = o[:, 3].astype(int)
    df = pd.DataFrame(dict(date=D.daydate[o[:, 0].astype(int)], u=o[:, 1] * 2 - 1.9, tin=D.sm[a], tout=D.sm[x] + 1, d=o[:, 4]))
    return df[~df.date.isin(NEWS["FOMC"])]
DD = {"nq": Data("nq_1m.npz"), "mnq": Data("mnq_fut.npz")}
def met(F, days):
    x = F.u * F.w; d = x.groupby(F.date).sum().reindex(days, fill_value=0.0); eq = d.cumsum()
    return dict(tpd=round(len(F) / len(days), 2), wr=round(100 * (F.u > 0).mean(), 1), pf=round(x[x > 0].sum() / -x[x <= 0].sum(), 3),
                sharpe=round(d.mean() / d.std() * 252 ** .5, 2), mo=round(d.mean() * 21), dd=round((eq.cummax() - eq).max()))
rows = []; KEEP = {}
for k, mode in ((9.0, 0), (0.5, 0), (0.35, 0), (0.5, 1)):
    for key in ("nq", "mnq"): KEEP[(k, mode, key)] = ondrift(DD[key], k, mode)
for prof in ("Ultra", "WR70Plus", "Core6"):
    for add in [None, (9.0, 0), (0.5, 0), (0.35, 0), (0.5, 1)]:
        r = dict(prof=prof, add="BASE" if add is None else f"ONDRIFT stop {add[0]} {'tendencia' if add[1] else 'siempre'}")
        for per in ("IS", "C24", "REAL"):
            F, days = T[prof][per]; F = F[["date", "mod", "tin", "tout", "d", "u", "w"]]
            if add is not None:
                O = KEEP[(add[0], add[1], "mnq" if per == "REAL" else "nq")]
                O = O[(O.date >= days.min()) & (O.date <= days.max())].assign(mod="ONDRIFT", w=1.0)
                F = conflict_filter(pd.concat([O[F.columns], F], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True))
            m = met(F, days); r.update({f"{per}_{kk}": v for kk, v in m.items()})
            if per == "REAL": r.update({f"R26_{kk}": v for kk, v in met(F[F.date >= 20260101], days[days >= 20260101]).items()})
        rows.append(r); print(r["prof"], r["add"], flush=True)
G = pd.DataFrame(rows); G.to_csv("overnight_port.csv", index=False); pd.set_option("display.width", 260)
for kk in ("tpd", "wr", "pf", "sharpe", "mo", "dd"):
    print(kk); print(G[["prof", "add"] + [f"{p}_{kk}" for p in ("IS", "C24", "REAL", "R26")]].to_string(index=False))
pickle.dump(KEEP, open("ondrift_trades.pkl", "wb"))
