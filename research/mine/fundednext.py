"""FundedNext Futures 50K (rules from helpfutures.fundednext.com, 2026-08-17 / 2026-10-07; user screenshots 2026-10-08) vs the
MFFU Rapid EOD and Lucid Flex results, exact dense grids, 12-month account slots, 9 tests (history / +1 tick / 600 bootstrap years).
Rapid Pro 50K ($159.99): eval target 3,000, EOD trailing 2,000 (locks at +100), no DLL, no consistency, 40 micros; funded: same
  drawdown, payout every >= 3 days when cycle profit >= 500 and best day of the cycle <= 40% of cycle profit, withdraw
  min(1,200, balance - B) >= 250 (no firm buffer: B is our own cushion), 90% split, account concluded after 5 rewards.
Direct 50K ($169.99, no eval): EOD trailing 2,000 (locks at +100, also at the first withdrawal), soft DLL 1,000, buffer 2,100 kept in
  the account, withdraw 800..1,200 when the ALL-TIME best day <= 20% of the current cycle profit, 90%, concluded after 5 rewards.
  An account daily profit stop G caps the best day (needed for the 20% rule). -> fundednext.csv"""
import sys, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
import acct1c_lib as A
from acct1c_life import UE, UT, WT
from mffu_rapid import ev_m


@njit(cache=True)
def fu_rp(FL, FC, k, idx, start, n, B):
    bal = 0.0; pk = 0.0; cash = 0.0; m = 0; cyc0 = 0.0; best = -1e9; nd = 0; d = start
    while d < n:
        t = idx[d]; thr = 100.0 if pk >= 2100.0 else pk - 2000.0
        if bal + k * FL[t] <= thr: return cash, m, -1, d
        c = k * FC[t]; bal += c; nd += 1
        if bal > pk: pk = bal
        if c > best: best = c
        prof = bal - cyc0; amt = min(1200.0, bal - B)
        if nd >= 3 and prof >= 500.0 and amt >= 250.0 and best <= 0.4 * prof:
            bal -= amt; cash += 0.9 * amt; m += 1; cyc0 = bal; best = -1e9; nd = 0
            if m >= 5: return cash, m, 1, d
        d += 1
    return cash, m, 0, n


@njit(cache=True)
def fu_direct(FL, FC, k, idx, start, n):
    bal = 0.0; pk = 0.0; cash = 0.0; m = 0; cyc0 = 0.0; best_all = 0.0; locked = False; d = start
    while d < n:
        t = idx[d]; thr = 100.0 if (locked or pk >= 2100.0) else pk - 2000.0
        if bal + k * FL[t] <= thr: return cash, m, -1, d
        c = k * FC[t]; bal += c
        if bal > pk: pk = bal
        if c > best_all: best_all = c
        prof = bal - cyc0; amt = min(1200.0, bal - 2100.0)
        if amt >= 800.0 and best_all <= 0.2 * prof:
            bal -= amt; cash += 0.9 * amt; m += 1; cyc0 = bal; locked = True
            if m >= 5: return cash, m, 1, d
        d += 1
    return cash, m, 0, n


@njit(cache=True)
def life_fn(EL, EC, C, ek, fee, FL, FC, fk, mode, B, idx, H, step, out):
    N = len(idx); r = 0
    for s in range(0, N - H, step):
        end = s + H; i = s; cash = 0.0; fees = 0.0; nev = 0; npass = 0; nb = 0; npay = 0
        while i < end:
            fees += fee; nev += 1
            if mode == 0:
                res, j = ev_m(EL, EC, C, 3000.0, 2000.0, 0.0, 1, idx, i, end)
                if res != 1:
                    i = j + 1; continue
                npass += 1; c, m, st, j2 = fu_rp(FL, FC, fk, idx, j + 1, end, B)
            else:
                npass += 1; c, m, st, j2 = fu_direct(FL, FC, fk, idx, i, end)
            cash += c; npay += m; nb += st == -1; i = j2 + 1
        out[r, 0] = cash - fees; out[r, 1] = nev; out[r, 2] = npass; out[r, 3] = nb; out[r, 4] = npay; r += 1
    return r


