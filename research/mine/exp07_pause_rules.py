"""exp07_pause_rules.py (2026-10-29, experimento 07 / frente 5C): reglas de pausa 1 y 4 del runbook dentro de la simulacion de campana.
Escenarios: completo / -35 % / cero (recorte constante, caminos de la base) y muere63 / muere126 (edge completo hasta ese dia del camino, cero despues;
arreglos de dias duplicados: indice t = copia con edge completo, n + t = copia sin edge). El dia de pausa depende solo del P&L del sistema por contrato
base (mezcla (0, 4) menos el recorte); cada plaza corre objective.seat_flow con fin = min(fin propio, dia de pausa).
Plan pre-registrado: docs/PLAN_2026-10-29_exp07.md. Run (desde research/mine): python3 exp07_pause_rules.py selftest | python3 exp07_pause_rules.py [NB]"""
import os, sys, json, time, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import prop_wf as P, objective as O, exp03_eval_size as E3
H = O.H; L = H + 25; MAXEV = O.MAXEV; MIXES = ((0, 4), (0, 8), (300, 4)); RULES = ("R0", "R1", "R4", "R14")
PLAN = (("MFFU 1x8", 3), ("L150 6c/3c", 5))


def arrays(days, M, FU, hc):
    """recorte constante: arreglos originales"""
    Hm = {m: P.haircut(days, M[m][2], hc) for m in MIXES}
    A = {name: O.seat_args(FU, hc, name, Hm) for name, _ in PLAN}
    return dict(M=M, A=A, x=M[(0, 4)][2] - Hm[(0, 4)])


def arrays_switch(days, M, FU):
    """copia 0 = edge completo (hc 0), copia 1 = edge cero (hc 1.0); indices n + t para la copia 1"""
    n = len(days); H0 = {m: P.haircut(days, M[m][2], 0.0) for m in MIXES}; H1 = {m: P.haircut(days, M[m][2], 1.0) for m in MIXES}
    M2 = {m: (np.ascontiguousarray(np.vstack([M[m][0], M[m][0]])), np.ascontiguousarray(np.vstack([M[m][1], M[m][1]])), np.concatenate([M[m][2], M[m][2]])) for m in MIXES}
    A = {}
    for name, _ in PLAN:
        a0 = O.seat_args(FU, 0.0, name, H0); a1 = O.seat_args(FU, 1.0, name, H1); mix = a0["mix"]
        FL = np.ascontiguousarray(np.hstack([a0["tiers"][0], a1["tiers"][0]])); FC = np.ascontiguousarray(np.hstack([a0["tiers"][1], a1["tiers"][1]]))
        A[name] = dict(a0, tiers=(FL, FC, a0["tiers"][2]), Hh=np.concatenate([H0[mix], H1[mix]]))
    return dict(M=M2, A=A, x=np.concatenate([M[(0, 4)][2] - H0[(0, 4)], M[(0, 4)][2] - H1[(0, 4)]]), n=n)


