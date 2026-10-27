"""Revisor exp05: implementacion de referencia del presupuesto (neto acumulado incremental, reinicio al cruzar un dia de revision
multiplo de 63) comparada plaza por plaza (flujo, mtm, registro de evals) con seat_flow_b, todas las celdas bootstrap del plan y contiguo."""
import sys, numpy as np
sys.path.insert(0, "/home/user/nqmaster-research/research/mine")
import prop_wf as P, objective as O, exp05_budget as E5
from numba import njit
race = P.race; fund_flow = O.fund_flow; H = O.H; L = H + 25; NB = 1000; MAXEV = O.MAXEV

@njit(cache=True)
def ref_seat(LO, CL, Hh, ep, fee, FL, FC, fp, idx, s0, end, flow, mtm, ev, act, B, quarterly, qlen):
    i = s0; k = 0; rec = np.zeros(5); acc = 0.0; last = s0; npaus = 0
    while i < end:
        for d in range(last, i):
            if quarterly and d % qlen == 0: acc = 0.0
            acc += flow[d]
        last = i
        if quarterly and i % qlen == 0 and i > s0: acc = 0.0      # revision justo hoy (antes de comprar)
        if acc < -B:
            npaus += 1
            i = min((i // qlen + 1) * qlen, end) if quarterly else end
            continue
        flow[i] -= fee; mtm[i] -= fee
        r, j = race(LO, CL, Hh, idx, i, end, ep)
        jj = j if j < end else end - 1
        if k < ev.shape[0]:
            ev[k, 0] = i; ev[k, 1] = r; ev[k, 2] = jj if r != 0 else end - 1; ev[k, 3] = -1; ev[k, 4] = 0
        if r != 1:
            k += 1; i = j + 1; continue
        if act > 0.0: flow[jj] -= act; mtm[jj] -= act
        fund_flow(FL, FC, fp, idx, j + 1, end, rec, flow, mtm)
        if k < ev.shape[0]:
            ev[k, 3] = j + 1 + rec[2] if rec[2] >= 0 else -1; ev[k, 4] = rec[3]
        k += 1; i = int(rec[4]) + 1
    return k, npaus

days, M, FU, PER = O.setup(); rng = np.random.default_rng(4242); n = len(days); idx = np.arange(n, dtype=np.int64)
for hc in P.HC:
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    AL, AM = O.seat_args(FU, hc, E5.L150, Hm), O.seat_args(FU, hc, E5.MF, Hm)
    for per, ii in PER.items():
        boot = [P.boot_idx(ii[0], ii[-1] + 1, L, rng) for _ in range(NB)]; cont = [idx[s0:s0 + L] for s0 in np.arange(ii[0], ii[-1] + 2 - L, 5)]
        out = []
        for c in ("T1500", "T2500", "T4000", "T6000", "A4000"):
            seats = 0; bad = 0; pa = 0; pb = 0
            for paths in (boot, cont):
                for bi in paths:
                    for A, cnt, j in ((AM, 3, 1), (AL, 5, 0)):
                        LO, CL, _ = M[A["mix"]]; FL, FC, fp = A["tiers"]; B = E5.CANDS[c][j]; q = E5.CANDS[c][2]
                        for s in range(cnt):
                            f0 = np.zeros(L); m0 = np.zeros(L); e0 = np.zeros((MAXEV, 5)); st = np.zeros(2); k0 = E5.run_b(M, A, bi, 5 * s, H, f0, m0, e0, B, q, st)
                            f1 = np.zeros(L); m1 = np.zeros(L); e1 = np.zeros((MAXEV, 5))
                            k1, np1 = ref_seat(LO, CL, A["Hh"], A["ep"], A["fee"], FL, FC, fp, bi, 5 * s, 5 * s + H, f1, m1, e1, A["act"], float(B), bool(q), 63)
                            seats += 1; pa += st[1]; pb += np1
                            if k0 != k1 or not (np.array_equal(f0, f1) and np.array_equal(m0, m1) and np.array_equal(e0[:k0], e1[:k1])) or st[1] != np1: bad += 1
            out.append(f"{c} {seats} plazas, pausas {int(pa)}/{int(pb)}, difs {bad}")
        print(f"hc{hc} {per}: " + " | ".join(out), flush=True)
