import json, numpy as np, sys
SP = "/tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad/r3/"
J = json.load(open("/home/user/nqmaster-research/research/mine/exp03_eval_size.json")); Z = np.load(SP + "r3_base_seed.npz")
def mine(a, b):   # escrito desde la definicion del plan, sin copiar exp03.paired
    g = a - b; m = np.median(b); thr = 0.05 * abs(m)
    return dict(med=np.median(g), lo=np.percentile(g, 5), hi=np.percentile(g, 95), P_gain=np.mean(g > 0), P_loss5=np.mean(g < -thr), rel=np.median(g) / abs(m))
mx = {}
for u in ("seat", "plan"):
    for hc in ((0.0, 0.35, 1.0) if u == "seat" else (0.0, 0.35)):
        for per in ("T1", "T2"):
            for k in (1, 2, 3, 4, 5):
                a = Z[f"{u}_k{k}_hc{hc}_{per}"]; b = Z[f"{u}_k6_hc{hc}_{per}"]; m = mine(a, b); j = J["pareado"][f"{u} k{k} vs k6 | hc{hc} | {per}"]
                d = max(abs(m["med"] - j["med"]), abs(m["lo"] - j["ci90"][0]), abs(m["hi"] - j["ci90"][1]), abs(m["P_gain"] - j["P_gain"]), abs(m["P_loss5"] - j["P_loss5"]), abs(m["rel"] - j["rel"]))
                mx[(u, hc, per, k)] = d
                # mediana del cociente vs cociente de medianas
                if u == "plan": print(f"{u} k{k} hc{hc} {per}: rel {m['rel']*100:+6.1f} %  (dif. de medianas {100*(np.median(a)/np.median(b)-1):+6.1f} %)  P_gain {m['P_gain']:.3f} P_loss5 {m['P_loss5']:.3f} ci90 [{m['lo']:+.0f},{m['hi']:+.0f}]  |dif vs JSON| {d:.2g}")
print("max |dif| entre mi pareado y el JSON:", max(mx.values()))
# mismo camino: correlacion entre candidato e incumbente (si fuesen caminos distintos seria ~0)
for hc in (0.0, 0.35):
    for per in ("T1", "T2"):
        print(f"corr(plan k5, plan k6) hc{hc} {per}: {np.corrcoef(Z[f'plan_k5_hc{hc}_{per}'], Z[f'plan_k6_hc{hc}_{per}'])[0,1]:.3f}; corr(k1,k6) {np.corrcoef(Z[f'plan_k1_hc{hc}_{per}'], Z[f'plan_k6_hc{hc}_{per}'])[0,1]:.3f}")
