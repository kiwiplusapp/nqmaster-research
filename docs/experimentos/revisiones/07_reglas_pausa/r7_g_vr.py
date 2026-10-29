"""Razon de varianzas a 63 dias del P&L por contrato base: historica vs nula (dias barajados) vs bloques de 21 dias barajados (lo que conserva el bootstrap)."""
import numpy as np
from r7_common import *
days, M, FU, PER, n, CONST, ARc, ARs, paths = load()
x = ARc["completo"]["x"]; rng = np.random.default_rng(1)
def vr(v, k=63):
    s = np.convolve(v, np.ones(k), "valid"); return s.var(ddof=1) / (k * v.var(ddof=1))
for per, ii in PER.items():
    v = x[ii]; h = vr(v)
    null = np.array([vr(rng.permutation(v)) for _ in range(500)])
    nb = len(v) // 21; blk = np.array([vr(np.concatenate([v[21*b:21*b+21] for b in rng.permutation(nb)])) for _ in range(500)])
    yrs = (days[ii] // 10000); dm = v - np.array([v[yrs == y].mean() for y in yrs])
    print(f"{per}: VR63 historica {h:.2f} | dias barajados p95 {np.percentile(null,95):.2f} (P>= hist {np.mean(null>=h):.3f}) | bloques 21 barajados med {np.median(blk):.2f} p95 {np.percentile(blk,95):.2f} | sin la media de cada anio {vr(dm):.2f}")
