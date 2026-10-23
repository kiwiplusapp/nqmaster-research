"""Batch 13 (2026-10-21): two strategies Federico brought from videos, tested with the house protocol on real NQ futures
(research/data/nqdb.npz 2010-06..2026-10; $ per MNQ incl. $1.90 + 1 tick; cost-normalised 0.345% ATR view for 2010-18).
All fills go through core.execute (market = next 1m bar open + 1 tick, stop entries at max(level, open) + 1 tick, limits need a 1-tick
trade-through, stops -1 tick, flat at MINE_FLAT 15:55). Max 2 trades per Globex session (maxday = 2), one position at a time.

F1  DOUBLE TOP / DOUBLE BOTTOM LIQUIDITY SWEEP (DT_CONT = the video's reading: the sweep IS the move; DT_REV = sweep then fade)
    Pivots on tf-minute bars (bar 5 / 15): pivot high = bar high strictly above the k highs before it and >= the k highs after it
    (k 2 / 5); a pivot is CONFIRMED only when bar p+k has completed (the setup is armed from the next 1m bar). Double top = two pivot
    highs 3..60 bars apart whose highs differ by <= tol (tol in ATR: 0.02 / 0.05 / 0.10; tol 0.0 = 4 ticks) with every high between
    them below the lower of the two (level untouched between) and a pattern depth (level - lowest low between the pivots) >= 0.10 ATR;
    level = the higher of the two highs (the liquidity pool sits above it). The search runs back 60 bars so the first pivot may sit
    in the prior session. Mirror for double bottoms. The first 1m bar whose high reaches level + b (b 0.0 = 1 tick, else b ATR) is
    the sweep; a sweep outside the window consumes the setup (the liquidity is gone). Windows: rth = sweep bar 09:35-15:29 (flat 15:55);
    on = 18:00-09:28, trade closed at 09:29. Context filter at the signal bar: none / vwap (RTH VWAP in rth, 18:00-session VWAP in on:
    longs only above, shorts only below) / sma200 (SMA of 200 completed tf bars) / trend (house daily trend, prev RTH close vs SMA20).
      DT_CONT  stop entry at level + b (signal bar = the bar before the sweep, fill on the sweep bar), stop at the pattern mid
               (st 'mid') or 0.25 ATR, target R x risk (R 0 = hold to the flat).
      DT_REV   ent 'stop': after the sweep bar, stop order back through the level (sell stop at the level after a double-top sweep),
               stop = sweep extreme + 0.05 ATR, valid 60 bars; ent 'lim': limit at level + b placed the bar before the sweep (fills
               on the sweep itself), stop 0.25 ATR beyond; target tgt x risk or the pattern mid ('mid'). Risk floored at 0.10 ATR,
               setups with risk > 1.0 ATR skipped.
F2  INITIAL BALANCE TO VWAP (ib = first 30 / 60 minutes of RTH; window until 15:00; one trade per IB side per day)
      IB_FADE     price trades to IBH + x ATR (x 0 / 0.05 / 0.1) after the IB -> short (mirror at the low) with target = RTH VWAP at
                  the signal bar (limit), only if the VWAP is >= d ATR away; stop sk ATR beyond the touch level (sk 0 = 2 x the distance
                  to the VWAP capped at 0.5 ATR); ent 'mkt' (market after the touch bar) or 'lim' (limit at the level, needs a tick
                  through); tf 1 = only against the daily trend side (fade of the IB high only when the daily trend is down).
      IB_BREAK    OCO stops at IBH + b / IBL - b from the IB end (first side touched wins, both in one bar cancels the day); ctx none /
                  trend (daily) / vwap (signal-bar close on the break side of the VWAP) / both; stop at the IB mid or the opposite side;
                  R 1 / 2 x risk, R 0 = 1 x the IB range.
      IB_RECLAIM  price breaks IBH + b, then (within wait minutes) a 1m close back below the RTH VWAP -> market short, stop = sweep high
                  + 0.05 ATR (sk 0) or sk ATR, target the IB low (tg 0) or tg x risk; mirror at the low; tf 1 = with the daily trend.
Grid: DT_CONT 1,536 + DT_REV 1,536 + IB_FADE 288 + IB_BREAK 144 + IB_RECLAIM 96 = 3,600 cells."""
import numpy as np, pandas as pd
from numba import njit
from core import S, TICK, ev_from_lists
from families import grid

