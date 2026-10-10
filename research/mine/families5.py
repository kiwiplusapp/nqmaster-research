"""Batch 5 (2026-10-09, 16 years of real NQ futures with real volume): families never mined before.
  DAY_MR      daily-bar setups (Connors-style): prior-day IBS (close location in the RTH range), two closes the same way,
              prior-day return; reversion or momentum; entry at a fixed clock time, stop / target in daily ATR.
  RVOL_DRIVE  relative volume of the RTH session so far (vs the same window over the prior 20 complete days) + the move
              since the open / prior close: high RVOL -> continuation, low RVOL -> fade (or the opposite, both mined).
  VOL_CLIMAX  5-minute volume climax (volume >= m x the same 5-minute slot's 20-day median) -> reversal or continuation.
  OR_FAIL     failed opening-range breakout: price breaks the 15/30/60-minute OR, then closes back inside -> trade the
              other way, stop above the breakout extreme.
All signals use bars up to the signal bar; entries at the next bar (market) as everywhere else (core.execute)."""
import numpy as np, pandas as pd
from numba import njit
from core import S, TICK, ev_from_lists
from families import grid, idx_at


def _daily(D):
    if hasattr(D, "_dly"): return D._dly
    rth = (D.om >= 570) & (D.om < 960)
    df = pd.DataFrame(dict(day=D.day[rth], h=D.h[rth], l=D.l[rth], c=D.c[rth], om=D.om[rth], v=D.v[rth]))
    g = df.groupby("day"); idx = range(D.nd)
    H = g.h.max().reindex(idx); L = g.l.min().reindex(idx); C = g.c.last().reindex(idx); last = g.om.last().reindex(idx)
    ok = last >= 959
    H, L, C = H.where(ok), L.where(ok), C.where(ok)
    out = dict(H1=H.shift(1).to_numpy(float), L1=L.shift(1).to_numpy(float), C1=C.shift(1).to_numpy(float),
               C2=C.shift(2).to_numpy(float), C3=C.shift(3).to_numpy(float))
    D._dly = out; return out


# ---------------------------------------------------------------- DAY_MR
SIG = {"IBS": 0, "DOWN2": 1, "RET": 2}

@njit(cache=True)
def _daymr(c, ds, eT, atr, trend, H1, L1, C1, C2, C3, sig, th, mode, tf, side, k, R):
    nd = len(ds); out = np.zeros((nd, 8)); n = 0
    for d in range(nd):
        e = eT[d]
        if e < 0 or e - 1 < ds[d] or atr[d] <= 0: continue
        A = atr[d]
        if np.isnan(C1[d]) or np.isnan(C2[d]): continue
        s = 0
        if sig == 0:
            rg = H1[d] - L1[d]
            if rg <= 0: continue
            ibs = (C1[d] - L1[d]) / rg
            if ibs <= th: s = 1
            elif ibs >= 1 - th: s = -1
        elif sig == 1:
            if np.isnan(C3[d]): continue
            r1 = C1[d] - C2[d]; r2 = C2[d] - C3[d]
            if r1 < 0 and r2 < 0 and (r1 + r2) <= -th * A: s = 1
            elif r1 > 0 and r2 > 0 and (r1 + r2) >= th * A: s = -1
        else:
            r1 = C1[d] - C2[d]
            if r1 <= -th * A: s = 1
            elif r1 >= th * A: s = -1
        if s == 0: continue
        s = s * mode
        if tf == 1 and s != trend[d]: continue
        if side == 1 and s != 1: continue
        i = e - 1
        sl = c[i] - s * k * A; tp = c[i] + s * R * k * A
        out[n, 0] = i; out[n, 1] = s; out[n, 2] = 0; out[n, 3] = c[i]; out[n, 4] = sl; out[n, 5] = tp; out[n, 6] = i; out[n, 7] = 420; n += 1
    return out[:n]


def gen_daymr(D, p):
    dl = _daily(D); sg, th = p["sg"]
    eT = idx_at(D.sm, D.ds, D.de, S(p["T"]))
    return ev_from_lists(_daymr(D.c, D.ds, eT, D.atr, D.trend, dl["H1"], dl["L1"], dl["C1"], dl["C2"], dl["C3"], SIG[sg], th,
                                p["mode"], p["tf"], p["side"], p["k"], p["R"]).tolist())


