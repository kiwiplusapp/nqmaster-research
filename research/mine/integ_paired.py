# Round 5 integration (2026-10-21), copied from the session scratchpad (paired_integ.py). Run from research/mine. Outputs: integ_paired.json (via integ_summ.py; the raw pickle goes to research/tmp/integ_paired.pkl)
import os
"""Integrator re-check 2026-10-21 (answers red-team objections 1,2,4,5,6,7,9). NQ-only prop_wf harness, paired bootstrap
(same 252-day block paths for every config), NB paths per (edge, period), fees in two homogeneous scenarios (all coupon / all list).
PRE-REGISTERED RULE (written before running):
  Lucid seat: incumbent = Lucid Flex 150K 6c/3c (runbook row since 10-19). A challenger replaces it only if, in BOTH fee scenarios and BOTH
  periods, its paired median gain in $/month at -35% edge is > 0 with P(gain) >= 0.80 AND its P(negative year) at -35% is not more than
  3 pts worse. Otherwise: no change. Same rule decides Flex 50K vs Pro 50K (reported as 'tie' if neither passes vs the other).
  MFFU eval: incumbent fix1x8; challengers fix2 / fix3 must pass the same rule AND not lose more than $100/month more at zero edge.
Variant 'end': the seat ENDS after npmax payouts (no rotation, no live income) -> how much income depends on rotation."""
import sys, json, numpy as np, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prop_wf as P
from numba import njit
race = P.race; fund = P.fund
NB = int(sys.argv[1]) if len(sys.argv) > 1 else 1000

@njit(cache=False)
def seat2(LO, CL, Hh, ep, fee, FL, FC, fp, idx, s0, end, out, act, stop_np):
    i = s0; cash = 0.0; fees = 0.0; nev = 0; npass = 0; nb = 0; npay = 0; first = -1.0; rec = np.zeros(5)
    while i < end:
        fees += fee; nev += 1
        r, j = race(LO, CL, Hh, idx, i, end, ep)
        if r != 1:
            i = j + 1; continue
        npass += 1; fees += act
        fund(FL, FC, fp, idx, j + 1, end, rec)
        if first < 0 and rec[0] >= 0: first = j + 1 + rec[0] - s0
        cash += rec[1]; npay += int(rec[3]); nb += rec[2] >= 0; i = int(rec[4]) + 1
        if stop_np > 0 and rec[2] < 0 and rec[3] >= stop_np: break
    out[0] = cash - fees; out[1] = nev; out[2] = npass; out[3] = nb; out[4] = npay; out[5] = first

P.FIRMS["LucidFlex150K"] = dict(T=9000.0, D=4500.0, cons=0.5, mind=1, G=4050.0, fee=285.0, kmax=6, fund="flex", Q=250.0, cap1=3000.0, npmax=5)
days, M = P.build_mix(); FU = P.Fund(days, M)
i1 = np.nonzero(days < P.T1_END)[0]; i2 = np.nonzero((days >= P.T1_END) & (days < P.T2_END))[0]
# name: firm, eval (pt,kA,kB,C,dL,goal,L), mix, funded (k,c,G,X,L), fee coupon, fee list
CFG = {
 "L150 6c/3c":      ("LucidFlex150K", (0, 6, 6, 0, 0, 0, 0), (0, 4), (3, 1687, 0, 6000, 0), 215.0, 285.0),
 "Flex50 2c/2c":    ("LucidFlex50K", (0, 2, 2, 0, 0, 0, 0), (0, 4), (2, 1000, 0, 4000, 0), 105.2, 146.0),
 "Flex50 2c/1c":    ("LucidFlex50K", (0, 2, 2, 0, 0, 0, 0), (0, 4), (1, 1000, 0, 4000, 0), 105.2, 146.0),
 "Pro50 4c/1c":     ("LucidPro50K", (0, 4, 4, 0, 0, 0, 0), (0, 4), (1, 1000, 1000, 2000, 0), 115.4, 192.0),
 "Pro50 4c/2c":     ("LucidPro50K", (0, 4, 4, 0, 0, 0, 0), (0, 4), (2, 1000, 1000, 2000, 0), 115.4, 192.0),
 "MFFU 1x8":        ("MFFU50K", (0, 1, 1, 0, 0, 0, 0), (0, 8), (1, 2000, 0, 4100, 0), 157.0, 157.0),
 "MFFU fix2":       ("MFFU50K", (0, 2, 2, 0, 0, 0, 0), (0, 4), (1, 2000, 0, 4100, 0), 157.0, 157.0),
 "MFFU fix3":       ("MFFU50K", (0, 3, 3, 0, 0, 0, 0), (0, 4), (1, 2000, 0, 4100, 0), 157.0, 157.0),
}
rng = np.random.default_rng(20261021); out = {}; t0 = time.time()
for hc in P.HC:
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    for per, ii in (("T1", i1), ("T2", i2)):
        paths = [P.boot_idx(ii[0], ii[-1] + 1, 252, rng) for _ in range(NB)]
        for nm, (firm, pe, mix, pf, fc, fl) in CFG.items():
            F = P.FIRMS[firm]; ep = P.ep_of(F, pe); FL, FC, fp = FU.tiers(hc, firm, pf); o = np.zeros(7)
            for fee_s, fee in (("coupon", fc), ("list", fl)):
                for var, snp in (("rot", 0), ("end", F["npmax"])):
                    if var == "end" and (F["npmax"] == 0 or fee_s == "list"): continue
                    x = np.zeros((NB, 7))
                    for b, bi in enumerate(paths):
                        seat2(M[mix][0], M[mix][1], Hm[mix], ep, fee, FL, FC, fp, bi, 0, 252, o, F.get("act", 0.0), snp); x[b] = o
                    out[(nm, fee_s, var, hc, per)] = x
        print(hc, per, round(time.time() - t0), flush=True)
import pickle; pickle.dump(out, open("../tmp/integ_paired.pkl", "wb"))
