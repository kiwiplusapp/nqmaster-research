"""exp05_budget.py (2026-10-27, experimento 05 / frente 5B): presupuesto por plaza (regla 6 del runbook) dentro de la simulacion,
medido con la funcion objetivo. seat_flow_b = objective.seat_flow + presupuesto: antes de comprar una eval la plaza mira su neto
(caja ya cobrada) desde la ultima revision (cada QLEN dias habiles desde el inicio del camino, comun a todas las plazas); si es < -B
no compra y espera a la revision siguiente. Modo anual: sin revisiones (como integ_budget.py). Regla pre-registrada:
docs/PLAN_2026-10-27_exp05.md. Run (desde research/mine): python3 exp05_budget.py selftest | python3 exp05_budget.py [NB]"""
import os, sys, json, time, numpy as np
from numba import njit
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import prop_wf as P, objective as O, exp03_eval_size as E3
race = P.race; fund_flow = O.fund_flow; H = O.H; MAXEV = O.MAXEV; QLEN = 63
CANDS = {"sin": (1e12, 1e12, 0), "T1500": (1500.0, 600.0, 1), "T2500": (2500.0, 900.0, 1), "T4000": (4000.0, 1500.0, 1), "T6000": (6000.0, 2500.0, 1), "A4000": (4000.0, 1500.0, 0)}
INC = "T4000"; L150 = "L150 6c/3c"; MF = "MFFU 1x8"


