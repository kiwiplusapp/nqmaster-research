# Round 5 integration (2026-10-21), copied from the session scratchpad (port_integ.py). Run from research/mine. Outputs: integ_port.json
import os
"""Integrator 2026-10-21: correlated plan distribution (objections 6 and 12). Same bootstrap path for every seat, 5-day stagger, 252 days each.
Plan A = 5 x Lucid Flex 150K 6c/3c + 3 x MFFU Rapid EOD 50K 1c x8 (preset defaults). Lucid modes: 'rot' = each seat independent, rebuys after 5 payouts;
'grad' = when any Lucid seat makes its 5th payout (moves to Live) ALL Lucid sim accounts close (unwithdrawn balances lost, no refund) and every
Lucid seat (incl. the graduated one, Live income counted as 0) starts a new eval the next day (art 16558826 reading; conservative)."""
import sys, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prop_wf as P
from numba import njit
race = P.race; fund = P.fund
NB = int(sys.argv[1]) if len(sys.argv) > 1 else 1000

@njit(cache=False)
def seat3(LO, CL, Hh, ep, fee, FL, FC, fp, idx, s0, end, out, stop_np):
    """as prop_wf.seat; stops at the first account that reaches stop_np payouts; out 0 net cash, 1 grad day (-1)"""
    i = s0; cash = 0.0; fees = 0.0; rec = np.zeros(5); out[1] = -1.0
    while i < end:
        fees += fee
        r, j = race(LO, CL, Hh, idx, i, end, ep)
        if r != 1:
            i = j + 1; continue
        fund(FL, FC, fp, idx, j + 1, end, rec)
        cash += rec[1]; i = int(rec[4]) + 1
        if stop_np > 0 and rec[2] < 0 and rec[3] >= stop_np:
            out[1] = rec[4]; break
    out[0] = cash - fees

P.FIRMS["LucidFlex150K"] = dict(T=9000.0, D=4500.0, cons=0.5, mind=1, G=4050.0, fee=285.0, kmax=6, fund="flex", Q=250.0, cap1=3000.0, npmax=5)
days, M = P.build_mix(); FU = P.Fund(days, M)
i1 = np.nonzero(days < P.T1_END)[0]; i2 = np.nonzero((days >= P.T1_END) & (days < P.T2_END))[0]
LUC = ("LucidFlex150K", (0, 6, 6, 0, 0, 0, 0), (0, 4), (3, 1687, 0, 6000, 0), 5)
MF = ("MFFU50K", (0, 1, 1, 0, 0, 0, 0), (0, 8), (1, 2000, 0, 4100, 0), 3)
rng = np.random.default_rng(4242); R = {}
for hc in P.HC:
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    for per, ii in (("T1", i1), ("T2", i2)):
        paths = [P.boot_idx(ii[0], ii[-1] + 1, 252 + 25, rng) for _ in range(NB)]
        for fee_s, lf in (("coupon", 215.0), ("list", 285.0)):
            for mode in ("rot", "grad"):
                tot = np.zeros(NB); luc = np.zeros(NB); mff = np.zeros(NB); ngrad = np.zeros(NB); o = np.zeros(2)
                firm, pe, mix, pf, cnt = LUC; F = P.FIRMS[firm]; epL = P.ep_of(F, pe); FLl, FCl, fpl = FU.tiers(hc, firm, pf); mixL = mix
                firm2, pe2, mix2, pf2, cnt2 = MF; F2 = P.FIRMS[firm2]; epM = P.ep_of(F2, pe2); FLm, FCm, fpm = FU.tiers(hc, firm2, pf2)
                for b, bi in enumerate(paths):
                    for s in range(cnt2):
                        seat3(M[mix2][0], M[mix2][1], Hm[mix2], epM, 157.0, FLm, FCm, fpm, bi, 5 * s, 5 * s + 252, o, 0); mff[b] += o[0] / 12
                    st = np.array([5 * j for j in range(cnt)]); en = st + 252; cur = st.copy()
                    if mode == "rot":
                        for j in range(cnt):
                            seat3(M[mixL][0], M[mixL][1], Hm[mixL], epL, lf, FLl, FCl, fpl, bi, cur[j], en[j], o, 0); luc[b] += o[0] / 12
                    else:
                        while True:
                            g = 10 ** 9
                            for j in range(cnt):
                                if cur[j] < en[j]:
                                    seat3(M[mixL][0], M[mixL][1], Hm[mixL], epL, lf, FLl, FCl, fpl, bi, cur[j], en[j], o, 5)
                                    if o[1] >= 0 and o[1] < g: g = int(o[1])
                            if g == 10 ** 9:
                                for j in range(cnt):
                                    if cur[j] < en[j]: seat3(M[mixL][0], M[mixL][1], Hm[mixL], epL, lf, FLl, FCl, fpl, bi, cur[j], en[j], o, 0); luc[b] += o[0] / 12
                                break
                            ngrad[b] += 1
                            for j in range(cnt):     # everything up to g is kept as realised; open balances are lost
                                if cur[j] < en[j] and cur[j] <= g:
                                    seat3(M[mixL][0], M[mixL][1], Hm[mixL], epL, lf, FLl, FCl, fpl, bi, cur[j], min(en[j], g + 1), o, 0); luc[b] += o[0] / 12
                                    cur[j] = g + 1
                    tot[b] = luc[b] + mff[b]
                k = f"hc{hc} | {per} | {fee_s} | {mode}"
                R[k] = dict(med=round(float(np.median(tot))), p10=round(float(np.percentile(tot, 10))), p25=round(float(np.percentile(tot, 25))),
                            p90=round(float(np.percentile(tot, 90))), Pneg=round(100 * float((tot < 0).mean()), 1),
                            luc_med=round(float(np.median(luc))), mffu_med=round(float(np.median(mff))), grads_per_yr=round(float(ngrad.mean()), 2))
                print(k, R[k], flush=True)
json.dump(R, open("integ_port.json", "w"), indent=1)
