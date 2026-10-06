"""Final verification v2 (corrected dense data: ENG10, LATEFH, ICT corrected, WR/C6 present) of Lucid 50K lifecycle candidates with
eval SIZING POLICIES (eval_pol50.py) and funded gating with gold WinRate or Robust. Tests: history (start every 3 days), +1 tick per
side, 1,000 block-bootstrap years; 3 periods. Eval account profit stop $1,400 at every size. -> final_verify2.csv"""
import sys, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
import prof_grid_lib
from acct_policy import vec
from acct_size import fu_g
from final_verify_lib import exits
T, D, Q, CAP, FEE, G = 3000.0, 2000.0, 150.0, 2000.0, 105.2, 1400.0
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
EVP = {"fijo 2": (2, 2, 0.0, 999, 2, 0.0), "fijo 1": (1, 1, 0.0, 999, 1, 0.0),
       "1 -> 2 desde el dia 8 (1 si colchon < 1000)": (1, 1, 1000.0, 8, 2, 2100.0),
       "2 (1 si colchon < 1250), 3 desde el dia 12": (2, 1, 1250.0, 12, 3, 2100.0),
       "1 -> 2 desde el dia 8 (1 si colchon < 1750)": (1, 1, 1750.0, 8, 2, 1500.0)}
FUND = {"gating + oro WinRate (EQ2)": ("UA_SAFE_GW", "UA_NOB_GW", "UA_FULL_GW"), "gating + oro Robust": ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR")}
rows = []
for per in ("IS", "C24", "REAL"):
    rng = np.random.default_rng(31); vs = {k: vec(per, "UA_FULL_GR", 0.0, G / k) for k in (1, 2, 3)}; nd = len(vs[1][0])
    IDX = [np.concatenate([np.arange(s, s + 10) % nd for s in rng.integers(0, nd, 27)])[:253] for _ in range(1000)]
    ce = exits(per, "UA_FULL_GR")
    for fn, fc in FUND.items():
        fv = [vec(per, c, 0.0, 0.0) for c in fc]; cf = np.array([exits(per, c) for c in fc])
        for en, (k0, kdd, c1, dsw, kl, goal) in EVP.items():
            for test in ("historia", "costo +1 tick", "Monte Carlo"):
                LO = np.zeros((4, nd)); CL = np.zeros((4, nd))
                for k in (1, 2, 3): LO[k] = k * (vs[k][0] - (ce if test == "costo +1 tick" else 0)); CL[k] = k * (vs[k][1] - (ce if test == "costo +1 tick" else 0))
                f0 = np.array([v[0] for v in fv]) - (cf if test == "costo +1 tick" else 0); f1 = np.array([v[1] for v in fv]) - (cf if test == "costo +1 tick" else 0)
                if test != "Monte Carlo":
                    out = np.zeros((1000, 6)); m = life_p(LO, CL, k0, kdd, c1, dsw, kl, goal, f0, f1, 2.0, 750.0, 1500.0, 4000.0, 252, 3, out); L = out[:m]
                else:
                    o1 = np.zeros((2, 6)); L = []
                    for idx in IDX:
                        life_p(LO[:, idx].copy(), CL[:, idx].copy(), k0, kdd, c1, dsw, kl, goal, f0[:, idx].copy(), f1[:, idx].copy(), 2.0, 750.0, 1500.0, 4000.0, 252, 252, o1); L.append(o1[0].copy())
                    L = np.array(L)
                rows.append(dict(per=per, fund=fn, evalp=en, test=test, mo=round(L[:, 0].mean() / 12), p10=round(np.percentile(L[:, 0], 10) / 12), ploss=round(100 * (L[:, 0] < 0).mean(), 1),
                                 evals=round(L[:, 1].mean(), 1), passes=round(L[:, 2].mean(), 2), fbust=round(L[:, 3].mean(), 2), payouts=round(L[:, 4].mean(), 1), dtp=round(L[:, 5].mean(), 1)))
    print(per, flush=True)
R = pd.DataFrame(rows); R.to_csv("final_verify2.csv", index=False); pd.set_option("display.width", 300); pd.set_option("display.max_colwidth", 60)
P = R.pivot_table(index=["fund", "evalp"], columns=["per", "test"], values="mo"); P["mean9"] = P.mean(1); P["min9"] = P.min(1); print(P.round(0).to_string())
print(R[R.test == "Monte Carlo"].pivot_table(index=["fund", "evalp"], columns="per", values=["ploss", "evals", "passes", "fbust", "dtp"]).round(1).to_string())
