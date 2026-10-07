"""LucidDirect 150K (no evaluation, $836): MLL $5,000 EOD trailing, locks at start +100 once the EOD peak reaches +5,100; soft DLL $3,000
(day lockout); payout cycle needs cycle profit >= $9,000 (first) / $4,500 (later) AND best day <= 20% of the cycle profit; withdraw
everything above the buffer (start + 5,100) up to the cap ($3,000 payouts 1-3, $3,500 payouts 4-5), min $500, 90% split; 5 payouts, then
the seat buys a new account (live review). Busted -> buy a new one. Same strategies (Ultra + night + gold Robust funded tiers by cushion),
k contracts, optional account daily profit stop G (keeps the best day small for the 20% rule). History / +1 tick / 1,000 bootstrap
years, $/month per seat vs LucidFlex 150K (6c/3c, $2,168). -> direct_sim.csv"""
import sys, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
import prof_grid_lib
import lc_lib as L
from acct_life import CFG
from acct_policy import vec
from final_verify_lib import exits
@njit(cache=True)
def seat(flo, fcl, c1, c2, H, FEE, MLL, LOCK, GOAL1, GOAL2, CAP1, CAP2, CONS):
    cash = 0.0; d = 0; nacc = 0; nbust = 0; npay = 0
    while d < H:
        cash -= FEE; nacc += 1
        bal = 0.0; pk = 0.0; cyc0 = 0.0; best = 0.0; m = 0; alive = True
        while d < H and alive:
            thr = 100.0 if pk >= LOCK else pk - MLL
            cu = bal - thr; j = 0 if cu < c1 else (1 if cu < c2 else 2)
            if bal + flo[j, d] <= thr: alive = False; nbust += 1; d += 1; break
            c = fcl[j, d]; bal += c
            if bal > pk: pk = bal
            if c > best: best = c
            cp = bal - cyc0; goal = GOAL1 if m == 0 else GOAL2
            if cp >= goal and best <= CONS * cp:
                amt = min(CAP1 if m < 3 else CAP2, bal - LOCK)
                if amt >= 500.0:
                    cash += 0.9 * amt; bal -= amt; cyc0 = bal; best = 0.0; m += 1; npay += 1
                    if m == 5: alive = False; d += 1; break
            d += 1
    return cash, nacc, nbust, npay
NIGHT = ["N:NF05", "N:LF06", "N:LF0430"]
F = tuple(L.define("DR_" + x, CFG[x] + NIGHT) for x in ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR"))
rows = []
for per in ("IS", "C24", "REAL"):
    cf = np.array([exits(per, c) for c in F])
    for k in (3, 4, 5):
        for G in (0.0, 900.0, 1200.0, 1800.0):
            fv = [vec(per, c, 3000.0 / k, G / k if G > 0 else 0.0) for c in F]; nd = len(fv[0][0])
            for test in ("historia", "costo +1 tick", "Monte Carlo"):
                cst = test == "costo +1 tick"
                f0 = k * (np.array([v[0] for v in fv]) - (cf if cst else 0)); f1 = k * (np.array([v[1] for v in fv]) - (cf if cst else 0))
                args = (1875.0, 3750.0, 252, 836.0, 5000.0, 5100.0, 9000.0, 4500.0, 3000.0, 3500.0, 0.2)
                if test != "Monte Carlo":
                    res = [seat(f0[:, s:s + 253].copy(), f1[:, s:s + 253].copy(), *args) for s in range(0, nd - 253, 3)]
                else:
                    res = []
                    for q in range(1000):
                        idx = np.concatenate([np.arange(s, s + 10) % nd for s in np.random.default_rng(31 + q).integers(0, nd, 27)])[:253]
                        res.append(seat(f0[:, idx].copy(), f1[:, idx].copy(), *args))
                o = np.array(res)
                rows.append(dict(per=per, k=k, G=G, test=test, mo=o[:, 0].mean() / 12, ploss=100 * (o[:, 0] < 0).mean(), cuentas=o[:, 1].mean(), quemadas=o[:, 2].mean(), cobros=o[:, 3].mean()))
    print(per, flush=True)
R = pd.DataFrame(rows); R.to_csv("direct_sim.csv", index=False); pd.set_option("display.width", 250)
S = R.groupby(["k", "G"]).agg(mean9=("mo", "mean"), min9=("mo", "min"), ploss=("ploss", "max"), cuentas=("cuentas", "mean"), quemadas=("quemadas", "mean"), cobros=("cobros", "mean")).round(1)
print(S.sort_values("mean9", ascending=False).to_string()); print("LucidFlex 150K 6c/3c reference: mean9 2168, min9 1981")
