"""Robustness lab, step 1 (2026-10-12, Federico: 'never lose an eval / funded account to a month like August'):
trade sets of the current profiles on REAL Databento NQ futures 2020-01 .. 2026-10 (db_long machinery, MinATR 150, FOMC skipped),
each trade with its entry price and initial stop -> $ risk per trade, and per-day minute paths (intraday equity low incl. open
adverse excursion, and close) for the account simulators (mffu_rapid.ev_m / fu_m).
Variants: Ultra, UltraLean, WR70Plus, Estable (eval safe set, no boosts) and Ultra / WR70Plus with a per-trade $ risk cap
(skip the trade when stop distance x $2 x size > cap). -> scratchpad robust2_paths.pkl, robust2_trades.pkl (repo)"""
import os, sys, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
# 2026-10-27 (experiment 01, S3): the path caches lived in a session scratchpad that no longer exists (not reproducible). They now go to
# research/tmp/scratch (git-ignored, rebuilt by acct_2027.build()) unless NQ_SCRATCH points elsewhere; the old location is used only if it still exists.
_OLD_SP = "/tmp/claude-0/-home-user-nqmaster-research/c6cc5ef6-fbab-51d6-8437-b8f6d9d1ef6e/scratchpad"
SP = os.environ.get("NQ_SCRATCH") or (_OLD_SP if os.path.isdir(_OLD_SP) else os.path.join(os.path.dirname(HERE), "tmp", "scratch"))
os.makedirs(SP, exist_ok=True)
import db_long
from db_long import NAME, entries_db
from wrq_lib import getD, S
import wrq_combo, wrq_port
from news import NEWS
SLIP = 0.25


def setup():
    E = entries_db(); wrq_port.entries()[NAME] = E
    D0 = getD(NAME); wrq_combo.FT[NAME] = pd.DataFrame({"tso": (D0.sm[E.fi.to_numpy()] - S(930)).astype(float)}, index=E.index)
    return E


def attach(X, E):
    k = E[["mod", "fi", "ent0", "et", "sl0"]].drop_duplicates(["mod", "fi"])
    X = X.merge(k, on=["mod", "fi"], how="left")
    X["e"] = X.ent0 + np.where(X.et == 0, X.d * SLIP, 0.0)
    X["risk"] = (X.e - X.sl0).abs() * 2.0 * X.w
    return X


def days_real():
    D = getD(NAME)
    dd = np.array(sorted(set(D.daydate[(D.ro >= 0)]))); dd = dd[dd >= 20200101]
    atr = pd.Series(D.atr, index=D.daydate).groupby(level=0).last().reindex(dd).to_numpy()
    return dd[(atr >= 150) & ~np.isin(dd, list(NEWS["FOMC"]))]


def minute_paths(X, days):
    D = getD(NAME); pos = {d: i for i, d in enumerate(days)}; nd = len(days)
    Rinc = np.zeros((nd, 1440)); OA = np.zeros((nd, 1440)); XA = np.zeros((nd, 1440)); OC = np.zeros((nd, 1440))
    for t in X.itertuples():
        r = pos.get(t.date)
        if r is None: continue
        s = t.d; w = t.w; q = np.arange(t.fi, t.xi); sm = D.sm[q]
        adv = ((D.l[q] - t.e) if s > 0 else (t.e - D.h[q])) * D.pv - D.comm
        cls = (D.c[q] - t.e) * s * D.pv - D.comm
        np.add.at(OA[r], sm, w * adv); np.add.at(OC[r], sm, w * cls)
        mx = D.sm[t.xi]; advx = ((D.l[t.xi] - t.e) if s > 0 else (t.e - D.h[t.xi])) * D.pv - D.comm
        Rinc[r, mx] += w * t.u; XA[r, mx] += w * min(advx, t.u)
    Rc = np.cumsum(Rinc, 1)
    low = Rc - Rinc + OA + XA; close = Rc + OC
    return low.min(1), close[:, -1], Rc[:, -1]


if __name__ == "__main__":
    E = setup(); days = days_real(); TR = {}; P = {}
    for prof in ("Ultra", "UltraLean", "WR70Plus", "Estable"):
        X = db_long.trades(prof, "DB"); X = X[X.date.isin(days)]
        TR[prof] = attach(X, E); print(prof, len(TR[prof]), "risk median", round(TR[prof].risk.median()), "p90", round(TR[prof].risk.quantile(0.9)), flush=True)
    for base in ("Ultra", "WR70Plus"):
        for cap in (200, 300, 400, 500):
            TR[f"{base}_cap{cap}"] = TR[base][TR[base].risk <= cap]
    for k, X in TR.items():
        lo, cl, fin = minute_paths(X, days); P[k] = (np.minimum(lo, cl), cl)
        print(k, len(X), "day-low min", round(lo.min()), flush=True)
    pickle.dump((days, P), open(os.path.join(SP, "robust2_paths.pkl"), "wb"))
    pickle.dump(TR, open(os.path.join(HERE, "robust2_trades.pkl"), "wb"))
