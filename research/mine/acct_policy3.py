"""Three-level cushion gating (SAFE < C1 <= NOB < C2 <= HI) with optional own daily loss stop DL and daily profit stop G.
Eval policies are ranked on IS only; C24 / REAL are out of sample. Funded policies (Lucid, payout threshold X) searched separately."""
import os, sys, itertools, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
from acct_policy import vec, CFG, GOLD, ULTRA
CFG["FULLG"] = ULTRA + GOLD + ["G:ASIA1R", "G:ENG0206"]
@njit(cache=True)
def pick(cu, C1, C2):
    return 0 if cu < C1 else (1 if cu < C2 else 2)
@njit(cache=True)
def run_lucid3(lo, cl, C1, C2, start):
    eq = 0.0; pk = 0.0; best = -1e9; d = start; n = lo.shape[1]
    while d < n:
        thr = 100.0 if pk >= 2100.0 else pk - 2000.0
        j = pick(eq - thr, C1, C2)
        if eq + lo[j, d] <= thr: return -1, d - start + 1
        c = cl[j, d]; eq += c
        if c > best: best = c
        if eq > pk: pk = eq
        if eq >= 3000.0 and best <= 0.5 * eq: return 1, d - start + 1
        d += 1
    return 0, d - start
@njit(cache=True)
def run_apex3(lo, cl, C1, C2, start, maxd):
    eq = 0.0; pk = 0.0; d = start; n = lo.shape[1]
    while d < n and d < start + maxd:
        thr = 100.0 if pk >= 2100.0 else pk - 2000.0
        j = pick(eq - thr, C1, C2); l_ = lo[j, d]; c = cl[j, d]
        if l_ <= -1000.0: l_ = -1000.0; c = -1000.0
        if eq + l_ <= thr: return -1, d - start + 1
        eq += c
        if eq > pk: pk = eq
        if eq >= 3000.0: return 1, d - start + 1
        d += 1
    return 0, maxd
@njit(cache=True)
def run_funded3(lo, cl, C1, C2, start, end, X):
    bal = 0.0; pk = 0.0; locked = False; cash = 0.0; n = 0; qd = 0; cyc0 = 0.0; d = start
    while d < end and d < lo.shape[1]:
        thr = 100.0 if (locked or pk >= 2100.0) else pk - 2000.0
        j = pick(bal - thr, C1, C2)
        if bal + lo[j, d] <= thr: return cash, n, -1
        c = cl[j, d]; bal += c
        if bal > pk: pk = bal
        if c >= 150.0: qd += 1
        if qd >= 5 and bal - cyc0 > 0 and bal >= X:
            amt = min(2000.0, 0.5 * bal)
            if amt >= 500.0:
                bal -= amt; cash += 0.9 * amt; n += 1; qd = 0; cyc0 = bal; locked = True
                if n == 5: return cash, n, 1
        d += 1
    return cash, n, 0
def arrays(per, cfgs, DL, G):
    V = [vec(per, c, DL, G) for c in cfgs]
    return np.ascontiguousarray(np.array([v[0] for v in V])), np.ascontiguousarray(np.array([v[1] for v in V]))
def ev_eval(per, cfgs, C1, C2, DL=0.0, G=0.0):
    lo, cl = arrays(per, cfgs, DL, G); nd = lo.shape[1]
    r = np.array([run_lucid3(lo, cl, C1, C2, s) for s in range(nd - 120)]); ok = r[:, 0] == 1; done = r[:, 0] != 0
    a = np.array([run_apex3(lo, cl, C1, C2, s, 21) for s in range(nd - 21)])
    return dict(L_pass=round(100 * ok.sum() / max(done.sum(), 1), 1), L_p21=round(100 * (ok & (r[:, 1] <= 21)).mean(), 1), L_p42=round(100 * (ok & (r[:, 1] <= 42)).mean(), 1),
                L_days=float(np.median(r[ok, 1])) if ok.any() else np.nan, A_pass=round(100 * (a[:, 0] == 1).mean(), 1), A_bust=round(100 * (a[:, 0] == -1).mean(), 1))
def ev_funded(per, cfgs, C1, C2, X, DL=0.0, G=0.0):
    lo, cl = arrays(per, cfgs, DL, G); nd = lo.shape[1]
    f = np.array([run_funded3(lo, cl, C1, C2, s, s + 252, X) for s in range(nd - 252)])
    return dict(F_bust=round(100 * (f[:, 2] == -1).mean(), 1), F_cash=round(f[:, 0].mean()), F_pay=round(f[:, 1].mean(), 2), F_all5=round(100 * (f[:, 1] == 5).mean(), 1))
if __name__ == "__main__":
    pd.set_option("display.width", 280); pd.set_option("display.max_rows", 300)
    PER = ("IS", "C24", "REAL"); rows = []
    for hi in ("FULL", "FULLG"):
        for C1, C2 in [(c1, c2) for c1 in (0, 400, 700, 900) for c2 in (900, 1200, 1500, 2000, 99999) if c2 > c1]:
            for DL in (0.0, 500.0, 700.0, 1000.0):
                for G in (0.0, 1400.0):
                    r = dict(hi=hi, C1=C1, C2=C2, DL=DL, G=G)
                    for per in PER: r.update({f"{per}_{k}": v for k, v in ev_eval(per, ("SAFE", "NOB", hi), C1, C2, DL, G).items()})
                    rows.append(r)
        print(hi, "eval done", flush=True)
    E = pd.DataFrame(rows); E.to_csv("acct_policy3_eval.csv", index=False)
    base = {per: ev_eval(per, ("ULTRA", "ULTRA", "ULTRA"), 0, 0) for per in PER}
    print("BASE Ultra:", base)
    cols = ["hi", "C1", "C2", "DL", "G"] + [f"{p}_{k}" for k in ("L_pass", "L_p21", "L_days", "A_pass") for p in PER]
    # IS-only ranking: maximise pass subject to median days <= baseline + 2 (speed kept), then show OOS
    for lab, cap in (("same speed (<= base + 2 days)", 2), ("up to +6 days", 6)):
        sub = E[E.IS_L_days <= base["IS"]["L_days"] + cap].sort_values(["IS_L_pass", "IS_L_p21"], ascending=False)
        print("\n==", lab); print(sub[cols].head(12).to_string(index=False))
    rows = []
    for C1, C2 in [(c1, c2) for c1 in (0, 600, 1000, 1500, 2000) for c2 in (1000, 1500, 2000, 3000, 99999) if c2 > c1]:
        for X in (3000.0, 4000.0, 5000.0, 6000.0):
            for DL in (0.0, 500.0, 700.0):
                r = dict(C1=C1, C2=C2, X=X, DL=DL)
                for per in PER: r.update({f"{per}_{k}": v for k, v in ev_funded(per, ("SAFE", "NOB", "FULL"), C1, C2, X, DL).items()})
                rows.append(r)
    F = pd.DataFrame(rows); F.to_csv("acct_policy3_funded.csv", index=False)
    fb = {per: ev_funded(per, ("ULTRA", "ULTRA", "ULTRA"), 0, 0, 5000.0) for per in PER}
    print("\nBASE funded Ultra X5000:", fb)
    fc = ["C1", "C2", "X", "DL"] + [f"{p}_{k}" for k in ("F_cash", "F_bust", "F_all5") for p in PER]
    print(F.sort_values("IS_F_cash", ascending=False)[fc].head(15).to_string(index=False))
    print(F.sort_values("IS_F_bust")[fc].head(10).to_string(index=False))
