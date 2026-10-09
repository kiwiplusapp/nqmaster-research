"""Robustness of funded22.py for the main plans: +1 tick per side on every trade, and a block bootstrap (20-day blocks,
400 synthetic 2-year paths per period, same paths for every plan). -> funded22_boot.csv"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
from funded22 import PROF, ACC, mats, window, W
from final_verify_lib import exits
PLANS = [("Ultra+noche+oro Robust", "Pro 50K", 4), ("Ultra+noche+oro Robust", "Pro 50K", 3), ("Ultra+noche+oro Robust", "Pro 25K", 2),
         ("Ultra+noche+oro Robust", "Flex 50K", 2), ("Ultra+noche+oro Robust", "Flex 50K", 1)]
if __name__ == "__main__":
    rows = []
    for per in ("IS", "C24", "REAL"):
        rng = np.random.default_rng(7); nd = None; IDX = None
        for pn, an, k in PLANS:
            T, D, cons, fee, kmax = ACC[an]; cfg = PROF[pn]; G = 0.4667 * T if cons > 0 else 0.0
            LO, CL = mats(per, cfg, G, kmax); nd = LO.shape[1]
            if IDX is None: IDX = [np.concatenate([np.arange(s, s + 20) % nd for s in rng.integers(0, nd, 26)])[:504] for _ in range(400)]
            ce = exits(per, cfg); LOc = LO.copy(); CLc = CL.copy()
            for kk in range(1, kmax + 1): LOc[kk] -= kk * ce; CLc[kk] -= kk * ce
            for test, (A, B) in (("historia", (LO, CL)), ("costo +1 tick", (LOc, CLc))):
                out = np.zeros((nd, 4)); m = window(A, B, T, D, cons, k, W, out); o = out[:m]
                rows.append(dict(per=per, plan=f"{an} {k}c", test=test, fondeada=100 * o[:, 1].mean(), intentos=o[:, 2].mean()))
            bs = []
            for idx in IDX:
                out = np.zeros((504, 4)); m = window(LO[:, idx].copy(), CL[:, idx].copy(), T, D, cons, k, W, out); bs.append(100 * out[:m, 1].mean())
            bs = np.array(bs)
            rows.append(dict(per=per, plan=f"{an} {k}c", test="bootstrap mediana", fondeada=np.median(bs)))
            rows.append(dict(per=per, plan=f"{an} {k}c", test="bootstrap peor 10%", fondeada=np.percentile(bs, 10)))
        print(per, flush=True)
    R = pd.DataFrame(rows); R.to_csv("funded22_boot.csv", index=False); pd.set_option("display.width", 220)
    print(R.pivot_table(index="plan", columns=["test", "per"], values="fondeada").round(1).to_string())
