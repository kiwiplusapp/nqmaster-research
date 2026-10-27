"""Revisor exp05: primer disparo del presupuesto predicho de forma independiente (trayectoria sin presupuesto, neto desde la revision
comun en cada dia de compra; anual: desde el inicio de la plaza) contra seat_flow_b plaza por plaza."""
import sys, numpy as np
sys.path.insert(0, "/home/user/nqmaster-research/research/mine")
import prop_wf as P, objective as O, exp05_budget as E5
H = O.H; L = H + 25; NB = 1000; MAXEV = O.MAXEV; Q = 63
days, M, FU, PER = O.setup(); rng = np.random.default_rng(4242); CC = ("T1500", "T2500", "T4000", "A4000")
for hc in P.HC:
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    AL, AM = O.seat_args(FU, hc, E5.L150, Hm), O.seat_args(FU, hc, E5.MF, Hm)
    for per, ii in PER.items():
        paths = [P.boot_idx(ii[0], ii[-1] + 1, L, rng) for _ in range(NB)]
        cnt = {c: [0, 0, 0] for c in CC}   # predichos, observados, inconsistencias
        for bi in paths:
            for A, n, j in ((AM, 3, 1), (AL, 5, 0)):
                for s in range(n):
                    s0 = 5 * s; f0 = np.zeros(L); m0 = np.zeros(L); e0 = np.zeros((MAXEV, 5)); k0 = O.run_seat(M, A, bi, s0, H, f0, m0, e0)
                    c0 = np.concatenate([[0.0], np.cumsum(f0)]); sp = e0[:k0, 0].astype(int)
                    for c in CC:
                        B = E5.CANDS[c][j]; q = E5.CANDS[c][2]
                        ref = np.maximum((sp // Q) * Q, s0) if q else np.full(len(sp), s0)
                        hit = np.nonzero(c0[sp] - c0[ref] < -B)[0]; pred = int(sp[hit[0]]) if len(hit) else -1
                        st = np.zeros(2); f1 = np.zeros(L); m1 = np.zeros(L); e1 = np.zeros((MAXEV, 5)); E5.run_b(M, A, bi, s0, H, f1, m1, e1, B, q, st)
                        obs = st[1] > 0; cnt[c][0] += pred >= 0; cnt[c][1] += obs
                        bad = (pred >= 0) != obs
                        if pred >= 0 and not bad: bad = not (np.array_equal(f0[:pred], f1[:pred]) and f1[pred] == 0.0 and f0[pred] < 0)
                        if pred < 0 and not bad: bad = not np.array_equal(f0, f1)
                        cnt[c][2] += bad
        print(f"hc{hc} {per}: " + " | ".join(f"{c} pred {v[0]} obs {v[1]} incons {v[2]}" for c, v in cnt.items()), flush=True)
