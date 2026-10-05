"""12-month lifecycle per account slot under joint eval + funded policies (Lucid Flex 50K, 1 contract per module).
Eval fee $105.2 per attempt; an eval may only START on a day whose NQ ATR ratio < atr_max (waiting is free); after a pass the
funded account starts the next day; funded = Lucid rules (EOD trailing 2,000 locking +100, payouts min(2000, 50%) after 5 days
>= $150 and profit >= X, 90% split, 5 payouts then the account graduates and the slot restarts with a new eval).
Configs (daily low / close vectors from the dense module grids) are chosen each day from the cushion: < c1 -> A, < c2 -> B, else C."""
import os, sys, itertools, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
from acct_policy import vec, hiatr, CFG, ULTRA, GOLD
CFG["FULLG"] = ULTRA + GOLD + ["G:ASIA1R", "G:ENG0206"]
CFG["SAFEG"] = CFG["SAFE"] + ["G:ASIA1R", "G:ENG0206", "G:LATE1430"]
@njit(cache=True)
def pick(cu, c1, c2): return 0 if cu < c1 else (1 if cu < c2 else 2)
@njit(cache=True)
def ev_run(lo, cl, c1, c2, start, n):
    eq = 0.0; pk = 0.0; best = -1e9; d = start
    while d < n:
        thr = 100.0 if pk >= 2100.0 else pk - 2000.0
        j = pick(eq - thr, c1, c2)
        if eq + lo[j, d] <= thr: return -1, d
        c = cl[j, d]; eq += c
        if c > best: best = c
        if eq > pk: pk = eq
        if eq >= 3000.0 and best <= 0.5 * eq: return 1, d
        d += 1
    return 0, n
@njit(cache=True)
def fu_run(lo, cl, c1, c2, start, n, X):
    bal = 0.0; pk = 0.0; locked = False; cash = 0.0; k = 0; qd = 0; cyc0 = 0.0; d = start
    while d < n:
        thr = 100.0 if (locked or pk >= 2100.0) else pk - 2000.0
        j = pick(bal - thr, c1, c2)
        if bal + lo[j, d] <= thr: return cash, k, -1, d
        c = cl[j, d]; bal += c
        if bal > pk: pk = bal
        if c >= 150.0: qd += 1
        if qd >= 5 and bal - cyc0 > 0 and bal >= X:
            amt = min(2000.0, 0.5 * bal)
            if amt >= 500.0:
                bal -= amt; cash += 0.9 * amt; k += 1; qd = 0; cyc0 = bal; locked = True
                if k == 5: return cash, k, 1, d
        d += 1
    return cash, k, 0, n
@njit(cache=True)
def life(elo, ecl, ec1, ec2, flo, fcl, fc1, fc2, X, okstart, H, step, fee, out):
    nd = elo.shape[1]; r = 0
    for s in range(0, nd - H, step):
        end = s + H; i = s; cash = 0.0; fees = 0.0; nev = 0; npass = 0; nbust = 0; npay = 0; ngrad = 0
        while i < end:
            while i < end and not okstart[i]: i += 1
            if i >= end: break
            fees += fee; nev += 1
            res, j = ev_run(elo, ecl, ec1, ec2, i, end)
            if res != 1: i = j + 1; continue
            npass += 1
            c, k, st, j2 = fu_run(flo, fcl, fc1, fc2, j + 1, end, X)
            cash += c; npay += k; nbust += st == -1; ngrad += st == 1; i = j2 + 1
        out[r, 0] = cash - fees; out[r, 1] = nev; out[r, 2] = npass; out[r, 3] = nbust; out[r, 4] = npay; out[r, 5] = ngrad; r += 1
    return r
def stack(per, cfgs, DL):
    V = [vec(per, c, DL, 0.0) for c in cfgs]
    return np.ascontiguousarray(np.array([v[0] for v in V])), np.ascontiguousarray(np.array([v[1] for v in V]))
