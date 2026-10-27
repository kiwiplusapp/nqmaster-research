import json, numpy as np
SP = "/tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad/r3/"
J = json.load(open("/home/user/nqmaster-research/research/mine/exp03_eval_size.json")); Z = np.load(SP + "r3_base_seed.npz")
names = ["med_mes", "p10_mes", "neg60", "evals_perdidas_mes", "aprobacion", "dias_aprobar", "dias_aprobar_p75", "evals_anio"]; mx = 0; cu_bad = 0; nc = 0
for k in range(1, 7):
    for hc in (0.0, 0.35):
        for per in ("T1", "T2"):
            m = Z[f"plan_k{k}_hc{hc}_{per}_m"]; r = J["plan"][f"plan k{k} | hc{hc} | {per}"]; nc += 1
            mx = max(mx, max(abs(m[i] - r[q]) for i, q in enumerate(names)))
            if [bool(x) for x in m[8:]] != list(r["cumple"].values()): cu_bad += 1
smx = 0; ns = 0
for k in range(1, 7):
    for hc in (0.0, 0.35, 1.0):
        for per in ("T1", "T2"):
            a = Z[f"seat_k{k}_hc{hc}_{per}"]; r = J["asiento"][f"L150 {k}c/3c | hc{hc} | {per}"]; ns += 1
            smx = max(smx, abs(np.median(a) - r["med_mes"]), abs(np.percentile(a, 10) - r["p10_mes"]))
print(f"plan: {nc} celdas, max|dif| en 8 metricas {mx:.2g}, celdas con 'cumple' distinto {cu_bad}; asiento: {ns} celdas, max|dif| mediana/p10 {smx:.2g}")
