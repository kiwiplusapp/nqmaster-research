"""1-contract study, step 5: does the START DAY matter? (a priori rules, not fitted): (a) daily ATR at the start <= 1.15 x its 60-session median (AtrStartMax
in NQMaster), (b) strategy P&L of the previous 10 trading days <= 0 ('start after a drawdown', the 2026-10-05 finding), (c) both.
P(funded within 22 / 33 trading days) with serial restarts, Lucid Flex 25K / 50K and Bulenox 25K, T1 vs T2.  -> smallacct_timing.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from smallacct_eval import SETUPS, prep
from smallacct_protocol import outcomes, protocol
from robust2_life import SP
from wrq_lib import getD
import robust2_build as RB

if __name__ == "__main__":
    days, P = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb")); n = len(days)
    D = getD(RB.NAME); atr = pd.Series(D.atr, index=D.daydate).groupby(level=0).last(); atr = atr[atr.index > 0]
    med = atr.rolling(60, min_periods=30).median(); ratio = (atr / med).reindex(days).to_numpy()
    fin = P[("UltraR", 0)][2]; prev10 = pd.Series(fin).rolling(10).sum().shift(1).to_numpy()
    s1 = np.nonzero((days >= 20200501) & (days < 20231101))[0]; s2 = np.nonzero(days >= 20240101)[0]; s2 = s2[s2 < n - 50]
    OUT = {}
    for name in ("Lucid Flex 25K", "Lucid Flex 50K", "Bulenox Opt2 25K", "MFFU Rapid EOD 50K"):
        T, D_, cons, mind, dll, fee = SETUPS[name]; G = 0.9 * cons * T if cons > 0 else 0.0
        hi = prep(P, ("UltraR", 0), G, dll, False)
        EL = np.ascontiguousarray(np.array([hi[0], hi[0]])); EC = np.ascontiguousarray(np.array([hi[1], hi[1]]))
        res, dd = outcomes(EL, EC, -1e9, T, D_, cons, mind, n)
        r = {}
        gates = {"all days": lambda s: True, "ATR<=1.15": lambda s: ratio[s] <= 1.15, "prev10<=0": lambda s: prev10[s] <= 0,
                 "ATR<=1.15 & prev10<=0": lambda s: ratio[s] <= 1.15 and prev10[s] <= 0, "ATR>1.15": lambda s: ratio[s] > 1.15, "prev10>0": lambda s: prev10[s] > 0}
        for gname, gf in gates.items():
            row = {}
            for W in (22, 33):
                a = [s for s in s1 if gf(s)]; b = [s for s in s2 if gf(s)]
                row[f"W{W}"] = dict(T1=protocol(res, dd, a, W, 1, 0, fee) + (len(a),), T2=protocol(res, dd, b, W, 1, 0, fee) + (len(b),))
            r[gname] = row
        OUT[name] = r
        print(name)
        for g, row in r.items(): print(f"   {g:24s} W22 T1 {row['W22']['T1']} T2 {row['W22']['T2']} | W33 T1 {row['W33']['T1'][0]} T2 {row['W33']['T2'][0]}")
    json.dump(OUT, open(os.path.join(HERE, "smallacct_timing.json"), "w"), indent=1)
