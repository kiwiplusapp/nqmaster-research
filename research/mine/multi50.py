"""N Lucid Flex 50K slots run in parallel on the SAME market path (same strategies -> correlated), eval starts staggered 5 trading
days apart. Final profile (eval UA+GR fixed 2, profit stop 1400; funded UA gating + GR 2c, payout at $4k). 1,500 block-bootstrap
years per period. Reports yearly income of the whole set ($/month), percentiles, P(negative year) and the cash needed up front
(worst running balance of eval fees vs payouts received, payouts credited when the funded account ends: conservative). -> multi50.csv"""
import sys, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
import lc_lib as L
from acct_policy import vec
from acct_size import fu_g
FEE = L.FEE
@njit(cache=True)
def slot(LO, CL, k0, kdd, c1, dsw, kl, goal, flo, fcl, fk, fc1, fc2, X, H):
    end = H; i = 0; run = 0.0; worst = 0.0; nev = 0; npay = 0
    while i < end:
        run -= FEE; nev += 1
        if run < worst: worst = run
        res, j = L.ev_p(LO, CL, k0, kdd, c1, dsw, kl, goal, i, end)
        if res != 1: i = j + 1; continue
        c, m, st, j2 = fu_g(flo, fcl, fk, fc1, fc2, j + 1, end, X, L.D, L.Q, L.CAP)
        run += c; npay += m; i = j2 + 1
    return run, worst, nev, npay
rows = []
for per in ("IS", "C24", "REAL"):
    vs = {k: vec(per, "UA_FULL_GR", 0.0, 1400.0 / k) for k in (1, 2, 3)}; nd = len(vs[1][0])
    LO = np.zeros((4, nd)); CL = np.zeros((4, nd))
    for k in (1, 2, 3): LO[k] = k * vs[k][0]; CL[k] = k * vs[k][1]
    fv = [vec(per, c, 0.0, 0.0) for c in ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR")]; F0 = np.array([v[0] for v in fv]); F1 = np.array([v[1] for v in fv])
    rng = np.random.default_rng(7); H = 252; NMAX = 10; res = {n: [] for n in (1, 2, 3, 5, 10)}; wor = {n: [] for n in (1, 2, 3, 5, 10)}
    for b in range(1500):
        idx = np.concatenate([np.arange(s, s + 10) % nd for s in rng.integers(0, nd, (H + 5 * NMAX) // 10 + 2)])[:H + 5 * NMAX + 1]
        out = []
        for a in range(NMAX):
            o = idx[5 * a: 5 * a + H + 1]
            out.append(slot(LO[:, o].copy(), CL[:, o].copy(), *L.FIXED2, F0[:, o].copy(), F1[:, o].copy(), 2.0, 750.0, 1500.0, 4000.0, H))
        for n in res:
            res[n].append(sum(x[0] for x in out[:n])); wor[n].append(sum(x[1] for x in out[:n]))
    for n in res:
        a = np.array(res[n]); w = np.array(wor[n])
        rows.append(dict(per=per, cuentas=n, mes_prom=round(a.mean() / 12), mes_p10=round(np.percentile(a, 10) / 12), mes_p90=round(np.percentile(a, 90) / 12),
                         P_anio_negativo=round(100 * (a < 0).mean(), 1), capital_p50=round(-np.median(w)), capital_p90=round(-np.percentile(w, 10))))
    print(per, flush=True)
R = pd.DataFrame(rows); R.to_csv("multi50.csv", index=False); pd.set_option("display.width", 200); print(R.to_string(index=False))