HOLD = 100000           # bars; every RTH trade is flat at MINE_FLAT anyway
FAR = 30.0              # 'hold' target = entry +- 30 ATR (never reached)
RMIN, RMAX = 0.10, 1.0  # risk floor / cap in ATR
DEP = 0.10              # minimum pattern depth in ATR
GAP_MIN, GAP_MAX = 3, 60
LIFE = 60               # a confirmed setup lives 60 tf bars
REV_EXP = 60            # reversal orders live 60 1m bars after the sweep
T_RTH0, T_RTH1, T_ON1, T930, T1500 = S(935), S(1530), S(929), S(930), S(1500)
CATEGORICAL13 = ("bar", "win", "filt", "st", "ent", "tgt", "ctx", "tf")
WIN = {"rth": 0, "on": 1}; FILT = {"none": 0, "vwap": 1, "sma200": 2, "trend": 3}


# ------------------------------------------------------------------------------------------------ F1 kernels
@njit(cache=True)
def _pivots(bh, bl, k):
    nb = len(bh); ph = np.zeros(nb, np.bool_); pl = np.zeros(nb, np.bool_)
    for p in range(k, nb - k):
        okh = True; okl = True
        for m in range(1, k + 1):
            if bh[p - m] >= bh[p] or bh[p + m] > bh[p]: okh = False
            if bl[p - m] <= bl[p] or bl[p + m] < bl[p]: okl = False
            if not okh and not okl: break
        ph[p] = okh; pl[p] = okl
    return ph, pl


@njit(cache=True)
def _setups(bh, bl, blast, bday, atr, ph, pl, k, tol_atr, tol_pts):
    """Double tops (side 1) / bottoms (side -1): [side, qi = last 1m index of the confirming bar p2+k, level, pattern reference]."""
    nb = len(bh); out = np.zeros((2 * nb, 4)); n = 0
    for p2 in range(k, nb - k):
        A = atr[bday[p2]]
        if A <= 0: continue
        tol = tol_pts if tol_atr <= 0 else tol_atr * A
        if ph[p2]:
            for p1 in range(p2 - GAP_MIN, max(k, p2 - GAP_MAX) - 1, -1):
                if not ph[p1]: continue
                if abs(bh[p1] - bh[p2]) > tol: continue
                lvl = max(bh[p1], bh[p2]); mn = min(bh[p1], bh[p2]); ok = True; lo = 1e18
                for m in range(p1 + 1, p2):
                    if bh[m] >= mn: ok = False; break
                for m in range(p1, p2 + 1):
                    if bl[m] < lo: lo = bl[m]
                if ok and lvl - lo >= DEP * A:
                    out[n, 0] = 1; out[n, 1] = blast[p2 + k]; out[n, 2] = lvl; out[n, 3] = lo; n += 1
                break
        if pl[p2]:
            for p1 in range(p2 - GAP_MIN, max(k, p2 - GAP_MAX) - 1, -1):
                if not pl[p1]: continue
                if abs(bl[p1] - bl[p2]) > tol: continue
                lvl = min(bl[p1], bl[p2]); mx = max(bl[p1], bl[p2]); ok = True; hi = -1e18
                for m in range(p1 + 1, p2):
                    if bl[m] <= mx: ok = False; break
                for m in range(p1, p2 + 1):
                    if bh[m] > hi: hi = bh[m]
                if ok and hi - lvl >= DEP * A:
                    out[n, 0] = -1; out[n, 1] = blast[p2 + k]; out[n, 2] = lvl; out[n, 3] = hi; n += 1
                break
    return out[:n]


