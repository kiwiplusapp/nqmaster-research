"""2026-10-27 (experiment 01, S2): research trade set of the 2027 default (ultra_d4) rebuilt on the instrument NinjaTrader trades,
MNQ (research/data/mnq_fut.npz, 2024-02 ..), for the parity check against the Strategy Analyzer. The reference set ultra_d4 is built on
Databento NQ (nqdb.npz) and 13 ICT, 5 MSEQS, 16 RV11 and several threshold-edge trades of the baseline mismatch were NQ-vs-MNQ data
differences, not port bugs. Same rules and parameters as six_build.py / cand16.py 'UltraR' (with_minstop, BE, ORBt, agreement
MOM1030/MOM13, boosts, context rules filt_sel pruned), MinATR 150, FOMC and short sessions skipped (SkipShortSessions), six-year
modules regenerated on MNQ with their exact grid rows. CPI09 keeps its nqdb trades (cpi_lab has no MNQ build; 26 trades, 92% parity).
Requires wrq_entries.pkl / wrq_feats.pkl rebuilt with the current code (python3 wrq_build.py && python3 wrq_feats.py).
-> six_ultra6_trades_mnq.pkl ('Ultra6'); nt_compare.research_set('ultra_d4_mnq').  Run from research/mine."""
import os, sys, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import cand16
from wrq_lib import getD
from wrq_port import ULTRA
from wrq_combo import BE, ORBt
from news import NEWS
import run_mine_db as M
from core import run_events
import six_build as SB
NAME = "mnq_fut.npz"

if __name__ == "__main__":
    full = pickle.load(open("filt_sel.pkl", "rb")); pruned = [(r, k) for r, k in full if (r["mod"], r["feat"]) not in (("ORB90", "vw"), ("ORB60", "atr"))]
    UR = {k: v for k, v in ULTRA.items() if k not in ("ENG10", "LATEFH")}
    X = cand16.trades(UR, cand16.with_minstop({**BE, **ORBt}, UR), ("MOM1030", "MOM13"), True, "REAL", pruned)
    if "atr" in X.columns: X = X[X.atr >= 150]
    U = X[["date", "mod", "tin", "tout", "d", "u", "w"]].copy()
    Q = pickle.load(open("ultraq_trades.pkl", "rb"))["UltraQ"][0]; cpi = Q[Q["mod"] == "CPI09"][["date", "mod", "tin", "tout", "d", "u", "w"]].copy()
    U = pd.concat([U, cpi], ignore_index=True); U.loc[U["mod"].isin(["MOM1030", "CPI09"]), "w"] = 4.0
    D = getD(NAME)
    dd = np.array(sorted(set(D.daydate[D.ro >= 0]))); atr = pd.Series(D.atr, index=D.daydate).groupby(level=0).last().reindex(dd).to_numpy()
    ok = set(dd[(atr >= 150) & ~np.isin(dd, list(NEWS["FOMC"]))].tolist())
    rth = (D.om >= 570) & (D.om < 960); last = pd.Series(D.om[rth]).groupby(D.day[rth]).max().reindex(range(D.nd)).fillna(0).to_numpy()
    ok -= set(D.daydate[np.where(last < 959)[0]].tolist())
    parts = [U[U.date.isin(ok)]]
    for nm in ("SO04", "RV11", "ORFAIL", "CAM3"):
        fam, j = SB.NEW[nm]; gen, grid, maxday = M.FAMILIES[fam]
        r = run_events(D, gen(D, grid[j]), flat=M.FLAT, maxday=maxday, slip=0.25); r = r[r.date.isin(ok)]
        parts.append(pd.DataFrame(dict(date=r.date.to_numpy(), mod=nm, tin=D.sm[r.fi.to_numpy().astype(int)], tout=D.sm[r.xi.to_numpy().astype(int)] + 1, d=r.d.to_numpy(), u=r.usd.to_numpy(), w=1.0)))
        print(nm, fam, j, len(r), "trades on MNQ", flush=True)
    A = pd.concat(parts, ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True)
    pickle.dump({"Ultra6": A}, open("six_ultra6_trades_mnq.pkl", "wb"))
    print(A["mod"].value_counts().to_dict(), len(A), "days", A.date.nunique())
