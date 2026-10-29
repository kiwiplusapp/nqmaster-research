"""Historia contigua: fechas de arranque de los planes pausados por R1 (completo, T2) para la afirmacion "2023 T3"; R4 con trimestres
calendario reales (parcial inicial contado / ignorado) y R1 de chequeo unico, en completo y -35 %."""
import numpy as np
from r7_common import *

days, M, FU, PER, n, CONST, ARc, ARs, paths = load()
idx = np.arange(n, dtype=np.int64)
qid = np.array([(int(d) // 10000) * 4 + ((int(d) // 100) % 100 - 1) // 3 for d in days])

def p_calreal(xs, q, include):
    # q: id de trimestre calendario por dia del camino
    cuts = [0] + [t for t in range(1, L) if q[t] != q[t - 1]] + [L]
    segs = list(zip(cuts[:-1], cuts[1:]))
    if not include and cuts[1] > 0 and q[0] == q[cuts[1] - 1] and cuts[1] < 63: segs = segs[1:]   # parcial inicial ignorado
    segs = [(a, b) for a, b in segs if b - a >= 40 or (include and a == 0)]                        # ultimo trimestre incompleto fuera
    sums = [(xs[a:b].sum(), b) for a, b in segs]
    for k in range(1, len(sums)):
        if sums[k - 1][0] < 0 and sums[k][0] < 0: return sums[k][1]
    return L

for sc in ("completo", "-35%"):
    AR = ARc[sc]
    for per, ii in PER.items():
        starts = np.arange(ii[0], ii[-1] + 2 - L, 5); res = {}
        for rule in ("R1", "R1u", "R4", "R4cal_inc", "R4cal_exc"):
            net = []; pz = []
            for s0 in starts:
                bi = idx[s0:s0 + L]; xs = AR["x"][bi]; q = qid[bi]
                p = (X.pause_day(xs, "R1") if rule == "R1" else (60 if xs[:60].sum() < 0 else L) if rule == "R1u" else X.pause_day(xs, "R4") if rule == "R4"
                     else p_calreal(xs, q, rule.endswith("inc")))
                net.append(X.plan_run(AR, bi, p)[4]); pz.append(p)
            net = np.array(net); pz = np.array(pz); res[rule] = (net, pz)
            print(f"CONTIG {sc:8s} {per} {rule:9s} n {len(starts)} paus {100*(pz<L).mean():5.1f}% med {np.median(net):7.0f} p10 {np.percentile(net,10):7.0f} Pneg {100*(net<0).mean():5.1f}", flush=True)
        if sc == "completo" and per == "T2":
            for rule in ("R1", "R4"):
                pz = res[rule][1]; st = [int(days[s]) for s, p in zip(starts, pz) if p < L]
                print(f"  arranques pausados {rule} completo T2: {st}")
