"""Strategy families for the miner. Each family: gen(D, p) -> event dict (core.ev_from_lists format), plus a grid of params.
All features are known at signal time (no look-ahead). Windows are in ET (converted to session minutes)."""
import itertools, numpy as np
from numba import njit
from core import S, TICK, ev_from_lists

BIG = 100000

# ---------------------------------------------------------------- helpers
@njit(cache=True)
def win_range(h, l, c, v, sm, ds, de, a, b, atr, bs_k):
    """Per day: range high/low, POC (volume spread over price bins of size bs_k*ATR) and last index of window [a,b)."""
    nd = len(ds); H = np.full(nd, np.nan); Lo = np.full(nd, np.nan); P = np.full(nd, np.nan); E = np.full(nd, -1)
    for d in range(nd):
        if ds[d] < 0 or atr[d] <= 0: continue
        hi = -1e18; lo = 1e18; last = -1
        for i in range(ds[d], de[d] + 1):
            if sm[i] >= a and sm[i] < b:
                if h[i] > hi: hi = h[i]
                if l[i] < lo: lo = l[i]
                last = i
        if last < 0: continue
        bs = max(0.25, bs_k * atr[d]); nb = int((hi - lo) / bs) + 1
        if nb > 2000: nb = 2000
        hist = np.zeros(nb)
        for i in range(ds[d], last + 1):
            if sm[i] >= a and sm[i] < b:
                b0 = int((l[i] - lo) / bs); b1 = int((h[i] - lo) / bs)
                if b0 < 0: b0 = 0
                if b1 >= nb: b1 = nb - 1
                w = v[i] / (b1 - b0 + 1)
                for q in range(b0, b1 + 1): hist[q] += w
        k = np.argmax(hist)
        H[d] = hi; Lo[d] = lo; P[d] = lo + (k + 0.5) * bs; E[d] = last
    return H, Lo, P, E


@njit(cache=True)
def idx_at(sm, ds, de, t):
    nd = len(ds); out = np.full(nd, -1)
    for d in range(nd):
        if ds[d] < 0: continue
        for i in range(ds[d], de[d] + 1):
            if sm[i] >= t:
                if sm[i] < t + 15: out[d] = i
                break
    return out


def grid(**kw):
    keys = list(kw); return [dict(zip(keys, vals)) for vals in itertools.product(*kw.values())]

# ---------------------------------------------------------------- F1 AMD: accumulation -> sweep -> POC retest
WINDOWS = {"ASIA18-00": (1800, 0, 300), "ASIA20-00": (2000, 0, 300), "LON00-03": (0, 300, 600), "PRE08-0930": (800, 930, 1100),
           "IB0930-1030": (930, 1030, 1300), "LUNCH12-1330": (1200, 1330, 1530), "ON18-0930": (1800, 930, 1130)}

@njit(cache=True)
def _amd(o, h, l, c, sm, ds, de, atr, trend, H, Lo, P, E, m_end, sweep_k, conf, em, st, sk, tg, R, wmax, tf, exp_m, hold):
    out = np.zeros((len(ds), 8)); k = 0
    for d in range(len(ds)):
        if E[d] < 0 or atr[d] <= 0 or np.isnan(H[d]): continue
        a = atr[d]; hi = H[d]; lo = Lo[d]; poc = P[d]
        if hi - lo > wmax * a: continue
        side = 0; ext = 0.0; br = -1; ci = -1
        i = E[d] + 1
        while i <= de[d] and sm[i] < m_end:
            if side == 0:
                if h[i] > hi + sweep_k * a: side = -1; ext = h[i]; br = i      # swept highs -> short bias
                elif l[i] < lo - sweep_k * a: side = 1; ext = l[i]; br = i
                if side != 0 and ((side == -1 and c[i] < hi) or (side == 1 and c[i] > lo)): ci = i; break
            else:
                if side == -1: ext = max(ext, h[i])
                else: ext = min(ext, l[i])
                if (side == -1 and c[i] < hi) or (side == 1 and c[i] > lo): ci = i; break
                if i - br >= conf: break
            i += 1
        if ci < 0: continue
        if tf == 1 and side != trend[d]: continue
        sl_ext = ext - side * 0.02 * a                 # beyond the sweep extreme
        if em == 0:                                    # market at confirmation close
            ref = c[ci]; si = ci; t = 0; px = ref
        else:                                          # wait for displacement through POC, then limit at POC
            si = -1
            for j in range(ci, de[d] + 1):
                if sm[j] >= m_end + exp_m: break
                if (side == -1 and h[j] > ext) or (side == 1 and l[j] < ext): break
                if (side == -1 and c[j] < poc) or (side == 1 and c[j] > poc): si = j; break
            if si < 0: continue
            ref = poc; t = 1; px = poc
        sl = sl_ext if st == 0 else ref - side * sk * a
        risk = (sl - ref) * (-side)
        if risk <= 0: continue
        tp = 0.0
        if tg == 0: tp = lo if side == -1 else hi
        else: tp = ref + side * R * risk
        if (side == 1 and tp <= ref) or (side == -1 and tp >= ref): continue
        out[k, 0] = si; out[k, 1] = side; out[k, 2] = t; out[k, 3] = px; out[k, 4] = sl; out[k, 5] = tp
        out[k, 6] = si + exp_m; out[k, 7] = hold; k += 1
    return out[:k]