def pause_day(xs, rule):
    """xs: P&L del sistema por contrato base por dia del camino (0..L-1). Devuelve el dia del camino desde el que se pausa (L = nunca)."""
    if rule == "R0": return L
    p = L
    if rule in ("R1", "R14"):
        c = np.concatenate([[0.0], np.cumsum(xs)])                  # c[t] = acumulado de los dias 0..t-1 (solo dias previos)
        hit = np.nonzero(c[60:L] < 0)[0]
        if len(hit): p = min(p, 60 + int(hit[0]))
    if rule in ("R4", "R14"):
        q = [xs[63 * k:63 * k + 63].sum() for k in range(L // 63)]
        for k in range(1, len(q)):
            if q[k - 1] < 0 and q[k] < 0: p = min(p, 63 * (k + 1)); break
    return p


def plan_run(AR, idx, p):
    """plan completo sobre un camino (idx = dias absolutos en los arreglos de AR) con pausa en el dia p del camino"""
    f_all = np.zeros(L); m_all = np.zeros(L); tot = 0.0; ev_all = np.zeros((8 * MAXEV, 5)); kk = 0; bal_pause = 0.0
    for name, cnt in PLAN:
        A = AR["A"][name]; LO, CL, _ = AR["M"][A["mix"]]; FL, FC, fp = A["tiers"]
        for s in range(cnt):
            s0 = 5 * s; end = min(s0 + H, p)
            f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((MAXEV, 5))
            k = O.seat_flow(LO, CL, A["Hh"], A["ep"], A["fee"], FL, FC, fp, idx, s0, end, f, mm, ev, A["act"]) if end > s0 else 0
            f_all += f; m_all += mm; tot += f.sum() / 12.0; ev_all[kk:kk + k] = ev[:k]; kk += k
    return f_all, m_all, ev_all, kk, tot


def cell(AR, paths, rule, xs_of):
    NB = len(paths); flows = np.zeros((NB, L)); mtms = np.zeros((NB, L)); tot = np.zeros(NB); evs = []; nev = []; pd = np.zeros(NB)
    for b, bi in enumerate(paths):
        p = pause_day(xs_of(bi), rule); pd[b] = p
        f, mm, ev, k, t = plan_run(AR, bi, p); flows[b] = f; mtms[b] = mm; tot[b] = t; evs.append(ev); nev.append(k)
    r = E3.plan_metrics(flows, mtms, evs, nev, tot)
    r.update(pausados_pct=100 * float((pd < L).mean()), dia_pausa_mediano=float(np.median(pd[pd < L])) if (pd < L).any() else None)
    return r, tot, pd


def main(NB=1000, selftest_only=False):
    days, M, FU, PER = O.setup(); t0 = time.time(); OUT = {"NB": NB, "escenarios": {}, "contiguo": {}, "pareado": {}, "pausa": {}}
    CONST = {"completo": 0.0, "-35%": 0.35, "cero": 1.0}; ARc = {k: arrays(days, M, FU, hc) for k, hc in CONST.items()}; ARs = arrays_switch(days, M, FU); n = len(days)
    rng = np.random.default_rng(4242); paths = {}
    for hc in P.HC:
        for per, ii in PER.items(): paths[(hc, per)] = [P.boot_idx(ii[0], ii[-1] + 1, L, rng) for _ in range(1000)][:NB]   # siempre 1.000 sorteos por celda (orden de la base)
    if selftest_only:
        base = json.load(open(os.path.join(HERE, "integ_port.json"))); bad = 0
        for sc, hc in CONST.items():
            for per in PER:
                r, tot, _ = cell(ARc[sc], paths[(hc, per)], "R0", lambda bi, x=ARc[sc]["x"]: x[bi])
                ref = base[f"hc{hc} | {per} | coupon | rot"]; d = (round(r["med_mes"]) - ref["med"], round(r["p10_mes"]) - ref["p10"])
                bad += any(d); print(f"selftest {sc} {per}: R0 med {r['med_mes']:.0f} p10 {r['p10_mes']:.0f} vs integ_port {ref['med']} {ref['p10']} -> dif {d}", flush=True)
        for per in PER:                                                                   # cambio fuera del camino = completo
            r0, t0c, _ = cell(ARc["completo"], paths[(0.0, per)][:200], "R1", lambda bi, x=ARc["completo"]["x"]: x[bi])
            r1, t1c, _ = cell(ARs, [bi + n * (np.arange(L) >= L) for bi in paths[(0.0, per)][:200]], "R1", lambda bi, x=ARs["x"]: x[bi])
            dd = float(np.abs(t0c - t1c).max()); bad += dd > 1e-6; print(f"selftest cambio fuera del camino {per}: max |dif| {dd:.2e}", flush=True)
        print("selftest:", "OK" if not bad else f"{bad} diferencias"); return bad
    SC = [(sc, ARc[sc], CONST[sc], None) for sc in CONST] + [("muere63", ARs, 0.0, 63), ("muere126", ARs, 0.0, 126)]
    NET = {}
    for sc, AR, hc, S in SC:
        for per in PER:
            P0 = paths[(hc, per)]
            pp = P0 if S is None else [bi + n * (np.arange(L) >= S) for bi in P0]
            for rule in RULES:
                r, tot, pd = cell(AR, pp, rule, lambda bi, x=AR["x"]: x[bi]); NET[(sc, per, rule)] = tot
                if S is not None and (pd < L).any(): r["demora_mediana_desde_cambio"] = float(np.median(pd[pd < L] - S)); r["pausados_antes_del_cambio_pct"] = 100 * float((pd < S).mean())
                OUT["escenarios"][f"{sc} | {per} | {rule}"] = r
                print(f"{time.time()-t0:5.0f}s {sc:9s} {per} {rule:3s} med {r['med_mes']:7.0f} p10 {r['p10_mes']:7.0f} Pneg {r['P_anio_neg']:5.1f} neg60 {r['neg60']:5.1f} pausados {r['pausados_pct']:5.1f} % dia {r['dia_pausa_mediano']}" + (f" demora {r.get('demora_mediana_desde_cambio')}" if S else ""), flush=True)
    for (sc, per, rule), v in NET.items():
        if rule != "R0": OUT["pareado"][f"{sc} | {per} | {rule} vs R0"] = E3.paired(v, NET[(sc, per, "R0")])
    idx = np.arange(n, dtype=np.int64)
    for sc in CONST:
        AR = ARc[sc]
        for per, ii in PER.items():
            pp = [idx[s0:s0 + L] for s0 in np.arange(ii[0], ii[-1] + 2 - L, 5)]
            for rule in RULES:
                r, tot, pd = cell(AR, pp, rule, lambda bi, x=AR["x"]: x[bi]); OUT["contiguo"][f"{sc} | {per} | {rule}"] = r
                print(f"{time.time()-t0:5.0f}s CONTIG {sc:9s} {per} {rule:3s} med {r['med_mes']:7.0f} p10 {r['p10_mes']:7.0f} neg60 {r['neg60']:5.1f} pausados {r['pausados_pct']:5.1f} %", flush=True)
    OUT["regla"] = decide(OUT); json.dump(OUT, open(os.path.join(HERE, "exp07_pause_rules.json"), "w"), indent=1)
    for k, v in OUT["regla"].items(): print(k, v)
    return OUT


def decide(OUT):
    R = {}
    for rule in ("R1", "R4", "R14"):
        g = lambda sc, per: OUT["pareado"][f"{sc} | {per} | {rule} vs R0"]
        h1 = all(g(sc, per)["P_loss5"] <= 0.20 for sc in ("completo", "-35%") for per in ("T1", "T2"))
        h2 = all(g("cero", per)["med"] > 0 and g("cero", per)["P_gain"] >= 0.80 for per in ("T1", "T2"))
        R[rule] = dict(H1_costo_bajo=h1, H2_protege_cero=h2, veredicto=("queda" if h1 and h2 else ("queda marcada: no protege dentro de 12 meses" if h1 else "se retira")))
    return R


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest": sys.exit(1 if main(1000, selftest_only=True) else 0)
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1000)
