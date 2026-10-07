"""Reusable Lucid Flex 50K lifecycle test (from final_verify2.py): eval sizing policy + funded cushion gating, 12-month slots,
tests = history (start every 3 days), +1 tick per side, 1,000 block-bootstrap years, on IS / C24 / REAL.
run(cands) -> DataFrame with $/month per slot for every candidate x period x test, plus summary (mean of 9, min of 9)."""
import sys, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
import prof_grid_lib
from acct_life import CFG
from acct_policy import vec
from acct_size import fu_g
from final_verify_lib import exits
T, D, Q, CAP, FEE = 3000.0, 2000.0, 150.0, 2000.0, 105.2
@njit(cache=True)
def ev_p(LO, CL, k0, kdd, c1, dsw, kl, goal, s, n):
    eq = 0.0; pk = 0.0; best = -1e9; d = s
    while d < n:
        thr = 100.0 if pk >= D + 100.0 else pk - D
        k = k0
        if eq - thr < c1: k = kdd
        elif d - s >= dsw and eq < goal: k = kl
        if eq + LO[k, d] <= thr: return -1, d
        c = CL[k, d]; eq += c
        if c > best: best = c
        if eq > pk: pk = eq
        if eq >= T and best <= 0.5 * eq: return 1, d
        d += 1
    return 0, n
@njit(cache=True)
def life_p(LO, CL, k0, kdd, c1, dsw, kl, goal, flo, fcl, fk, fc1, fc2, X, H, step, out):
    nd = LO.shape[1]; r = 0
    for s in range(0, nd - H, step):
        end = s + H; i = s; cash = 0.0; fees = 0.0; nev = 0; npass = 0; nb = 0; npay = 0; dtp = 0.0
        while i < end:
            fees += FEE; nev += 1
            res, j = ev_p(LO, CL, k0, kdd, c1, dsw, kl, goal, i, end)
            if res != 1: i = j + 1; continue
            npass += 1; dtp += j - i + 1
            c, m, st, j2 = fu_g(flo, fcl, fk, fc1, fc2, j + 1, end, X, D, Q, CAP)
            cash += c; npay += m; nb += st == -1; i = j2 + 1
        out[r, 0] = cash - fees; out[r, 1] = nev; out[r, 2] = npass; out[r, 3] = nb; out[r, 4] = npay; out[r, 5] = dtp / max(npass, 1); r += 1
    return r
FIXED2 = (2, 2, 0.0, 999, 2, 0.0)
def define(name, mods):
    CFG[name] = list(mods); return name
def run(cands, periods=("IS", "C24", "REAL"), tests=("historia", "costo +1 tick", "Monte Carlo"), nmc=1000, G=1400.0, fk=2.0, c1=750.0, c2=1500.0, X=4000.0):
    """cands: {name: (eval_cfg, (funded SAFE, NOB, FULL cfgs), eval_policy tuple)}"""
    rows = []
    for per in periods:
        rng = np.random.default_rng(31)
        for nm, (ec, fc, pol) in cands.items():
            vs = {k: vec(per, ec, 0.0, G / k) for k in (1, 2, 3)}; nd = len(vs[1][0])
            IDX = [np.concatenate([np.arange(s, s + 10) % nd for s in np.random.default_rng(31 + q).integers(0, nd, 27)])[:253] for q in range(nmc)]
            ce = exits(per, ec); fv = [vec(per, c, 0.0, 0.0) for c in fc]; cf = np.array([exits(per, c) for c in fc])
            for test in tests:
                cost = test == "costo +1 tick"
                LO = np.zeros((4, nd)); CL = np.zeros((4, nd))
                for k in (1, 2, 3): LO[k] = k * (vs[k][0] - (ce if cost else 0)); CL[k] = k * (vs[k][1] - (ce if cost else 0))
                f0 = np.array([v[0] for v in fv]) - (cf if cost else 0); f1 = np.array([v[1] for v in fv]) - (cf if cost else 0)
                fkk = fk
                if isinstance(fk, tuple): mul = np.array(fk, float)[:, None]; f0 = f0 * mul; f1 = f1 * mul; fkk = 1.0      # per-tier contracts
                if test != "Monte Carlo":
                    out = np.zeros((1000, 6)); m = life_p(LO, CL, *pol, f0, f1, fkk, c1, c2, X, 252, 3, out); L = out[:m]
                else:
                    o1 = np.zeros((2, 6)); L = []
                    for idx in IDX:
                        life_p(LO[:, idx].copy(), CL[:, idx].copy(), *pol, f0[:, idx].copy(), f1[:, idx].copy(), fkk, c1, c2, X, 252, 252, o1); L.append(o1[0].copy())
                    L = np.array(L)
                rows.append(dict(per=per, cand=nm, test=test, mo=L[:, 0].mean() / 12, p10=np.percentile(L[:, 0], 10) / 12, ploss=100 * (L[:, 0] < 0).mean(),
                                 evals=L[:, 1].mean(), passes=L[:, 2].mean(), fbust=L[:, 3].mean(), payouts=L[:, 4].mean(), dtp=L[:, 5].mean()))
    R = pd.DataFrame(rows)
    S = R.groupby("cand").agg(mean9=("mo", "mean"), min9=("mo", "min"), ploss=("ploss", "max"), fbust=("fbust", "mean")).round(1)
    return R, S
