"""5 Lucid slots on the same market path (eval starts 5 days apart), with and without the NF05 overnight fade, 150K (6c/3c) and
50K (2c/2c). 1,500 bootstrap years per period. -> multi150b.csv"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
import prof_grid_lib
import lc_lib as LL
from acct_life import CFG
from acct_policy import vec
from acct_bigger import ACC
from multi150 import slot
E_NF = LL.define("UA_FULL_GR+NF05", CFG["UA_FULL_GR"] + ["N:NF05"])
F_NF = tuple(LL.define(x + "+NF05", CFG[x] + ["N:NF05"]) for x in ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR"))
F_0 = ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR")
SET = {"150K 6c/3c + NF05": ("150K", 6, 3, True), "150K 6c/3c": ("150K", 6, 3, False), "50K 2c/2c + NF05": ("50K", 2, 2, True), "50K 2c/2c": ("50K", 2, 2, False)}
rows = []
for per in ("IS", "C24", "REAL"):
    for nm, (acc, ek, fk, nf) in SET.items():
        T, D, Q, CAP, FEE = ACC[acc]; sc = D / 2000.0
        EC = E_NF if nf else "UA_FULL_GR"; FC = F_NF if nf else F_0
        ev = vec(per, EC, 0.0, 0.4667 * T / ek); nd = len(ev[0]); LO = ek * ev[0]; CL = ek * ev[1]
        fv = [vec(per, c, 0.0, 0.0) for c in FC]; F0 = fk * np.array([v[0] for v in fv]); F1 = fk * np.array([v[1] for v in fv])
        rng = np.random.default_rng(7); H = 252; tot = []; wor = []
        for b in range(1500):
            idx = np.concatenate([np.arange(s, s + 10) % nd for s in rng.integers(0, nd, (H + 25) // 10 + 2)])[:H + 26]
            r = []
            for a in range(5):
                o = idx[5 * a: 5 * a + H + 1]
                r.append(slot(LO[o].copy(), CL[o].copy(), F0[:, o].copy(), F1[:, o].copy(), 750.0 * sc, 1500.0 * sc, 2.0 * CAP, T, D, Q, CAP, FEE, H))
            tot.append(sum(x[0] for x in r)); wor.append(sum(x[1] for x in r))
        a = np.array(tot); w = np.array(wor)
        rows.append(dict(per=per, plan=nm, mes_prom=round(a.mean() / 12), mes_p10=round(np.percentile(a, 10) / 12), mes_p90=round(np.percentile(a, 90) / 12),
                         P_anio_negativo=round(100 * (a < 0).mean(), 1), capital_p50=round(-np.median(w)), capital_p90=round(-np.percentile(w, 10))))
    print(per, flush=True)
R = pd.DataFrame(rows); R.to_csv("multi150b.csv", index=False); pd.set_option("display.width", 220); print(R.to_string(index=False))