def run_life(per, ev, fu, atr_max, X, H=252, step=3):
    (ecfg, ec1, ec2, eDL), (fcfg, fc1, fc2, fDL) = ev, fu
    elo, ecl = stack(per, ecfg, eDL); flo, fcl = stack(per, fcfg, fDL)
    ok = hiatr(per) < atr_max if atr_max > 0 else np.ones(elo.shape[1], bool)
    out = np.zeros((1000, 6)); n = life(elo, ecl, ec1, ec2, flo, fcl, fc1, fc2, X, ok, H, step, 105.2, out); o = out[:n]
    return dict(mo=round(o[:, 0].mean() / 12), p10=round(np.percentile(o[:, 0], 10) / 12), evals=round(o[:, 1].mean(), 2), passes=round(o[:, 2].mean(), 2),
                fbust=round(o[:, 3].mean(), 2), payouts=round(o[:, 4].mean(), 2), grads=round(o[:, 5].mean(), 2))
if __name__ == "__main__":
    pd.set_option("display.width", 300); pd.set_option("display.max_rows", 300)
    PER = ("IS", "C24", "REAL")
    EVAL = {"Ultra": (("ULTRA",) * 3, 0, 0, 0.0), "FULL": (("FULL",) * 3, 0, 0, 0.0)}
    for C in (600, 900, 1200, 1500):
        for DL in (0.0, 500.0, 700.0, 1000.0):
            EVAL[f"S<{C}<=F DL{int(DL)}"] = (("SAFE", "SAFE", "FULL"), C, C, DL)
            EVAL[f"S<{C}<=FG DL{int(DL)}"] = (("SAFE", "SAFE", "FULLG"), C, C, DL)
    EVAL["SAFE"] = (("SAFE",) * 3, 0, 0, 0.0); EVAL["NOB"] = (("NOB",) * 3, 0, 0, 0.0)
    FUND = {"Ultra": (("ULTRA",) * 3, 0, 0, 0.0), "SAFE": (("SAFE",) * 3, 0, 0, 0.0), "SAFEG": (("SAFEG",) * 3, 0, 0, 0.0)}
    for c1 in (1000, 1500, 2000):
        for hi in ("NOB", "FULL", "FULLG"):
            FUND[f"S<{c1}<={hi}"] = (("SAFE", "SAFE", hi), c1, c1, 0.0)
            FUND[f"SG<{c1}<={hi}"] = (("SAFEG", "SAFEG", hi), c1, c1, 0.0)
    rows = []
    # stage 1: eval policies with a fixed funded policy; stage 2: funded policies with the best eval policies
    for en, ev in EVAL.items():
        for am in (0.0, 1.15):
            r = dict(eval=en, atr=am, fund="S<1500<=NOB", X=6000)
            for per in PER: r.update({f"{per}_{k}": v for k, v in run_life(per, ev, FUND["S<1500<=NOB"], am, 6000.0).items()})
            rows.append(r)
    A = pd.DataFrame(rows); A.to_csv("acct_life_eval.csv", index=False)
    cols = ["eval", "atr"] + [f"{p}_{k}" for k in ("mo", "p10", "evals", "passes", "fbust", "payouts") for p in PER]
    print(A.sort_values("IS_mo", ascending=False)[cols].head(25).to_string(index=False))
    print(A[A["eval"].isin(["Ultra", "FULL", "SAFE", "NOB"])][cols].to_string(index=False))
    top = A.sort_values("IS_mo", ascending=False)["eval"].head(4).tolist() + ["Ultra"]
    rows = []
    for en in dict.fromkeys(top):
        for fn, fu in FUND.items():
            for X in (4000.0, 5000.0, 6000.0, 7000.0):
                r = dict(eval=en, atr=1.15, fund=fn, X=X)
                for per in PER: r.update({f"{per}_{k}": v for k, v in run_life(per, EVAL[en], fu, 1.15, X).items()})
                rows.append(r)
        print("funded stage", en, flush=True)
    B = pd.DataFrame(rows); B.to_csv("acct_life_fund.csv", index=False)
    cols = ["eval", "fund", "X"] + [f"{p}_{k}" for k in ("mo", "p10", "fbust", "payouts", "grads") for p in PER]
    print(B.sort_values("IS_mo", ascending=False)[cols].head(30).to_string(index=False))
    base = B[(B["eval"] == "Ultra") & (B.fund == "Ultra") & (B.X == 5000.0)]
    print("BASE:"); print(base[cols].to_string(index=False))
