import json, numpy as np
SP = "/tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad/r3/"
J = json.load(open("/home/user/nqmaster-research/research/mine/exp03_eval_size.json")); Z = np.load(SP + "r3_base_seed.npz")
for (k, hc, per) in ((5, 0.0, "T1"), (4, 0.0, "T2"), (5, 0.0, "T2"), (5, 0.35, "T2")):
    a = Z[f"plan_k{k}_hc{hc}_{per}"]; b = Z[f"plan_k6_hc{hc}_{per}"]; g = a - b; j = J["pareado"][f"plan k{k} vs k6 | hc{hc} | {per}"]
    print(k, hc, per, "caminos con |g|<1e-6:", int((np.abs(g) < 1e-6).sum()), " P_gain mio", (g > 0).mean(), "JSON", j["P_gain"], " P_gain con g>1e-6", (g > 1e-6).mean(),
          " P_loss5 mio", (g < -0.05 * abs(np.median(b))).mean(), "JSON", j["P_loss5"])
