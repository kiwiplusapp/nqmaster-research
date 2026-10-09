"""wrq_pbo: probability of backtest overfitting (CSCV, S=16) for 'pick the best exit variant' per module, on the module's daily
P&L over CFD 2020-26 (IS + C24) and over REAL, using every exit variant tried in wrq_exits.py (58 per module) plus the fine
grid neighbours are not included (they are a subset of the same idea). Also pooled across modules (module x variant columns
padded to all days). -> wrq_pbo.csv"""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wrq_lib import pbo

if __name__ == "__main__":
    DL = pickle.load(open("wrq_exits_daily.pkl", "rb"))
    mods = sorted({k[0] for k in DL}); rows = []
    for m in mods:
        for lab, pers in (("CFD 2020-26", ("IS", "C24")), ("REAL 2024-26", ("REAL",))):
            cols = {}
            for (mm, vn, per), s in DL.items():
                if mm == m and per in pers: cols.setdefault(vn, []).append(s)
            M = pd.DataFrame({k: pd.concat(v) for k, v in cols.items()}).fillna(0.0).sort_index()
            r = pbo(M.to_numpy()); r.update(mod=m, sample=lab, days=len(M)); rows.append(r)
        print(m, flush=True)
    R = pd.DataFrame(rows); R.to_csv("wrq_pbo.csv", index=False)
    pd.set_option("display.width", 250); print(R.to_string())
