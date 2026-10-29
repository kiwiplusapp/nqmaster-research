"""Pregunta 5: media y desvio diario del P&L por contrato base, dias para separar -35 % de cero, efecto de la autocorrelacion (razon de varianzas)
historica y en los caminos bootstrap (bloques de 21 dias). Tambien la media del neto del plan sin edge (R0) y condiciones D1 por regla."""
import json, numpy as np
from math import erf, sqrt
from r7_common import *

days, M, FU, PER, n, CONST, ARc, ARs, paths = load()
Phi = lambda z: 0.5 * (1 + erf(z / sqrt(2)))
x = ARc["completo"]["x"]
for per, ii in PER.items():
    v = x[ii]; mu = v.mean(); sd = v.std(ddof=1)
    n2 = (2 * sd / (0.65 * mu)) ** 2
    vr = {}
    for k in (21, 60, 63, 126):
        s = np.array([v[a:a + k].sum() for a in range(0, len(v) - k + 1)])       # sumas solapadas
        vr[k] = s.var(ddof=1) / (k * sd ** 2)
    # caminos bootstrap (los de la base, completo): varianza de la suma de 60 y 126 dias
    pb = paths[(0.0, per)]
    s60 = np.array([x[bi[:60]].sum() for bi in pb]); s126 = np.array([x[bi[:126]].sum() for bi in pb])
    print(f"{per}: dias {len(v)} media {mu:6.1f} desvio {sd:6.1f} | n (dif 0,65*mu = 2 EE) {n2:5.0f} | n (cada hipotesis a 2 EE del umbral medio) {4*n2:5.0f}")
    print(f"     razon de varianzas historica (sumas solapadas) {', '.join(f'{k}d {vr[k]:.2f}' for k in vr)} -> n ajustado ~{n2*vr[63]:.0f} (con VR63)")
    print(f"     bootstrap: var(suma60)/(60 sd^2) {s60.var()/(60*sd**2):.2f}  var(suma126)/(126 sd^2) {s126.var()/(126*sd**2):.2f}")
    for hc in (0.35, 1.0):
        m = (1 - hc) * mu
        print(f"     hc {hc}: P(suma 60 d < 0) normal iid {Phi(-m*60/(sd*sqrt(60))):.3f}  | con VR60 {Phi(-m*60/(sd*sqrt(60*vr[60]))):.3f}")
# media y mediana del neto sin edge (R0): convexidad de los retiros
J = json.load(open(os.path.join(MINE, "exp07_pause_rules.json")))
for per in PER:
    net0 = np.array([X.plan_run(ARc["cero"], bi, L)[4] for bi in paths[(1.0, per)]])
    print(f"cero {per}: neto R0 media {net0.mean():7.0f} mediana {np.median(net0):7.0f} P(<0) {(net0<0).mean():.3f} p90 {np.percentile(net0,90):7.0f}")
# condiciones D1 (M1 y M2; M4/M5 son de la eval de Lucid y no dependen de la pausa) por regla en completo y -35 %
print("\nD1 por regla (med > 2.759, p10 >= 1.600, neg60 < 10 %):")
for sc in ("completo", "-35%"):
    for per in PER:
        row = []
        for rule in ("R0", "R1", "R4", "R14"):
            r = J["escenarios"][f"{sc} | {per} | {rule}"]
            row.append(f"{rule} {'+' if r['med_mes']>2759 else '-'}med {'+' if r['p10_mes']>=1600 else '-'}p10({r['p10_mes']:.0f}) {'+' if r['neg60']<10 else '-'}neg60({r['neg60']:.1f})")
        print(f"  {sc:8s} {per}: " + " | ".join(row))