SG = [("IBS", 0.15), ("IBS", 0.25), ("IBS", 0.35), ("DOWN2", 0.0), ("DOWN2", 0.3), ("DOWN2", 0.6), ("RET", 0.3), ("RET", 0.6), ("RET", 1.0)]
GRID_DAYMR = grid(sg=SG, mode=(1, -1), tf=(0, 1), side=(0, 1), T=(930, 1000, 1030), k=(0.2, 0.35, 0.5), R=(0.3, 0.5, 1.0, 99.0))


# ---------------------------------------------------------------- RVOL_DRIVE
def _rvol(D, T):
    key = f"_rv{T}"
    if hasattr(D, key): return getattr(D, key)
    e = idx_at(D.sm, D.ds, D.de, S(T)); nd = D.nd
    cv = np.cumsum(np.r_[0.0, D.v])
    vol = np.full(nd, np.nan)
    ok = (e > 0) & (D.ro >= 0) & (e > D.ro)
    vol[ok] = cv[e[ok]] - cv[D.ro[ok]]                         # volume RTH open -> bar before T
    s = pd.Series(vol)
    base = s.rolling(20, min_periods=10).mean().shift(1).to_numpy()
    rv = vol / base
    setattr(D, key, (e, rv)); return e, rv


def gen_rvol(D, p):
    e, rv = _rvol(D, p["T"]); kind, lim = p["cond"]
    i = e - 1; ok = (e > 0) & (D.ro >= 0) & (D.atr > 0) & np.isfinite(rv)
    ok &= (rv >= lim) if kind == "hi" else (rv <= lim)
    ii = np.where(ok, i, 0)
    ref = np.where(p["ref"] == "open", D.o[np.maximum(D.ro, 0)], D.pdc)
    mv = D.c[ii] - ref
    ok &= np.isfinite(mv) & (np.abs(mv) >= p["x"] * D.atr)
    s = np.sign(mv) * p["dm"]
    if p["tf"] == 1: ok &= (s == D.trend)
    ok &= s != 0
    dd = np.where(ok)[0]
    if len(dd) == 0: return ev_from_lists([])
    A = D.atr[dd]; ci = D.c[i[dd]]; sd = s[dd]
    sl = ci - sd * p["k"] * A; tp = ci + sd * p["R"] * p["k"] * A
    L = np.column_stack([i[dd], sd, np.zeros(len(dd)), ci, sl, tp, i[dd], np.full(len(dd), 400)])
    return ev_from_lists(L.tolist())


GRID_RVOL = grid(T=(1000, 1015, 1030, 1100), cond=(("hi", 1.3), ("hi", 1.6), ("lo", 0.8), ("lo", 0.65)), ref=("open", "pdc"),
                 x=(0.1, 0.25, 0.4), dm=(1, -1), tf=(0, 1), k=(0.15, 0.25, 0.4), R=(0.3, 0.5, 1.0, 99.0))