@njit(cache=True)
def _dt_scan(o, h, l, c, sm, day, atr, trend, vw, sv, sma, side, qi, L, ref, mode, b, win, filt, st, R, ent, tgt, life):
    """mode 0 CONT / 1 REV; ent (REV) 0 stop back through the level, 1 limit at the sweep level; win 0 rth / 1 on; filt 0 none, 1 vwap,
    2 sma200, 3 trend; st > 0 ATR stop, st 0 = pattern mid (CONT); tgt > 0 R multiple, tgt 0 = pattern mid (REV)."""
    n = len(c); ns = len(qi); out = np.zeros((ns, 8)); k = 0
    for s in range(ns):
        q = int(qi[s]); sd = int(side[s]); A = atr[day[q]]
        if A <= 0 or q + 1 >= n: continue
        bp = TICK if b <= 0 else b * A
        lv = L[s] + sd * bp
        jmax = min(q + life, n - 1)
        for j in range(q + 1, jmax + 1):
            if sd == 1:
                if h[j] < lv: continue
            else:
                if l[j] > lv: continue
            # first sweep of level + b: the setup is consumed here whatever happens next
            t = sm[j]
            if win == 0:
                if t < T_RTH0 or t >= T_RTH1: break
            else:
                if t >= T_ON1: break
            d = sd if mode == 0 else -sd
            si = j if (mode == 1 and ent == 0) else j - 1
            if filt == 1:
                v = vw[si] if win == 0 else sv[si]
                if np.isnan(v) or (c[si] - v) * d <= 0: break
            elif filt == 2:
                if np.isnan(sma[si]) or (c[si] - sma[si]) * d <= 0: break
            elif filt == 3:
                if trend[day[si]] != d: break
            mid = 0.5 * (L[s] + ref[s])
            if mode == 0:
                px = lv; et = 2; ex = j
                risk = (px - mid) * d if st <= 0 else st * A
                if risk < RMIN * A: risk = RMIN * A
                if risk > RMAX * A: break
                sl = px - d * risk
                tp = px + d * (R * risk if R > 0 else FAR * A)
            else:
                if ent == 0:
                    px = L[s]; et = 2; ex = j + REV_EXP
                    ext = h[j] if sd == 1 else l[j]
                    risk = (ext - px) * sd + 0.05 * A
                else:
                    px = lv; et = 1; ex = j + REV_EXP
                    risk = 0.25 * A
                if risk < RMIN * A: risk = RMIN * A
                if risk > RMAX * A: break
                sl = px - d * risk
                if tgt > 0: tp = px + d * tgt * risk
                else:
                    tp = mid
                    if (tp - px) * d < 2 * TICK: break
            hold = HOLD
            if win == 1:                       # overnight trade: out at the close of the 09:29 bar
                m = j
                while m < n and day[m] == day[j] and sm[m] < T930: m += 1
                if m < n and day[m] == day[j]: hold = max(1, m - j - 1)
            out[k, 0] = si; out[k, 1] = d; out[k, 2] = et; out[k, 3] = px; out[k, 4] = sl; out[k, 5] = tp; out[k, 6] = ex; out[k, 7] = hold; k += 1
            break
    return out[:k]


# ------------------------------------------------------------------------------------------------ F2 kernels
@njit(cache=True)
def _ib(h, l, sm, ro, de, t_end):
    nd = len(ro); H = np.full(nd, np.nan); L = np.full(nd, np.nan); I0 = np.full(nd, -1, np.int64)
    for d in range(nd):
        r = ro[d]
        if r < 1 or sm[r] != T930: continue
        hi = -1e18; lo = 1e18; cnt = 0; j = r
        while j <= de[d] and sm[j] < t_end:
            if h[j] > hi: hi = h[j]
            if l[j] < lo: lo = l[j]
            cnt += 1; j += 1
        if cnt < (t_end - T930) - 5 or j > de[d]: continue
        H[d] = hi; L[d] = lo; I0[d] = j
    return H, L, I0


