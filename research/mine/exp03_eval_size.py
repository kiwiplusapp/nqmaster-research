"""exp03_eval_size.py (2026-10-27, experimento 03 / frente 5B): tamano de la eval de Lucid Flex 150K medido con la funcion objetivo.
Candidatos: eval fija k in {1..6} contratos (6 = incumbente); fondeada 3c, G 4.050, fee 215 (cupon) sin cambios; MFFU 1x8 sin cambios.
Mismos caminos que objective.baseline (rng 20261021 asientos, 4242 plan; mismo orden de sorteo) -> ganancia pareada por camino.
Regla de decision pre-registrada: docs/PLAN_2026-10-27_exp03.md. Salida: exp03_eval_size.json + exp03_eval_size.md.
Run (desde research/mine): python3 exp03_eval_size.py [NB]"""
import os, sys, json, time, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import prop_wf as P, objective as O
KS = (1, 2, 3, 4, 5, 6); INC = 6; H = O.H; MAXEV = O.MAXEV; MF = "MFFU 1x8"


def args_k(FU, hc, k, Hm):
    F = P.FIRMS["LucidFlex150K"]
    return dict(ep=P.ep_of(F, (0, k, k, 0, 0, 0, 0)), mix=(0, 4), fee=215.0, fee_list=285.0, tiers=FU.tiers(hc, "LucidFlex150K", (3, 1687, 0, 6000, 0)), act=0.0, Hh=Hm[(0, 4)])


def p22(days, M, A, ii):
    LO, CL, _ = M[A["mix"]]; n = len(days); idx = np.arange(n, dtype=np.int64); res = np.zeros(n, np.int64); end = np.zeros(n, np.int64)
    P.race_all(LO, CL, A["Hh"], idx, A["ep"], res, end); o = P.eval_metrics(res, end, ii, A["fee"], n)
    return dict(p22_3=o["p22_3"], p22_1=o["p22_1"], p120_3=o["p120_3"], fees22_3=o["fees22_3"])


def seat_cell(M, A, paths, s0=0):
    NB = len(paths); flows = np.zeros((NB, H)); mtms = np.zeros((NB, H)); evs = []; nev = []
    for b, bi in enumerate(paths):
        ev = np.zeros((MAXEV, 5)); k = O.run_seat(M, A, bi, s0, H, flows[b], mtms[b], ev); evs.append(ev); nev.append(k)
    return flows, mtms, evs, nev


def plan_cell(M, FU, hc, k, Hm, paths, mf):
    """mf: (flows, mtms, evs, nev, tot) de los 3 MFFU sobre los mismos caminos (iguales para todo k)."""
    NB = len(paths); L = H + 25; A = args_k(FU, hc, k, Hm); flows = mf[0].copy(); mtms = mf[1].copy(); tot = mf[4].copy(); evs = []; nev = []
    for b, bi in enumerate(paths):
        ev_all = np.zeros((8 * MAXEV, 5)); kk = mf[3][b]; ev_all[:kk] = mf[2][b][:kk]
        for s in range(5):
            f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((MAXEV, 5)); kq = O.run_seat(M, A, bi, 5 * s, H, f, mm, ev)
            flows[b] += f; mtms[b] += mm; tot[b] += f.sum() / 12.0; ev_all[kk:kk + kq] = ev[:kq]; kk += kq
        evs.append(ev_all); nev.append(kk)
    return flows, mtms, evs, nev, tot


def mffu_cell(M, FU, hc, Hm, paths):
    NB = len(paths); L = H + 25; A = O.seat_args(FU, hc, MF, Hm); flows = np.zeros((NB, L)); mtms = np.zeros((NB, L)); tot = np.zeros(NB); evs = []; nev = []
    for b, bi in enumerate(paths):
        ev_all = np.zeros((8 * MAXEV, 5)); kk = 0
        for s in range(3):
            f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((MAXEV, 5)); kq = O.run_seat(M, A, bi, 5 * s, H, f, mm, ev)
            flows[b] += f; mtms[b] += mm; tot[b] += f.sum() / 12.0; ev_all[kk:kk + kq] = ev[:kq]; kk += kq
        evs.append(ev_all); nev.append(kk)
    return flows, mtms, evs, nev, tot


def plan_metrics(flows, mtms, evs, nev, tot, lo=20, hi=H):
    r = dict(med_mes=float(np.median(tot)), p10_mes=float(np.percentile(tot, 10)), p90_mes=float(np.percentile(tot, 90)), P_anio_neg=100 * float((tot < 0).mean()))
    rw = O.metrics(flows, mtms, evs, nev, lo, hi); r.update({q: v for q, v in rw.items() if q not in ("med_mes", "p10_mes", "p90_mes", "P_anio_neg")}); r["cumple"] = O.verdict(r); return r


def paired(a, b):
    g = a - b; mb = float(np.median(b))
    return dict(med=float(np.median(g)), ci90=[float(np.percentile(g, 5)), float(np.percentile(g, 95))], P_gain=float((g > 0).mean()),
                P_loss5=float((g < -0.05 * abs(mb)).mean()), rel=float(np.median(g) / abs(mb)) if mb else float("nan"))


