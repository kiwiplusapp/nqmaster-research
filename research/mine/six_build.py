"""2026-10-16: research trade set of NQMaster Ultra with the six-year modules (for nt_compare / parity_check --set ultra6 and the edge
monitor): six_trades.pkl 'Ultra' (UltraR + CPI09, MOM1030/CPI09 x4) + LATEFH (cand16 'Ultra') + the 7 mined modules under their
NinjaTrader names, only on days NQMaster trades (no FOMC, ATR >= 150). Real Databento NQ from 2020-10-15. -> six_ultra6_trades.pkl"""
import os, sys, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import six_lib as S
from wrq_lib import getD
NEW = {"CA04V": ("CLOCK_ANCHOR", 916), "SO04": ("CLOCK_ANCHOR", 1527), "GD03": ("G_DRIVE", 3922), "RV11": ("RVOL_DRIVE", 4226),
       "ENG26": ("ENGULF_4H", 25), "ORFAIL": ("OR_FAIL", 142), "CAM3": ("PIVOT_FADE", 365)}

if __name__ == "__main__":
    D = getD("nqdb.npz"); TR = {}
    for f in ("trades_db_old.pkl", "trades_db_new.pkl"): TR.update(pickle.load(open(os.path.join(HERE, f), "rb")))
    U = S.base()[["date", "mod", "tin", "tout", "d", "u", "w"]]
    X = pickle.load(open(os.path.join(HERE, "cand16_trades.pkl"), "rb"))["Ultra"][0]; L = X[(X["mod"] == "LATEFH") & (X.date >= S.START)][["date", "mod", "tin", "tout", "d", "u", "w"]]
    import robust2_build as RB
    ok = set(RB.days_real())                                  # NQMaster skips FOMC days and days with ATR < 150 (MinAtrPoints)
    L = L[L.date.isin(ok)]; parts = [U, L]
    for nm, key in NEW.items():
        t = TR[key]["real"]; t = t[(t.date >= S.START) & t.date.isin(ok)]
        parts.append(pd.DataFrame(dict(date=t.date.to_numpy(), mod=nm, tin=D.sm[t.fi.to_numpy().astype(int)], tout=D.sm[t.xi.to_numpy().astype(int)] + 1,
                                       d=t.d.to_numpy(), u=t.usd.to_numpy(), w=1.0)))
    A = pd.concat(parts, ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True)
    pickle.dump({"Ultra6": A}, open(os.path.join(HERE, "six_ultra6_trades.pkl"), "wb"))
    print(A["mod"].value_counts().to_dict(), len(A))
