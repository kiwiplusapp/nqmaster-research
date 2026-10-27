"""Revisor exp05: (a) autotest del script; (b) T4000 trimestral con fee de lista de Lucid ($285): cuantas plazas lo alcanzarian;
(c) lectura alternativa 'acumula sin reinicio hasta disparar, pausa hasta la revision comun siguiente, despues referencia nueva'."""
import os, sys, json, time, numpy as np
sys.path.insert(0, "/home/user/nqmaster-research/research/mine")
import prop_wf as P, objective as O, exp05_budget as E5, exp03_eval_size as E3
from numba import njit
race = P.race; fund_flow = O.fund_flow; H = O.H; MAXEV = O.MAXEV; L = H + 25; NB = 1000; Q = 63

@njit(cache=True)
def seat_flow_c(LO, CL, Hh, ep, fee, FL, FC, fp, idx, s0, end, flow, mtm, ev, act, budget, qlen, stats):
    i = s0; k = 0; rec = np.zeros(5); ref = s0
    while i < end:
        net = 0.0
        for d in range(ref, i): net += flow[d]
        if net < -budget:
            nxt = (i // qlen + 1) * qlen
            if nxt > end: nxt = end
            stats[0] += nxt - i; stats[1] += 1; i = nxt; ref = nxt; continue
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

def plan_c(M, AL, AM, paths, bl, bm):
    flows = np.zeros((len(paths), L)); mtms = np.zeros((len(paths), L)); tot = np.zeros(len(paths)); evs = []; nev = []; st = np.zeros(2)
    for b, bi in enumerate(paths):
        ev_all = np.zeros((8 * MAXEV, 5)); kk = 0
        for A, cnt, bud in ((AM, 3, bm), (AL, 5, bl)):
            LO, CL, _ = M[A["mix"]]; FL, FC, fp = A["tiers"]
            for s in range(cnt):
                f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((MAXEV, 5))
                kq = seat_flow_c(LO, CL, A["Hh"], A["ep"], A["fee"], FL, FC, fp, bi, 5 * s, 5 * s + H, f, mm, ev, A["act"], float(bud), Q, st)
                flows[b] += f; mtms[b] += mm; tot[b] += f.sum() / 12.0; ev_all[kk:kk + kq] = ev[:kq]; kk += kq
        evs.append(ev_all); nev.append(kk)
    return flows, mtms, evs, nev, tot, st / len(paths)

def main():
    print("(a)", "diferencias:", E5.selftest(150), flush=True)
    t0 = time.time(); days, M, FU, PER = O.setup(); rng = np.random.default_rng(4242); X = json.load(open("/home/user/nqmaster-research/research/mine/exp05_budget.json"))
    for hc in P.HC:
        Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
        AL, AM = O.seat_args(FU, hc, E5.L150, Hm), O.seat_args(FU, hc, E5.MF, Hm)
        for per, ii in PER.items():
            paths = [P.boot_idx(ii[0], ii[-1] + 1, L, rng) for _ in range(NB)]
            # (b) lista: L150 sin presupuesto con fee 285, neto desde la revision comun en cada compra
            trig = 0; mn = 0.0
            for bi in paths:
                for s in range(5):
                    f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((MAXEV, 5)); k = O.run_seat(M, AL, bi, 5 * s, H, f, mm, ev, 285.0)
                    c = np.concatenate([[0.0], np.cumsum(f)]); sp = ev[:k, 0].astype(int); q0 = np.maximum((sp // Q) * Q, 5 * s)
                    v = (c[sp] - c[q0]).min() if k else 0.0; mn = min(mn, v); trig += v < -4000
            # (c) lectura alternativa, presupuesto de la regla 6
            flows, mtms, evs, nev, tot, st = plan_c(M, AL, AM, paths, 4000.0, 1500.0); r = E3.plan_metrics(flows, mtms, evs, nev, tot)
            b = X["plan"][f"plan T4000 | hc{hc} | {per}"]
            print(f"hc{hc} {per}: (b) fee lista 285: L150 plazas-camino que llegarian a -4.000 en el trimestre: {trig}/5000 (min {mn:.0f}) | "
                  f"(c) reinicio solo tras pausa: med {r['med_mes']:.0f} p10 {r['p10_mes']:.0f} Pneg {r['P_anio_neg']:.1f} neg60 {r['neg60']:.1f} [=0 {r['neg60_cero']:.1f}] evals/a {r['evals_anio']:.1f} evperd {r['evals_perdidas_mes']:.2f} pausa d/a {st[0]:.0f} cumple {sum(r['cumple'].values())} "
                  f"| T4000 trimestral: med {b['med_mes']:.0f} p10 {b['p10_mes']:.0f} Pneg {b['P_anio_neg']:.1f} cumple {sum(b['cumple'].values())}", flush=True)

if __name__ == "__main__":
    main()