def cached_range(D, a, b, bs):
    if not hasattr(D, "_wr"): D._wr = {}
    key = (a, b, bs)
    if key not in D._wr: D._wr[key] = win_range(D.h, D.l, D.c, D.v, D.sm, D.ds, D.de, a, b, D.atr, bs)
    return D._wr[key]

def gen_amd(D, p):
    a0, a1, m1 = WINDOWS[p["win"]]
    H, Lo, P, E = cached_range(D, S(a0), S(a1), 0.01)
    ev = _amd(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, H, Lo, P, E, S(m1), p["sweep"], p["conf"], p["em"], p["st"], 0.15,
              p["tg"], p["R"], p["wmax"], p["tf"], 60, p["hold"])
    return ev_from_lists(ev.tolist())

GRID_AMD = [dict(win=w, sweep=s, conf=cf, em=em, st=st, tg=tg, R=R, wmax=wm, tf=tf, hold=240)
            for w, s, cf, em, st, (tg, R), wm, tf in itertools.product(WINDOWS, (0.0, 0.05), (5, 15), (0, 1), (0, 1), ((0, 0), (1, 1.0), (1, 2.0)), (0.5, 1.5), (0, 1))]

# ---------------------------------------------------------------- F2 session range breakout (stop entry, first breach)
@njit(cache=True)
def _rbreak(h, l, c, sm, ds, de, atr, trend, H, Lo, E, m_end, cap, tgR, wmin, wmax, tf, hold, stopmode):
    out = np.zeros((len(ds), 8)); k = 0
    for d in range(len(ds)):
        if E[d] < 0 or atr[d] <= 0: continue
        a = atr[d]; hi = H[d]; lo = Lo[d]; w = hi - lo
        if w < wmin * a or w > wmax * a: continue
        for i in range(E[d] + 1, de[d] + 1):
            if sm[i] >= m_end: break
            up = h[i] >= hi + TICK; dn = l[i] <= lo - TICK
            if up and dn: break
            if up or dn:
                s = 1 if up else -1
                if tf == 1 and s != trend[d]: break
                px = hi + TICK if s == 1 else lo - TICK
                if stopmode == 0: dist = min(w, cap * a)
                else: dist = min(w / 2, cap * a)
                sl = px - s * dist; tp = px + s * tgR * dist
                out[k, 0] = i - 1; out[k, 1] = s; out[k, 2] = 2; out[k, 3] = px; out[k, 4] = sl; out[k, 5] = tp; out[k, 6] = i; out[k, 7] = hold; k += 1
                break
    return out[:k]

def gen_rbreak(D, p):
    a0, a1, m1 = WINDOWS[p["win"]]
    H, Lo, P, E = cached_range(D, S(a0), S(a1), 0.01)
    return ev_from_lists(_rbreak(D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, H, Lo, E, S(m1), p["cap"], p["R"], p["wmin"], p["wmax"], p["tf"], p["hold"], p["sm"]).tolist())

GRID_RBREAK = grid(win=list(WINDOWS), cap=(0.2, 0.35), R=(0.5, 1.0, 2.0), wmin=(0.0, 0.2), wmax=(0.6, 2.0), tf=(0, 1), hold=(240,), sm=(0, 1))

# ---------------------------------------------------------------- F3 level breakout -> retest (limit at the level)
LEVELS = {"PD": (0, 3), "ON": (1, 4), "LONDON": (2, 5), "VA": (-1, -1)}

@njit(cache=True)
def _lretest(o, h, l, c, sm, ds, de, atr, trend, LH, LL, w0, w1, bk, s_k, R, tf, expm, hold):
    out = np.zeros((2 * len(ds), 8)); k = 0
    for d in range(len(ds)):
        if ds[d] < 0 or atr[d] <= 0: continue
        a = atr[d]
        for side in (1, -1):
            lev = LH[d] if side == 1 else LL[d]
            if np.isnan(lev): continue
            if tf == 1 and side != trend[d]: continue
            done = False
            for i in range(ds[d], de[d] + 1):
                if sm[i] < w0: continue
                if sm[i] >= w1 or done: break
                if (side == 1 and c[i] > lev + bk * a) or (side == -1 and c[i] < lev - bk * a):
                    # require that the level was not already exceeded before the window (fresh break)
                    sl = lev - side * s_k * a; tp = lev + side * R * s_k * a
                    out[k, 0] = i; out[k, 1] = side; out[k, 2] = 1; out[k, 3] = lev; out[k, 4] = sl; out[k, 5] = tp; out[k, 6] = i + expm; out[k, 7] = hold; k += 1
                    done = True
    return out[:k]

