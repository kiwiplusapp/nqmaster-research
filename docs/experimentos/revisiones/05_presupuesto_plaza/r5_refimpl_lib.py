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