@njit(cache=True)
def _ibfade(o, h, l, c, sm, day, atr, trend, vw, IBH, IBL, I0, x, sk, dmin, ent, tf, t1):
    n = len(c); nd = len(I0); out = np.zeros((2 * nd, 8)); k = 0
    for d in range(nd):
        i0 = I0[d]; A = atr[d]
        if i0 < 1 or A <= 0 or np.isnan(IBH[d]): continue
        upl = IBH[d] + x * A; dnl = IBL[d] - x * A; doneH = False; doneL = False; j = i0
        while j < n and day[j] == d and sm[j] < t1:
            for ii in range(2):
                sd = 1 - 2 * ii
                if ii == 0 and doneH: continue
                if ii == 1 and doneL: continue
                lv = upl if sd == 1 else dnl
                if sd == 1:
                    if h[j] < lv: continue
                else:
                    if l[j] > lv: continue
                if ii == 0: doneH = True
                else: doneL = True
                dr = -sd
                if tf == 1 and trend[d] != dr: continue
                si = j if ent == 0 else j - 1
                v = vw[si]
                if np.isnan(v) or (lv - v) * sd < dmin * A: continue
                if ent == 0: px = c[j]; et = 0; ex = j + 1
                else: px = lv; et = 1; ex = j + 30
                if sk > 0: risk = sk * A + (lv - px) * sd
                else: risk = min(2.0 * (lv - v) * sd, 0.5 * A) + (lv - px) * sd
                if risk < RMIN * A: risk = RMIN * A
                if risk > RMAX * A: continue
                sl = px - dr * risk; tp = v
                if (tp - px) * dr < 2 * TICK: continue
                out[k, 0] = si; out[k, 1] = dr; out[k, 2] = et; out[k, 3] = px; out[k, 4] = sl; out[k, 5] = tp; out[k, 6] = ex; out[k, 7] = HOLD; k += 1
            j += 1
    return out[:k]


@njit(cache=True)
def _ibbreak(o, h, l, c, sm, day, atr, trend, vw, IBH, IBL, I0, b, ctx, st, R, t1):
    n = len(c); nd = len(I0); out = np.zeros((nd, 8)); k = 0
    for d in range(nd):
        i0 = I0[d]; A = atr[d]
        if i0 < 1 or A <= 0 or np.isnan(IBH[d]): continue
        bp = TICK if b <= 0 else b * A; up = IBH[d] + bp; dn = IBL[d] - bp; rng = IBH[d] - IBL[d]; j = i0
        while j < n and day[j] == d and sm[j] < t1:
            bu = h[j] >= up; bd = l[j] <= dn
            if bu and bd: break
            if bu or bd:
                dr = 1 if bu else -1; px = up if bu else dn; si = j - 1
                if (ctx == 1 or ctx == 3) and trend[d] != dr: break
                if ctx == 2 or ctx == 3:
                    v = vw[si]
                    if np.isnan(v) or (c[si] - v) * dr <= 0: break
                sl0 = 0.5 * (IBH[d] + IBL[d]) if st == 0 else (dn if dr == 1 else up)
                risk = (px - sl0) * dr
                if risk < RMIN * A: risk = RMIN * A
                if risk > RMAX * A: break
                sl = px - dr * risk; tp = px + dr * (R * risk if R > 0 else rng)
                if (tp - px) * dr < 2 * TICK: break
                out[k, 0] = si; out[k, 1] = dr; out[k, 2] = 2; out[k, 3] = px; out[k, 4] = sl; out[k, 5] = tp; out[k, 6] = j; out[k, 7] = HOLD; k += 1
                break
            j += 1
    return out[:k]


