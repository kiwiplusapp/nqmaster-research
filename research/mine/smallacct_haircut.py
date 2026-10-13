"""1-contract study, step 7: realistic expectations. Remove 35% of the average daily edge (and the +1 tick cost) from every day, then redo the
single-eval and serial-restart numbers. Edge = mean daily P&L of UltraR over the period of the start days.  -> smallacct_haircut.json"""
import os, sys, json, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from smallacct_eval import SETUPS, stats, run_starts
from smallacct_protocol import outcomes, protocol
from robust2_life import vectors, SP
if __name__ == "__main__":
    days, P = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb")); n = len(days)
    s1 = np.nonzero((days >= 20200301) & (days < 20231101))[0]; s2 = np.nonzero(days >= 20240101)[0]; s2 = s2[s2 < n - 50]
    low, close, fin = P[("UltraR", 0)]; c = P[("UltraR", 0, "cost")]
    mu1 = float(fin[s1].mean()); mu2 = float(fin[s2].mean()); print("mean daily P&L UltraR T1", round(mu1), "T2", round(mu2), flush=True)
    OUT = {}
    for name in ("Lucid Flex 25K", "Lucid Pro 25K", "Bulenox Opt2 25K", "FundedNext Rapid Pro 25K", "Lucid Flex 50K", "MFFU Rapid EOD 50K"):
        T, D, cons, mind, dll, fee = SETUPS[name]; G = 0.9 * cons * T if cons > 0 else 0.0; r = {}
        for hc in (0.0, 0.35, 0.60, 1.0):
            h = np.where(np.arange(n) < s2[0], hc * mu1, hc * mu2)          # per-day haircut of the period's own mean
            lo, cl = vectors(low - c[:, None] - h[:, None], close - c[:, None] - h[:, None], fin - c - h, G)
            if dll > 0:
                hit = lo <= -dll; cl = np.where(hit, -float(dll), cl); lo = np.where(hit, -float(dll), lo)
            EL = np.ascontiguousarray(np.array([lo, lo])); EC = np.ascontiguousarray(np.array([cl, cl]))
            res, dd = outcomes(EL, EC, -1e9, T, D, cons, mind, n)
            r[f"edge-{int(hc*100)}%"] = dict(W22=dict(T1=protocol(res, dd, s1, 22, 1, 0, fee), T2=protocol(res, dd, s2, 22, 1, 0, fee)),
                                           W33=dict(T1=protocol(res, dd, s1, 33, 1, 0, fee)[0], T2=protocol(res, dd, s2, 33, 1, 0, fee)[0]),
                                           single_p22=dict(T1=stats(*run_starts(EL, EC, -1e9, T, D, cons, mind, np.arange(n), s1[s1 < n - 120]))["p22"], T2=stats(*run_starts(EL, EC, -1e9, T, D, cons, mind, np.arange(n), s2[s2 < n - 120]))["p22"]))
        OUT[name] = r; print(name)
        for k, v in r.items(): print(f"   {k:10s} funded<=22d serial T1 {v['W22']['T1'][0]:5.1f} T2 {v['W22']['T2'][0]:5.1f} (evals {v['W22']['T2'][1]}, ${v['W22']['T2'][2]}) | <=33d T1 {v['W33']['T1']:5.1f} T2 {v['W33']['T2']:5.1f} | single p22 T1 {v['single_p22']['T1']} T2 {v['single_p22']['T2']}")
    json.dump(OUT, open(os.path.join(HERE, "smallacct_haircut.json"), "w"), indent=1)
