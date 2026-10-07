"""5 slots (Lucid cap: 5 funded accounts per household) on the same market path, eval starts 5 days apart: 150K (eval 7c / funded 3c
and eval 6c / funded 3c) vs 50K (final 2c / 2c). 1,500 bootstrap years per period. Also the max simultaneous micro contracts per
account (eval and funded) to check Lucid's limits (150K eval 100 micros, funded start 40). -> multi150.csv"""
import sys, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
from acct_bigger import ev_q, ACC
from acct_policy import vec
from acct_size import fu_g
from acct_lab import Z
from acct_life import CFG
import prof_grid_lib
@njit(cache=True)
def slot(LO, CL, flo, fcl, c1, c2, X, T, D, Q, CAP, FEE, H):
    i = 0; run = 0.0; worst = 0.0
    while i < H:
        run -= FEE
        if run < worst: worst = run
        res, j = ev_q(LO, CL, i, H, T, D)
        if res != 1: i = j + 1; continue
        c, m, st, j2 = fu_g(flo, fcl, 1.0, c1, c2, j + 1, H, X, D, Q, CAP)
        run += c; i = j2 + 1
    return run, worst
SET = {"150K eval 7c / fondeada 3c": ("150K", 7, 3), "150K eval 6c / fondeada 3c": ("150K", 6, 3), "50K eval 2c / fondeada 2c (final)": ("50K", 2, 2)}
rows = []
for per in ("IS", "C24", "REAL"):
    FC = ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR"); fv = [vec(per, c, 0.0, 0.0) for c in FC]
    for nm, (acc, ek, fk) in SET.items():
        T, D, Q, CAP, FEE = ACC[acc]; sc = D / 2000.0
        ev = vec(per, "UA_FULL_GR", 0.0, 0.4667 * T / ek); nd = len(ev[0]); LO = ek * ev[0]; CL = ek * ev[1]
        F0 = fk * np.array([v[0] for v in fv]); F1 = fk * np.array([v[1] for v in fv])
        rng = np.random.default_rng(7); H = 252; tot = []; wor = []
        for b in range(1500):
            idx = np.concatenate([np.arange(s, s + 10) % nd for s in rng.integers(0, nd, (H + 25) // 10 + 2)])[:H + 26]
            r = [slot(LO[idx[5 * a: 5 * a + H + 1]].copy(), CL[idx[5 * a: 5 * a + H + 1]].copy(), F0[:, idx[5 * a: 5 * a + H + 1]].copy(), F1[:, idx[5 * a: 5 * a + H + 1]].copy(),
                      750.0 * sc, 1500.0 * sc, 2.0 * CAP, T, D, Q, CAP, FEE, H) for a in range(5)]
            tot.append(sum(x[0] for x in r)); wor.append(sum(x[1] for x in r))
        a = np.array(tot); w = np.array(wor)
        rows.append(dict(per=per, plan=nm, mes_prom=round(a.mean() / 12), mes_p10=round(np.percentile(a, 10) / 12), mes_p90=round(np.percentile(a, 90) / 12),
                         P_anio_negativo=round(100 * (a < 0).mean(), 1), capital_p50=round(-np.median(w)), capital_p90=round(-np.percentile(w, 10))))
    # max simultaneous micro contracts at 1 contract per module (NQ + gold), from the dense position grids is not stored -> use trade lists
    print(per, flush=True)
R = pd.DataFrame(rows); R.to_csv("multi150.csv", index=False); pd.set_option("display.width", 220); print(R.to_string(index=False))
