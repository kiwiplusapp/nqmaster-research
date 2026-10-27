"""Revisor exp05: dias en pausa por anio (8 plazas) de T1500 / T2500 con reanudacion en la revision comun vs JSON."""
import sys, json, numpy as np
sys.path.insert(0, "/home/user/nqmaster-research/research/mine")
import prop_wf as P, objective as O, exp05_budget as E5
from numba import njit
race = P.race; fund_flow = O.fund_flow; H = O.H; L = H + 25; NB = 1000; MAXEV = O.MAXEV
X = json.load(open("/home/user/nqmaster-research/research/mine/exp05_budget.json"))

@njit(cache=True)
def seat_fix(LO, CL, Hh, ep, fee, FL, FC, fp, idx, s0, end, flow, mtm, ev, act, budget, quarterly, qlen, stats):
    """seat_flow_b con una sola linea cambiada: la pausa termina en la revision comun siguiente ((i // qlen + 1) * qlen)."""
    i = s0; k = 0; rec = np.zeros(5)
    while i < end:
        if budget < 1e11:
            q0 = (i // qlen) * qlen if quarterly else 0
            if q0 < s0: q0 = s0
            net = 0.0
            for d in range(q0, i): net += flow[d]
            if net < -budget:
                nxt = (i // qlen + 1) * qlen if quarterly else end
                if nxt > end: nxt = end
                stats[0] += nxt - i; stats[1] += 1; i = nxt; continue
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
    return k

days, M, FU, PER = O.setup(); rng = np.random.default_rng(4242)
for hc in P.HC:
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    AL, AM = O.seat_args(FU, hc, E5.L150, Hm), O.seat_args(FU, hc, E5.MF, Hm)
    for per, ii in PER.items():
        paths = [P.boot_idx(ii[0], ii[-1] + 1, L, rng) for _ in range(NB)]; row = []
        for c in ("T1500", "T2500"):
            bl, bm, q = E5.CANDS[c]; st = np.zeros(2)
            for bi in paths:
                for A, cnt, bud in ((AM, 3, bm), (AL, 5, bl)):
                    LO, CL, _ = M[A["mix"]]; FL, FC, fp = A["tiers"]
                    for s in range(cnt):
                        f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((MAXEV, 5))
                        seat_fix(LO, CL, A["Hh"], A["ep"], A["fee"], FL, FC, fp, bi, 5 * s, 5 * s + H, f, mm, ev, A["act"], float(bud), bool(q), 63, st)
            j = X["plan"][f"plan {c} | hc{hc} | {per}"]
            row.append(f"{c} dias pausa/anio corregido {st[0]/NB:.1f} (JSON {j['dias_pausa_plan_anio']:.1f}), pausas {st[1]/NB:.2f} (JSON {j['pausas_plan_anio']:.2f})")
        print(f"hc{hc} {per}: " + " | ".join(row), flush=True)