@njit(cache=True)
def _ibreclaim(o, h, l, c, sm, day, atr, trend, vw, IBH, IBL, I0, b, sk, tg, wait, tf, t1):
    n = len(c); nd = len(I0); out = np.zeros((2 * nd, 8)); k = 0
    for d in range(nd):
        i0 = I0[d]; A = atr[d]
        if i0 < 1 or A <= 0 or np.isnan(IBH[d]): continue
        bp = TICK if b <= 0 else b * A; up = IBH[d] + bp; dn = IBL[d] - bp
        stH = 0; stL = 0; extH = 0.0; extL = 0.0; tbH = 0; tbL = 0; j = i0
        while j < n and day[j] == d and sm[j] < t1:
            if stH == 0 and h[j] >= up: stH = 1; extH = h[j]; tbH = j
            if stH == 1:
                if h[j] > extH: extH = h[j]
                if j - tbH > wait: stH = 2
                elif not np.isnan(vw[j]) and c[j] < vw[j]:
                    stH = 2
                    if tf == 0 or trend[d] == -1:
                        px = c[j]; risk = (extH - px) + 0.05 * A if sk <= 0 else sk * A
                        if risk < RMIN * A: risk = RMIN * A
                        if risk <= RMAX * A:
                            sl = px + risk; tp = IBL[d] if tg <= 0 else px - tg * risk
                            if px - tp >= 2 * TICK:
                                out[k, 0] = j; out[k, 1] = -1; out[k, 2] = 0; out[k, 3] = px; out[k, 4] = sl; out[k, 5] = tp; out[k, 6] = j + 1; out[k, 7] = HOLD; k += 1
            if stL == 0 and l[j] <= dn: stL = 1; extL = l[j]; tbL = j
            if stL == 1:
                if l[j] < extL: extL = l[j]
                if j - tbL > wait: stL = 2
                elif not np.isnan(vw[j]) and c[j] > vw[j]:
                    stL = 2
                    if tf == 0 or trend[d] == 1:
                        px = c[j]; risk = (px - extL) + 0.05 * A if sk <= 0 else sk * A
                        if risk < RMIN * A: risk = RMIN * A
                        if risk <= RMAX * A:
                            sl = px - risk; tp = IBH[d] if tg <= 0 else px + tg * risk
                            if tp - px >= 2 * TICK:
                                out[k, 0] = j; out[k, 1] = 1; out[k, 2] = 0; out[k, 3] = px; out[k, 4] = sl; out[k, 5] = tp; out[k, 6] = j + 1; out[k, 7] = HOLD; k += 1
            j += 1
    return out[:k]


# ------------------------------------------------------------------------------------------------ helpers / caches
def _c13(D):
    if not hasattr(D, "_c13"): D._c13 = {}
    return D._c13


def dt_setups(D, bar, k, tol):
    C = _c13(D); key = ("set", bar, k, tol)
    if key in C: return C[key]
    B = D.bars(bar); pk = ("piv", bar, k)
    if pk not in C: C[pk] = _pivots(np.ascontiguousarray(B["h"]), np.ascontiguousarray(B["l"]), k)
    ph, pl = C[pk]
    st = _setups(np.ascontiguousarray(B["h"]), np.ascontiguousarray(B["l"]), np.ascontiguousarray(B["last"]).astype(np.int64), np.ascontiguousarray(B["day"]).astype(np.int64),
                 D.atr.astype(np.float64), ph, pl, k, float(tol), 4 * TICK)
    C[key] = tuple(np.ascontiguousarray(st[:, i]) for i in range(4)); return C[key]


def sma1m(D, bar):
    """SMA of 200 completed tf bars known at each 1m bar (the bar's own tf bar counts only on its last 1m bar)."""
    C = _c13(D); key = ("sma", bar)
    if key in C: return C[key]
    B = D.bars(bar); bc = B["c"]; nb = len(bc)
    s = pd.Series(bc).rolling(200, min_periods=200).mean().to_numpy()
    idx = np.repeat(np.arange(nb), B["last"] - B["first"] + 1)
    out = np.where(idx > 0, s[np.maximum(idx - 1, 0)], np.nan); out[B["last"]] = s
    C[key] = np.ascontiguousarray(out, dtype=np.float64); return C[key]


def _nan(D):
    return np.full(D.n, np.nan)


def _ev(arr):
    return ev_from_lists(arr.tolist())


def _base(D):
    return (D.o, D.h, D.l, D.c, D.sm, D.day, D.atr.astype(np.float64), D.trend)


