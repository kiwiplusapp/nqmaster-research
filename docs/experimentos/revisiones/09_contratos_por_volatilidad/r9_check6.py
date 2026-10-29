"""r9_check6: prueba independiente del camino V1 (contratos que varian por dia): seat_flow_v con kv contra objective.seat_flow (nucleo de la base)
alimentado con matrices pre-escaladas por dia: LO'[t] = kv[t] * (LO[t] - h[t]), CL' igual, Hh = 0, eval de 1 contrato; fondeada con FL1 x kf."""
import os, sys, numpy as np
MINE = "/home/user/nqmaster-research/research/mine"; os.chdir(MINE); sys.path.insert(0, MINE)
import prop_wf as P, objective as O, exp09_volsize as X
days, M, FU, PER = O.setup(); atr = X.atr_days(days); ke, kf = X.kvecs(days, atr, "V1"); H = O.H; MAXEV = O.MAXEV
rng = np.random.default_rng(99); bad = 0; tot = 0; maxd = 0.0
for hc in (0.0, 0.35):
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}; A = X.l150_args(FU, hc, Hm, kf)
    LO, CL, _ = M[(0, 4)]; h = Hm[(0, 4)]
    LOs = np.ascontiguousarray(ke[:, None] * (LO - h[:, None])); CLs = np.ascontiguousarray(ke[:, None] * (CL - h[:, None])); z = np.zeros(len(days))
    ep1 = P.ep_of(P.FIRMS["LucidFlex150K"], (0, 1, 1, 0, 0, 0, 0)); FL, FC, fp = A["tiers"]
    for per, ii in PER.items():
        for _ in range(200):
            bi = P.boot_idx(ii[0], ii[-1] + 1, H, rng)
            f0 = np.zeros(H); m0 = np.zeros(H); e0 = np.zeros((MAXEV, 5)); k0 = O.seat_flow(LOs, CLs, z, ep1, 215.0, FL, FC, fp, bi, 0, H, f0, m0, e0, 0.0)
            f1 = np.zeros(H); m1 = np.zeros(H); e1 = np.zeros((MAXEV, 5)); k1 = X.run_l150(M, A, bi, 0, H, f1, m1, e1, ke)
            tot += 1; same = k0 == k1 and np.array_equal(e0[:k0], e1[:k1]); d = max(np.abs(f0 - f1).max(), np.abs(m0 - m1).max()); maxd = max(maxd, d)
            bad += (not same) or d > 1e-6
print(f"V1 (kv variable): {tot} asientos, {bad} diferencias (evals al bit; flujo/mtm max |diff| {maxd:.2e}) contra objective.seat_flow con matrices pre-escaladas")
