"""(1) R0 por camino contra una corrida independiente con objective.run_seat (orden PLAN de objective); (2) escenarios de cambio contra
re-indexado independiente por camino; (3) pause_day contra implementacion independiente con bucles; (4) truncado de la pausa."""
import time, numpy as np
from r7_common import *

days, M, FU, PER, n, CONST, ARc, ARs, paths = load(); t0 = time.time()

# ---------- (1) R0 = base por camino (independiente: objective.run_seat con seat_args propios, orden L150 primero)
for sc, hc in CONST.items():
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    for per in PER:
        mx = 0.0; tots = []
        for bi in paths[(hc, per)]:
            tot = 0.0
            for name, cnt in O.PLAN:
                A = O.seat_args(FU, hc, name, Hm)
                for s in range(cnt):
                    f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((O.MAXEV, 5)); O.run_seat(M, A, bi, 5 * s, H, f, mm, ev); tot += f.sum() / 12.0
            t1 = X.plan_run(ARc[sc], bi, L)[4]; mx = max(mx, abs(tot - t1)); tots.append(tot)
        tots = np.array(tots)
        print(f"(1) R0 {sc:8s} {per}: max|dif| por camino {mx:.2e}  med {np.median(tots):.1f} p10 {np.percentile(tots,10):.1f}", flush=True)

# ---------- (2) cambio de regimen: re-indexado independiente
# construyo para cada camino arreglos propios de L dias: dia d del camino -> dia bi[d] con recorte 0 si d < S y recorte 1.0 si d >= S
H0 = {m: P.haircut(days, M[m][2], 0.0) for m in X.MIXES}; H1 = {m: P.haircut(days, M[m][2], 1.0) for m in X.MIXES}
def indep_switch(bi, S, p=L):
    w = np.arange(L) >= S; tot = 0.0; idx = np.arange(L, dtype=np.int64)
    for name, cnt in X.PLAN:
        firm, pe, mix, pf, fc, fl = O.SEATS[name]
        LO, CL, FIN = M[mix]; LOp = np.ascontiguousarray(LO[bi]); CLp = np.ascontiguousarray(CL[bi])
        Hh = np.where(w, H1[mix][bi], H0[mix][bi])
        T0 = FU.tiers(0.0, firm, pf); T1 = FU.tiers(1.0, firm, pf)
        FL = np.ascontiguousarray(np.where(w[None, :], T1[0][:, bi], T0[0][:, bi])); FC = np.ascontiguousarray(np.where(w[None, :], T1[1][:, bi], T0[1][:, bi]))
        ep = P.ep_of(P.FIRMS[firm], pe); act = float(P.FIRMS[firm].get("act", 0.0))
        for s in range(cnt):
            s0 = 5 * s; end = min(s0 + H, p)
            f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((O.MAXEV, 5))
            if end > s0: O.seat_flow(LOp, CLp, Hh, ep, fc, FL, FC, T0[2], idx, s0, end, f, mm, ev, act)
            tot += f.sum() / 12.0
    xs = np.where(w, M[(0, 4)][2][bi] - H1[(0, 4)][bi], M[(0, 4)][2][bi] - H0[(0, 4)][bi])
    return tot, xs

for S in (0, 63, 126):
    for per in PER:
        mx = 0.0; mxx = 0.0; mxp = 0.0
        for bi in paths[(0.0, per)][:300]:
            b2 = sw(bi, n, S); t_exp = X.plan_run(ARs, b2, L)[4]; t_ind, xs = indep_switch(bi, S)
            mx = max(mx, abs(t_exp - t_ind)); mxx = max(mxx, float(np.abs(ARs["x"][b2] - xs).max()))
            for rule in ("R1", "R4"):                                       # con pausa tambien
                p = X.pause_day(ARs["x"][b2], rule)
                if p < L: mxp = max(mxp, abs(X.plan_run(ARs, b2, p)[4] - indep_switch(bi, S, p)[0]))
        print(f"(2) cambio S={S:3d} {per}: max|dif| neto R0 {mx:.2e} | x {mxx:.2e} | neto con pausa R1/R4 {mxp:.2e}", flush=True)
# S = 0 sobre la copia 1 == escenario cero con los mismos indices
mx = 0.0
for bi in paths[(1.0, "T2")][:300]:
    mx = max(mx, abs(X.plan_run(ARs, bi + n, L)[4] - X.plan_run(ARc["cero"], bi, L)[4]))
print(f"(2) copia 1 completa == 'cero': max|dif| {mx:.2e}")

# ---------- (3) pause_day contra implementacion independiente (bucles, solo dias previos)
def p_r1(xs):
    acc = 0.0
    for t in range(L):
        if t >= 60 and acc < 0: return t        # acc = suma de dias 0..t-1
        acc += xs[t]
    return L
def p_r4(xs):
    prev = None; acc = 0.0
    for t in range(L):
        acc += xs[t]
        if t % 63 == 62:                          # cierra el trimestre (t+1) // 63 - 1
            if prev is not None and prev < 0 and acc < 0: return t + 1
            prev = acc; acc = 0.0
    return L
bad = 0; cnt = 0
for key, pl in paths.items():
    for S in (None, 63, 126):
        if S is not None and key[0] != 0.0: continue
        AR = ARc[{0.0: "completo", 0.35: "-35%", 1.0: "cero"}[key[0]]] if S is None else ARs
        for bi in pl:
            b2 = bi if S is None else sw(bi, n, S); xs = AR["x"][b2]
            a1, a4, a14 = X.pause_day(xs, "R1"), X.pause_day(xs, "R4"), X.pause_day(xs, "R14")
            e1, e4 = p_r1(xs), p_r4(xs); cnt += 1
            if (a1, a4, a14) != (e1, e4, min(e1, e4)): bad += 1
            # sin lookahead: cambiar todo lo que pasa desde el dia p no cambia p
            if a14 < L:
                ys = xs.copy(); ys[a14:] = 1e6
                if X.pause_day(ys, "R14") != a14: bad += 1
print(f"(3) pause_day vs independiente + perturbacion desde p: {cnt} caminos, {bad} diferencias")

# ---------- (4) truncado: flujo con pausa = flujo R0 en dias < p (salvo nada) y 0 desde p; ninguna eval/fondeada empieza en >= p
bad = 0; cnt = 0; dmax = 0.0
for sc in ("completo", "-35%", "cero"):
    hc = CONST[sc]
    for per in PER:
        for bi in paths[(hc, per)]:
            p = X.pause_day(ARc[sc]["x"][bi], "R14")
            if p >= L: continue
            f0 = X.plan_run(ARc[sc], bi, L)[0]; f1, m1, ev, k, _ = X.plan_run(ARc[sc], bi, p); cnt += 1
            dmax = max(dmax, float(np.abs(f0[:p] - f1[:p]).max()))
            if np.abs(f1[p:]).max() > 0 or np.abs(m1[p:]).max() > 0 or (k and ev[:k, 0].max() >= p): bad += 1
print(f"(4) truncado: {cnt} caminos pausados; max|flujo pausa - flujo R0| en dias < p = {dmax:.2e}; {bad} con flujo/mtm/eval desde p")
print(f"{time.time()-t0:.0f}s")
