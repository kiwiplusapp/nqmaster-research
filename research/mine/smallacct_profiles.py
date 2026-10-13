"""1-contract study, step 6: which PROFILE for the 25K / 50K eval? (always-on, no gating) UltraR vs WR70R vs Estable vs risk-capped UltraR, serial restarts,
P(funded within 22 / 33 trading days), T1 vs T2.  -> smallacct_profiles.json"""
import os, sys, json, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from smallacct_eval import SETUPS, prep, stats, run_starts
from smallacct_protocol import outcomes, protocol
from robust2_life import SP
if __name__ == "__main__":
    days, P = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb")); n = len(days)
    s1 = np.nonzero((days >= 20200301) & (days < 20231101))[0]; s2 = np.nonzero(days >= 20240101)[0]; s2 = s2[s2 < n - 50]
    OUT = {}
    for name in ("Lucid Flex 25K", "Bulenox Opt2 25K", "Lucid Flex 50K"):
        T, D, cons, mind, dll, fee = SETUPS[name]; G = 0.9 * cons * T if cons > 0 else 0.0; r = {}
        for key in (("UltraR", 0), ("UltraR", 300), ("UltraR", 200), ("UltraR", 150), ("WR70R", 0), ("WR70R", 300), ("Estable", 0)):
            for t1 in (False, True):
                hi = prep(P, key, G, dll, t1); EL = np.ascontiguousarray(np.array([hi[0], hi[0]])); EC = np.ascontiguousarray(np.array([hi[1], hi[1]]))
                res, dd = outcomes(EL, EC, -1e9, T, D, cons, mind, n)
                lab = f"{key[0]}{key[1] or ''}" + (" +1tick" if t1 else "")
                r[lab] = dict(W22=dict(T1=protocol(res, dd, s1, 22, 1, 0, fee), T2=protocol(res, dd, s2, 22, 1, 0, fee)), W33=dict(T1=protocol(res, dd, s1, 33, 1, 0, fee)[0], T2=protocol(res, dd, s2, 33, 1, 0, fee)[0]),
                               single=dict(T1=stats(*run_starts(EL, EC, -1e9, T, D, cons, mind, np.arange(n), s1[s1 < n - 120])), T2=stats(*run_starts(EL, EC, -1e9, T, D, cons, mind, np.arange(n), s2[s2 < n - 120]))))
        OUT[name] = r; print(name)
        for lab, v in r.items(): print(f"   {lab:18s} funded<=22d serial T1 {v['W22']['T1'][0]:5.1f} T2 {v['W22']['T2'][0]:5.1f} | <=33d T1 {v['W33']['T1']:5.1f} T2 {v['W33']['T2']:5.1f} | single eval p22 T1 {v['single']['T1']['p22']} T2 {v['single']['T2']['p22']} ever T2 {v['single']['T2']['pass_ever']}")
    json.dump(OUT, open(os.path.join(HERE, "smallacct_profiles.json"), "w"), indent=1)
