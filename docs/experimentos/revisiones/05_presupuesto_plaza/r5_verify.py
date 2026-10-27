"""Revisor exp05: verificacion independiente (no escribe en el repo)."""
import os, sys, time, numpy as np
sys.path.insert(0, "/home/user/nqmaster-research/research/mine")
import prop_wf as P, objective as O, exp05_budget as E5
from numba import njit
H = O.H; MAXEV = O.MAXEV; L = H + 25; Q = 63
BUD = {"T1500": (1500, 600), "T2500": (2500, 900), "T4000": (4000, 1500), "T6000": (6000, 2500)}

def seat_mins(f, s0, end, starts):
    """f: flujo del asiento sin presupuesto. Devuelve minimos de: neto desde revision comun (todos los dias / dias de compra),
    revision propia del asiento, ventana movil <=63 dias, acumulado anual."""
    c = np.concatenate([[0.0], np.cumsum(f[s0:end])])   # c[t] = sum f[s0:s0+t]
    n = end - s0; d = np.arange(s0, end)                # dia de chequeo (antes de comprar en d): suma [q0, d)
    q0 = np.maximum((d // Q) * Q, s0); com = c[d - s0] - c[q0 - s0]
    q0o = s0 + ((d - s0) // Q) * Q; own = c[d - s0] - c[q0o - s0]
    # ventana movil: suma f[a:b], b-a <= 63, dentro de [s0,end]
    best = 0.0
    for b in range(1, n + 1):
        a0 = max(0, b - Q); m = c[b] - c[a0:b + 1].max()
        if m < best: best = m
    sp = starts.astype(int); comb = (c[sp - s0] - c[np.maximum((sp // Q) * Q, s0) - s0]).min() if len(sp) else 0.0
    return com.min(), comb, own.min(), best, c.min()

def boot_sets(seed, Lp, NB, days, PER):
    rng = np.random.default_rng(seed); S = {}
    for hc in P.HC:
        for per, ii in PER.items(): S[(hc, per)] = [P.boot_idx(ii[0], ii[-1] + 1, Lp, rng) for _ in range(NB)]
    return S

def main():
    t0 = time.time(); days, M, FU, PER = O.setup(); NB = 1000
    PS = boot_sets(4242, L, NB, days, PER)
    n = len(days); idx = np.arange(n, dtype=np.int64)
    out = {}
    for hc in P.HC:
        Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
        AL, AM = O.seat_args(FU, hc, E5.L150, Hm), O.seat_args(FU, hc, E5.MF, Hm)
        for per, ii in PER.items():
            for src, paths in (("boot", PS[(hc, per)]), ("contig", [idx[s0:s0 + L] for s0 in np.arange(ii[0], ii[-1] + 2 - L, 5)])):
                R = {"L": [], "M": []}
                for bi in paths:
                    for A, cnt, nm in ((AM, 3, "M"), (AL, 5, "L")):
                        for s in range(cnt):
                            f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((MAXEV, 5)); k = O.run_seat(M, A, bi, 5 * s, H, f, mm, ev)
                            R[nm].append(seat_mins(f, 5 * s, 5 * s + H, ev[:k, 0]) + (k,))
                for nm in ("L", "M"):
                    X = np.array(R[nm]); j = 0 if nm == "L" else 1
                    row = {"n": len(X), "min_com_cualquier_dia": X[:, 0].min(), "min_com_dia_compra": X[:, 1].min(), "min_rev_propia": X[:, 2].min(), "min_movil63": X[:, 3].min(), "min_anual": X[:, 4].min(),
                           "evals_anio_med": float(np.median(X[:, 5])), "evals_anio_max": X[:, 5].max()}
                    for c, b in BUD.items():
                        row[f"{c}_dispara_com"] = int((X[:, 1] < -b[j]).sum()); row[f"{c}_movil"] = int((X[:, 3] < -b[j]).sum()); row[f"{c}_propia"] = int((X[:, 2] < -b[j]).sum())
                    row["p01_movil63"] = float(np.percentile(X[:, 3], 1)); row["p01_com"] = float(np.percentile(X[:, 1], 1))
                    out[(hc, per, src, nm)] = row
                    print(f"{time.time()-t0:5.0f}s hc{hc} {per} {src:6s} {nm} n {row['n']:5d} min neto rev.comun(dia compra) {row['min_com_dia_compra']:8.0f} (cualq. dia {row['min_com_cualquier_dia']:8.0f}) rev.propia {row['min_rev_propia']:8.0f} movil63 {row['min_movil63']:8.0f} p01 movil {row['p01_movil63']:7.0f} anual {row['min_anual']:8.0f} | dispara com T1500/T2500/T4000/T6000 "
                          + "/".join(str(row[f'{c}_dispara_com']) for c in BUD) + " | movil " + "/".join(str(row[f'{c}_movil']) for c in BUD) + " | propia " + "/".join(str(row[f'{c}_propia']) for c in BUD), flush=True)

if __name__ == "__main__":
    main()