def level_arrays(D, lv):
    if lv == "VA": return D.pd_vah, D.pd_val
    a, b = LEVELS[lv]; return D.L[:, a], D.L[:, b]

def gen_lretest(D, p):
    LH, LL = level_arrays(D, p["lv"])
    return ev_from_lists(_lretest(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, LH, LL, S(p["w0"]), S(p["w1"]), p["bk"], p["s"], p["R"], p["tf"], 60, p["hold"]).tolist())

GRID_LRETEST = grid(lv=list(LEVELS), w0=(930, 1000), w1=(1200, 1430), bk=(0.03, 0.1), s=(0.1, 0.2), R=(0.5, 1.0, 2.0), tf=(0, 1), hold=(240,))

# ---------------------------------------------------------------- F4 level sweep-and-reclaim fade (turtle soup at fixed levels)
@njit(cache=True)
def _lfade(o, h, l, c, sm, ds, de, atr, trend, LH, LL, w0, w1, sweep_k, conf, tgmode, R, tf, hold, vwap):
    out = np.zeros((2 * len(ds), 8)); k = 0
    for d in range(len(ds)):
        if ds[d] < 0 or atr[d] <= 0: continue
        a = atr[d]
        for side in (-1, 1):                      # side = trade direction; -1 fades the high level
            lev = LH[d] if side == -1 else LL[d]
            if np.isnan(lev): continue
            if tf == 1 and side != trend[d]: continue
            br = -1; ext = 0.0; pre = False
            for i in range(ds[d], de[d] + 1):
                if sm[i] < w0:
                    if (side == -1 and h[i] > lev) or (side == 1 and l[i] < lev): pre = True
                    continue
                if sm[i] >= w1 or pre: break
                if br < 0:
                    if (side == -1 and h[i] > lev + sweep_k * a) or (side == 1 and l[i] < lev - sweep_k * a): br = i; ext = h[i] if side == -1 else l[i]
                    else: continue
                if side == -1: ext = max(ext, h[i])
                else: ext = min(ext, l[i])
                if (side == -1 and c[i] < lev) or (side == 1 and c[i] > lev):
                    sl = ext - side * 0.02 * a; risk = (c[i] - sl) * side
                    if risk <= 0: break
                    if tgmode == 0: tp = c[i] + side * R * risk
                    else:
                        tp = vwap[i]
                        if np.isnan(tp) or (tp - c[i]) * side <= 0.25 * risk: break
                    out[k, 0] = i; out[k, 1] = side; out[k, 2] = 0; out[k, 3] = c[i]; out[k, 4] = sl; out[k, 5] = tp; out[k, 6] = i; out[k, 7] = hold; k += 1
                    break
                if i - br >= conf: break
    return out[:k]

def gen_lfade(D, p):
    LH, LL = level_arrays(D, p["lv"])
    return ev_from_lists(_lfade(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, LH, LL, S(p["w0"]), S(p["w1"]), p["sweep"], p["conf"], p["tg"], p["R"], p["tf"], p["hold"], D.vwap).tolist())

GRID_LFADE = grid(lv=list(LEVELS), w0=(930, 1000), w1=(1130, 1500), sweep=(0.0, 0.05), conf=(3, 10), tg=(0, 1), R=(1.0, 2.0), tf=(0, 1), hold=(240,))

# ---------------------------------------------------------------- F5 VWAP pullback in a trending day
@njit(cache=True)
def _vwpb(c, h, l, sm, ds, de, atr, trend, vwap, w0, w1, x, s_k, R, tf, expm, hold, off):
    out = np.zeros((len(ds), 8)); k = 0
    for d in range(len(ds)):
        if ds[d] < 0 or atr[d] <= 0: continue
        a = atr[d]; mx = 0.0; mn = 0.0
        for i in range(ds[d], de[d] + 1):
            if np.isnan(vwap[i]): continue
            dv = (c[i] - vwap[i]) / a
            mx = max(mx, dv); mn = min(mn, dv)
            if sm[i] < w0: continue
            if sm[i] >= w1: break
            side = 0
            if mx >= x and c[i] > vwap[i] + off * a: side = 1
            elif mn <= -x and c[i] < vwap[i] - off * a: side = -1
            if side == 0: continue
            if tf == 1 and side != trend[d]: continue
            px = vwap[i] + side * off * a; sl = px - side * s_k * a; tp = px + side * R * s_k * a
            out[k, 0] = i; out[k, 1] = side; out[k, 2] = 1; out[k, 3] = px; out[k, 4] = sl; out[k, 5] = tp; out[k, 6] = i + expm; out[k, 7] = hold; k += 1
            break
    return out[:k]

