"""Whole household plan: 5 LucidFlex 150K (eval 6c / funded 3c) + N Apex 150K EOD (eval 5c / PA 2c), every account on the same market path
(same strategies -> correlated), starts staggered 5 days. 1,500 bootstrap years per period. Monthly income of the whole set, bad year (p10),
P(negative year), cash needed up front (eval fees before payouts, conservative). -> combo_sim.csv"""
import sys, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
import prof_grid_lib
import lc_lib as LL
from acct_life import CFG
from acct_policy import vec
from acct_bigger import ACC
from multi150 import slot as lucid_slot
from apex150 import ev as apex_ev, pa as apex_pa
@njit(cache=True)
def apex_slot(LO, CL, flo, fcl, c1, c2, T, D, Q, CAPS, FEE, ACT, H):
    i = 0; run = 0.0; worst = 0.0
    while i < H:
        run -= FEE
        if run < worst: worst = run
        res, j = apex_ev(LO, CL, i, H, T, D)
        if res != 1: i = j + 1; continue
        run -= ACT
        if run < worst: worst = run
        c, m, st, j2 = apex_pa(flo, fcl, c1, c2, j + 1, H, D, Q, CAPS)
        run += c; i = j2 + 1
    return run, worst
NIGHT = ["N:NF05", "N:LF06", "N:LF0430"]
E = LL.define("CB_E", CFG["UA_FULL_GR"] + NIGHT); F = tuple(LL.define("CB_" + x, CFG[x] + NIGHT) for x in ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR"))
CAPS = np.array([2500.0, 3000.0, 3000.0, 3000.0, 4000.0, 5000.0])
PLANS = {"5 Lucid 150K": (5, 0), "5 Lucid + 5 Apex 150K": (5, 5), "5 Lucid + 10 Apex 150K": (5, 10), "5 Lucid + 20 Apex 150K": (5, 20)}
rows = []
for per in ("IS", "C24", "REAL"):
    T, D, Q, CAP, FEE = ACC["150K"]
    evL = vec(per, E, 0.0, 0.4667 * T / 6); fvL = [vec(per, c, 0.0, 0.0) for c in F]; nd = len(evL[0])
    LOl = 6 * evL[0]; CLl = 6 * evL[1]; F0l = 3 * np.array([v[0] for v in fvL]); F1l = 3 * np.array([v[1] for v in fvL])
    evA = vec(per, E, 2000.0 / 5, 0.0); fvA = [vec(per, c, 2000.0 / 2, 0.0) for c in F]
    LOa = 5 * evA[0]; CLa = 5 * evA[1]; F0a = 2 * np.array([v[0] for v in fvA]); F1a = 2 * np.array([v[1] for v in fvA])
    rng = np.random.default_rng(7); H = 252; NA = 25; tot = {p: [] for p in PLANS}; wor = {p: [] for p in PLANS}
    for b in range(1500):
        idx = np.concatenate([np.arange(s, s + 10) % nd for s in rng.integers(0, nd, (H + 5 * NA) // 10 + 2)])[:H + 5 * NA + 1]
        lr = []
        for a in range(5):
            o = idx[5 * a: 5 * a + H + 1]
            lr.append(lucid_slot(LOl[o].copy(), CLl[o].copy(), F0l[:, o].copy(), F1l[:, o].copy(), 1687.5, 3375.0, 6000.0, T, D, Q, CAP, FEE, H))
        ar = []
        for a in range(20):
            o = idx[5 * a + 2: 5 * a + 2 + H + 1]
            ar.append(apex_slot(LOa[o].copy(), CLa[o].copy(), F0a[:, o].copy(), F1a[:, o].copy(), 1500.0, 3000.0, 9000.0, 4000.0, 250.0, CAPS, 150.0, 119.0, H))
        for p, (nl, na) in PLANS.items():
            tot[p].append(sum(x[0] for x in lr[:nl]) + sum(x[0] for x in ar[:na])); wor[p].append(sum(x[1] for x in lr[:nl]) + sum(x[1] for x in ar[:na]))
    for p in PLANS:
        a = np.array(tot[p]); w = np.array(wor[p])
        rows.append(dict(per=per, plan=p, mes_prom=round(a.mean() / 12), mes_p10=round(np.percentile(a, 10) / 12), mes_p90=round(np.percentile(a, 90) / 12),
                         P_anio_negativo=round(100 * (a < 0).mean(), 1), capital_p50=round(-np.median(w)), capital_p90=round(-np.percentile(w, 10))))
    print(per, flush=True)
R = pd.DataFrame(rows); R.to_csv("combo_sim.csv", index=False); pd.set_option("display.width", 220); print(R.to_string(index=False))
