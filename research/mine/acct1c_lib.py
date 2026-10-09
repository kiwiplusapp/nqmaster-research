"""acct1c: ONE-contract eval + funded lifecycle for Lucid Flex / LucidPro (50K, optional 100K), exact dense minute grids.
Library only (no work at import). Day vectors (intraday low incl. open adverse, close) are built from weighted sums of the dense
module grids (research/tmp/dense, read-only) with optional account daily profit stop G / daily loss stop DL (acct_lab.day_vectors).
Eval: two gears chosen at the start of each day from the cushion (equity - EOD trailing threshold): gear 1 (fast) when cushion >= C,
gear 0 (stable) below (C = 0 -> always gear 1). Lucid Flex consistency: best day <= cons x profit. Optional ATR start filter
(an eval may only be bought on a day with NQ ATR / 60-day median < 1.15; waiting is free but costs slot time).
Funded: three tiers (SAFE / NO-BOOST / FULL) by cushion c1 / c2 (NQMaster FundedCushionSafe / FundedCushionFull).
  Flex funded: EOD trailing D locking at +100, payout after 5 days >= Q with balance >= X: min(cap, 50% of balance), 90% split,
               5 payouts then the slot restarts (graduation to live is not counted = conservative).
  Pro funded : payout when balance - (D + 100) >= max(500, min(X, cap)), cycle profit >= 500, best day of cycle <= 40% of cycle
               profit, >= 3 days in the cycle; caps 2,000 then 2,500; 90% split; 5 payouts then restart.
All simulators take an index array (history = arange, bootstrap = 10-day block resample) so arrays are never copied."""
import sys, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
import prof_grid_lib  # noqa: F401  (defines CFG profile lists, no work at import)
from acct_life import CFG
from acct_lab import Z, day_vectors
from acct_policy import hiatr

PERS = ("IS", "C24", "REAL")
NIGHT = ["N:NF05", "N:LF06", "N:LF0430"]
GW = ["G:OD1030", "G:ENG0408", "G:SVWAP22"]
GR = GW + ["G:ASIA1R", "G:ENG0206"]
_fix = {"U:ICT": "U:ICTF", "U1:ICT": "U1:ICTF", "WR:ICT": "U:ICTF", "WR1:ICT": "U1:ICTF"}
fix = lambda ks: [_fix.get(k, k) for k in ks]
UA_FULL = fix(CFG["UA_FULL"]) + NIGHT                    # Ultra (ampliado) + night, corrected ICT x2
UA_NOB = fix(CFG["UA_NOB"]) + NIGHT
UA_SAFE = fix(CFG["UA_SAFE"]) + NIGHT
WR_FULL = fix(CFG["WR_FULL"]) + NIGHT + ["N:LATE15"]     # WR70Plus + NightOnWr70 (+ LATE15), corrected ICT x2
WR_NOB = fix(CFG["WR_NOB"]) + NIGHT + ["N:LATE15"]
WR_SAFE = fix(CFG["WR_SAFE"]) + NIGHT + ["N:LATE15"]
EST = None
for line in open("gate84_sets.txt"):
    if line.startswith("ESTABLE"): EST = [k for k in line.split(":", 1)[1].split() if not k.startswith("G:")]
# NQMaster EvalSafeSet=Estable under WR70Plus: EstableSig modules that WR70Plus runs (CRT11, ORB90, MSEQ, REV06, VOLB trend 0.5R, VW13)
WEST = ["WR1:CRT11", "WR1:ORB90", "WR1:MSEQ", "WR1:REV06", "WR1:VOLB_tf1", "WR1:VW13"]


def items(nq, gold=(), gw=1.0, nqw=1.0):
    d = {}
    for k in nq: d[k] = d.get(k, 0.0) + nqw
    for k in gold: d[k] = d.get(k, 0.0) + gw
    return tuple(sorted(d.items()))


_LR = {}; _DV = {}; _EX = {}; _WARNED = set()
def _key(per, k):
    """REAL has no 'U1:MSEQS' grid: use the Ultra version 'U:MSEQS' (MSEQS boosts are rare) and warn once"""
    z = Z(per)
    if k + "|L" in z.files: return k
    alt = "U:" + k.split(":", 1)[1]
    if (per, k) not in _WARNED: print(f"WARNING {per}: {k} missing -> {alt}", flush=True); _WARNED.add((per, k))
    return alt
def _sum(per, it):
    key = (per, it)
    if key not in _LR:
        if len(_LR) >= 8: _LR.pop(next(iter(_LR)))
        z = Z(per); nd = len(z["days"]); L = np.zeros((nd, 1440), np.float32); R = np.zeros((nd, 1440), np.float32)
        for k, w in it:
            k = _key(per, k); L += np.float32(w) * z[k + "|L"]; R += np.float32(w) * z[k + "|R"]
        _LR[key] = (L, R)
    return _LR[key]


