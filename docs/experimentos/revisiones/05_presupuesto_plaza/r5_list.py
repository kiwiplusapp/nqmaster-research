"""Revisor exp05: plan T4000 trimestral vs sin presupuesto con fee de lista de Lucid ($285), mismos caminos (rng 4242)."""
import sys, numpy as np
sys.path.insert(0, "/home/user/nqmaster-research/research/mine")
import prop_wf as P, objective as O, exp05_budget as E5, exp03_eval_size as E3
H = O.H; L = H + 25; NB = 1000
days, M, FU, PER = O.setup(); rng = np.random.default_rng(4242)
for hc in P.HC:
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    AL, AM = O.seat_args(FU, hc, E5.L150, Hm), O.seat_args(FU, hc, E5.MF, Hm); AL = dict(AL, fee=285.0)
    for per, ii in PER.items():
        paths = [P.boot_idx(ii[0], ii[-1] + 1, L, rng) for _ in range(NB)]
        R = {}
        for c in ("sin", "T4000"):
            flows, mtms, evs, nev, tot, st = E5.plan_cell(M, AL, AM, paths, c); r = E3.plan_metrics(flows, mtms, evs, nev, tot); R[c] = (r, st, tot)
        a, b = R["sin"], R["T4000"]; g = E3.paired(b[2], a[2])
        print(f"lista hc{hc} {per}: sin med {a[0]['med_mes']:.0f} p10 {a[0]['p10_mes']:.0f} Pneg {a[0]['P_anio_neg']:.1f} cumple {sum(a[0]['cumple'].values())} | T4000 med {b[0]['med_mes']:.0f} p10 {b[0]['p10_mes']:.0f} Pneg {b[0]['P_anio_neg']:.1f} cumple {sum(b[0]['cumple'].values())} pausa d/a {b[1][0]:.1f} | caminos distintos {(a[2] != b[2]).sum()}", flush=True)
