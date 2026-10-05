"""Account lab on the dense module grids (dense_build.py). Daily-resolution prop simulators (intraday low checked before EOD).
Lucid Flex 50K eval : target 3,000, EOD trailing 2,000 (locks at +100 once EOD peak >= 2,100), consistency best day <= 50% of profit.
Apex 50K 2026 EOD    : target 3,000, EOD trailing 2,000 (locks at +100 at 2,100), DLL 1,000 = day liquidated at -1,000, 21 sessions.
Lucid funded         : EOD trailing 2,000 locking +100; payout when >=5 days >= $150, profit >= X, amount min(2000, 50%), 90% split, 5 payouts.
Intraday overlays: own daily loss stop DL (flatten at the first minute equity <= -DL), daily profit stop G (flatten when realized >= G)."""
import os, sys, pickle, numpy as np, pandas as pd
from numba import njit
RES = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); DN = os.path.join(RES, "tmp", "dense")
META = pickle.load(open(os.path.join(DN, "meta.pkl"), "rb"))
_Z = {}
def Z(per):
    if per not in _Z: _Z[per] = np.load(os.path.join(DN, f"{per}.npz"))
    return _Z[per]
def group(m):
    b = m.split(":")[1]
    for g in ("ORB60", "ORB90", "MSEQS", "MSEQ", "CRT11", "ICT", "MOM1030", "MOM11", "MOM13", "ON07", "REV06", "VW13", "VOLB", "LON", "LATE15", "ASIA", "ENG0408", "ENG0206", "ENG0610", "OD1030", "SVWAP22", "DRIVE11", "LATE1430"):
        if b.startswith(g): return g
    return b
_cache = {}
def sums(per, mods):
    key = (per, tuple(sorted(mods)))
    if key in _cache: return _cache[key]
    z = Z(per); nd = len(z["days"]); L = np.zeros((nd, 1440), np.float32); R = np.zeros((nd, 1440), np.float32)
    for m in mods:
        if m + "|L" in z.files: L += z[m + "|L"]; R += z[m + "|R"]
    if len(_cache) > 64: _cache.clear()
    _cache[key] = (L, R); return L, R
def day_vectors(L, R, DL=0.0, G=0.0):
    """low, close per day under intraday stops (DL: own daily loss stop on open equity; G: daily realized profit stop)."""
    nd = L.shape[0]; low = L.min(1).astype(np.float64); close = R[:, -1].astype(np.float64)
    if DL > 0 or G > 0:
        hitL = (L <= -DL) if DL > 0 else np.zeros_like(L, bool); hitG = (R >= G) if G > 0 else np.zeros_like(R, bool)
        anyh = hitL | hitG; has = anyh.any(1); t = np.where(has, anyh.argmax(1), 1439)
        for d in np.nonzero(has)[0]:
            tt = t[d]; low[d] = L[d, :tt + 1].min(); close[d] = L[d, tt]       # flatten at the minute's adverse price
    return low, np.minimum(close, np.maximum(close, low))
@njit(cache=True)
def lucid_eval(low, close, start, k):
    eq = 0.0; pk = 0.0; best = -1e9; d = start; n = len(low)
    while d < n:
        thr = 100.0 if pk >= 2100.0 else pk - 2000.0
        if eq + k * low[d] <= thr: return -1, d - start + 1
        dp = k * close[d]; eq += dp
        if dp > best: best = dp
        if eq > pk: pk = eq
        if eq >= 3000.0 and best <= 0.5 * eq: return 1, d - start + 1
        d += 1
    return 0, d - start
@njit(cache=True)
def apex_eod(low, close, start, k, maxd):
    eq = 0.0; pk = 0.0; d = start; n = len(low)
    while d < n and d < start + maxd:
        thr = 100.0 if pk >= 2100.0 else pk - 2000.0
        lo = k * low[d]; c = k * close[d]
        if lo <= -1000.0: lo = -1000.0; c = -1000.0
        if eq + lo <= thr: return -1, d - start + 1
        eq += c
        if eq > pk: pk = eq
        if eq >= 3000.0: return 1, d - start + 1
        d += 1
    return 0, maxd
@njit(cache=True)
def lucid_funded(low, close, start, end, k, X):
    bal = 0.0; pk = 0.0; locked = False; cash = 0.0; n = 0; qd = 0; cyc0 = 0.0; d = start
    while d < end and d < len(low):
        thr = 100.0 if (locked or pk >= 2100.0) else pk - 2000.0
        if bal + k * low[d] <= thr: return cash, n, -1, d
        dp = k * close[d]; bal += dp
        if bal > pk: pk = bal
        if dp >= 150.0: qd += 1
        if qd >= 5 and bal - cyc0 > 0 and bal >= X:
            amt = min(2000.0, 0.5 * bal)
            if amt >= 500.0:
                bal -= amt; cash += 0.9 * amt; n += 1; qd = 0; cyc0 = bal; locked = True
                if n == 5: return cash, n, 1, d
        d += 1
    return cash, n, 0, end
def eval_stats(low, close, k=1.0, horizon=120):
    nd = len(low); st = range(0, nd - horizon)
    r = np.array([lucid_eval(low, close, s, k) for s in st]); ok = r[:, 0] == 1; bust = r[:, 0] == -1; done = ok | bust
    a = np.array([apex_eod(low, close, s, k, 21) for s in range(nd - 21)])
    f = np.array([lucid_funded(low, close, s, s + 252, k, 5000.0) for s in range(max(1, nd - 252))])
    return dict(L_pass=round(100 * ok.sum() / max(done.sum(), 1), 1), L_p21=round(100 * (ok & (r[:, 1] <= 21)).mean(), 1), L_p42=round(100 * (ok & (r[:, 1] <= 42)).mean(), 1),
                L_days=float(np.median(r[ok, 1])) if ok.any() else np.nan, A_pass=round(100 * (a[:, 0] == 1).mean(), 1), A_bust=round(100 * (a[:, 0] == -1).mean(), 1),
                F_bust=round(100 * (f[:, 2] == -1).mean(), 1), F_cash=round(f[:, 0].mean()), F_all5=round(100 * (f[:, 1] == 5).mean(), 1),
                mo=round(close.mean() * 21 * k), sh=round(close.mean() / close.std() * 252 ** .5, 2))
def stats_for(mods, per, DL=0.0, G=0.0, k=1.0):
    L, R = sums(per, mods); low, close = day_vectors(L, R, DL, G); return eval_stats(low, close, k)
if __name__ == "__main__":
    ULTRA = [m for m in META["IS"] if m.startswith("U:")]
    pd.set_option("display.width", 250)
    rows = []
    for nm, mods in (("Ultra (NQMaster)", ULTRA), ("Ultra + oro WinRate", ULTRA + ["G:OD1030", "G:ENG0408", "G:SVWAP22"]),
                     ("Ultra + oro Robust", ULTRA + ["G:OD1030", "G:ENG0408", "G:SVWAP22", "G:ASIA1R", "G:ENG0206"])):
        for per in ("IS", "C24", "REAL"):
            rows.append(dict(set=nm, per=per, **stats_for(mods, per)))
    print(pd.DataFrame(rows).to_string(index=False))
