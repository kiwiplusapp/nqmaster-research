"""Candidate profiles for the 2026-10-12 overhaul, fully rebuilt (conflict filter, agreement, confluence and context rules recomputed)
on REAL Databento NQ 2020-26 (MinATR 150) and cost-normalised 2010-19:
  Ultra       today
  UltraR      Ultra - ENG10 - LATEFH, context boosts ORB90-vw and ORB60-atr removed, structure stops >= 0.10 ATR
  UltraR-ON   UltraR - ON07
  UltraWR     UltraR - ON07 - LON - ICT  (win-rate oriented)
  WR70Plus    today;  WR70R = WR70Plus with the same two boosts removed and the 0.10 ATR minimum stop
-> cand16.json, cand16_trades.pkl"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import robust2_build as RB
import wrq_port, wrq_combo, db_long
from wrq_lib import getD
from wrq_port import ULTRA, WR70
from wrq_combo import BE, ORBt, VTSO
from news import NEWS
STRUCT = ["ORB60", "ORB90", "VOLB", "VOLB_tf1", "MSEQ", "MSEQS", "CRT11", "ICT", "LON", "ENG10"]
MINSTOP = 0.10


def minstop(prev=None):
    def k(E, name):
        D = getD(name); ok = ((E.ent0 - E.sl0).abs() / D.atr[D.day[E.fi.to_numpy()]] >= MINSTOP).to_numpy()
        return ok & (prev(E, name) if prev is not None else True)
    return k


def with_minstop(over, mods):
    o = {k: v for k, v in over.items() if k in mods}
    for m in mods:
        if m in STRUCT:
            p, kf = o.get(m, ({}, None)); o[m] = (p, minstop(kf))
    return o


def trades(mods, over, agr, boosts, per, sel):
    wrq_port._SEL = sel
    wrq_port.PROFILES["_f"] = mods
    X = wrq_combo.build(per, "_f", over, tuple(a for a in agr if a in mods))
    if not boosts: X["w"] = 1.0
    return X.sort_values(["date", "tin"]).reset_index(drop=True)


def stats(X, lo, hi, real, alld, atr_d):
    s = X[(X.date >= lo) & (X.date < hi)]; x = s.u * s.w
    r = dict(n=int(len(s)), wr=round(100 * float((s.u > 0).mean()), 2), pf=round(float(x[x > 0].sum() / -x[x <= 0].sum()), 3))
    if real:
        dd = alld[(alld >= lo) & (alld < hi)]; dd = dd[atr_d.reindex(dd).to_numpy() >= 150]
        d = x.groupby(s.date).sum().reindex(dd, fill_value=0.0); eq = d.cumsum(); mo = d.groupby(d.index // 100).sum()
        r.update(tpd=round(len(s) / len(dd), 2), per_month=round(float(d.mean() * 21)), sharpe=round(float(d.mean() / d.std() * np.sqrt(252)), 2),
                 max_dd=round(float((eq.cummax() - eq).max())), worst_month=round(float(mo.min())), neg_months=int((mo < 0).sum()), months=int(len(mo)))
    return r


if __name__ == "__main__":
    RB.setup(); D = getD(RB.NAME)
    alld = np.array(sorted(set(D.daydate[(D.ro >= 0)]))); alld = alld[~np.isin(alld, list(NEWS["FOMC"]))]
    atr_d = pd.Series(D.atr, index=D.daydate).groupby(level=0).last()
    full = pickle.load(open(os.path.join(HERE, "filt_sel.pkl"), "rb"))
    pruned = [(r, k) for r, k in full if (r["mod"], r["feat"]) not in (("ORB90", "vw"), ("ORB60", "atr"))]
    UR = {k: v for k, v in ULTRA.items() if k not in ("ENG10", "LATEFH")}
    C = {"Ultra": (ULTRA, {**BE, **ORBt}, ("MOM1030", "MOM13"), True, full, False),
         "UltraR": (UR, {**BE, **ORBt}, ("MOM1030", "MOM13"), True, pruned, True),
         "UltraR-ON": ({k: v for k, v in UR.items() if k != "ON07"}, {**BE, **ORBt}, ("MOM1030", "MOM13"), True, pruned, True),
         "UltraWR": ({k: v for k, v in UR.items() if k not in ("ON07", "LON", "ICT")}, {**BE, **ORBt}, ("MOM1030", "MOM13"), True, pruned, True),
         "WR70Plus": (WR70, {**ORBt, **VTSO}, (), True, full, False),
         "WR70R": (WR70, {**ORBt, **VTSO}, (), True, pruned, True)}
    OUT = {}; TRD = {}
    for name, (mods, over, agr, boosts, sel, ms) in C.items():
        o = with_minstop(over, mods) if ms else {k: v for k, v in over.items() if k in mods}
        Xr = trades(mods, o, agr, boosts, "DB", sel); Xr = Xr[Xr.atr >= 150]; Xn = trades(mods, o, agr, boosts, "DB_N", sel)
        TRD[name] = (Xr, Xn)
        rec = {"2010-14n": stats(Xn, 20100601, 20150101, False, alld, atr_d), "2015-19n": stats(Xn, 20150101, 20200101, False, alld, atr_d),
               "2020-23": stats(Xr, 20200101, 20240101, True, alld, atr_d), "2024-26": stats(Xr, 20240101, 20991231, True, alld, atr_d)}
        OUT[name] = rec
        print(f"{name:10s}", " | ".join(f"{k}: WR {v['wr']} PF {v['pf']}" + (f" $/mo {v['per_month']} Sh {v['sharpe']} DD {v['max_dd']} wMo {v['worst_month']} neg {v['neg_months']}/{v['months']} tpd {v['tpd']}" if 'per_month' in v else "") for k, v in rec.items()), flush=True)
    wrq_port._SEL = full
    json.dump(OUT, open(os.path.join(HERE, "cand16.json"), "w"), indent=1)
    pickle.dump(TRD, open(os.path.join(HERE, "cand16_trades.pkl"), "wb"))