def main(NB=1000):
    days, M, FU, PER = O.setup(); t0 = time.time(); OUT = {"NB": NB, "KS": KS, "asiento": {}, "plan": {}, "asiento_contiguo": {}, "plan_contiguo": {}, "pareado": {}}
    NET = {}
    rng = np.random.default_rng(20261021)
    for hc in P.HC:
        Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
        for per, ii in PER.items():
            paths = [P.boot_idx(ii[0], ii[-1] + 1, H, rng) for _ in range(NB)]
            for k in KS:
                A = args_k(FU, hc, k, Hm); flows, mtms, evs, nev = seat_cell(M, A, paths); r = O.metrics(flows, mtms, evs, nev); r["cumple"] = O.verdict(r); r.update(p22(days, M, A, ii))
                OUT["asiento"][f"L150 {k}c/3c | hc{hc} | {per}"] = r; NET[("seat", k, hc, per)] = flows.sum(1) / 12.0
                print(f"{time.time()-t0:5.0f}s seat k{k} hc{hc:<4} {per} med {r['med_mes']:6.0f} p10 {r['p10_mes']:6.0f} neg60 {r['neg60']:4.1f} evperd {r['evals_perdidas_mes']:.3f} aprob {r['aprobacion']:4.1f} p22_3 {r['p22_3']:4.1f} dias {r['dias_aprobar']:3.0f} (p75 {r['dias_aprobar_p75']:3.0f}) cumple {sum(r['cumple'].values())}", flush=True)
    rng = np.random.default_rng(4242); L = H + 25
    for hc in P.HC:
        Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
        for per, ii in PER.items():
            paths = [P.boot_idx(ii[0], ii[-1] + 1, L, rng) for _ in range(NB)]; mf = mffu_cell(M, FU, hc, Hm, paths)
            for k in KS:
                flows, mtms, evs, nev, tot = plan_cell(M, FU, hc, k, Hm, paths, mf); r = plan_metrics(flows, mtms, evs, nev, tot)
                OUT["plan"][f"plan k{k} | hc{hc} | {per}"] = r; NET[("plan", k, hc, per)] = tot
                print(f"{time.time()-t0:5.0f}s PLAN k{k} hc{hc:<4} {per} med {r['med_mes']:6.0f} p10 {r['p10_mes']:6.0f} neg60 {r['neg60']:4.1f} evperd {r['evals_perdidas_mes']:.2f} aprob {r['aprobacion']:4.1f} dias {r['dias_aprobar']:3.0f} cumple {sum(r['cumple'].values())}", flush=True)
    for (u, k, hc, per), v in NET.items():
        if k != INC: OUT["pareado"][f"{u} k{k} vs k{INC} | hc{hc} | {per}"] = paired(v, NET[(u, INC, hc, per)])
    # historia contigua
    n = len(days); idx = np.arange(n, dtype=np.int64)
    for hc in P.HC:
        Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
        for per, ii in PER.items():
            st = np.arange(ii[0], ii[-1] + 2 - H, 5); stp = np.arange(ii[0], ii[-1] + 2 - L, 5)
            mfp = mffu_cell(M, FU, hc, Hm, [idx[s0:s0 + L] for s0 in stp])
            for k in KS:
                A = args_k(FU, hc, k, Hm); flows, mtms, evs, nev = seat_cell(M, A, [idx[s0:s0 + H] for s0 in st]); r = O.metrics(flows, mtms, evs, nev); r["cumple"] = O.verdict(r)
                OUT["asiento_contiguo"][f"L150 {k}c/3c | hc{hc} | {per}"] = r
                flows, mtms, evs, nev, tot = plan_cell(M, FU, hc, k, Hm, [idx[s0:s0 + L] for s0 in stp], mfp); r = plan_metrics(flows, mtms, evs, nev, tot)
                OUT["plan_contiguo"][f"plan k{k} | hc{hc} | {per}"] = r
                print(f"{time.time()-t0:5.0f}s CONTIG k{k} hc{hc:<4} {per} plan med {r['med_mes']:6.0f} p10 {r['p10_mes']:6.0f} neg60 {r['neg60']:4.1f} evperd {r['evals_perdidas_mes']:.2f} aprob {r['aprobacion']:4.1f} dias {r['dias_aprobar']:3.0f} cumple {sum(r['cumple'].values())}", flush=True)
    OUT["regla"] = decide(OUT); json.dump(OUT, open(os.path.join(HERE, "exp03_eval_size.json"), "w"), indent=1); write_md(OUT); return OUT


