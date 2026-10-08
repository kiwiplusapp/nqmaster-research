"""news_cost.py follow-up: per-module cost of the MFFU T1 blackout (flatten at 08:28 / 13:58) vs skipping the module's trades on
T1 days altogether. -> news_cost2.csv"""
import sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, "."); sys.path.insert(0, "..")
from core import Data
from news_cost import adjust, T1_AM, MIN, ULTRA, WR70
if __name__ == "__main__":
    E = pickle.load(open("wrq_entries.pkl", "rb")); rows = []
    fn = lambda d: ([828] if d in T1_AM else []) + ([1358] if d in MIN else [])
    for name, splits in (("nq_1m.npz", (("IS", 20200101, 20240101), ("C24", 20240101, 20990101))), ("mnq_fut.npz", (("REAL", 20240101, 20990101),))):
        D = Data(name); T0 = E[name]; T0 = T0[~T0.fomc].reset_index(drop=True)
        for per, a, b in splits:
            T = T0[(T0.date >= a) & (T0.date < b)].reset_index(drop=True); u, hit = adjust(D, T, fn)
            t1 = T.date.isin(T1_AM | MIN).to_numpy()
            for mod, g in T.groupby("mod"):
                ix = g.index.to_numpy()
                rows.append(dict(per=per, mod=mod, n_hit=int(hit[ix].sum()), base=round(T.u0[ix].sum()), flatten=round(u[ix].sum()),
                                 skip_t1_days=round(T.u0[ix][~t1[ix]].sum()), t1_day_pnl=round(T.u0[ix][t1[ix]].sum())))
    R = pd.DataFrame(rows); R.to_csv("news_cost2.csv", index=False)
    P = R.pivot_table(index="mod", columns="per", values=["n_hit", "base", "flatten", "skip_t1_days"]).astype(int)
    pd.set_option("display.width", 250); print(P[[c for c in P.columns if c[0] in ("n_hit",)] + [c for c in P.columns if c[0] in ("base", "flatten", "skip_t1_days")]].to_string())
