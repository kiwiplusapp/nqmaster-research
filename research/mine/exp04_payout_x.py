"""exp04_payout_x.py (2026-10-27, experimento 04 / frente 5B): umbral de retiro X de la Lucid Flex 150K fondeada medido con la funcion objetivo.
Candidatos X in XS (6.000 = incumbente, FundedPayoutAt del preset Lucid150K); eval 6c, fondeada 3c, risk cap 300 bajo 1.687, Q 250, tope 3.000 sin cambios.
Mismos caminos que objective.baseline (rng 20261021 asientos, 4242 plan) -> ganancia pareada. Regla pre-registrada: docs/PLAN_2026-10-27_exp04.md.
Run (desde research/mine): python3 exp04_payout_x.py [NB]  -> exp04_payout_x.json + exp04_payout_x.md"""
import os, sys, json, time, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import prop_wf as P, objective as O, exp03_eval_size as E3
XS = (4600, 5000, 6000, 7000, 8000, 10000, 12000); INC = 6000; H = O.H; MAXEV = O.MAXEV


def args_x(FU, hc, X, Hm):
    F = P.FIRMS["LucidFlex150K"]
    return dict(ep=P.ep_of(F, (0, 6, 6, 0, 0, 0, 0)), mix=(0, 4), fee=215.0, fee_list=285.0, tiers=FU.tiers(hc, "LucidFlex150K", (3, 1687, 0, X, 0)), act=0.0, Hh=Hm[(0, 4)])


def plan_cell(M, A, paths, mf):
    L = H + 25; flows = mf[0].copy(); mtms = mf[1].copy(); tot = mf[4].copy(); evs = []; nev = []
    for b, bi in enumerate(paths):
        ev_all = np.zeros((8 * MAXEV, 5)); kk = mf[3][b]; ev_all[:kk] = mf[2][b][:kk]
        for s in range(5):
            f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((MAXEV, 5)); kq = O.run_seat(M, A, bi, 5 * s, H, f, mm, ev)
            flows[b] += f; mtms[b] += mm; tot[b] += f.sum() / 12.0; ev_all[kk:kk + kq] = ev[:kq]; kk += kq
        evs.append(ev_all); nev.append(kk)
    return flows, mtms, evs, nev, tot


