"""r4_paired.py: empates exactos en la ganancia pareada, P(g<0), lecturas alternativas de la regla y signos contiguo vs bootstrap."""
import json, pickle, numpy as np
SP = "/tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad/"
D = pickle.load(open(SP + "r4_net.pkl", "rb")); NET = D["NET"]; J = json.load(open("/home/user/nqmaster-research/research/mine/exp04_payout_x.json"))
XS = (4600, 5000, 6000, 7000, 8000, 10000, 12000); INC = 6000
print("== ganancia pareada: empates exactos (|g| < 1e-6), P(g>0), P(g<0), mediana, mediana condicionada a g != 0 ==")
for u in ("plan", "seat"):
    for hc in (0.0, 0.35):
        for per in ("T1", "T2"):
            b = NET[(u, INC, hc, per)]
            for X in XS:
                if X == INC: continue
                a = NET[(u, X, hc, per)]; g = a - b; z = np.abs(g) < 1e-6; jj = J["pareado"][f"{u} X{X} vs X{INC} | hc{hc} | {per}"]
                gn = g[~z]
                print(f"{u:4s} hc{hc:<4} {per} X{X:<5} ties {100*z.mean():5.1f}%  P>0 {np.mean(g>0):.2f} P<0 {np.mean(g<0):.2f}  med {np.median(g):+8.1f} (json {jj['med']:+8.1f}) rel {jj['rel']*100:+5.1f}%  med|g!=0 {np.median(gn) if len(gn) else 0:+8.1f}  P(g>0|g!=0) {np.mean(gn>0) if len(gn) else 0:.2f}  P_loss5 {jj['P_loss5']:.2f}  ci90 [{jj['ci90'][0]:+.0f},{jj['ci90'][1]:+.0f}]")
print()
print("== tamano de la diferencia de 'exactamente 0': cuantos caminos del plan hc0.35 T1 tienen todos los asientos L150 sin diferencia ==")
for hc in (0.0, 0.35):
    for per in ("T1", "T2"):
        b = NET[("plan", INC, hc, per)]; m = NET[("mffu", hc, per)]
        print(f"hc{hc} {per}: plan L150 parte (tot - mffu) mediana X6000 {np.median(b-m):.0f}; P(L150 parte del plan <= 0) {np.mean(b-m <= 0):.2f}")
print()
print("== regla: puntajes T1 y lecturas alternativas ==")
for X in XS:
    a = J["plan"][f"plan X{X} | hc0.0 | T1"]; c = J["plan"][f"plan X{X} | hc0.35 | T1"]
    sa = sum(a["cumple"].values()); sc = sum(c["cumple"].values())
    a2 = J["plan"][f"plan X{X} | hc0.0 | T2"]; c2 = J["plan"][f"plan X{X} | hc0.35 | T2"]
    g1 = J["pareado"].get(f"plan X{X} vs X{INC} | hc0.35 | T1"); g0 = J["pareado"].get(f"plan X{X} vs X{INC} | hc0.0 | T1")
    print(f"X{X:<5} T1 score {sa}+{sc}={sa+sc}  med hc0 {a['med_mes']:8.1f} med hc0.35 {c['med_mes']:8.1f} p10 hc0.35 {c['p10_mes']:7.1f} neg60 hc0.35 {c['neg60']:5.2f}  | T2 score {sum(a2['cumple'].values())}+{sum(c2['cumple'].values())}"
          + (f"  | pareado T1 hc0.35 P_gain {g1['P_gain']:.2f} med {g1['med']:+.1f}; hc0 P_gain {g0['P_gain']:.2f}" if g1 else ""))
print("max P_gain T1 hc0.35 entre X != 6000:", max(J["pareado"][f"plan X{X} vs X{INC} | hc0.35 | T1"]["P_gain"] for X in XS if X != INC))
print("max P_gain T1 hc0   entre X != 6000:", max(J["pareado"][f"plan X{X} vs X{INC} | hc0.0 | T1"]["P_gain"] for X in XS if X != INC))
# alternativa: P(g>=0) en vez de P(g>0)
for X in XS:
    if X == INC: continue
    g = NET[("plan", X, 0.35, "T1")] - NET[("plan", INC, 0.35, "T1")]
    print(f"  X{X} T1 hc0.35 P(g>=0) {np.mean(g>=-1e-6):.2f}")
# bootstrap del desempate: con que frecuencia 6000 tiene la mayor mediana hc0.35 T1 al remuestrear caminos (mismos indices para todos)
rng = np.random.default_rng(1); T = np.array([NET[("plan", X, 0.35, "T1")] for X in XS]); win = np.zeros(len(XS))
for _ in range(2000):
    ii = rng.integers(0, T.shape[1], T.shape[1]); win[np.argmax(np.median(T[:, ii], axis=1))] += 1
print("bootstrap del desempate (mayor mediana hc0.35 T1, 2000 remuestreos):", {X: round(w / 2000, 3) for X, w in zip(XS, win)})
print()
print("== signos contiguo vs bootstrap (diferencia X - 6000) ==")
for hc in ("0.0", "0.35"):
    for per in ("T1", "T2"):
        for q in ("med_mes", "p10_mes", "neg60", "evals_perdidas_mes", "cuentas_perdidas_mes", "retiros_anio"):
            row = []
            for X in XS:
                if X == INC: continue
                db = J["plan"][f"plan X{X} | hc{hc} | {per}"][q] - J["plan"][f"plan X{INC} | hc{hc} | {per}"][q]
                dc = J["plan_contiguo"][f"plan X{X} | hc{hc} | {per}"][q] - J["plan_contiguo"][f"plan X{INC} | hc{hc} | {per}"][q]
                flip = "*" if np.sign(db) != np.sign(dc) and abs(dc) > 1e-9 and abs(db) > 1e-9 else " "
                row.append(f"X{X}: {db:+8.2f}/{dc:+8.2f}{flip}")
            print(f"hc{hc:<4} {per} {q:22s} " + "  ".join(row))
print()
print("== cumple contiguo (plan) ==")
for hc in ("0.0", "0.35"):
    for per in ("T1", "T2"):
        print(f"hc{hc} {per}: " + "  ".join(f"X{X}:{sum(J['plan_contiguo'][f'plan X{X} | hc{hc} | {per}']['cumple'].values())}" + "".join("+" if v else "-" for v in J['plan_contiguo'][f'plan X{X} | hc{hc} | {per}']['cumple'].values()) for X in XS))
print("== cumple bootstrap (plan) ==")
for hc in ("0.0", "0.35"):
    for per in ("T1", "T2"):
        print(f"hc{hc} {per}: " + "  ".join(f"X{X}:{sum(J['plan'][f'plan X{X} | hc{hc} | {per}']['cumple'].values())}" + "".join("+" if v else "-" for v in J['plan'][f'plan X{X} | hc{hc} | {per}']['cumple'].values()) for X in XS))
print()
print("== ganancia pareada sobre historia contigua (plan; mismos inicios) ==")
for hc in (0.0, 0.35):
    for per in ("T1", "T2"):
        b = NET[("pcont", INC, hc, per)]
        print(f"hc{hc} {per} n {len(b)}: " + "  ".join(f"X{X}: med {np.median(NET[('pcont', X, hc, per)] - b):+7.0f} P>0 {np.mean(NET[('pcont', X, hc, per)] - b > 0):.2f} P<0 {np.mean(NET[('pcont', X, hc, per)] - b < 0):.2f}" for X in XS if X != INC))