# ---------------------------------------------------------------- VOL_CLIMAX (5-minute bars)
def _climax_ratio(D):
    if hasattr(D, "_vcr"): return D._vcr
    B = D.bars(5)
    df = pd.DataFrame(dict(day=B["day"], slot=B["sm"] // 5, v=B["v"]))
    P = df.pivot_table(index="day", columns="slot", values="v", aggfunc="sum")
    med = P.rolling(20, min_periods=10).median().shift(1)
    m = med.stack().rename("med").reset_index()
    j = df.merge(m, on=["day", "slot"], how="left")
    r = (j.v / j.med).to_numpy()
    D._vcr = r; return r


@njit(cache=True)
def _climax(o, h, l, c, sm5, last, day5, atr, trend, ratio, w0, w1, m, mode, wick, rng, stopm, R, tf):
    n5 = len(c); out = np.zeros((n5, 8)); k = 0
    for b in range(n5):
        if sm5[b] < w0 or sm5[b] >= w1: continue
        r = ratio[b]
        if not (r >= m): continue
        d = day5[b]; A = atr[d]
        if A <= 0: continue
        rg = h[b] - l[b]
        if rg <= 0 or rg < rng * A: continue
        bs = 1 if c[b] > o[b] else (-1 if c[b] < o[b] else 0)
        if bs == 0: continue
        if wick == 1:
            adv = (h[b] - max(o[b], c[b])) if bs == 1 else (min(o[b], c[b]) - l[b])
            if adv < 0.4 * rg: continue
        s = -bs if mode == 1 else bs
        if tf == 1 and s != trend[d]: continue
        cc = c[b]
        if stopm == 0:
            sl = (h[b] + TICK) if s == -1 else (l[b] - TICK)
            risk = (cc - sl) * s
            if risk < 0.03 * A or risk > 0.3 * A: continue
        else:
            risk = 0.2 * A; sl = cc - s * risk
        tp = cc + s * R * risk
        out[k, 0] = last[b]; out[k, 1] = s; out[k, 2] = 0; out[k, 3] = cc; out[k, 4] = sl; out[k, 5] = tp; out[k, 6] = last[b]; out[k, 7] = 120; k += 1
    return out[:k]


def gen_climax(D, p):
    B = D.bars(5); r = _climax_ratio(D)
    return ev_from_lists(_climax(B["o"], B["h"], B["l"], B["c"], B["sm"], B["last"], B["day"], D.atr, D.trend, r,
                                 S(p["win"][0]), S(p["win"][1]), p["m"], p["mode"], p["wick"], p["rng"], p["stop"], p["R"], p["tf"]).tolist())


GRID_CLIMAX = grid(m=(2.0, 3.0, 4.0), mode=(1, -1), wick=(0, 1), rng=(0.0, 0.1), stop=(0, 1), R=(0.3, 0.5, 1.0),
                   win=((945, 1200), (1200, 1545)), tf=(0, 1))


# ---------------------------------------------------------------- OR_FAIL
TG = {"R0.5": 0, "R1": 1, "mid": 2, "opp": 3}

@njit(cache=True)
def _orfail(o, h, l, c, sm, ro, de, atr, trend, T, w1, bk, tfb, tg, tf):
    nd = len(ro); out = np.zeros((nd, 8)); n = 0
    for d in range(nd):
        r = ro[d]
        if r < 0 or atr[d] <= 0: continue
        A = atr[d]; hi = -1e18; lo = 1e18; q = r
        while q <= de[d] and sm[q] - sm[r] < T:
            hi = max(hi, h[q]); lo = min(lo, l[q]); q += 1
        if q > de[d]: continue
        brk = 0; ext = 0.0; bi = -1
        for j in range(q, de[d] + 1):
            if sm[j] >= w1: break
            if brk == 0:
                if h[j] > hi + bk * A: brk = 1; ext = h[j]; bi = j
                elif l[j] < lo - bk * A: brk = -1; ext = l[j]; bi = j
                if brk == 0: continue
            else:
                if brk == 1: ext = max(ext, h[j])
                else: ext = min(ext, l[j])
            if j - bi > 30: break                                  # failure must come within 30 minutes
            if tfb == 5 and (sm[j] - sm[r]) % 5 != 4: continue     # 5-minute closes only
            back = (brk == 1 and c[j] < hi) or (brk == -1 and c[j] > lo)
            if not back: continue
            s = -brk
            if tf == 1 and s != trend[d]: break
            if tf == -1 and s == trend[d]: break
            sl = ext + TICK if s == -1 else ext - TICK
            risk = (c[j] - sl) * s
            if risk < 0.03 * A or risk > 0.4 * A: break
            if tg == 0: tp = c[j] + s * 0.5 * risk
            elif tg == 1: tp = c[j] + s * risk
            elif tg == 2: tp = (hi + lo) / 2
            else: tp = lo if s == -1 else hi
            if (tp - c[j]) * s <= TICK: break
            out[n, 0] = j; out[n, 1] = s; out[n, 2] = 0; out[n, 3] = c[j]; out[n, 4] = sl; out[n, 5] = tp; out[n, 6] = j; out[n, 7] = 240; n += 1
            break
    return out[:n]


def gen_orfail(D, p):
    return ev_from_lists(_orfail(D.o, D.h, D.l, D.c, D.sm, D.ro, D.de, D.atr, D.trend, p["T"], S(p["w1"]), p["bk"], p["tfb"], TG[p["tg"]], p["tf"]).tolist())


GRID_ORFAIL = grid(T=(15, 30, 60), w1=(1200, 1400), bk=(0.0, 0.05, 0.1), tfb=(1, 5), tg=tuple(TG), tf=(0, 1, -1))

FAMILIES5 = {"DAY_MR": (gen_daymr, GRID_DAYMR, 1), "RVOL_DRIVE": (gen_rvol, GRID_RVOL, 1),
             "VOL_CLIMAX": (gen_climax, GRID_CLIMAX, 2), "OR_FAIL": (gen_orfail, GRID_ORFAIL, 1)}
