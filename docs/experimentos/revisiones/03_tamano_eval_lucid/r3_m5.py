import sys, os, numpy as np
sys.path.insert(0, "/home/user/nqmaster-research/research/mine"); os.chdir("/home/user/nqmaster-research/research/mine")
import prop_wf as P, objective as O
days, M, FU, PER = O.setup(); H = O.H; L = H + 25; F = P.FIRMS["LucidFlex150K"]; NB = 1000
rng = np.random.default_rng(4242)
for hc in (0.0, 0.35):
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    for per, ii in PER.items():
        paths = [P.boot_idx(ii[0], ii[-1] + 1, L, rng) for _ in range(NB)]
        if per != "T1": continue
        Amf = O.seat_args(FU, hc, "MFFU 1x8", Hm); mf = []
        for bi in paths:
            for s in range(3):
                f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((O.MAXEV, 5)); q = O.run_seat(M, Amf, bi, 5 * s, H, f, mm, ev); mf.append(ev[:q].copy())
        mf = np.concatenate(mf); mok = mf[mf[:, 1] == 1]; dm = mok[:, 2] - mok[:, 0] + 1
        for k in (4, 5, 6):
            A = dict(O.seat_args(FU, hc, "L150 6c/3c", Hm)); A["ep"] = P.ep_of(F, (0, k, k, 0, 0, 0, 0)); lu = []
            for bi in paths:
                for s in range(5):
                    f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((O.MAXEV, 5)); q = O.run_seat(M, A, bi, 5 * s, H, f, mm, ev); lu.append(ev[:q].copy())
            lu = np.concatenate(lu); ok = lu[lu[:, 1] == 1]; dl = ok[:, 2] - ok[:, 0] + 1; pool = np.concatenate([dl, dm])
            print(f"hc{hc} {per} k{k}: mediana dias L150 sola {np.median(dl):.0f} (n aprob {len(dl)}, P(<=10) {np.mean(dl<=10):.3f}) | MFFU sola {np.median(dm):.0f} (n {len(dm)}) | plan (pool) {np.median(pool):.0f}, P(<=10) en pool {np.mean(pool<=10):.3f}")
