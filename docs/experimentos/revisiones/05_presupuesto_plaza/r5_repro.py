"""Revisor exp05: reproduce las celdas del plan (bootstrap y contiguo) desde el script comprometido, sin escribir en el repo;
compara con exp05_budget.json, integ_budget.json; aisla la unica pausa de T4000; caminos identicos sin vs T4000."""
import os, sys, json, time, numpy as np
sys.path.insert(0, "/home/user/nqmaster-research/research/mine")
import prop_wf as P, objective as O, exp05_budget as E5, exp03_eval_size as E3
D = "/home/user/nqmaster-research/research/mine/"
X = json.load(open(D + "exp05_budget.json")); IB = json.load(open(D + "integ_budget.json"))
H = O.H; L = H + 25; NB = 1000

def main():
    t0 = time.time(); days, M, FU, PER = O.setup(); rng = np.random.default_rng(4242); NET = {}; FLOWS = {}; worst = 0.0; nd = 0
    for hc in P.HC:
        Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
        AL, AM = O.seat_args(FU, hc, E5.L150, Hm), O.seat_args(FU, hc, E5.MF, Hm)
        for per, ii in PER.items():
            paths = [P.boot_idx(ii[0], ii[-1] + 1, L, rng) for _ in range(NB)]
            for c in E5.CANDS:
                flows, mtms, evs, nev, tot, st = E5.plan_cell(M, AL, AM, paths, c); r = E3.plan_metrics(flows, mtms, evs, nev, tot)
                NET[(c, hc, per)] = tot; FLOWS[(c, hc, per)] = (flows, np.array(nev))
                j = X["plan"][f"plan {c} | hc{hc} | {per}"]
                for k, v in r.items():
                    if isinstance(v, float) and not np.isnan(v):
                        dv = abs(v - j[k]); worst = max(worst, dv); nd += dv > 1e-9
                if r["cumple"] != j["cumple"]: nd += 1; print("CUMPLE DIFF", c, hc, per)
                if c == "A4000":
                    ib = IB[f"hc{hc} | {per} | coupon | budget L4000 M1500"]
                    mine = dict(med=round(float(np.median(tot))), p10=round(float(np.percentile(tot, 10))), p25=round(float(np.percentile(tot, 25))), Pneg=round(100 * float((tot < 0).mean()), 1), worst=round(float(tot.min())))
                    print(f"A4000 vs integ_budget hc{hc} {per}: mio {mine} | integ {ib} | igual {mine == ib}")
            print(f"{time.time()-t0:5.0f}s hc{hc} {per} reproducido", flush=True)
    print(f"plan bootstrap: max |dif| contra exp05_budget.json = {worst:.3g}, metricas con dif > 1e-9: {nd}")
    # pareado
    pw = 0.0
    for (c, hc, per), v in NET.items():
        if c != E5.INC:
            g = E3.paired(v, NET[(E5.INC, hc, per)]); j = X["pareado"][f"plan {c} vs {E5.INC} | hc{hc} | {per}"]
            pw = max(pw, abs(g["med"] - j["med"]), abs(g["P_loss5"] - j["P_loss5"]), abs(g["P_gain"] - j["P_gain"]))
    print("pareado: max |dif| =", pw)
    # sin vs T4000 camino por camino
    for hc in P.HC:
        for per in PER:
            a, b = FLOWS[("sin", hc, per)], FLOWS[("T4000", hc, per)]
            dif = np.nonzero(np.any(a[0] != b[0], axis=1) | (a[1] != b[1]))[0]
            print(f"sin vs T4000 hc{hc} {per}: caminos con flujo o n.o de evals distinto: {len(dif)}", (dif[:5].tolist() if len(dif) else ""),
                  ("" if not len(dif) else f"| neto/mes sin {NET[('sin',hc,per)][dif[0]]:.2f} T4000 {NET[('T4000',hc,per)][dif[0]]:.2f} | evals {a[1][dif[0]]} vs {b[1][dif[0]]} | dias con dif {np.nonzero(a[0][dif[0]] != b[0][dif[0]])[0].tolist()}"))
    return FLOWS

if __name__ == "__main__":
    main()