def decide(OUT):
    """Regla pre-registrada: eleccion en T1 (condiciones cumplidas hc0 + hc0.35, desempate mediana hc0.35); confirmacion en T2."""
    sc = {}
    for k in KS:
        a, b = OUT["plan"][f"plan k{k} | hc0.0 | T1"], OUT["plan"][f"plan k{k} | hc0.35 | T1"]
        sc[k] = (sum(a["cumple"].values()) + sum(b["cumple"].values()), b["med_mes"])
    ks = max(KS, key=lambda k: sc[k]); R = dict(puntajes_T1={str(k): list(v) for k, v in sc.items()}, k_elegido=int(ks))
    if ks == INC: R["veredicto"] = "sin cambio: el incumbente 6c gana la eleccion en T1"; return R
    inc2 = {hc: OUT["plan"][f"plan k{INC} | hc{hc} | T2"]["cumple"] for hc in (0.0, 0.35)}; cand2 = {hc: OUT["plan"][f"plan k{ks} | hc{hc} | T2"]["cumple"] for hc in (0.0, 0.35)}
    perdidas = [f"hc{hc}:{m}" for hc in (0.0, 0.35) for m, v in inc2[hc].items() if v and not cand2[hc][m]]
    g = OUT["pareado"][f"plan k{ks} vs k{INC} | hc0.35 | T2"]; ok_gain = (g["med"] > 0 and g["P_gain"] >= 0.80) or (g["rel"] >= -0.05 and g["P_loss5"] <= 0.20)
    c_inc = [OUT["plan_contiguo"][f"plan k{INC} | hc0.0 | {p}"]["neg60"] for p in ("T1", "T2")]; c_k = [OUT["plan_contiguo"][f"plan k{ks} | hc0.0 | {p}"]["neg60"] for p in ("T1", "T2")]
    ok_contig = all(ck <= ci + 2.0 for ck, ci in zip(c_k, c_inc))
    R.update(condiciones_perdidas_T2=perdidas, ganancia_pareada_T2_hc035=g, contiguo_neg60_inc=c_inc, contiguo_neg60_k=c_k, confirma=(not perdidas) and ok_gain and ok_contig)
    if R["confirma"]: R["veredicto"] = f"k = {ks} confirma en T2: reemplaza al 6c"
    else:
        why = (["pierde " + ", ".join(perdidas)] if perdidas else []) + ([] if ok_gain else ["ganancia pareada hc0.35 fuera de la regla"]) + ([] if ok_contig else ["neg60 contiguo empeora > 2 pts"])
        R["veredicto"] = f"k = {ks} gana en T1 pero NO confirma en T2 ({'; '.join(why)}): sin cambio"
    return R


def write_md(OUT):
    L = [f"# Experimento 03: tamano de la eval de Lucid 150K (k contratos) — {OUT['NB']} caminos\n", f"Regla: {OUT['regla']['veredicto']}\n",
         "| unidad | k | edge | periodo | med $/mes | p10 | P(anio<0) % | neg60 % (mtm) [=0] | evals/anio | evals perd./mes | aprob. % | p22_3 % | dias (p75) | cumple | pareado vs 6c: med [ci90] P(gain) P(loss>5%) |", "|" + "---|" * 15]
    for sec, u in (("asiento", "seat"), ("plan", "plan")):
        for key, r in OUT[sec].items():
            nm, hc, per = [x.strip() for x in key.split("|")]; k = int(nm.split("k")[1][0]) if sec == "plan" else int(nm.split(" ")[1][0])
            pk = f"{u} k{k} vs k{INC} | {hc} | {per}"; g = OUT["pareado"].get(pk)
            gs = f"{g['med']:+.0f} [{g['ci90'][0]:+.0f}, {g['ci90'][1]:+.0f}] {g['P_gain']:.2f} {g['P_loss5']:.2f}" if g else "—"
            cs = " ".join(("+" if v else "-") + n for n, v in r["cumple"].items())
            L.append(f"| {sec} | {k} | {hc} | {per} | {r['med_mes']:.0f} | {r['p10_mes']:.0f} | {r['P_anio_neg']:.1f} | {r['neg60']:.1f} ({r['neg60_mtm']:.1f}) [{r['neg60_cero']:.1f}] | {r['evals_anio']:.1f} | {r['evals_perdidas_mes']:.3f} | {r['aprobacion']:.1f} | {('%.1f' % r['p22_3']) if 'p22_3' in r else '—'} | {r['dias_aprobar']:.0f} ({r['dias_aprobar_p75']:.0f}) | {sum(r['cumple'].values())} {cs} | {gs} |")
    L += ["", "Historia contigua:", "", "| unidad | k | edge | periodo | n | med $/mes | p10 | neg60 % | evals perd./mes | aprob. % | dias | cumple |", "|" + "---|" * 12]
    for sec in ("asiento_contiguo", "plan_contiguo"):
        for key, r in OUT[sec].items():
            nm, hc, per = [x.strip() for x in key.split("|")]
            L.append(f"| {sec} | {nm} | {hc} | {per} | {r['n_caminos']} | {r['med_mes']:.0f} | {r['p10_mes']:.0f} | {r['neg60']:.1f} | {r['evals_perdidas_mes']:.2f} | {r['aprobacion']:.1f} | {r['dias_aprobar']:.0f} | {sum(r['cumple'].values())} |")
    open(os.path.join(HERE, "exp03_eval_size.md"), "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1000)