if __name__ == "__main__":
    rows = []; nmc = 600
    UF = A.items(A.UA_FULL, A.GR); WF = WT[2]
    CASES = []
    for ek in (1, 2, 3, 4):
        for fk in (1, 2):
            for B in (2100.0, 3100.0):
                CASES.append((f"Rapid Pro: eval Ultra {ek}c -> funded Ultra {fk}c, keep ${B:.0f}", 0, ek, fk, UF, B, 0.0))
    CASES.append(("Rapid Pro: eval Estable 1c -> funded Ultra 1c, keep $2100", 0, 1, 1, "EST", 2100.0, 0.0))
    for fk in (1, 2):
        for G in (0.0, 250.0, 300.0, 400.0, 600.0):
            CASES.append((f"Direct: Ultra {fk}c, daily profit stop ${G:.0f}", 1, 0, fk, UF, 0.0, G))
            CASES.append((f"Direct: WR70Plus {fk}c, daily profit stop ${G:.0f}", 1, 0, fk, WF, 0.0, G))
    for per in A.PERS:
        nd = A.ndays(per); IDX = [A.boot_idx(nd, q, 253, 10, 31) for q in range(nmc)]; hidx = np.arange(nd, dtype=np.int64)
        for nm, mode, ek, fk, it, B, G in CASES:
            for cost in (False, True):
                if it == "EST":
                    lH, cH = A.dv(per, UE[0]); lL, cL = A.dv(per, UE[1]); C = 1200.0
                    eH = A.exits(per, UE[0]) if cost else 0.0; eL = A.exits(per, UE[1]) if cost else 0.0
                    EL = np.ascontiguousarray(np.array([lL - eL, lH - eH])); EC = np.ascontiguousarray(np.array([cL - eL, cH - eH]))
                    fit = UF
                else:
                    l_, c_ = A.dv(per, it); e = A.exits(per, it) if cost else 0.0; C = 0.0
                    EL = np.ascontiguousarray(np.array([ek * (l_ - e), ek * (l_ - e)])); EC = np.ascontiguousarray(np.array([ek * (c_ - e), ek * (c_ - e)])); fit = it
                fl, fc = A.dv(per, fit, 1000.0 / fk if mode == 1 else 0.0, G / fk if G > 0 else 0.0); fe = A.exits(per, fit) if cost else 0.0
                FL = np.ascontiguousarray(fl - fe); FC = np.ascontiguousarray(fc - fe); fee = 159.99 if mode == 0 else 169.99
                for test in (("costo +1 tick",) if cost else ("historia", "Monte Carlo")):
                    if test != "Monte Carlo":
                        out = np.zeros((nd, 5)); m = life_fn(EL, EC, C, ek, fee, FL, FC, float(fk), mode, B, hidx, 252, 3, out); Lr = out[:m]
                    else:
                        Lr = np.zeros((nmc, 5)); o1 = np.zeros((2, 5))
                        for q, idx in enumerate(IDX):
                            life_fn(EL, EC, C, ek, fee, FL, FC, float(fk), mode, B, idx, 252, 252, o1); Lr[q] = o1[0]
                    rows.append(dict(per=per, case=nm, test=test, mo=Lr[:, 0].mean() / 12, ploss=100 * (Lr[:, 0] < 0).mean(), accounts=Lr[:, 1].mean(),
                                     funded=Lr[:, 2].mean(), busts=Lr[:, 3].mean(), rewards=Lr[:, 4].mean()))
        print(per, flush=True)
    R = pd.DataFrame(rows); R.to_csv("fundednext.csv", index=False); pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 70); pd.set_option("display.max_rows", 100)
    S = R.groupby("case").agg(mean9=("mo", "mean"), min9=("mo", "min"), ploss=("ploss", "max"), accounts=("accounts", "mean"), busts=("busts", "mean"), rewards=("rewards", "mean")).round(1)
    print(S.sort_values("mean9", ascending=False).to_string())
