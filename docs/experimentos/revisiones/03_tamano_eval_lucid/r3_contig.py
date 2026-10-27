import sys, os, json, numpy as np
sys.path.insert(0, "/home/user/nqmaster-research/research/mine"); os.chdir("/home/user/nqmaster-research/research/mine")
import prop_wf as P, objective as O
days, M, FU, PER = O.setup(); n = len(days); idx = np.arange(n, dtype=np.int64); H = O.H; L = H + 25; F = P.FIRMS["LucidFlex150K"]
J = json.load(open("exp03_eval_size.json"))
for hc in (0.0, 0.35):
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    for per, ii in PER.items():
        stp = np.arange(ii[0], ii[-1] + 2 - L, 5); tot = {}
        for k in (5, 6):
            A = dict(O.seat_args(FU, hc, "L150 6c/3c", Hm)); A["ep"] = P.ep_of(F, (0, k, k, 0, 0, 0, 0)); t = np.zeros(len(stp))
            for b, s0 in enumerate(stp):
                for s in range(5):     # MFFU identico entre k: se omite (se cancela en la diferencia pareada)
                    f = np.zeros(n); mm = np.zeros(n); ev = np.zeros((O.MAXEV, 5)); O.run_seat(M, A, idx, int(s0) + 5 * s, H, f, mm, ev); t[b] += f.sum() / 12.0
            tot[k] = t
        g = tot[5] - tot[6]; mb = np.median(tot[6]); full6 = J["plan_contiguo"][f"plan k6 | hc{hc} | {per}"]["med_mes"]
        print(f"contiguo hc{hc} {per} n={len(stp)}: L150x5 k5-k6 por inicio: mediana {np.median(g):+.0f} $/mes ({100*np.median(g)/abs(full6):+.1f}% de la mediana del plan 6c {full6:.0f}); "
              f"P(k5>k6) {(g>0).mean():.2f}; P(k5<k6) {(g<0).mean():.2f}; P(perder >5% de la mediana del plan) {(g < -0.05*abs(full6)).mean():.2f}; media {g.mean():+.0f}")
# reglas con M5 relajado (lectura de "si relaja M5" del informe)
KS = range(1, 7)
for nm, thr in (("M5 <= 10 (plan)", 10), ("M5 <= 11", 11), ("M5 <= 12", 12), ("sin M5", 1e9)):
    sc = {}
    for k in KS:
        tot = 0
        for hc in ("0.0", "0.35"):
            r = J["plan"][f"plan k{k} | hc{hc} | T1"]; c = dict(r["cumple"]); c["dias_aprobar"] = r["dias_aprobar"] <= thr; tot += sum(c.values())
        sc[k] = (tot, J["plan"][f"plan k{k} | hc0.35 | T1"]["med_mes"])
    w = max(KS, key=lambda k: sc[k]); print(f"{nm:16s}: " + " ".join(f"k{k}={sc[k][0]}" for k in KS) + f" -> k* = {w}")
# fees: diferencia de evals compradas por anio (plan) k6 - k5, y de evals perdidas
for hc in ("0.0", "0.35"):
    for per in ("T1", "T2"):
        a = J["plan"][f"plan k5 | hc{hc} | {per}"]; b = J["plan"][f"plan k6 | hc{hc} | {per}"]
        print(f"hc{hc} {per}: evals compradas/anio k6-k5 = {b['evals_anio']-a['evals_anio']:.2f} -> ${215*(b['evals_anio']-a['evals_anio']):.0f}; evals perdidas/anio k6-k5 = {12*(b['evals_perdidas_mes']-a['evals_perdidas_mes']):.2f} -> ${215*12*(b['evals_perdidas_mes']-a['evals_perdidas_mes']):.0f}; "
              f"evals perd. rel {100*(a['evals_perdidas_mes']/b['evals_perdidas_mes']-1):+.1f}%; aprob {a['aprobacion']-b['aprobacion']:+.1f} pts; neg60 {a['neg60']-b['neg60']:+.2f} pts")
