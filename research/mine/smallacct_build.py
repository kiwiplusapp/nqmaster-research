"""1-contract pass-probability study, step 1 (2026-10-13): minute paths for the current profiles (UltraR = Ultra after the 2026-10-12 overhaul,
WR70R, Estable, each with per-trade $ risk caps) on real Databento NQ 2020-26. Saves the full per-day low/close/final paths so the eval
simulator can apply any daily profit stop G (consistency rules) and daily loss limit (DLL) per firm. -> scratchpad smallacct_paths.pkl"""
import os, sys, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import robust2_build as RB
from robust2_life import full_paths, SP

if __name__ == "__main__":
    E = RB.setup(); days = pickle.load(open(os.path.join(SP, "robust2_paths.pkl"), "rb"))[0]
    C16 = pickle.load(open(os.path.join(HERE, "cand16_trades.pkl"), "rb")); R2 = pickle.load(open(os.path.join(HERE, "robust2_trades.pkl"), "rb"))
    srcs = {"UltraR": C16["UltraR"][0], "WR70R": C16["WR70R"][0], "Estable": R2["Estable"]}
    out = {}
    for nm, X in srcs.items():
        X = X[X.date.isin(days)]
        X = RB.attach(X, E) if "risk" not in X.columns else X
        for cap in (0, 150, 200, 300):
            XX = X if cap == 0 else X[X.risk <= cap]
            out[(nm, cap)] = full_paths(XX, days)
            c = (XX.w * 1.0).groupby(XX.date).sum().reindex(days, fill_value=0.0).to_numpy()
            out[(nm, cap, "cost")] = c                      # contracts traded per day (extra tick per side stress = -2 ticks x $0.5 x c ... see eval)
            print(nm, cap, len(XX), flush=True)
    pickle.dump((days, out), open(os.path.join(SP, "smallacct_paths.pkl"), "wb"))
