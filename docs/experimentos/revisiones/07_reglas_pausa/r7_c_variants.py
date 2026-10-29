"""Lecturas alternativas de las reglas y techo de H2:
R1u  = chequeo unico en el dia 60; R1m8 = R1 con la mezcla (0, 8) (MFFU) como contrato base;
R4ci = trimestres calendario con desfase u ~ U{0..62} por camino, trimestre parcial inicial contado; R4ce = idem, parcial ignorado;
ORAC = oraculo que no opera nunca (pausa en el dia 0) -> techo de H2.  Tambien la media de la ganancia pareada."""
import json, numpy as np
from r7_common import *

days, M, FU, PER, n, CONST, ARc, ARs, paths = load()
J = json.load(open(os.path.join(MINE, "exp07_pause_rules.json")))
x8 = {sc: M[(0, 8)][2] - P.haircut(days, M[(0, 8)][2], hc) for sc, hc in CONST.items()}
x8s = np.concatenate([x8["completo"], x8["cero"]])
urng = np.random.default_rng(777)

def p_cal(xs, u, include):
    bounds = ([0, u] if (u > 0 and include) else [u]) + [u + 63 * k for k in range(1, 6)]
    bounds = [b for b in bounds if b <= L]
    q = [(xs[a:b].sum(), b) for a, b in zip(bounds[:-1], bounds[1:])]
    for k in range(1, len(q)):
        if q[k - 1][0] < 0 and q[k][0] < 0: return q[k][1]
    return L

def pause(rule, xs, x8p, u):
    if rule == "R1": return X.pause_day(xs, "R1")
    if rule == "R4": return X.pause_day(xs, "R4")
    if rule == "R1u": return 60 if xs[:60].sum() < 0 else L
    if rule == "R1m8": return X.pause_day(x8p, "R1")
    if rule == "R4ci": return p_cal(xs, u, True)
    if rule == "R4ce": return p_cal(xs, u, False)
    if rule == "ORAC": return 0

RULES = ("R1", "R1u", "R1m8", "R4", "R4ci", "R4ce", "ORAC")
OUT = {}
for sc, AR, hc, S in [(sc, ARc[sc], CONST[sc], None) for sc in CONST] + [("muere63", ARs, 0.0, 63), ("muere126", ARs, 0.0, 126)]:
    for per in PER:
        pp = paths[(hc, per)] if S is None else [sw(bi, n, S) for bi in paths[(hc, per)]]
        X8 = x8[sc] if S is None else x8s
        U = urng.integers(0, 63, len(pp))
        net0 = np.array([X.plan_run(AR, bi, L)[4] for bi in pp])
        for rule in RULES:
            if rule == "ORAC" and sc != "cero": continue
            net = net0.copy(); pd = np.full(len(pp), L)
            for b, bi in enumerate(pp):
                p = pause(rule, AR["x"][bi], X8[bi], int(U[b])); pd[b] = p
                if p < L: net[b] = X.plan_run(AR, bi, p)[4]
            g = E3.paired(net, net0); gm = float((net - net0).mean())
            OUT[(sc, per, rule)] = g
            ref = J["pareado"].get(f"{sc} | {per} | {rule} vs R0")
            chk = "" if ref is None else f" [JSON Pg {ref['P_gain']:.3f} Pl5 {ref['P_loss5']:.3f}]"
            print(f"{sc:8s} {per} {rule:5s} paus {100*(pd<L).mean():5.1f}% dia med {np.median(pd[pd<L]) if (pd<L).any() else float('nan'):5.0f} | med {np.median(net):7.0f} p10 {np.percentile(net,10):7.0f} Pneg {100*(net<0).mean():5.1f} | "
                  f"ganancia med {g['med']:6.0f} media {gm:6.0f} Pg {g['P_gain']:.3f} Pl5 {g['P_loss5']:.3f}{chk}", flush=True)

print("\nDecision por regla (H1: Pl5 <= 0,20 en completo y -35 %, T1 y T2; H2: med > 0 y Pg >= 0,80 en cero T1 y T2)")
for rule in RULES:
    if rule == "ORAC":
        h2 = all(OUT[("cero", per, rule)]["med"] > 0 and OUT[("cero", per, rule)]["P_gain"] >= 0.80 for per in PER)
        print(f"ORAC: H2 {h2}  Pg {[round(OUT[('cero', per, rule)]['P_gain'], 3) for per in PER]}"); continue
    h1 = all(OUT[(sc, per, rule)]["P_loss5"] <= 0.20 for sc in ("completo", "-35%") for per in PER)
    h2 = all(OUT[("cero", per, rule)]["med"] > 0 and OUT[("cero", per, rule)]["P_gain"] >= 0.80 for per in PER)
    print(f"{rule:5s} H1 {h1} H2 {h2} -> {'queda' if h1 and h2 else ('marcada' if h1 else 'se retira')}  Pl5 {[round(OUT[(sc, per, rule)]['P_loss5'], 3) for sc in ('completo', '-35%') for per in PER]}")
