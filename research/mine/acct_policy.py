"""State-dependent module sets for a fixed 1-contract account ("cushion gating"), plus intraday daily stops and ATR gating.
Configs (all 1 contract per module):
  FULL = Ultra (NQMaster rules, x2 boosts) + gold WinRate (OD1030, ENG0408, SVWAP22)
  NOB  = FULL without boosts (every weight capped at 1, ICT 1)
  SAFE = modules whose mu/sigma^2 on IS (CFD 2020-23) is > 1.0 per $1000, no boosts:
         ORB60, ORB90, MSEQ, MSEQS, CRT11, ICT, MOM13 (all w=1), VW13, ON07, REV06, LATE15 + gold WinRate
Policy: cushion = equity - threshold (start of day). cushion >= C -> HI config, else LO config. Optional: high-ATR day -> LO.
Lucid eval / Apex EOD eval / Lucid funded as acct_lab (daily resolution, intraday low first)."""
import os, sys, itertools, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
from acct_lab import sums, day_vectors, META, Z
from core import Data
GOLD = ["G:OD1030", "G:ENG0408", "G:SVWAP22"]
ULTRA = [m for m in META["IS"] if m.startswith("U:")]
NOB = [("U1:" + m[2:]) if ("U1:" + m[2:]) in META["IS"] else m for m in ULTRA]
SAFE = ["U1:ORB60", "U1:ORB90", "U1:MSEQ", "U:MSEQS", "U1:CRT11", "U1:ICT", "U1:MOM13", "U:VW13", "U:ON07", "U:REV06", "N:LATE15"]
CFG = {"FULL": ULTRA + GOLD, "NOB": NOB + GOLD, "SAFE": SAFE + GOLD, "ULTRA": ULTRA}

@njit(cache=True)
def run_lucid(lowH, closeH, lowL, closeL, hiatr, C, start, useatr):
    eq = 0.0; pk = 0.0; best = -1e9; d = start; n = len(lowH)
    while d < n:
        thr = 100.0 if pk >= 2100.0 else pk - 2000.0
        hi = (eq - thr) >= C and not (useatr and hiatr[d])
        lo_ = lowH[d] if hi else lowL[d]; c = closeH[d] if hi else closeL[d]
        if eq + lo_ <= thr: return -1, d - start + 1
        eq += c
        if c > best: best = c
        if eq > pk: pk = eq
        if eq >= 3000.0 and best <= 0.5 * eq: return 1, d - start + 1
        d += 1
    return 0, d - start
@njit(cache=True)
def run_apex(lowH, closeH, lowL, closeL, hiatr, C, start, useatr, maxd):
    eq = 0.0; pk = 0.0; d = start; n = len(lowH)
    while d < n and d < start + maxd:
        thr = 100.0 if pk >= 2100.0 else pk - 2000.0
        hi = (eq - thr) >= C and not (useatr and hiatr[d])
        lo_ = lowH[d] if hi else lowL[d]; c = closeH[d] if hi else closeL[d]
        if lo_ <= -1000.0: lo_ = -1000.0; c = -1000.0
        if eq + lo_ <= thr: return -1, d - start + 1
        eq += c
        if eq > pk: pk = eq
        if eq >= 3000.0: return 1, d - start + 1
        d += 1
    return 0, maxd
@njit(cache=True)
def run_funded(lowH, closeH, lowL, closeL, hiatr, C, start, end, useatr, X):
    bal = 0.0; pk = 0.0; locked = False; cash = 0.0; n = 0; qd = 0; cyc0 = 0.0; d = start
    while d < end and d < len(lowH):
        thr = 100.0 if (locked or pk >= 2100.0) else pk - 2000.0
        hi = (bal - thr) >= C and not (useatr and hiatr[d])
        lo_ = lowH[d] if hi else lowL[d]; c = closeH[d] if hi else closeL[d]
        if bal + lo_ <= thr: return cash, n, -1
        bal += c
        if bal > pk: pk = bal
        if c >= 150.0: qd += 1
        if qd >= 5 and bal - cyc0 > 0 and bal >= X:
            amt = min(2000.0, 0.5 * bal)
            if amt >= 500.0:
                bal -= amt; cash += 0.9 * amt; n += 1; qd = 0; cyc0 = bal; locked = True
                if n == 5: return cash, n, 1
        d += 1
    return cash, n, 0