def gen_vwpb(D, p):
    return ev_from_lists(_vwpb(D.c, D.h, D.l, D.sm, D.ds, D.de, D.atr, D.trend, D.vwap, S(p["w0"]), S(p["w1"]), p["x"], p["s"], p["R"], p["tf"], p["exp"], p["hold"], p["off"]).tolist())

GRID_VWPB = grid(w0=(1000, 1100), w1=(1300, 1500), x=(0.15, 0.3, 0.5), s=(0.1, 0.2), R=(0.5, 1.0, 2.0), tf=(0, 1), exp=(60, 180), hold=(240,), off=(0.0, 0.03))

# ---------------------------------------------------------------- F6 VWAP band fade
@njit(cache=True)
def _vwband(c, sm, ds, de, atr, trend, vwap, vsd, w0, w1, m, s_k, tgmode, tf, hold, maxn):
    out = np.zeros((4 * len(ds), 8)); k = 0
    for d in range(len(ds)):
        if ds[d] < 0 or atr[d] <= 0: continue
        a = atr[d]; nn = 0; last = -100
        for i in range(ds[d], de[d] + 1):
            if sm[i] < w0 or np.isnan(vwap[i]) or vsd[i] <= 0: continue
            if sm[i] >= w1 or nn >= maxn: break
            side = 0
            if c[i] > vwap[i] + m * vsd[i]: side = -1
            elif c[i] < vwap[i] - m * vsd[i]: side = 1
            if side == 0 or i - last < 30: continue
            if tf == 1 and side != trend[d]: continue
            if tf == -1 and side == trend[d]: continue
            sl = c[i] - side * s_k * a
            tp = vwap[i] if tgmode == 0 else vwap[i] - side * vsd[i]
            if (tp - c[i]) * side <= 0: continue
            out[k, 0] = i; out[k, 1] = side; out[k, 2] = 0; out[k, 3] = c[i]; out[k, 4] = sl; out[k, 5] = tp; out[k, 6] = i; out[k, 7] = hold; k += 1
            nn += 1; last = i
    return out[:k]

def gen_vwband(D, p):
    return ev_from_lists(_vwband(D.c, D.sm, D.ds, D.de, D.atr, D.trend, D.vwap, D.vsd, S(p["w0"]), S(p["w1"]), p["m"], p["s"], p["tg"], p["tf"], p["hold"], 3).tolist())

GRID_VWBAND = grid(w0=(1000, 1100), w1=(1400, 1530), m=(2.0, 2.5, 3.0), s=(0.1, 0.2, 0.3), tg=(0, 1), tf=(0, 1, -1), hold=(60, 240))

# ---------------------------------------------------------------- F7 opening drive momentum / F8 opening-drive pullback
@njit(cache=True)
def _odrive(o, h, l, c, sm, ds, de, atr, trend, ro, T, x, stopmode, s_k, R, tf, hold, mode, f):
    out = np.zeros((len(ds), 8)); k = 0
    for d in range(len(ds)):
        r = ro[d]
        if r < 0 or atr[d] <= 0: continue
        a = atr[d]; op = o[r]; hi = -1e18; lo = 1e18; j = -1
        for i in range(r, de[d] + 1):
            if sm[i] - sm[r] >= T: j = i - 1; break
            hi = max(hi, h[i]); lo = min(lo, l[i])
        if j < 0: continue
        mv = c[j] - op
        if abs(mv) < x * a: continue
        side = 1 if mv > 0 else -1
        if tf == 1 and side != trend[d]: continue
        if mode == 0:                                   # momentum at end of drive
            sl = (lo - TICK if side == 1 else hi + TICK) if stopmode == 0 else c[j] - side * s_k * a
            risk = (c[j] - sl) * side
            if risk <= 0: continue
            if stopmode == 0 and risk > 0.5 * a: sl = c[j] - side * 0.5 * a; risk = 0.5 * a
            tp = c[j] + side * R * risk
            out[k, 0] = j; out[k, 1] = side; out[k, 2] = 0; out[k, 3] = c[j]; out[k, 4] = sl; out[k, 5] = tp; out[k, 6] = j; out[k, 7] = hold; k += 1
        else:                                           # limit at retracement f of the drive
            ext = hi if side == 1 else lo; base = lo if side == 1 else hi
            px = ext - side * f * abs(ext - base)
            sl = base - side * 0.02 * a; tp = ext if R <= 0 else px + side * R * abs(px - sl)
            if (px - sl) * side <= 0: continue
            out[k, 0] = j; out[k, 1] = side; out[k, 2] = 1; out[k, 3] = px; out[k, 4] = sl; out[k, 5] = tp; out[k, 6] = j + 120; out[k, 7] = hold; k += 1
    return out[:k]

def gen_odrive(D, p):
    return ev_from_lists(_odrive(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, D.ro, p["T"], p["x"], p["stop"], 0.2, p["R"], p["tf"], p["hold"], 0, 0.0).tolist())