def ib_levels(D, ib):
    C = _c13(D); key = ("ib", ib)
    if key not in C: C[key] = _ib(D.h, D.l, D.sm, D.ro, D.de, T930 + ib)
    return C[key]


# ------------------------------------------------------------------------------------------------ generators
def _dt(D, p, mode):
    side, qi, L, ref = dt_setups(D, p["bar"], p["k"], p["tol"])
    sma = sma1m(D, p["bar"]) if p["filt"] == "sma200" else _nan(D)
    st = 0.0 if p.get("st", "mid") == "mid" else float(p["st"]); tgt = 0.0 if p.get("tgt", "mid") == "mid" else float(p["tgt"])
    ent = 1 if p.get("ent", "stop") == "lim" else 0
    out = _dt_scan(*_base(D), D.vwap, D.svwap, sma, side, qi, L, ref, mode, float(p["b"]), WIN[p["win"]], FILT[p["filt"]], st, float(p.get("R", 0.0)), ent, tgt, LIFE * p["bar"])
    return _ev(out)


def gen_dt_cont(D, p): return _dt(D, p, 0)
def gen_dt_rev(D, p): return _dt(D, p, 1)


PAT = dict(bar=(5, 15), k=(2, 5), tol=(0.0, 0.02, 0.05, 0.10), win=("rth", "on"), filt=("none", "vwap", "sma200", "trend"))
GRID_DT_CONT = grid(**PAT, b=(0.0, 0.05), st=("mid", 0.25), R=(1.0, 2.0, 0.0))
GRID_DT_REV = grid(**PAT, b=(0.0, 0.05), ent=("stop", "lim"), tgt=(0.5, 1.5, "mid"))


def gen_ib_fade(D, p):
    H, L, I0 = ib_levels(D, p["ib"])
    return _ev(_ibfade(*_base(D), D.vwap, H, L, I0, float(p["x"]), float(p["sk"]), float(p["d"]), 1 if p["ent"] == "lim" else 0, p["tf"], T1500))


def gen_ib_break(D, p):
    H, L, I0 = ib_levels(D, p["ib"]); ctx = {"none": 0, "trend": 1, "vwap": 2, "both": 3}[p["ctx"]]
    return _ev(_ibbreak(*_base(D), D.vwap, H, L, I0, float(p["b"]), ctx, 0 if p["st"] == "mid" else 1, float(p["R"]), T1500))


def gen_ib_reclaim(D, p):
    H, L, I0 = ib_levels(D, p["ib"])
    return _ev(_ibreclaim(*_base(D), D.vwap, H, L, I0, float(p["b"]), float(p["sk"]), float(p["tg"]), p["wait"], p["tf"], T1500))


GRID_IB_FADE = grid(ib=(30, 60), x=(0.0, 0.05, 0.1), sk=(0.0, 0.15, 0.25, 0.35), d=(0.1, 0.2, 0.3), ent=("lim", "mkt"), tf=(0, 1))
GRID_IB_BREAK = grid(ib=(30, 60), b=(0.0, 0.05, 0.1), ctx=("none", "trend", "vwap", "both"), st=("mid", "opp"), R=(1.0, 2.0, 0.0))
GRID_IB_RECLAIM = grid(ib=(30, 60), b=(0.0, 0.05), sk=(0.0, 0.25), tg=(0.0, 1.0, 2.0), wait=(60, 120), tf=(0, 1))

FAMILIES13 = {"DT_CONT": (gen_dt_cont, GRID_DT_CONT, 2), "DT_REV": (gen_dt_rev, GRID_DT_REV, 2),
              "IB_FADE": (gen_ib_fade, GRID_IB_FADE, 2), "IB_BREAK": (gen_ib_break, GRID_IB_BREAK, 2), "IB_RECLAIM": (gen_ib_reclaim, GRID_IB_RECLAIM, 2)}

if __name__ == "__main__":
    print({k: len(v[1]) for k, v in FAMILIES13.items()}, sum(len(v[1]) for v in FAMILIES13.values()))