ATR = {}
def hiatr(per):
    if per not in ATR:
        D = Data("mnq_fut.npz" if per == "REAL" else "nq_1m.npz"); days = Z(per)["days"]
        a = pd.Series(D.atr, index=D.daydate).groupby(level=0).last().reindex(days).ffill().to_numpy()
        med = pd.Series(a).rolling(60, min_periods=20).median().shift(1).bfill().to_numpy()
        ATR[per] = a / med
    return ATR[per]
_V = {}
def vec(per, cfg, DL, G):
    key = (per, cfg, DL, G)
    if key not in _V:
        L, R = sums(per, CFG[cfg]); _V[key] = day_vectors(L, R, DL, G)
    return _V[key]
def evaluate(per, hi, lo, C, DL=0.0, G=0.0, atrq=0.0, X=5000.0):
    lH, cH = vec(per, hi, DL, G); lL, cL = vec(per, lo, DL, G); nd = len(lH)
    ha = hiatr(per) > atrq if atrq > 0 else np.zeros(nd, bool); ua = atrq > 0
    r = np.array([run_lucid(lH, cH, lL, cL, ha, C, s, ua) for s in range(nd - 120)]); ok = r[:, 0] == 1; done = r[:, 0] != 0
    a = np.array([run_apex(lH, cH, lL, cL, ha, C, s, ua, 21) for s in range(nd - 21)])
    f = np.array([run_funded(lH, cH, lL, cL, ha, C, s, s + 252, ua, X) for s in range(nd - 252)])
    return dict(L_pass=round(100 * ok.sum() / max(done.sum(), 1), 1), L_p21=round(100 * (ok & (r[:, 1] <= 21)).mean(), 1), L_p42=round(100 * (ok & (r[:, 1] <= 42)).mean(), 1),
                L_days=float(np.median(r[ok, 1])) if ok.any() else np.nan, A_pass=round(100 * (a[:, 0] == 1).mean(), 1), A_bust=round(100 * (a[:, 0] == -1).mean(), 1),
                F_bust=round(100 * (f[:, 2] == -1).mean(), 1), F_cash=round(f[:, 0].mean()), F_pay=round(f[:, 1].mean(), 2))
if __name__ == "__main__":
    pd.set_option("display.width", 260); pd.set_option("display.max_rows", 400)
    rows = []
    grid = [("ULTRA", "ULTRA", 0)] + [(h, l, C) for h in ("FULL", "NOB") for l in ("SAFE", "NOB") for C in (0, 600, 900, 1200, 1500, 1800, 99999) if not (l == h)]
    grid += [("SAFE", "SAFE", 0), ("FULL", "FULL", 0), ("NOB", "NOB", 0)]
    for hi, lo, C in dict.fromkeys(grid):
        for DL in (0.0, 600.0, 800.0):
            for atrq in (0.0, 1.25):
                r = dict(hi=hi, lo=lo, C=C, DL=DL, atrq=atrq)
                for per in ("IS", "C24", "REAL"):
                    s = evaluate(per, hi, lo, C, DL, 0.0, atrq); r.update({f"{per}_{k}": v for k, v in s.items()})
                rows.append(r)
        print(hi, lo, C, flush=True)
    P = pd.DataFrame(rows); P.to_csv("acct_policy.csv", index=False)
    cols = ["hi", "lo", "C", "DL", "atrq"] + [f"{p}_{k}" for k in ("L_pass", "L_p21", "L_days", "F_bust") for p in ("IS", "C24", "REAL")]
    P["score_is"] = P.IS_L_pass + 0.5 * P.IS_L_p21 - 0.3 * P.IS_F_bust
    print(P.sort_values("score_is", ascending=False)[cols].head(40).to_string(index=False))
    print(P[(P.hi == "ULTRA") | ((P.C == 0) & (P.DL == 0) & (P.atrq == 0))][cols].to_string(index=False))
