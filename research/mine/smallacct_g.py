"""1-contract study, step 9: the daily profit stop that enforces the eval consistency rule. For each firm, G in a grid; a pass only counts when the
best day <= cons x total profit (checked in ev_m), so too high a G fails the rule and too low a G slows the eval.  -> smallacct_g.json"""
import os, sys, json, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from smallacct_eval import SETUPS, prep, stats, run_starts
from smallacct_protocol import outcomes, protocol
from robust2_life import SP
if __name__ == "__main__":
    days, P = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb")); n = len(days)
    s1 = np.nonzero((days >= 20200301) & (days < 20231101))[0]; s2 = np.nonzero(days >= 20240101)[0]; s2 = s2[s2 < n - 50]
    GR = {"Lucid Flex 25K": (250, 350, 450, 560, 700, 900, 0), "Lucid Flex 50K": (500, 700, 1000, 1350, 1700, 0), "MFFU Rapid EOD 50K": (400, 600, 800, 1000, 1400, 0),
          "MFFU Rapid EOD 25K*": (200, 300, 400, 600, 0), "Tradeify Select 25K": (200, 300, 450, 600, 0)}
    OUT = {}
    for name, gs in GR.items():
        T, D, cons, mind, dll, fee = SETUPS[name]; r = {}
        for g in gs:
            hi = prep(P, ("UltraR", 0), float(g), dll, True); EL = np.ascontiguousarray(np.array([hi[0], hi[0]])); EC = np.ascontiguousarray(np.array([hi[1], hi[1]]))
            res, dd = outcomes(EL, EC, -1e9, T, D, cons, mind, n)
            r[g] = dict(W22=dict(T1=protocol(res, dd, s1, 22, 1, 0, fee)[0], T2=protocol(res, dd, s2, 22, 1, 0, fee)[0]), W33=dict(T1=protocol(res, dd, s1, 33, 1, 0, fee)[0], T2=protocol(res, dd, s2, 33, 1, 0, fee)[0]))
        OUT[name] = r; print(name, "(cons", cons, ", 0 = no stop):", {g: (v["W22"]["T1"], v["W22"]["T2"]) for g, v in r.items()})
    json.dump(OUT, open(os.path.join(HERE, "smallacct_g.json"), "w"), indent=1)