def gen_odpb(D, p):
    return ev_from_lists(_odrive(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, D.ro, p["T"], p["x"], 0, 0.0, p["R"], p["tf"], p["hold"], 1, p["f"]).tolist())

GRID_ODRIVE = grid(T=(5, 15, 30, 60), x=(0.05, 0.15, 0.3), stop=(0, 1), R=(0.5, 1.0, 2.0), tf=(0, 1), hold=(120, 400))
GRID_ODPB = grid(T=(15, 30, 60), x=(0.1, 0.2, 0.35), f=(0.382, 0.5, 0.618), R=(0.0, 1.0, 2.0), tf=(0, 1), hold=(240,))

# ---------------------------------------------------------------- 5-minute pattern families
@njit(cache=True)
def _p5(kind, o, h, l, c, sme, last, day, ds_atr_d, atr, trend, vwap, w0, w1, N, s_k, R, tf, vwf, hold, maxday, extra):
    """kind: 0 donchian breakout, 1 consecutive-bar mean reversion, 2 fractal sweep, 3 FVG retest, 4 order-block retest,
    5 BB squeeze breakout, 6 engulfing at VWAP, 7 inside-bar (mother) breakout."""
    n = len(c); out = np.zeros((n // 4 + 10, 8)); k = 0; cur = -1; cnt = 0
    for i in range(60, n):
        d = day[i]
        if d != cur: cur = d; cnt = 0
        if sme[i] < w0 or sme[i] >= w1 or cnt >= maxday: continue
        a = atr[d]
        if a <= 0 or day[i - N - 2] != d: continue
        side = 0; t = 0; px = c[i]; sl = 0.0; tp = 0.0
        if kind == 0:
            hh = -1e18; ll = 1e18
            for j in range(i - N, i): hh = max(hh, h[j]); ll = min(ll, l[j])
            if c[i] > hh: side = 1
            elif c[i] < ll: side = -1
            if side != 0: sl = c[i] - side * s_k * a
        elif kind == 1:
            dn = True; up = True
            for j in range(i - N + 1, i + 1):
                if not (c[j] < c[j - 1]): dn = False
                if not (c[j] > c[j - 1]): up = False
            if dn: side = 1
            elif up: side = -1
            if side != 0: sl = c[i] - side * s_k * a
        elif kind == 2:
            w = N
            for j in range(i - 24, i - w):
                if day[j - w] != d: continue
                isH = True; isL = True
                for q in range(1, w + 1):
                    if not (h[j] > h[j - q] and h[j] > h[j + q]): isH = False
                    if not (l[j] < l[j - q] and l[j] < l[j + q]): isL = False
                if isH and h[i] > h[j] and c[i] < h[j]:
                    ok = True
                    for q in range(j + 1, i):
                        if h[q] > h[j]: ok = False
                    if ok: side = -1; sl = h[i] + 0.02 * a; break
                if isL and l[i] < l[j] and c[i] > l[j]:
                    ok = True
                    for q in range(j + 1, i):
                        if l[q] < l[j]: ok = False
                    if ok: side = 1; sl = l[i] - 0.02 * a; break
        elif kind == 3:
            if l[i] > h[i - 2] and (l[i] - h[i - 2]) >= extra * a: side = 1; t = 1; px = l[i]; sl = h[i - 2] - 0.02 * a
            elif h[i] < l[i - 2] and (l[i - 2] - h[i]) >= extra * a: side = -1; t = 1; px = h[i]; sl = l[i - 2] + 0.02 * a
        elif kind == 4:
            hh = -1e18; ll = 1e18
            for j in range(i - 6, i): hh = max(hh, h[j]); ll = min(ll, l[j])
            body = c[i] - o[i]
            if body >= extra * a and c[i] > hh:
                for j in range(i - 1, i - 4, -1):
                    if c[j] < o[j]: side = 1; t = 1; px = h[j]; sl = l[j] - 0.02 * a; break
            elif -body >= extra * a and c[i] < ll:
                for j in range(i - 1, i - 4, -1):
                    if c[j] > o[j]: side = -1; t = 1; px = l[j]; sl = h[j] + 0.02 * a; break
        elif kind == 5:
            m = 0.0; sd = 0.0
            for j in range(i - 19, i + 1): m += c[j]
            m /= 20
            for j in range(i - 19, i + 1): sd += (c[j] - m) ** 2
            sd = np.sqrt(sd / 20)
            wmin = 1e18
            for q in range(i - N, i):
                mq = 0.0; sq = 0.0
                for j in range(q - 19, q + 1): mq += c[j]
                mq /= 20
                for j in range(q - 19, q + 1): sq += (c[j] - mq) ** 2
                wmin = min(wmin, np.sqrt(sq / 20))
            if sd <= wmin * 1.1:
                if c[i] > m + 2 * sd: side = 1; sl = m
                elif c[i] < m - 2 * sd: side = -1; sl = m
        elif kind == 6:
            if np.isnan(vwap[i]): continue
            if c[i - 1] < o[i - 1] and c[i] > o[i] and c[i] >= o[i - 1] and o[i] <= c[i - 1] and min(l[i], l[i - 1]) <= vwap[i] + extra * a and c[i] > vwap[i]:
                side = 1; sl = min(l[i], l[i - 1]) - 0.02 * a
            elif c[i - 1] > o[i - 1] and c[i] < o[i] and c[i] <= o[i - 1] and o[i] >= c[i - 1] and max(h[i], h[i - 1]) >= vwap[i] - extra * a and c[i] < vwap[i]:
                side = -1; sl = max(h[i], h[i - 1]) + 0.02 * a
        elif kind == 7:
            mi = i - 1
            if h[i] < h[mi] and l[i] > l[mi] and (h[mi] - l[mi]) <= s_k * a:
                side = trend[d] if trend[d] != 0 else 0
                if side == 1: t = 2; px = h[mi] + TICK; sl = l[mi] - TICK
                elif side == -1: t = 2; px = l[mi] - TICK; sl = h[mi] + TICK
        if side == 0: continue
        if tf == 1 and side != trend[d]: continue
        if vwf == 1 and not np.isnan(vwap[i]) and (c[i] - vwap[i]) * side < 0: continue
        if vwf == -1 and not np.isnan(vwap[i]) and (c[i] - vwap[i]) * side > 0: continue
        risk = (px - sl) * side
        if risk <= 0 or risk > 0.6 * a: continue
        tp = px + side * R * risk
        out[k, 0] = last[i]; out[k, 1] = side; out[k, 2] = t; out[k, 3] = px; out[k, 4] = sl; out[k, 5] = tp
        out[k, 6] = last[i] + (60 if t == 1 else 5); out[k, 7] = hold; k += 1; cnt += 1
        if k >= len(out) - 1: break
    return out[:k]

P5_KINDS = {"DONCH": 0, "CONSEC": 1, "FRACTAL": 2, "FVG": 3, "OB": 4, "SQUEEZE": 5, "ENGULF": 6, "INSIDE": 7}

def gen_p5(D, p):
    B = D.bars(p.get("tf5", 5))
    return ev_from_lists(_p5(P5_KINDS[p["kind"]], B["o"], B["h"], B["l"], B["c"], B["sme"], B["last"], B["day"], D.atr, D.atr, D.trend, B["vwap"],
                             S(p["w0"]), S(p["w1"]), p["N"], p["s"], p["R"], p["tf"], p["vwf"], p["hold"], p["maxday"], p["extra"]).tolist())

GRID_P5 = (grid(kind=("DONCH",), N=(12, 24, 48), s=(0.15, 0.25), R=(1.0, 2.0), tf=(1,), vwf=(0, 1), w0=(1000,), w1=(1430,), hold=(120, 400), maxday=(2,), extra=(0.0,)) +
           grid(kind=("CONSEC",), N=(3, 4, 5), s=(0.15, 0.25), R=(0.3, 0.5, 1.0), tf=(1,), vwf=(0, 1), w0=(1000,), w1=(1530,), hold=(60, 240), maxday=(3,), extra=(0.0,)) +
           grid(kind=("FRACTAL",), N=(2, 3), s=(0.0,), R=(1.0, 2.0, 3.0), tf=(0, 1), vwf=(0, -1), w0=(1000,), w1=(1500,), hold=(120, 400), maxday=(2,), extra=(0.0,)) +
           grid(kind=("FVG",), N=(3,), s=(0.0,), R=(1.0, 2.0, 3.0), tf=(1,), vwf=(0, 1), w0=(1000,), w1=(1500,), hold=(120, 400), maxday=(2,), extra=(0.01, 0.03), tf5=(5, 15)) +
           grid(kind=("OB",), N=(6,), s=(0.0,), R=(1.0, 2.0, 3.0), tf=(1,), vwf=(0, 1), w0=(1000,), w1=(1500,), hold=(120, 400), maxday=(2,), extra=(0.05, 0.1), tf5=(5, 15)) +
           grid(kind=("SQUEEZE",), N=(24, 48), s=(0.0,), R=(1.0, 2.0), tf=(0, 1), vwf=(0, 1), w0=(1000,), w1=(1500,), hold=(120, 400), maxday=(2,), extra=(0.0,)) +
           grid(kind=("ENGULF",), N=(3,), s=(0.0,), R=(1.0, 1.5, 2.0), tf=(1,), vwf=(0,), w0=(1000,), w1=(1500,), hold=(120, 400), maxday=(2,), extra=(0.02, 0.05), tf5=(5, 15)) +
           grid(kind=("INSIDE",), N=(3,), s=(0.1, 0.2), R=(1.0, 2.0), tf=(1,), vwf=(0, 1), w0=(1000,), w1=(1500,), hold=(120, 400), maxday=(2,), extra=(0.0,), tf5=(15, 30)))

# ---------------------------------------------------------------- F9 value-area 80% rule
@njit(cache=True)
def _va80(o, h, l, c, sm, ds, de, atr, trend, ro, vah, val, w1, nb, s_k, tf, hold):
    out = np.zeros((len(ds), 8)); k = 0
    for d in range(len(ds)):
        r = ro[d]
        if r < 0 or atr[d] <= 0 or np.isnan(vah[d]): continue
        a = atr[d]; op = o[r]; side = 0
        if op > vah[d]: side = -1
        elif op < val[d]: side = 1
        if side == 0: continue
        if tf == 1 and side != trend[d]: continue
        inside = 0
        for i in range(r, de[d] + 1):
            if sm[i] >= w1: break
            if c[i] < vah[d] and c[i] > val[d]: inside += 1
            else: inside = 0
            if inside >= nb:
                tp = val[d] if side == -1 else vah[d]
                sl = c[i] - side * s_k * a
                if (tp - c[i]) * side <= 0: break
                out[k, 0] = i; out[k, 1] = side; out[k, 2] = 0; out[k, 3] = c[i]; out[k, 4] = sl; out[k, 5] = tp; out[k, 6] = i; out[k, 7] = hold; k += 1
                break
    return out[:k]

def gen_va80(D, p):
    return ev_from_lists(_va80(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, D.ro, D.pd_vah, D.pd_val, S(p["w1"]), p["nb"], p["s"], p["tf"], p["hold"]).tolist())

GRID_VA80 = grid(w1=(1100, 1300, 1500), nb=(5, 15, 30), s=(0.15, 0.25, 0.4), tf=(0, 1), hold=(120, 400))

# ---------------------------------------------------------------- F10 clock-time mean reversion / momentum vs anchors
@njit(cache=True)
def _clock(c, sm, ds, de, atr, trend, ref, anchor, T, x, mode, s_k, R, tgmode, tf, hold):
    """At time T: dist = (c - anchor)/ATR. mode 1 = momentum (trade in direction of dist), -1 = fade toward the anchor."""
    out = np.zeros((len(ds), 8)); k = 0
    for d in range(len(ds)):
        i = ref[d]
        if i < 0 or atr[d] <= 0 or np.isnan(anchor[i]): continue
        a = atr[d]; dist = (c[i] - anchor[i]) / a
        if abs(dist) < x: continue
        side = (1 if dist > 0 else -1) * mode
        if tf == 1 and side != trend[d]: continue
        sl = c[i] - side * s_k * a
        tp = anchor[i] if (tgmode == 1 and mode == -1) else c[i] + side * R * s_k * a
        if (tp - c[i]) * side <= 0: continue
        out[k, 0] = i; out[k, 1] = side; out[k, 2] = 0; out[k, 3] = c[i]; out[k, 4] = sl; out[k, 5] = tp; out[k, 6] = i; out[k, 7] = hold; k += 1
    return out[:k]

def anchor_array(D, name):
    if name == "VWAP": return D.vwap
    if name == "SVWAP": return D.svwap
    if name == "PDPOC": return D.pd_poc[D.day]
    if name == "PDC": return D.pdc[D.day]
    if name == "RTHOPEN":
        a = np.full(D.n, np.nan); ok = D.ro[D.day] >= 0; a[ok] = D.o[D.ro[D.day][ok]]
        a[D.sm < S(930)] = np.nan; return a
    if name == "SOPEN": return D.o[D.ds[D.day]]

def gen_clock(D, p):
    ref = idx_at(D.sm, D.ds, D.de, S(p["T"]))
    return ev_from_lists(_clock(D.c, D.sm, D.ds, D.de, D.atr, D.trend, ref, anchor_array(D, p["anc"]), S(p["T"]), p["x"], p["mode"], p["s"], p["R"], p["tg"], p["tf"], p["hold"]).tolist())

GRID_CLOCK = (grid(anc=("VWAP",), T=(1130, 1200, 1230, 1300, 1400), x=(0.15, 0.3, 0.45), mode=(-1, 1), s=(0.15, 0.25), R=(0.5, 1.0), tg=(0, 1), tf=(0, 1), hold=(120,)) +
              grid(anc=("SVWAP",), T=(2000, 2200, 0, 200, 400), x=(0.1, 0.2, 0.3), mode=(-1, 1), s=(0.15, 0.25), R=(0.5, 1.0), tg=(0, 1), tf=(0, 1), hold=(120,)) +
              grid(anc=("PDPOC", "PDC"), T=(1000, 1030, 1100), x=(0.2, 0.4), mode=(-1, 1), s=(0.15, 0.25), R=(0.5, 1.0), tg=(0, 1), tf=(0, 1), hold=(240,)) +
              grid(anc=("SOPEN",), T=(300, 400, 600, 800), x=(0.1, 0.2, 0.35), mode=(-1, 1), s=(0.15, 0.25), R=(0.5, 1.0), tg=(0,), tf=(0, 1), hold=(120, 330)))

# ---------------------------------------------------------------- F11 gap and go
@njit(cache=True)
def _gap(o, h, l, c, sm, ds, de, atr, trend, ro, pdc, x, nfirst, R, tf, hold, fade):
    out = np.zeros((len(ds), 8)); k = 0
    for d in range(len(ds)):
        r = ro[d]
        if r < 0 or atr[d] <= 0 or np.isnan(pdc[d]): continue
        a = atr[d]; g = (o[r] - pdc[d]) / a
        if abs(g) < x: continue
        side = 1 if g > 0 else -1
        if fade == 1: side = -side
        if tf == 1 and side != trend[d]: continue
        j = r + nfirst - 1
        if j > de[d]: continue
        hi = -1e18; lo = 1e18
        for i in range(r, j + 1): hi = max(hi, h[i]); lo = min(lo, l[i])
        if (c[j] - o[r]) * side <= 0: continue
        sl = lo - TICK if side == 1 else hi + TICK; risk = (c[j] - sl) * side
        if risk <= 0 or risk > 0.5 * a: continue
        tp = c[j] + side * R * risk if fade == 0 else pdc[d]
        if (tp - c[j]) * side <= 0: continue
        out[k, 0] = j; out[k, 1] = side; out[k, 2] = 0; out[k, 3] = c[j]; out[k, 4] = sl; out[k, 5] = tp; out[k, 6] = j; out[k, 7] = hold; k += 1
    return out[:k]

def gen_gap(D, p):
    return ev_from_lists(_gap(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, D.ro, D.pdc, p["x"], p["nf"], p["R"], p["tf"], p["hold"], p["fade"]).tolist())

GRID_GAP = grid(x=(0.05, 0.15, 0.3), nf=(5, 15, 30), R=(0.5, 1.0, 2.0), tf=(0, 1), hold=(120, 400), fade=(0, 1))

# ---------------------------------------------------------------- F12 HOD/LOD breakout -> retest of the old extreme
@njit(cache=True)
def _hodre(o, h, l, c, sm, ds, de, atr, trend, ro, w0, w1, bk, s_k, R, tf, expm, hold):
    out = np.zeros((len(ds), 8)); k = 0
    for d in range(len(ds)):
        r = ro[d]
        if r < 0 or atr[d] <= 0: continue
        a = atr[d]; hi = -1e18; lo = 1e18
        for i in range(r, de[d] + 1):
            if sm[i] >= w1: break
            if sm[i] >= w0:
                s = 0
                if c[i] > hi + bk * a: s = 1
                elif c[i] < lo - bk * a: s = -1
                if s != 0 and (tf == 0 or s == trend[d]):
                    lev = hi if s == 1 else lo
                    out[k, 0] = i; out[k, 1] = s; out[k, 2] = 1; out[k, 3] = lev; out[k, 4] = lev - s * s_k * a; out[k, 5] = lev + s * R * s_k * a
                    out[k, 6] = i + expm; out[k, 7] = hold; k += 1
                    break
            hi = max(hi, h[i]); lo = min(lo, l[i])
    return out[:k]

def gen_hodre(D, p):
    return ev_from_lists(_hodre(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, D.ro, S(p["w0"]), S(p["w1"]), p["bk"], p["s"], p["R"], p["tf"], p["exp"], p["hold"]).tolist())

GRID_HODRE = grid(w0=(1030, 1130), w1=(1400, 1500), bk=(0.02, 0.06), s=(0.1, 0.2), R=(0.5, 1.0, 2.0), tf=(0, 1), exp=(30, 90), hold=(240,))

FAMILIES = {"AMD_POC": (gen_amd, GRID_AMD, 1), "RANGE_BREAK": (gen_rbreak, GRID_RBREAK, 1), "LEVEL_RETEST": (gen_lretest, GRID_LRETEST, 2),
            "LEVEL_FADE": (gen_lfade, GRID_LFADE, 2), "VWAP_PULLBACK": (gen_vwpb, GRID_VWPB, 1), "VWAP_BAND": (gen_vwband, GRID_VWBAND, 3),
            "OPEN_DRIVE": (gen_odrive, GRID_ODRIVE, 1), "OD_PULLBACK": (gen_odpb, GRID_ODPB, 1), "PATTERN_5M": (gen_p5, GRID_P5, 2),
            "VA_80": (gen_va80, GRID_VA80, 1), "CLOCK_ANCHOR": (gen_clock, GRID_CLOCK, 1), "GAP": (gen_gap, GRID_GAP, 1), "HOD_RETEST": (gen_hodre, GRID_HODRE, 1)}