@njit(cache=True)
def seat_flow_b(LO, CL, Hh, ep, fee, FL, FC, fp, idx, s0, end, flow, mtm, ev, act, budget, quarterly, qlen, stats):
    """objective.seat_flow con presupuesto. stats[0] += dias en pausa, stats[1] += pausas."""
    i = s0; k = 0; rec = np.zeros(5)
    while i < end:
        if budget < 1e11:
            q0 = (i // qlen) * qlen if quarterly else 0
            if q0 < s0: q0 = s0
            net = 0.0
            for d in range(q0, i): net += flow[d]
            if net < -budget:
                nxt = (i // qlen + 1) * qlen if quarterly else end      # revision comun siguiente (fix 27-oct, revision adversarial: antes q0 + qlen con q0 recortado a s0)
                if nxt > end: nxt = end
                stats[0] += nxt - i; stats[1] += 1; i = nxt; continue
        flow[i] -= fee; mtm[i] -= fee
        r, j = race(LO, CL, Hh, idx, i, end, ep)
        jj = j if j < end else end - 1
        if k < ev.shape[0]:
            ev[k, 0] = i; ev[k, 1] = r; ev[k, 2] = jj if r != 0 else end - 1; ev[k, 3] = -1; ev[k, 4] = 0
        if r != 1:
            k += 1; i = j + 1; continue
        if act > 0.0: flow[jj] -= act; mtm[jj] -= act
        fund_flow(FL, FC, fp, idx, j + 1, end, rec, flow, mtm)
        if k < ev.shape[0]:
            ev[k, 3] = j + 1 + rec[2] if rec[2] >= 0 else -1; ev[k, 4] = rec[3]
        k += 1; i = int(rec[4]) + 1
    return k


def run_b(M, A, bi, s0, L, flow, mtm, ev, budget, quarterly, stats):
    LO, CL, _ = M[A["mix"]]; FL, FC, fp = A["tiers"]
    return seat_flow_b(LO, CL, A["Hh"], A["ep"], A["fee"], FL, FC, fp, bi, s0, s0 + L, flow, mtm, ev, A["act"], float(budget), bool(quarterly), QLEN, stats)


def seat_cell(M, A, paths, budget, quarterly):
    NB = len(paths); flows = np.zeros((NB, H)); mtms = np.zeros((NB, H)); evs = []; nev = []; st = np.zeros(2)
    for b, bi in enumerate(paths):
        ev = np.zeros((MAXEV, 5)); k = run_b(M, A, bi, 0, H, flows[b], mtms[b], ev, budget, quarterly, st); evs.append(ev); nev.append(k)
    return flows, mtms, evs, nev, st / NB


def plan_cell(M, AL, AM, paths, cand):
    bl, bm, q = CANDS[cand]; NB = len(paths); L = H + 25; flows = np.zeros((NB, L)); mtms = np.zeros((NB, L)); tot = np.zeros(NB); evs = []; nev = []; st = np.zeros(2)
    for b, bi in enumerate(paths):
        ev_all = np.zeros((8 * MAXEV, 5)); kk = 0
        for A, cnt, bud in ((AM, 3, bm), (AL, 5, bl)):
            for s in range(cnt):
                f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((MAXEV, 5)); kq = run_b(M, A, bi, 5 * s, H, f, mm, ev, bud, q, st)
                flows[b] += f; mtms[b] += mm; tot[b] += f.sum() / 12.0; ev_all[kk:kk + kq] = ev[:kq]; kk += kq
        evs.append(ev_all); nev.append(kk)
    return flows, mtms, evs, nev, tot, st / NB


def ref_seat_b(M, A, bi, s0, L, budget, quarterly):
    """referencia independiente en Python (lista explicita de revisiones comunes) para el autotest con presupuesto finito"""
    LO, CL, _ = M[A["mix"]]; FL, FC, fp = A["tiers"]; end = s0 + L; flow = np.zeros(len(bi)); mtm = np.zeros(len(bi)); rec = np.zeros(5)
    reviews = list(range(QLEN, end + QLEN, QLEN)) if quarterly else []
    i = s0; nev = 0; paused = 0
    while i < end:
        last = max([s0] + [r for r in reviews if r <= i]); net = float(flow[last:i].sum())
        if net < -budget:
            nxt = min([r for r in reviews if r > i] + [end]); paused += min(nxt, end) - i; i = min(nxt, end); continue
        flow[i] -= A["fee"]; mtm[i] -= A["fee"]; nev += 1
        r, j = race(LO, CL, A["Hh"], bi, i, end, A["ep"])
        if r != 1:
            i = j + 1; continue
        fund_flow(FL, FC, fp, bi, j + 1, end, rec, flow, mtm); i = int(rec[4]) + 1
    return flow, nev, paused


def selftest(NB=150):
    days, M, FU, PER = O.setup(); rng = np.random.default_rng(3); bad = 0; tot = 0
    for hc in P.HC:
        Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
        for per, ii in PER.items():
            for name in (L150, MF):
                A = O.seat_args(FU, hc, name, Hm)
                for _ in range(NB):
                    bi = P.boot_idx(ii[0], ii[-1] + 1, H, rng)
                    f0 = np.zeros(H); m0 = np.zeros(H); e0 = np.zeros((MAXEV, 5)); k0 = O.run_seat(M, A, bi, 0, H, f0, m0, e0)
                    for q in (0, 1):
                        f1 = np.zeros(H); m1 = np.zeros(H); e1 = np.zeros((MAXEV, 5)); k1 = run_b(M, A, bi, 0, H, f1, m1, e1, 1e12, q, np.zeros(2))
                        tot += 1
                        if k0 != k1 or not (np.array_equal(f0, f1) and np.array_equal(m0, m1) and np.array_equal(e0[:k0], e1[:k1])): bad += 1
    print(f"selftest: {tot} asientos con presupuesto infinito, {bad} diferencias contra objective.run_seat (flujo, mtm y registro de evals identicos)")
    bad2 = 0; tot2 = 0; npaused = 0; rng = np.random.default_rng(5)
    for hc in (1.0, 0.35):                                        # presupuesto finito y plazas escalonadas (s0 > 0) contra la referencia
        Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
        for per, ii in PER.items():
            for name, bud in ((L150, 1500.0), (L150, 2500.0), (MF, 600.0)):
                A = O.seat_args(FU, hc, name, Hm)
                for _ in range(NB // 3):
                    bi = P.boot_idx(ii[0], ii[-1] + 1, H + 25, rng)
                    for s0 in (0, 5, 10, 15, 20):
                        for q in (1, 0):
                            f1 = np.zeros(H + 25); m1 = np.zeros(H + 25); e1 = np.zeros((MAXEV, 5)); st = np.zeros(2)
                            k1 = run_b(M, A, bi, s0, H, f1, m1, e1, bud, q, st); fr, kr, pr = ref_seat_b(M, A, bi, s0, H, bud, q)
                            tot2 += 1; npaused += st[0] > 0
                            if k1 != kr or not np.allclose(f1, fr) or abs(st[0] - pr) > 0: bad2 += 1
    print(f"selftest: {tot2} asientos con presupuesto finito y s0 en 0..20 ({npaused} con pausa), {bad2} diferencias contra la referencia independiente (flujo, evals y dias de pausa)")
    return bad + bad2


def main(NB=1000):
    days, M, FU, PER = O.setup(); t0 = time.time(); OUT = {"NB": NB, "CANDS": {k: list(v) for k, v in CANDS.items()}, "asiento": {}, "plan": {}, "plan_contiguo": {}, "pareado": {}}; NET = {}
    rng = np.random.default_rng(20261021)
    for hc in P.HC:
        Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
        for per, ii in PER.items():
            paths = [P.boot_idx(ii[0], ii[-1] + 1, H, rng) for _ in range(NB)]
            for name, j in ((L150, 0), (MF, 1)):
                A = O.seat_args(FU, hc, name, Hm)
                for c, v in CANDS.items():
                    flows, mtms, evs, nev, st = seat_cell(M, A, paths, v[j], v[2]); r = O.metrics(flows, mtms, evs, nev); r["cumple"] = O.verdict(r); r["dias_pausa_anio"] = float(st[0]); r["pausas_anio"] = float(st[1])
                    OUT["asiento"][f"{name} {c} | hc{hc} | {per}"] = r
            print(f"{time.time()-t0:5.0f}s asientos hc{hc} {per}", flush=True)
    rng = np.random.default_rng(4242); L = H + 25
    for hc in P.HC:
        Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
        AL, AM = O.seat_args(FU, hc, L150, Hm), O.seat_args(FU, hc, MF, Hm)
        for per, ii in PER.items():
            paths = [P.boot_idx(ii[0], ii[-1] + 1, L, rng) for _ in range(NB)]
            for c in CANDS:
                flows, mtms, evs, nev, tot, st = plan_cell(M, AL, AM, paths, c); r = E3.plan_metrics(flows, mtms, evs, nev, tot); r["dias_pausa_plan_anio"] = float(st[0]); r["pausas_plan_anio"] = float(st[1])
                OUT["plan"][f"plan {c} | hc{hc} | {per}"] = r; NET[(c, hc, per)] = tot
                print(f"{time.time()-t0:5.0f}s PLAN {c:5s} hc{hc:<4} {per} med {r['med_mes']:6.0f} p10 {r['p10_mes']:6.0f} Pneg {r['P_anio_neg']:4.1f} neg60 {r['neg60']:4.1f} [=0 {r['neg60_cero']:4.1f}] evperd {r['evals_perdidas_mes']:.2f} evals/a {r['evals_anio']:5.1f} pausa d/a {st[0]:5.0f} cumple {sum(r['cumple'].values())}", flush=True)
    for (c, hc, per), v in NET.items():
        if c != INC: OUT["pareado"][f"plan {c} vs {INC} | hc{hc} | {per}"] = E3.paired(v, NET[(INC, hc, per)])
    n = len(days); idx = np.arange(n, dtype=np.int64)
    for hc in P.HC:
        Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
        AL, AM = O.seat_args(FU, hc, L150, Hm), O.seat_args(FU, hc, MF, Hm)
        for per, ii in PER.items():
            pp = [idx[s0:s0 + L] for s0 in np.arange(ii[0], ii[-1] + 2 - L, 5)]
            for c in CANDS:
                flows, mtms, evs, nev, tot, st = plan_cell(M, AL, AM, pp, c); r = E3.plan_metrics(flows, mtms, evs, nev, tot); OUT["plan_contiguo"][f"plan {c} | hc{hc} | {per}"] = r
                print(f"{time.time()-t0:5.0f}s CONTIG {c:5s} hc{hc:<4} {per} med {r['med_mes']:6.0f} p10 {r['p10_mes']:6.0f} neg60 {r['neg60']:4.1f} evperd {r['evals_perdidas_mes']:.2f} cumple {sum(r['cumple'].values())}", flush=True)
    OUT["regla"] = decide(OUT); json.dump(OUT, open(os.path.join(HERE, "exp05_budget.json"), "w"), indent=1); write_md(OUT); print(OUT["regla"]["veredicto"]); return OUT


def decide(OUT):
    pl = lambda c, hc, per: OUT["plan"][f"plan {c} | hc{hc} | {per}"]
    sc = {c: sum(pl(c, 0.0, "T1")["cumple"].values()) + sum(pl(c, 0.35, "T1")["cumple"].values()) for c in CANDS}
    R = dict(puntajes_T1=sc, p10_cero_T1={c: pl(c, 1.0, "T1")["p10_mes"] for c in CANDS})
    best = max(sc.values()); top = [c for c in CANDS if sc[c] == best]
    if sc[INC] == best:
        ok = [c for c in top if c != INC and pl(c, 1.0, "T1")["p10_mes"] >= pl(INC, 1.0, "T1")["p10_mes"] + 300.0 and OUT["pareado"][f"plan {c} vs {INC} | hc0.35 | T1"]["P_loss5"] <= 0.20]
        R["candidatos_por_desempate"] = ok
        if not ok: R["elegido"] = INC; R["veredicto"] = "sin cambio: la regla 6 del runbook (T4000) gana la eleccion en T1"; return R
        ch = max(ok, key=lambda c: pl(c, 1.0, "T1")["p10_mes"])
    else:
        ch = max(top, key=lambda c: pl(c, 1.0, "T1")["p10_mes"])
    R["elegido"] = ch
    perdidas = [f"hc{hc}:{m}" for hc in (0.0, 0.35) for m, v in pl(INC, hc, "T2")["cumple"].items() if v and not pl(ch, hc, "T2")["cumple"][m]]
    g = OUT["pareado"][f"plan {ch} vs {INC} | hc0.35 | T2"]; ok_gain = g["P_loss5"] <= 0.20
    ok_p10 = pl(ch, 1.0, "T2")["p10_mes"] >= pl(INC, 1.0, "T2")["p10_mes"]
    cont = {f"hc{hc} {p}": (OUT["plan_contiguo"][f"plan {INC} | hc{hc} | {p}"]["neg60"], OUT["plan_contiguo"][f"plan {ch} | hc{hc} | {p}"]["neg60"]) for hc in (0.0, 0.35) for p in ("T1", "T2")}
    ok_cont = all(x <= i + 2.0 for i, x in cont.values())
    R.update(condiciones_perdidas_T2=perdidas, ganancia_pareada_T2_hc035=g, p10_cero_T2=[pl(INC, 1.0, "T2")["p10_mes"], pl(ch, 1.0, "T2")["p10_mes"]], contiguo_neg60_inc_vs_cand=cont, confirma=(not perdidas) and ok_gain and ok_p10 and ok_cont)
    if R["confirma"]: R["veredicto"] = f"{ch} confirma en T2: reemplaza a la regla 6 del runbook (T4000)" + (" -> sacar la regla 6" if ch == "sin" else "")
    else:
        why = (["pierde " + ", ".join(perdidas)] if perdidas else []) + ([] if ok_gain else ["P(perder > 5 %) con -35 % en T2 > 0,20"]) + ([] if ok_p10 else ["p10 con edge cero en T2 peor"]) + ([] if ok_cont else ["neg60 contiguo empeora > 2 pts"])
        R["veredicto"] = f"{ch} gana en T1 pero NO confirma en T2 ({'; '.join(why)}): la regla 6 queda como esta"
    return R


def write_md(OUT):
    L = [f"# Experimento 05: presupuesto por plaza — {OUT['NB']} caminos\n", f"Regla: {OUT['regla']['veredicto']}\n",
         "| plan | edge | periodo | med $/mes | p10 | P(anio<0) % | neg60 % [=0] | evals/anio | evals perd./mes | aprob. % | dias | dias en pausa por anio (8 plazas) | cumple | pareado vs T4000: med [ci90] P(gain) P(loss>5%) |", "|" + "---|" * 14]
    for key, r in OUT["plan"].items():
        nm, hc, per = [x.strip() for x in key.split("|")]; c = nm.split(" ")[1]; g = OUT["pareado"].get(f"plan {c} vs {INC} | {hc} | {per}")
        gs = f"{g['med']:+.0f} [{g['ci90'][0]:+.0f}, {g['ci90'][1]:+.0f}] {g['P_gain']:.2f} {g['P_loss5']:.2f}" if g else "—"
        L.append(f"| {c} | {hc} | {per} | {r['med_mes']:.0f} | {r['p10_mes']:.0f} | {r['P_anio_neg']:.1f} | {r['neg60']:.1f} [{r['neg60_cero']:.1f}] | {r['evals_anio']:.1f} | {r['evals_perdidas_mes']:.2f} | {r['aprobacion']:.1f} | {r['dias_aprobar']:.0f} | {r['dias_pausa_plan_anio']:.0f} | {sum(r['cumple'].values())} | {gs} |")
    L += ["", "Historia contigua:", "", "| plan | edge | periodo | n | med $/mes | p10 | neg60 % [=0] | evals perd./mes | cumple |", "|" + "---|" * 9]
    for key, r in OUT["plan_contiguo"].items():
        nm, hc, per = [x.strip() for x in key.split("|")]
        L.append(f"| {nm.split(' ')[1]} | {hc} | {per} | {r['n_caminos']} | {r['med_mes']:.0f} | {r['p10_mes']:.0f} | {r['neg60']:.1f} [{r['neg60_cero']:.1f}] | {r['evals_perdidas_mes']:.2f} | {sum(r['cumple'].values())} |")
    L += ["", "Asientos (bootstrap):", "", "| asiento | edge | periodo | med $/mes | p10 | neg60 % [=0] | evals perd./mes | dias en pausa por anio | cumple |", "|" + "---|" * 9]
    for key, r in OUT["asiento"].items():
        nm, hc, per = [x.strip() for x in key.split("|")]
        L.append(f"| {nm} | {hc} | {per} | {r['med_mes']:.0f} | {r['p10_mes']:.0f} | {r['neg60']:.1f} [{r['neg60_cero']:.1f}] | {r['evals_perdidas_mes']:.3f} | {r['dias_pausa_anio']:.0f} | {sum(r['cumple'].values())} |")
    open(os.path.join(HERE, "exp05_budget.md"), "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest": sys.exit(1 if selftest() else 0)
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1000)
