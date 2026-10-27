import numpy as np, json
SP = "/tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad/r3/"
J = json.load(open("/home/user/nqmaster-research/research/mine/exp03_eval_size.json")); KS = (1, 2, 3, 4, 5, 6)
cn = ["med_mes", "p10_mes", "neg60", "evals_perdidas_mes", "aprobacion", "dias_aprobar"]
for nm in ("r3_base_seed", "r3_seed11", "r3_seed22", "r3_seed33"):
    Z = np.load(SP + nm + ".npz"); m = lambda k, hc, per: Z[f"plan_k{k}_hc{hc}_{per}_m"]
    sc = {k: (int(m(k, 0.0, "T1")[8:].sum() + m(k, 0.35, "T1")[8:].sum()), float(m(k, 0.35, "T1")[0])) for k in KS}
    w = max(KS, key=lambda k: sc[k])
    s = f"{nm:13s} T1: " + " ".join(f"k{k}={sc[k][0]}" for k in KS) + f" | med hc0.35 k5 {sc[5][1]:.0f} k6 {sc[6][1]:.0f} | dias k5 hc0/hc0.35 {m(5,0.0,'T1')[5]:.0f}/{m(5,0.35,'T1')[5]:.0f} | k* = {w}"
    for k in (5, w):
        if k == 6: continue
        lost = [f"hc{hc}:{cn[i]}" for hc in (0.0, 0.35) for i in range(6) if m(6, hc, "T2")[8 + i] and not m(k, hc, "T2")[8 + i]]
        a = Z[f"plan_k{k}_hc0.35_T2"]; b = Z[f"plan_k6_hc0.35_T2"]; g = a - b; mb = np.median(b)
        okg = (np.median(g) > 0 and (g > 0).mean() >= 0.8) or (np.median(g) / abs(mb) >= -0.05 and (g < -0.05 * abs(mb)).mean() <= 0.2)
        s += f"\n      paso 2 para k{k}: pierde {lost}; pareado hc0.35 T2 rel {100*np.median(g)/abs(mb):+.1f}% P_gain {(g>0).mean():.2f} P_loss5 {(g < -0.05*abs(mb)).mean():.2f} -> ok {okg}"
    print(s)
