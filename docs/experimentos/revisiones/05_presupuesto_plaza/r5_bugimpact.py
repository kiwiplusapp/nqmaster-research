"""Revisor exp05: (1) donde difieren seat_flow_b y la referencia (s0 de la plaza, dia de la primera pausa, dia de reanudacion);
(2) impacto en las metricas del plan de T1500 / T2500 si la plaza en pausa reanuda en la revision comun (dia 63) y no en s0 + 63."""
import sys, json, numpy as np
sys.path.insert(0, "/home/user/nqmaster-research/research/mine"); sys.path.insert(0, "/tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad")
import prop_wf as P, objective as O, exp05_budget as E5, exp03_eval_size as E3
from r5_refimpl_lib import ref_seat
H = O.H; L = H + 25; NB = 1000; MAXEV = O.MAXEV
X = json.load(open("/home/user/nqmaster-research/research/mine/exp05_budget.json"))

def plan_ref(M, AL, AM, paths, c):
    bl, bm, q = E5.CANDS[c]; flows = np.zeros((len(paths), L)); mtms = np.zeros((len(paths), L)); tot = np.zeros(len(paths)); evs = []; nev = []; npa = 0
    for b, bi in enumerate(paths):
        ev_all = np.zeros((8 * MAXEV, 5)); kk = 0
        for A, cnt, bud in ((AM, 3, bm), (AL, 5, bl)):
            LO, CL, _ = M[A["mix"]]; FL, FC, fp = A["tiers"]
            for s in range(cnt):
                f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((MAXEV, 5))
                kq, npz = ref_seat(LO, CL, A["Hh"], A["ep"], A["fee"], FL, FC, fp, bi, 5 * s, 5 * s + H, f, mm, ev, A["act"], float(bud), bool(q), 63)
                flows[b] += f; mtms[b] += mm; tot[b] += f.sum() / 12.0; ev_all[kk:kk + kq] = ev[:kq]; kk += kq; npa += npz
        evs.append(ev_all); nev.append(kk)
    return flows, mtms, evs, nev, tot

days, M, FU, PER = O.setup(); rng = np.random.default_rng(4242); NET = {}; diag = {}
for hc in P.HC:
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    AL, AM = O.seat_args(FU, hc, E5.L150, Hm), O.seat_args(FU, hc, E5.MF, Hm)
    for per, ii in PER.items():
        paths = [P.boot_idx(ii[0], ii[-1] + 1, L, rng) for _ in range(NB)]
        # (1) diagnostico T1500
        if hc == 1.0:
            by_s = {}; first_q = 0; tot_d = 0
            for bi in paths[:200]:
                for A, cnt, j in ((AM, 3, 1), (AL, 5, 0)):
                    LO, CL, _ = M[A["mix"]]; FL, FC, fp = A["tiers"]; B = E5.CANDS["T1500"][j]
                    for s in range(cnt):
                        f0 = np.zeros(L); m0 = np.zeros(L); e0 = np.zeros((MAXEV, 5)); st = np.zeros(2); k0 = E5.run_b(M, A, bi, 5 * s, H, f0, m0, e0, B, 1, st)
                        f1 = np.zeros(L); m1 = np.zeros(L); e1 = np.zeros((MAXEV, 5)); k1, _ = ref_seat(LO, CL, A["Hh"], A["ep"], A["fee"], FL, FC, fp, bi, 5 * s, 5 * s + H, f1, m1, e1, A["act"], float(B), True, 63)
                        if not np.array_equal(f0, f1):
                            by_s[s] = by_s.get(s, 0) + 1; tot_d += 1
                            # primera compra distinta: en seat_flow_b, en la referencia
                            s0s = e0[:k0, 0].astype(int); s1s = e1[:k1, 0].astype(int); m = min(len(s0s), len(s1s)); dd = np.nonzero(s0s[:m] != s1s[:m])[0]
                            if len(dd):
                                a, b2 = s0s[dd[0]], s1s[dd[0]]
                                if b2 == 63 and a == 5 * s + 63: first_q += 1
            print(f"hc{hc} {per} T1500 (200 caminos): plazas distintas {tot_d}, por s {by_s}; primera diferencia = reanuda en 63 (ref) vs s0+63 (seat_flow_b): {first_q}", flush=True)
        for c in ("T1500", "T2500", "T4000"):
            flows, mtms, evs, nev, tot = plan_ref(M, AL, AM, paths, c); r = E3.plan_metrics(flows, mtms, evs, nev, tot); NET[(c, hc, per)] = tot
            j = X["plan"][f"plan {c} | hc{hc} | {per}"]
            print(f"  hc{hc} {per} {c}: ref med {r['med_mes']:.0f} p10 {r['p10_mes']:.0f} Pneg {r['P_anio_neg']:.1f} neg60 {r['neg60']:.2f} evals/a {r['evals_anio']:.1f} cumple {sum(r['cumple'].values())} "
                  f"| JSON med {j['med_mes']:.0f} p10 {j['p10_mes']:.0f} Pneg {j['P_anio_neg']:.1f} neg60 {j['neg60']:.2f} evals/a {j['evals_anio']:.1f} cumple {sum(j['cumple'].values())}", flush=True)
for c in ("T1500", "T2500"):
    for hc in P.HC:
        for per in PER:
            g = E3.paired(NET[(c, hc, per)], NET[("T4000", hc, per)]); j = X["pareado"][f"plan {c} vs T4000 | hc{hc} | {per}"]
            print(f"pareado {c} hc{hc} {per}: ref P_loss5 {g['P_loss5']:.3f} med {g['med']:.0f} | JSON P_loss5 {j['P_loss5']:.3f} med {j['med']:.0f}")
