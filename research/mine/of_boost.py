"""Expected effect of NQMaster's order-flow boost (UseOrderFlowBoost) on the research trades, as implemented in NQMaster.cs:
size x2 when the session cumulative delta (aggressor buy - sell since 18:00 ET / volume, measured before the fill bar) agrees with
the trade by >= 0.015; 'cap' = never above 2x the base size (OrderFlowStack off, default), 'stack' = x2 on top of other x2 boosts.
Ultra on real NQ futures (db_long_trades.pkl, Databento), 2026-04-01..10-08, $ per MNQ contract (base size 1).
IS = Apr-Jun (where the 0.015 threshold, the top-20% edge, was read), OOS = Jul-Oct.  -> of_boost.json
Reference for Federico's Strategy Analyzer run (Tick Replay, boost ON vs OFF): ~16% of entries boosted, $ +32% (cap)."""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from wrq_lib import getD


def pf(x):
    x = np.asarray(x); l = -x[x <= 0].sum()
    return round(float(x[x > 0].sum() / l), 3) if l > 0 else None


def stats(s, x):
    d = x.groupby(s.date.to_numpy()).sum(); eq = d.cumsum()
    return dict(net=round(float(x.sum())), pf=pf(x), max_dd=round(float((eq.cummax() - eq).max())))


if __name__ == "__main__":
    M = pickle.load(open(os.path.join(HERE, "of_minutes.pkl"), "rb"))
    D = getD("nqdb.npz"); ep = np.load(os.path.join(os.path.dirname(HERE), "data", "nqdb.npz"))["epoch"]
    S = M.reindex(ep).fillna(0.0); cb, cs = np.cumsum(np.r_[0, S.buy.to_numpy()]), np.cumsum(np.r_[0, S.sell.to_numpy()])
    first = D.ds[D.day]
    Xr, _ = pickle.load(open(os.path.join(HERE, "db_long_trades.pkl"), "rb"))["Ultra"]
    X = Xr[(Xr.atr >= 150) & (Xr.date >= 20260401)].copy()
    i = X.fi.to_numpy(); B = cb[i] - cb[first[i]]; A = cs[i] - cs[first[i]]
    X["cvd"] = np.where(B + A > 0, (B - A) / np.maximum(B + A, 1), np.nan) * X.d.to_numpy()
    X = X[ep[i] - 30 >= M.index.min()]
    OUT = {"trades": int(len(X)), "is_quintile_edges": [round(float(v), 4) for v in np.nanquantile(X.loc[X.date < 20260701, "cvd"], [0.2, 0.4, 0.6, 0.8])], "thresholds": {}}
    for thr in (0.010, 0.015, 0.020):
        rec = {}
        for lab, m in (("IS_Apr_Jun", X.date < 20260701), ("OOS_Jul_Oct", X.date >= 20260701), ("ALL", X.date > 0)):
            s = X[m]; hit = (s.cvd >= thr).to_numpy()
            rec[lab] = dict(n=int(len(s)), boosted_pct=round(100 * float(hit.mean()), 1),
                            off=stats(s, s.u * s.w), cap=stats(s, s.u * np.where(hit, np.maximum(s.w, 2), s.w)), stack=stats(s, s.u * s.w * np.where(hit, 2, 1)))
        OUT["thresholds"][str(thr)] = rec
        print(thr, json.dumps(rec), flush=True)
    X["hit"] = X.cvd >= 0.015
    OUT["by_module_0.015"] = {md: {("boosted" if h else "not"): dict(n=int(len(g)), pnl=round(float((g.u * g.w).sum())), wr=round(100 * float((g.u > 0).mean()), 1))
                                    for h, g in grp.groupby("hit")} for md, grp in X.groupby("mod")}
    OUT["avg_trade_by_month_0.015"] = {str(mo): {("boosted" if h else "not"): round(float((g.u * g.w).mean()), 1) for h, g in grp.groupby("hit")}
                                       for mo, grp in X.groupby(X.date // 100)}
    json.dump(OUT, open(os.path.join(HERE, "of_boost.json"), "w"), indent=1)
