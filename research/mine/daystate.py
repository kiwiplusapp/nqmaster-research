"""Intraday day-state at each trade's entry (information available BEFORE the entry minute only):
 er   : efficiency ratio of 1-min closes from the RTH open to the minute before entry = |C - O_rth| / sum|dC|
 rng  : RTH range so far / daily ATR
 mv   : (C - O_rth) / ATR, oriented with the trade direction (>0 = trade goes with the day's move)
 vw   : (C - VWAP) / ATR oriented with the trade
 ibx  : 1 if the initial balance (09:30-10:30) has been broken in the trade direction, -1 against, 0 none/not yet
Also the final day type (trend day = |RTH close - open| / range > 0.5) for diagnostics only (look-ahead, never used as a filter).
Output: daystate_trades.pkl {prof: {per: DataFrame with features}}"""
import os, sys, pickle, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
from core import Data
T = pickle.load(open("robust_trades.pkl", "rb"))

@njit(cache=True)
def feats(o, h, l, c, v, sm, ro_i, de_i, tin, d, atr, out):
    # ro_i: index of RTH open bar for the trade's day, de_i: last index of the session; tin = session minute of entry
    for t in range(len(tin)):
        a = ro_i[t]
        if a < 0 or atr[t] <= 0:
            for k in range(6): out[t, k] = np.nan
            continue
        # entry index: first bar with sm >= tin
        j = a
        while j <= de_i[t] and sm[j] < tin[t]: j += 1
        e = j - 1                                     # last bar fully known before entry
        if e < a:                                     # entry before / at the RTH open: no intraday info yet
            for k in range(6): out[t, k] = np.nan
            continue
        O = o[a]; path = 0.0; hi = h[a]; lo = l[a]; pv = 0.0; vv = 0.0; ibh = -1e18; ibl = 1e18
        for q in range(a, e + 1):
            if q > a: path += abs(c[q] - c[q - 1])
            else: path += abs(c[q] - O)
            hi = max(hi, h[q]); lo = min(lo, l[q]); tp = (h[q] + l[q] + c[q]) / 3; pv += tp * v[q]; vv += v[q]
            if sm[q] < sm[a] + 60: ibh = max(ibh, h[q]); ibl = min(ibl, l[q])
        C = c[e]
        out[t, 0] = abs(C - O) / path if path > 0 else 0.0
        out[t, 1] = (hi - lo) / atr[t]
        out[t, 2] = (C - O) * d[t] / atr[t]
        out[t, 3] = (C - pv / vv) * d[t] / atr[t] if vv > 0 else np.nan
        ib = 0
        if sm[e] >= sm[a] + 60:
            up = False; dn = False
            for q in range(a, e + 1):
                if sm[q] >= sm[a] + 60:
                    if h[q] > ibh: up = True
                    if l[q] < ibl: dn = True
            if up and not dn: ib = 1
            elif dn and not up: ib = -1
            elif up and dn: ib = 2
        out[t, 4] = ib * d[t] if ib != 2 else 0
        out[t, 5] = 1.0 if ib == 2 else 0.0

def add_feats(F, D):
    date2day = pd.Series(np.arange(D.nd), index=D.daydate)
    date2day = date2day[~date2day.index.duplicated(keep="last")]
    dd = F.date.map(date2day).fillna(-1).astype(int).to_numpy()
    ro = np.where(dd >= 0, D.ro[np.maximum(dd, 0)], -1); de = np.where(dd >= 0, D.de[np.maximum(dd, 0)], -1)
    atr = np.where(dd >= 0, D.atr[np.maximum(dd, 0)], 0.0)
    out = np.zeros((len(F), 6))
    feats(D.o, D.h, D.l, D.c, D.v, D.sm, ro.astype(np.int64), de.astype(np.int64), F.tin.to_numpy().astype(np.int64), F.d.to_numpy().astype(np.float64), atr, out)
    F = F.copy(); F["er"], F["rng"], F["mv"], F["vw"], F["ibx"], F["ib2"] = out.T
    # diagnostic final day type
    rth = (D.om >= 570) & (D.om < 960)
    g = pd.DataFrame(dict(date=D.date[rth], o=D.o[rth], h=D.h[rth], l=D.l[rth], c=D.c[rth])).groupby("date").agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"))
    td = ((g.c - g.o).abs() / (g.h - g.l)) > 0.5; F["trendday"] = F.date.map(td)
    F["daydir_ok"] = F.date.map(np.sign(g.c - g.o)) * F.d          # look-ahead diagnostic
    return F
DD = {"nq": Data("nq_1m.npz"), "mnq": Data("mnq_fut.npz")}
OUT = {}
for prof, PP in T.items():
    for per, (F, days) in PP.items():
        OUT.setdefault(prof, {})[per] = (add_feats(F, DD["mnq" if per == "REAL" else "nq"]), days)
pickle.dump(OUT, open("daystate_trades.pkl", "wb"))
# ---- quick diagnostics on Ultra
def pf(x): return x[x > 0].sum() / -x[x <= 0].sum() if (x <= 0).any() else np.nan
pd.set_option("display.width", 250)
for prof in ("Ultra",):
    for per in ("IS", "C24", "REAL"):
        F = OUT[prof][per][0]; F["x"] = F.u * F.w
        print(f"\n== {prof} {per}: trades {len(F)}, with intraday info {F.er.notna().sum()}")
        print("  final trend day x with-day-direction (look-ahead diagnostic):")
        print(F.groupby(["trendday", F.daydir_ok > 0]).x.agg(["size", "sum", pf]).round(2).to_string())
        G = F[F.er.notna()].copy()
        qs = OUT[prof]["IS"][0].pipe(lambda X: X[X.er.notna()]).er.quantile([1 / 3, 2 / 3]).to_numpy()
        G["er_t"] = pd.cut(G.er, [-1, qs[0], qs[1], 2], labels=["ER bajo", "ER medio", "ER alto"])
        G["mv_s"] = np.sign(G.mv)
        print("  ER tercile (IS cuts %.3f %.3f) x trade with/against the day's move so far:" % tuple(qs))
        print(G.groupby(["er_t", "mv_s"], observed=True).x.agg(["size", "sum", pf]).round(2).to_string())