def dv(per, it, DL=0.0, G=0.0):
    """day low / close vectors (1 base contract) of the weighted module set under an account loss stop DL / profit stop G"""
    key = (per, it, DL, G)
    if key not in _DV:
        L, R = _sum(per, it); lo, cl = day_vectors(L, R, DL, G); _DV[key] = (lo.copy(), cl.copy())
    return _DV[key]


def exits(per, it):
    """extra cost of +1 tick per side per day: $1 per MNQ exit, $2 per MGC exit (x weight)"""
    key = (per, it)
    if key not in _EX:
        z = Z(per); out = np.zeros(len(z["days"]))
        for k, w in it:
            R = z[_key(per, k) + "|R"]; ch = (np.abs(np.diff(R, axis=1)) > 1e-6).sum(1); out += w * ch * (2.0 if k.startswith("G:") else 1.0)
        _EX[key] = out
    return _EX[key]


def ndays(per): return len(Z(per)["days"])


def boot_idx(nd, q, length=253, block=10, seed=31):
    rng = np.random.default_rng(seed + q)
    return np.concatenate([np.arange(s, s + block) % nd for s in rng.integers(0, nd, length // block + 2)])[:length].astype(np.int64)


# ------------------------------------------------------------------ simulators
@njit(cache=True)
def ev1(EL, EC, C, T, D, cons, idx, s, n):
    """one eval from sequence position s; EL/EC[g, day]; returns (1 pass / -1 bust / 0 open, last position)"""
    eq = 0.0; pk = 0.0; best = -1e9; d = s
    while d < n:
        t = idx[d]
        thr = 100.0 if pk >= D + 100.0 else pk - D
        g = 1 if eq - thr >= C else 0
        if eq + EL[g, t] <= thr: return -1, d
        c = EC[g, t]; eq += c
        if c > best: best = c
        if eq > pk: pk = eq
        if eq >= T and (cons <= 0.0 or best <= cons * eq): return 1, d
        d += 1
    return 0, n


@njit(cache=True)
def tier(cu, c1, c2): return 0 if cu < c1 else (1 if cu < c2 else 2)


@njit(cache=True)
def fu_flex(FL, FC, c1, c2, idx, start, n, X, D, Q, cap):
    bal = 0.0; pk = 0.0; locked = False; cash = 0.0; m = 0; qd = 0; cyc0 = 0.0; d = start
    while d < n:
        t = idx[d]
        thr = 100.0 if (locked or pk >= D + 100.0) else pk - D
        j = tier(bal - thr, c1, c2)
        if bal + FL[j, t] <= thr: return cash, m, -1, d
        c = FC[j, t]; bal += c
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
def fu_pro(FL, FC, c1, c2, idx, start, n, X, D, cap1, cap2, pcons, npmax, mindays):
    bal = 0.0; pk = 0.0; cash = 0.0; m = 0; cyc0 = 0.0; best = -1e9; nd = 0; d = start; buf = D + 100.0
    while d < n:
        t = idx[d]
        thr = 100.0 if pk >= buf else pk - D
        j = tier(bal - thr, c1, c2)
        if bal + FL[j, t] <= thr: return cash, m, -1, d
        c = FC[j, t]; bal += c; nd += 1
        if bal > pk: pk = bal
        if c > best: best = c
        prof = bal - cyc0; cap = cap1 if m == 0 else cap2; amt = min(cap, bal - buf)
        if nd >= mindays and prof >= 500.0 and amt >= max(500.0, min(X, cap)) and best <= pcons * prof:
            bal -= amt; cash += 0.9 * amt; m += 1; cyc0 = bal; best = -1e9; nd = 0
            if m == npmax: return cash, m, 1, d
        d += 1
    return cash, m, 0, n


@njit(cache=True)
def life(EL, EC, C, T, D, cons, okst, fee, FL, FC, c1, c2, firm, X, Q, cap1, cap2, idx, H, step, out):
    """12-month slots (H sequence days) starting every `step` positions; out columns:
    0 net cash, 1 evals bought, 2 passes, 3 funded busts, 4 payouts, 5 mean eval days of passed evals, 6 funded days, 7 gross cash, 8 waiting days"""
    N = len(idx); r = 0
    for s in range(0, N - H, step):
        end = s + H; i = s; cash = 0.0; fees = 0.0; nev = 0; npass = 0; nb = 0; npay = 0; dtp = 0.0; fdays = 0.0; wait = 0.0
        while i < end:
            while i < end and not okst[idx[i]]:
                i += 1; wait += 1.0
            if i >= end: break
            fees += fee; nev += 1
            res, j = ev1(EL, EC, C, T, D, cons, idx, i, end)
            if res != 1:
                i = j + 1; continue
            npass += 1; dtp += j - i + 1
            if firm == 0: c, m, st, j2 = fu_flex(FL, FC, c1, c2, idx, j + 1, end, X, D, Q, cap1)
            else: c, m, st, j2 = fu_pro(FL, FC, c1, c2, idx, j + 1, end, X, D, cap1, cap2, 0.4, 5, 3)
            fdays += min(j2, end - 1) - j
            cash += c; npay += m; nb += st == -1; i = j2 + 1
        out[r, 0] = cash - fees; out[r, 1] = nev; out[r, 2] = npass; out[r, 3] = nb; out[r, 4] = npay
        out[r, 5] = dtp / max(npass, 1); out[r, 6] = fdays; out[r, 7] = cash; out[r, 8] = wait; r += 1
    return r


@njit(cache=True)
def eval_all(EL, EC, C, T, D, cons, idx, nmin, out):
    """every start position with >= nmin positions left: (result, trading days used)"""
    N = len(idx); m = N - nmin
    for s in range(m):
        r, j = ev1(EL, EC, C, T, D, cons, idx, s, N); out[s, 0] = r; out[s, 1] = j - s + 1
    return m


@njit(cache=True)
def funded_within(EL, EC, C, T, D, cons, idx, W, out):
    """buy a new eval the day after every bust: funded within W trading days? (first-eval result, funded flag, attempts, days)"""
    N = len(idx); m = N - W
    for s in range(m):
        i = s; att = 0; first = 0.0; ok = 0.0; dd = 0.0
        while i < s + W:
            att += 1
            r, j = ev1(EL, EC, C, T, D, cons, idx, i, s + W)
            if att == 1: first = 1.0 if r == 1 else 0.0
            if r == 1:
                ok = 1.0; dd = j - s + 1; break
            if r == 0: break
            i = j + 1
        out[s, 0] = first; out[s, 1] = ok; out[s, 2] = att; out[s, 3] = dd
    return m


def esumm(o, mask=None):
    if mask is not None: o = o[mask]
    ps = o[:, 0] == 1; done = o[:, 0] != 0
    return dict(pass_pct=100 * ps.sum() / max(done.sum(), 1), bust_pct=100 * (o[:, 0] == -1).sum() / max(done.sum(), 1),
                p22=100 * (ps & (o[:, 1] <= 22)).mean(), p33=100 * (ps & (o[:, 1] <= 33)).mean(),
                med_days=float(np.median(o[ps, 1])) if ps.any() else np.nan, mean_days=float(o[ps, 1].mean()) if ps.any() else np.nan)


# ------------------------------------------------------------------ funded with NQMaster AdaptiveSize (DD-from-peak sizing)
@njit(cache=True)
def fu_flex_dd(FL, FC, NQC, S, idx, start, n, X, D, Q, cap):
    """Flex funded where NQMaster runs AdaptiveSize: tier 1 (SizeHigh) while the strategy's cumulative NQ P&L is less than S
    below its peak (EOD, measured from go-live, withdrawals do not count), tier 0 (SizeLow) otherwise. Decision at day start.
    FL/FC[j]: account day low / close at tier j (NQ size j + fixed gold); NQC[j]: NQ-only close at tier j."""
    bal = 0.0; pk = 0.0; locked = False; cash = 0.0; m = 0; qd = 0; cyc0 = 0.0; d = start; cum = 0.0; cpk = 0.0
    while d < n:
        t = idx[d]
        thr = 100.0 if (locked or pk >= D + 100.0) else pk - D
        j = 1 if cpk - cum < S else 0
        if bal + FL[j, t] <= thr: return cash, m, -1, d
        c = FC[j, t]; bal += c; cum += NQC[j, t]
        if cum > cpk: cpk = cum
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
def life_dd(EL, EC, C, T, D, cons, okst, fee, FL, FC, NQC, S, X, Q, cap, idx, H, step, out):
    """as life() with Flex funded + AdaptiveSize (fu_flex_dd)"""
    N = len(idx); r = 0
    for s in range(0, N - H, step):
        end = s + H; i = s; cash = 0.0; fees = 0.0; nev = 0; npass = 0; nb = 0; npay = 0; dtp = 0.0; fdays = 0.0; wait = 0.0
        while i < end:
            while i < end and not okst[idx[i]]:
                i += 1; wait += 1.0
            if i >= end: break
            fees += fee; nev += 1
            res, j = ev1(EL, EC, C, T, D, cons, idx, i, end)
            if res != 1:
                i = j + 1; continue
            npass += 1; dtp += j - i + 1
            c, m, st, j2 = fu_flex_dd(FL, FC, NQC, S, idx, j + 1, end, X, D, Q, cap)
            fdays += min(j2, end - 1) - j
            cash += c; npay += m; nb += st == -1; i = j2 + 1
        out[r, 0] = cash - fees; out[r, 1] = nev; out[r, 2] = npass; out[r, 3] = nb; out[r, 4] = npay
        out[r, 5] = dtp / max(npass, 1); out[r, 6] = fdays; out[r, 7] = cash; out[r, 8] = wait; r += 1
    return r
