"""LucidFlex 50K vs 100K (and 150K) with the same strategies at 1 contract per module (and 2 on 100K for reference).
Rules (Lucid support pages, verified 2026-10-03 via proea.app / damnpropfirms.com):
  50K : target 3,000, MLL 2,000 EOD trailing, locks at +100 once EOD >= +2,100; funded payout days >= $150, cap $2,000
  100K: target 6,000, MLL 3,000, locks at +100 once EOD >= +3,100;  payout days >= $200, cap $2,500
  150K: target 9,000, MLL 4,500, locks at +100 once EOD >= +4,600;  payout days >= $250, cap $3,000
Eval 50% consistency; funded: 5 qualifying days, payout min(cap, 50% of profit) >= $500, 90% split, 5 payouts then the slot restarts.
Fees: 50K $105.2 (user's price), 100K $215 and 150K $285 (list price with the usual ~30% coupon)."""
import sys, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
from acct_life import stack, CFG
from acct_policy import hiatr
@njit(cache=True)
def pick(cu, c1, c2): return 0 if cu < c1 else (1 if cu < c2 else 2)
@njit(cache=True)
def ev_g(lo, cl, k, c1, c2, start, n, T, D):
    eq = 0.0; pk = 0.0; best = -1e9; d = start
    while d < n:
        thr = 100.0 if pk >= D + 100.0 else pk - D
        j = pick(eq - thr, c1, c2)
        if eq + k * lo[j, d] <= thr: return -1, d
        c = k * cl[j, d]; eq += c
        if c > best: best = c
        if eq > pk: pk = eq
        if eq >= T and best <= 0.5 * eq: return 1, d
        d += 1
    return 0, n
@njit(cache=True)
def fu_g(lo, cl, k, c1, c2, start, n, X, D, Q, cap):
    bal = 0.0; pk = 0.0; locked = False; cash = 0.0; m = 0; qd = 0; cyc0 = 0.0; d = start
    while d < n:
        thr = 100.0 if (locked or pk >= D + 100.0) else pk - D
        j = pick(bal - thr, c1, c2)
        if bal + k * lo[j, d] <= thr: return cash, m, -1, d
        c = k * cl[j, d]; bal += c
        if bal > pk: pk = bal
        if c >= Q: qd += 1
        if qd >= 5 and bal - cyc0 > 0 and bal >= X:
            amt = min(cap, 0.5 * bal)
            if amt >= 500.0:
                bal -= amt; cash += 0.9 * amt; m += 1; qd = 0; cyc0 = bal; locked = True
                if m == 5: return cash, m, 1, d
        d += 1
    return cash, m, 0, n
@njit(cache=True)
def life_g(elo, ecl, ek, ec1, ec2, flo, fcl, fk, fc1, fc2, X, T, D, Q, cap, fee, H, step, out):
    nd = elo.shape[1]; r = 0
    for s in range(0, nd - H, step):
        end = s + H; i = s; cash = 0.0; fees = 0.0; nev = 0; npass = 0; nb = 0; npay = 0; days_to_pass = 0.0
        while i < end:
            fees += fee; nev += 1
            res, j = ev_g(elo, ecl, ek, ec1, ec2, i, end, T, D)
            if res != 1: i = j + 1; continue
            npass += 1; days_to_pass += j - i + 1
            c, m, st, j2 = fu_g(flo, fcl, fk, fc1, fc2, j + 1, end, X, D, Q, cap)
            cash += c; npay += m; nb += st == -1; i = j2 + 1
        out[r, 0] = cash - fees; out[r, 1] = nev; out[r, 2] = npass; out[r, 3] = nb; out[r, 4] = npay; out[r, 5] = days_to_pass / max(npass, 1); r += 1
    return r
@njit(cache=True)
def eval_stats(lo, cl, k, c1, c2, T, D, out):
    nd = lo.shape[1]; r = 0
    for s in range(nd - 150):
        res, j = ev_g(lo, cl, k, c1, c2, s, nd, T, D); out[r, 0] = res; out[r, 1] = j - s + 1; r += 1
    return r
ACC = {"50K": (3000.0, 2000.0, 150.0, 2000.0, 105.2), "100K": (6000.0, 3000.0, 200.0, 2500.0, 215.0), "150K": (9000.0, 4500.0, 250.0, 3000.0, 285.0)}
PROT = {"HOY": (("ULTRA",) * 3, 0, 0, ("ULTRA",) * 3, 0, 0), "EQUILIBRIO": (("FULLG",) * 3, 0, 0, ("SAFE", "SAFE", "FULL"), 750, 750)}
if __name__ == "__main__":
    pd.set_option("display.width", 260); rows = []
    for per in ("IS", "C24", "REAL"):
        for pn, (ecfg, ec1, ec2, fcfg, fc1, fc2) in PROT.items():
            elo, ecl = stack(per, ecfg, 0.0); flo, fcl = stack(per, fcfg, 0.0)
            for an, (T, D, Q, cap, fee) in ACC.items():
                sc = D / 2000.0
                for k in ((1.0, 2.0) if an != "50K" else (1.0,)):
                    o = np.zeros((2000, 2)); n = eval_stats(elo, ecl, k, ec1 * sc * k, ec2 * sc * k, T, D, o); e = o[:n]
                    ok = e[:, 0] == 1; done = e[:, 0] != 0
                    for X in (sorted({round(2 * cap * f / 500) * 500 for f in (1.0, 1.2, 1.5, 2.0)})):
                        out = np.zeros((1000, 6)); m = life_g(elo, ecl, k, ec1 * sc * k, ec2 * sc * k, flo, fcl, k, fc1 * sc * k, fc2 * sc * k, float(X), T, D, Q, cap, fee, 252, 3, out); L = out[:m]
                        rows.append(dict(per=per, prot=pn, acct=an, k=int(k), X=X, eval_pass=round(100 * ok.sum() / max(done.sum(), 1), 1), eval_days=float(np.median(e[ok, 1])),
                                         eval_p30=round(100 * (ok & (e[:, 1] <= 30)).mean(), 1), mo=round(L[:, 0].mean() / 12), p10=round(np.percentile(L[:, 0], 10) / 12),
                                         evals=round(L[:, 1].mean(), 2), fbust=round(L[:, 3].mean(), 2), payouts=round(L[:, 4].mean(), 2)))
        print(per, flush=True)
    R = pd.DataFrame(rows); R.to_csv("acct_size.csv", index=False)
    best = R.loc[R.groupby(["per", "prot", "acct", "k"]).mo.idxmax()]
    print(best.sort_values(["prot", "acct", "k", "per"]).to_string(index=False))
