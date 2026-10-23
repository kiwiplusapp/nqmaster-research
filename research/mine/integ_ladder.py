# Round 5 integration (2026-10-21), copied from the session scratchpad (ladder_integ.py). Run from research/mine. Outputs: integ_ladder.json
import os
"""Integrator 2026-10-21 (objection 8): MFFU funded ladder vs keep-4,100, same NQ-only prop_wf harness, paired 1000 paths, eval 1c x8."""
import sys, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prop_wf as P
days, M = P.build_mix(); FU = P.Fund(days, M)
i1 = np.nonzero(days < P.T1_END)[0]; i2 = np.nonzero((days >= P.T1_END) & (days < P.T2_END))[0]
rng = np.random.default_rng(31337); NB = 1000; F = P.FIRMS["MFFU50K"]; ep = P.ep_of(F, (0, 1, 1, 0, 0, 0, 0)); R = {}
for hc in P.HC:
    Hm = P.haircut(days, M[(0, 8)][2], hc)
    for per, ii in (("T1", i1), ("T2", i2)):
        paths = [P.boot_idx(ii[0], ii[-1] + 1, 252, rng) for _ in range(NB)]; X = {}
        for nm, pf in (("keep4100", (1, 2000, 0, 4100, 0)), ("ladder", ("lad", 2000, 0, 11100, 0)), ("ladder+stop1500", ("lad", 2000, 0, 11100, 1500))):
            FL, FC, fp = FU.tiers(hc, "MFFU50K", pf); o = np.zeros(7); x = np.zeros((NB, 7))
            for b, bi in enumerate(paths):
                P.seat(M[(0, 8)][0], M[(0, 8)][1], Hm, ep, 157.0, FL, FC, fp, bi, 0, 252, o, 0.0); x[b] = o
            X[nm] = x
        for nm, x in X.items():
            v = x[:, 0] / 12; g = v - X["keep4100"][:, 0] / 12; f = x[:, 5]
            R[f"{nm} | hc{hc} | {per}"] = dict(med=round(float(np.median(v))), p10=round(float(np.percentile(v, 10))), Pneg=round(100 * float((v < 0).mean()), 1),
                busts=round(float(x[:, 3].mean()), 2), pay62=round(100 * float(((f >= 0) & (f < 62)).mean()), 1),
                gain_med=round(float(np.median(g))), gain_ci90=[round(float(np.percentile(g, 5))), round(float(np.percentile(g, 95)))], P_gain=round(float((g > 0).mean()), 3))
            print(nm, hc, per, R[f"{nm} | hc{hc} | {per}"], flush=True)
json.dump(R, open("integ_ladder.json", "w"), indent=1)
