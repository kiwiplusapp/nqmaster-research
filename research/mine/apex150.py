"""Apex Trader Funding 2026 (EOD) 150K per account slot, to add accounts beyond Lucid's 5-funded cap (Apex: up to 20 PAs per household).
Rules (damnpropfirms / quantvps, Oct-2026): eval target $9,000, EOD trailing DD $4,000 (locks at +100), soft DLL $2,000, no eval consistency;
PA: EOD trailing $4,000 (safety net start + 4,100), soft DLL $2,000, payout after 5 qualifying days (>= $250) with no single day >= 50% of
the cycle profit, withdraw above the safety net up to the cap ladder 2,500 / 3,000 / 3,000 / 3,000 / 4,000 / 5,000, min $500, 100% split,
6 payouts then the slot restarts. Fees: eval $150 (discounted 150K EOD, assumption) + PA activation $119 on passing.
Same strategies (eval Ultra + night + gold Robust; PA gating tiers), contracts grid. -> apex150.csv"""
import sys, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
import prof_grid_lib
import lc_lib as L
from acct_life import CFG
from acct_policy import vec
from final_verify_lib import exits
@njit(cache=True)
def ev(LO, CL, s, n, T, D):
    eq = 0.0; pk = 0.0; d = s
    while d < n:
        thr = 100.0 if pk >= D + 100.0 else pk - D
        if eq + LO[d] <= thr: return -1, d
        eq += CL[d]
        if eq > pk: pk = eq
        if eq >= T: return 1, d
        d += 1
    return 0, n
@njit(cache=True)
def pa(flo, fcl, c1, c2, s, n, D, Q, CAPS):
    bal = 0.0; pk = 0.0; cash = 0.0; m = 0; qd = 0; cyc0 = 0.0; best = 0.0; d = s
    while d < n:
        thr = 100.0 if pk >= D + 100.0 else pk - D
        cu = bal - thr; j = 0 if cu < c1 else (1 if cu < c2 else 2)
        if bal + flo[j, d] <= thr: return cash, m, -1, d
        c = fcl[j, d]; bal += c
        if bal > pk: pk = bal
        if c >= Q: qd += 1
        if c > best: best = c
        cp = bal - cyc0
        if qd >= 5 and cp > 0 and best < 0.5 * cp:
            amt = min(CAPS[m], bal - (D + 100.0))
            if amt >= 500.0:
                bal -= amt; cash += amt; m += 1; qd = 0; cyc0 = bal; best = 0.0
                if m == 6: return cash, m, 1, d
        d += 1
    return cash, m, 0, n
@njit(cache=True)
def life(LO, CL, flo, fcl, c1, c2, T, D, Q, CAPS, FEE, ACT, H, step, out):
    nd = LO.shape[0]; r = 0
    for s in range(0, nd - H, step):
        end = s + H; i = s; cash = 0.0; fees = 0.0; nev = 0; npass = 0; nb = 0; npay = 0
        while i < end:
            fees += FEE; nev += 1
            res, j = ev(LO, CL, i, end, T, D)
            if res != 1: i = j + 1; continue
            npass += 1; fees += ACT
            c, m, st, j2 = pa(flo, fcl, c1, c2, j + 1, end, D, Q, CAPS)
            cash += c; npay += m; nb += st == -1; i = j2 + 1
        out[r, 0] = cash - fees; out[r, 1] = nev; out[r, 2] = npass; out[r, 3] = nb; out[r, 4] = npay; r += 1
    return r
if __name__ == "__main__":
    NIGHT = ["N:NF05", "N:LF06", "N:LF0430"]
    E = L.define("AP_E", CFG["UA_FULL_GR"] + NIGHT); F = tuple(L.define("AP_" + x, CFG[x] + NIGHT) for x in ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR"))
    T, D, Q, FEE, ACT = 9000.0, 4000.0, 250.0, 150.0, 119.0; CAPS = np.array([2500.0, 3000.0, 3000.0, 3000.0, 4000.0, 5000.0]); sc = D / 2000.0
    rows = []
    for per in ("IS", "C24", "REAL"):
        ce = exits(per, E); cf = np.array([exits(per, c) for c in F])
        for ek, fk in ((4, 3), (5, 3), (6, 3), (5, 2), (5, 4)):
            evv = vec(per, E, 2000.0 / ek, 0.0); fv = [vec(per, c, 2000.0 / fk, 0.0) for c in F]; nd = len(evv[0])
            for test in ("historia", "costo +1 tick", "Monte Carlo"):
                cst = test == "costo +1 tick"
                LO = ek * (evv[0] - (ce if cst else 0)); CL = ek * (evv[1] - (ce if cst else 0))
                f0 = fk * (np.array([v[0] for v in fv]) - (cf if cst else 0)); f1 = fk * (np.array([v[1] for v in fv]) - (cf if cst else 0))
                args = (750.0 * sc, 1500.0 * sc, T, D, Q, CAPS, FEE, ACT)
                if test != "Monte Carlo":
                    out = np.zeros((1000, 6)); m = life(LO, CL, f0, f1, *args, 252, 3, out); Lr = out[:m]
                else:
                    o1 = np.zeros((2, 6)); Lr = []
                    for q in range(1000):
                        idx = np.concatenate([np.arange(s, s + 10) % nd for s in np.random.default_rng(31 + q).integers(0, nd, 27)])[:253]
                        life(LO[idx].copy(), CL[idx].copy(), f0[:, idx].copy(), f1[:, idx].copy(), *args, 252, 252, o1); Lr.append(o1[0].copy())
                    Lr = np.array(Lr)
                rows.append(dict(per=per, ek=ek, fk=fk, test=test, mo=Lr[:, 0].mean() / 12, ploss=100 * (Lr[:, 0] < 0).mean(), evals=Lr[:, 1].mean(), passes=Lr[:, 2].mean(), pabust=Lr[:, 3].mean(), payouts=Lr[:, 4].mean()))
        print(per, flush=True)
    R = pd.DataFrame(rows); R.to_csv("apex150.csv", index=False); pd.set_option("display.width", 250)
    S = R.groupby(["ek", "fk"]).agg(mean9=("mo", "mean"), min9=("mo", "min"), ploss=("ploss", "max"), evals=("evals", "mean"), pabust=("pabust", "mean"), payouts=("payouts", "mean"))
    S["pass_rate"] = (100 * R.groupby(["ek", "fk"]).passes.sum() / R.groupby(["ek", "fk"]).evals.sum()).values
    print(S.round(1).sort_values("mean9", ascending=False).to_string())