def main(NB=1000):
    days, M, FU, PER = O.setup(); t0 = time.time(); OUT = {"NB": NB, "XS": XS, "asiento": {}, "plan": {}, "asiento_contiguo": {}, "plan_contiguo": {}, "pareado": {}}; NET = {}
    rng = np.random.default_rng(20261021)
    for hc in P.HC:
        Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
        for per, ii in PER.items():
            paths = [P.boot_idx(ii[0], ii[-1] + 1, H, rng) for _ in range(NB)]
            for X in XS:
                A = args_x(FU, hc, X, Hm); flows, mtms, evs, nev = E3.seat_cell(M, A, paths); r = O.metrics(flows, mtms, evs, nev); r["cumple"] = O.verdict(r)
                OUT["asiento"][f"L150 X{X} | hc{hc} | {per}"] = r; NET[("seat", X, hc, per)] = flows.sum(1) / 12.0
                print(f"{time.time()-t0:5.0f}s seat X{X:<5} hc{hc:<4} {per} med {r['med_mes']:6.0f} p10 {r['p10_mes']:6.0f} neg60 {r['neg60']:4.1f} (mtm {r['neg60_mtm']:4.1f}) evperd {r['evals_perdidas_mes']:.3f} ctas {r['cuentas_perdidas_mes']:.3f} ret/a {r['retiros_anio']:4.1f} cumple {sum(r['cumple'].values())}", flush=True)
    rng = np.random.default_rng(4242); L = H + 25
    for hc in P.HC:
        Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
        for per, ii in PER.items():
            paths = [P.boot_idx(ii[0], ii[-1] + 1, L, rng) for _ in range(NB)]; mf = E3.mffu_cell(M, FU, hc, Hm, paths)
            for X in XS:
                flows, mtms, evs, nev, tot = plan_cell(M, args_x(FU, hc, X, Hm), paths, mf); r = E3.plan_metrics(flows, mtms, evs, nev, tot)
                OUT["plan"][f"plan X{X} | hc{hc} | {per}"] = r; NET[("plan", X, hc, per)] = tot
                print(f"{time.time()-t0:5.0f}s PLAN X{X:<5} hc{hc:<4} {per} med {r['med_mes']:6.0f} p10 {r['p10_mes']:6.0f} neg60 {r['neg60']:4.1f} evperd {r['evals_perdidas_mes']:.2f} ctas {r['cuentas_perdidas_mes']:.2f} aprob {r['aprobacion']:4.1f} dias {r['dias_aprobar']:3.0f} cumple {sum(r['cumple'].values())}", flush=True)
    for (u, X, hc, per), v in NET.items():
        if X != INC: OUT["pareado"][f"{u} X{X} vs X{INC} | hc{hc} | {per}"] = E3.paired(v, NET[(u, INC, hc, per)])
    n = len(days); idx = np.arange(n, dtype=np.int64)
    for hc in P.HC:
        Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
        for per, ii in PER.items():
            st = np.arange(ii[0], ii[-1] + 2 - H, 5); stp = np.arange(ii[0], ii[-1] + 2 - L, 5)
            pp = [idx[s0:s0 + L] for s0 in stp]; mfp = E3.mffu_cell(M, FU, hc, Hm, pp)
            for X in XS:
                A = args_x(FU, hc, X, Hm); flows, mtms, evs, nev = E3.seat_cell(M, A, [idx[s0:s0 + H] for s0 in st]); r = O.metrics(flows, mtms, evs, nev); r["cumple"] = O.verdict(r)
                OUT["asiento_contiguo"][f"L150 X{X} | hc{hc} | {per}"] = r
                flows, mtms, evs, nev, tot = plan_cell(M, A, pp, mfp); r = E3.plan_metrics(flows, mtms, evs, nev, tot); OUT["plan_contiguo"][f"plan X{X} | hc{hc} | {per}"] = r
                print(f"{time.time()-t0:5.0f}s CONTIG X{X:<5} hc{hc:<4} {per} plan med {r['med_mes']:6.0f} p10 {r['p10_mes']:6.0f} neg60 {r['neg60']:4.1f} evperd {r['evals_perdidas_mes']:.2f} cumple {sum(r['cumple'].values())}", flush=True)
    OUT["regla"] = decide(OUT); json.dump(OUT, open(os.path.join(HERE, "exp04_payout_x.json"), "w"), indent=1); write_md(OUT); print(OUT["regla"]["veredicto"]); return OUT


def decide(OUT):
    sc = {}
    for X in XS:
        a, b = OUT["plan"][f"plan X{X} | hc0.0 | T1"], OUT["plan"][f"plan X{X} | hc0.35 | T1"]
        sc[X] = (sum(a["cumple"].values()) + sum(b["cumple"].values()), b["med_mes"])
    xs = max(XS, key=lambda x: sc[x]); R = dict(puntajes_T1={str(x): list(v) for x, v in sc.items()}, X_elegido=int(xs))
    if xs == INC: R["veredicto"] = "sin cambio: el incumbente X = 6.000 gana la eleccion en T1"; return R
    tie = sc[xs][0] == sc[INC][0]; R["empate_en_condiciones"] = tie
    if tie:
        g1 = OUT["pareado"][f"plan X{xs} vs X{INC} | hc0.35 | T1"]; R["ganancia_pareada_T1_hc035"] = g1
        if not (g1["P_gain"] >= 0.80):
            R["veredicto"] = f"sin cambio: X = {xs} empata en condiciones con 6.000 y no le gana en T1 con P(gain) >= 0,80 (P = {g1['P_gain']:.2f})"; return R
    inc2 = {hc: OUT["plan"][f"plan X{INC} | hc{hc} | T2"]["cumple"] for hc in (0.0, 0.35)}; cand2 = {hc: OUT["plan"][f"plan X{xs} | hc{hc} | T2"]["cumple"] for hc in (0.0, 0.35)}
    perdidas = [f"hc{hc}:{m}" for hc in (0.0, 0.35) for m, v in inc2[hc].items() if v and not cand2[hc][m]]
    g = OUT["pareado"][f"plan X{xs} vs X{INC} | hc0.35 | T2"]
    ok_gain = (g["med"] > 0 and g["P_gain"] >= 0.80) if tie else (g["P_loss5"] <= 0.20)
    c_inc = [OUT["plan_contiguo"][f"plan X{INC} | hc0.0 | {p}"]["neg60"] for p in ("T1", "T2")]; c_x = [OUT["plan_contiguo"][f"plan X{xs} | hc0.0 | {p}"]["neg60"] for p in ("T1", "T2")]
    ok_contig = all(cx <= ci + 2.0 for cx, ci in zip(c_x, c_inc))
    R.update(condiciones_perdidas_T2=perdidas, ganancia_pareada_T2_hc035=g, contiguo_neg60_inc=c_inc, contiguo_neg60_x=c_x, confirma=(not perdidas) and ok_gain and ok_contig)
    if R["confirma"]: R["veredicto"] = f"X = {xs} confirma en T2: reemplaza a 6.000"
    else:
        why = (["pierde " + ", ".join(perdidas)] if perdidas else []) + ([] if ok_gain else ["ganancia pareada hc0.35 T2 fuera de la regla"]) + ([] if ok_contig else ["neg60 contiguo empeora > 2 pts"])
        R["veredicto"] = f"X = {xs} gana en T1 pero NO confirma en T2 ({'; '.join(why)}): sin cambio"
    return R


