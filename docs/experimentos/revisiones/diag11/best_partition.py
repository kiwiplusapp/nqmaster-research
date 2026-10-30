"""Revision diag 11: la particion MAS favorable posible elegida directamente por la metrica post-hoc en T1 (cota optimista, in-sample)."""
import os, sys, numpy as np
MINE = "/home/user/nqmaster-research/research/mine"; sys.path.insert(0, MINE); os.chdir(MINE)
import diag_partition as P
D = P.daily(); t1 = D.index < 20230101; mods = list(D.columns); m1 = D[t1].mean(); tot = m1.sum()
X1, X2 = D[t1], D[~t1]
i1 = P.boot_idx(len(X1), np.random.default_rng(P.SEED)); i2 = P.boot_idx(len(X2), np.random.default_rng(P.SEED))
def busts(x, idx, thr): return P.renewal(np.ascontiguousarray(x[idx]), thr)[0].mean()
f1 = X1.sum(axis=1).to_numpy(); f2 = X2.sum(axis=1).to_numpy()
base1 = {t: 2 * busts(f1, i1, t) for t in P.THR}; base2 = {t: 2 * busts(f2, i2, t) for t in P.THR}
rng = np.random.default_rng(7); cands = []; seen = 0
for _ in range(6000):
    msk = rng.random(len(mods)) < 0.5; A = [m for m, k in zip(mods, msk) if k]; B = [m for m, k in zip(mods, msk) if not k]
    if not A or not B or abs(m1[A].sum() - tot / 2) > 0.1 * tot / 2: continue
    seen += 1
    a = 2 * X1[A].sum(axis=1).to_numpy(); b = 2 * X1[B].sum(axis=1).to_numpy()
    r = max((busts(a, i1, t) + busts(b, i1, t)) / base1[t] for t in P.THR)
    cands.append((r, A, B))
cands.sort(key=lambda z: z[0])
print("particiones evaluadas (medias T1 a +-10%%): %d; base T1 por par %s; T2 %s" % (seen, {k: round(v, 2) for k, v in base1.items()}, {k: round(v, 2) for k, v in base2.items()}))
print("peor cociente T1 (max sobre umbrales) de la mejor particion: %.2f; p10 %.2f; mediana %.2f" % (cands[0][0], cands[len(cands) // 10][0], cands[len(cands) // 2][0]))
for r, A, B in cands[:3]:
    a = 2 * X2[A].sum(axis=1).to_numpy(); b = 2 * X2[B].sum(axis=1).to_numpy()
    r2 = {t: round((busts(a, i2, t) + busts(b, i2, t)) / base2[t], 2) for t in P.THR}
    print("  T1 max cociente %.2f | T2 cocientes %s | A=%s" % (r, r2, A))
