"""Lucid allows only 5 funded accounts per household (10 accounts in total, $750K combined) -> income PER ACCOUNT decides once
more than 5 slots are wanted. LucidFlex rules (tradetanto / proptradingvibes, Oct-2026): 50K 3k/2k EOD MLL, $150 days, cap $2,000;
100K 6k/3k, $200, cap $2,500; 150K 9k/4.5k, $250, cap $3,000; MLL locks at start +100; payouts 50% of profit up to the cap, 90%,
5 payouts. Eval fees (coupon) 50K $105, 100K $215, 150K $285. Same strategies (eval UA+GR, funded UA gating + GR) scaled by k
contracts; eval profit stop = 0.467 x target (1400 of 3000); funded cushion tiers and payout threshold scaled with the MLL / cap.
Tests: history, +1 tick, 1,000 bootstrap years on IS / C24 / REAL. -> acct_bigger.csv"""
import sys, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
import prof_grid_lib
from acct_policy import vec
from acct_size import fu_g
from final_verify_lib import exits
@njit(cache=True)
def ev_q(LO, CL, s, n, T, D):
    eq = 0.0; pk = 0.0; best = -1e9; d = s
    while d < n:
        thr = 100.0 if pk >= D + 100.0 else pk - D
        if eq + LO[d] <= thr: return -1, d
        c = CL[d]; eq += c
        if c > best: best = c
        if eq > pk: pk = eq
        if eq >= T and best <= 0.5 * eq: return 1, d
        d += 1
    return 0, n
@njit(cache=True)
def life_q(LO, CL, flo, fcl, fc1, fc2, X, T, D, Q, CAP, FEE, H, step, out):
    nd = LO.shape[0]; r = 0
    for s in range(0, nd - H, step):
        end = s + H; i = s; cash = 0.0; fees = 0.0; nev = 0; npass = 0; nb = 0; npay = 0; dtp = 0.0
        while i < end:
            fees += FEE; nev += 1
            res, j = ev_q(LO, CL, i, end, T, D)
            if res != 1: i = j + 1; continue
            npass += 1; dtp += j - i + 1
            c, m, st, j2 = fu_g(flo, fcl, 1.0, fc1, fc2, j + 1, end, X, D, Q, CAP)
            cash += c; npay += m; nb += st == -1; i = j2 + 1
        out[r, 0] = cash - fees; out[r, 1] = nev; out[r, 2] = npass; out[r, 3] = nb; out[r, 4] = npay; out[r, 5] = dtp / max(npass, 1); r += 1
    return r
ACC = {"50K": (3000.0, 2000.0, 150.0, 2000.0, 105.2), "100K": (6000.0, 3000.0, 200.0, 2500.0, 215.0), "150K": (9000.0, 4500.0, 250.0, 3000.0, 285.0)}
if __name__ == "__main__":
    CANDS = [("50K", 2, 2), ("100K", 2, 2), ("100K", 3, 3), ("100K", 4, 4), ("100K", 4, 3), ("150K", 3, 3), ("150K", 4, 4), ("150K", 5, 5), ("150K", 6, 6), ("150K", 6, 4)]
    rows = []
    for per in ("IS", "C24", "REAL"):
        ce = exits(per, "UA_FULL_GR"); FC = ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR"); fv = [vec(per, c, 0.0, 0.0) for c in FC]; cf = np.array([exits(per, c) for c in FC])
        for acc, ek, fk in CANDS:
            T, D, Q, CAP, FEE = ACC[acc]; G = 0.4667 * T; sc = D / 2000.0
            ev = vec(per, "UA_FULL_GR", 0.0, G / ek); nd = len(ev[0])
            IDX = [np.concatenate([np.arange(s, s + 10) % nd for s in np.random.default_rng(31 + q).integers(0, nd, 27)])[:253] for q in range(1000)]
            for test in ("historia", "costo +1 tick", "Monte Carlo"):
                cst = test == "costo +1 tick"
                LO = ek * (ev[0] - (ce if cst else 0)); CL = ek * (ev[1] - (ce if cst else 0))
                f0 = fk * (np.array([v[0] for v in fv]) - (cf if cst else 0)); f1 = fk * (np.array([v[1] for v in fv]) - (cf if cst else 0))
                args = (750.0 * sc, 1500.0 * sc, 2.0 * CAP, T, D, Q, CAP, FEE)
                if test != "Monte Carlo":
                    out = np.zeros((1000, 6)); m = life_q(LO, CL, f0, f1, *args, 252, 3, out); Lr = out[:m]
                else:
                    o1 = np.zeros((2, 6)); Lr = []
                    for idx in IDX: life_q(LO[idx].copy(), CL[idx].copy(), f0[:, idx].copy(), f1[:, idx].copy(), *args, 252, 252, o1); Lr.append(o1[0].copy())
                    Lr = np.array(Lr)
                rows.append(dict(per=per, cuenta=acc, k_eval=ek, k_fondeada=fk, test=test, mo=Lr[:, 0].mean() / 12, ploss=100 * (Lr[:, 0] < 0).mean(),
                                 evals=Lr[:, 1].mean(), passes=Lr[:, 2].mean(), fbust=Lr[:, 3].mean(), payouts=Lr[:, 4].mean(), dtp=Lr[:, 5].mean()))
        print(per, flush=True)
    R = pd.DataFrame(rows); R.to_csv("acct_bigger.csv", index=False); pd.set_option("display.width", 250)
    R["cand"] = R.cuenta + " eval " + R.k_eval.astype(str) + "c / fondeada " + R.k_fondeada.astype(str) + "c"
    print(R.pivot_table(index="cand", columns=["per", "test"], values="mo").round(0).to_string())
    S = R.groupby("cand").agg(mean9=("mo", "mean"), min9=("mo", "min"), ploss=("ploss", "max"), evals=("evals", "mean"), pass_rate=("passes", "sum"), fbust=("fbust", "mean"), payouts=("payouts", "mean"), dias_eval=("dtp", "mean"))
    S["pass_rate"] = (100 * R.groupby("cand").passes.sum() / R.groupby("cand").evals.sum()).round(1)
    print(S.round(1).sort_values("mean9", ascending=False).to_string())