def write_md(OUT):
    L = [f"# Experimento 04: umbral de retiro X de la Lucid 150K fondeada — {OUT['NB']} caminos\n", f"Regla: {OUT['regla']['veredicto']}\n",
         "| unidad | X | edge | periodo | med $/mes | p10 | P(anio<0) % | neg60 % (mtm) [=0] | evals/anio | evals perd./mes | ctas perd./mes | retiros/anio | aprob. % | dias (p75) | cumple | pareado vs 6.000: med [ci90] P(gain) P(loss>5%) |", "|" + "---|" * 16]
    for sec, u in (("asiento", "seat"), ("plan", "plan")):
        for key, r in OUT[sec].items():
            nm, hc, per = [x.strip() for x in key.split("|")]; X = int(nm.split("X")[1]); g = OUT["pareado"].get(f"{u} X{X} vs X{INC} | {hc} | {per}")
            gs = f"{g['med']:+.0f} [{g['ci90'][0]:+.0f}, {g['ci90'][1]:+.0f}] {g['P_gain']:.2f} {g['P_loss5']:.2f}" if g else "—"
            cs = " ".join(("+" if v else "-") + n for n, v in r["cumple"].items())
            L.append(f"| {sec} | {X} | {hc} | {per} | {r['med_mes']:.0f} | {r['p10_mes']:.0f} | {r['P_anio_neg']:.1f} | {r['neg60']:.1f} ({r['neg60_mtm']:.1f}) [{r['neg60_cero']:.1f}] | {r['evals_anio']:.1f} | {r['evals_perdidas_mes']:.3f} | {r['cuentas_perdidas_mes']:.3f} | {r['retiros_anio']:.1f} | {r['aprobacion']:.1f} | {r['dias_aprobar']:.0f} ({r['dias_aprobar_p75']:.0f}) | {sum(r['cumple'].values())} {cs} | {gs} |")
    L += ["", "Historia contigua:", "", "| unidad | X | edge | periodo | n | med $/mes | p10 | neg60 % | evals perd./mes | ctas perd./mes | retiros/anio | cumple |", "|" + "---|" * 12]
    for sec in ("asiento_contiguo", "plan_contiguo"):
        for key, r in OUT[sec].items():
            nm, hc, per = [x.strip() for x in key.split("|")]
            L.append(f"| {sec} | {nm} | {hc} | {per} | {r['n_caminos']} | {r['med_mes']:.0f} | {r['p10_mes']:.0f} | {r['neg60']:.1f} | {r['evals_perdidas_mes']:.2f} | {r['cuentas_perdidas_mes']:.3f} | {r['retiros_anio']:.1f} | {sum(r['cumple'].values())} |")
    open(os.path.join(HERE, "exp04_payout_x.md"), "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1000)
