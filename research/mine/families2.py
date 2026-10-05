"""Second batch of classic families: volatility breakout (L. Williams), floor/Camarilla pivots, round numbers, prior-week levels,
RSI divergence at session extremes, overnight-inventory fade, inside-day breakout."""
import itertools, numpy as np, pandas as pd
from numba import njit
from core import S, TICK, ev_from_lists
from families import grid, _lfade, _lretest


@njit(cache=True)
def _volbreak(o, h, l, c, sm, ds, de, atr, trend, ro, pdh, pdl, k_, s_k, R, tf, w1, hold, stopmode):
    out = np.zeros((len(ds), 8)); kk = 0
    for d in range(len(ds)):
        r = ro[d]
        if r < 0 or atr[d] <= 0 or np.isnan(pdh[d]): continue
        a = atr[d]; rng = pdh[d] - pdl[d]; up = o[r] + k_ * rng; dn = o[r] - k_ * rng
        for i in range(r, de[d] + 1):
            if sm[i] >= w1: break
            s = 0
            if h[i] >= up: s = 1
            elif l[i] <= dn: s = -1
            if s == 0: continue
            if tf == 1 and s != trend[d]: break
            px = up if s == 1 else dn
            sl = px - s * s_k * a if stopmode == 1 else o[r]
            if (px - sl) * s <= 0: break
            tp = px + s * R * abs(px - sl)
            out[kk, 0] = i - 1; out[kk, 1] = s; out[kk, 2] = 2; out[kk, 3] = px; out[kk, 4] = sl; out[kk, 5] = tp; out[kk, 6] = i; out[kk, 7] = hold; kk += 1
            break
    return out[:kk]

def gen_volbreak(D, p):
    return ev_from_lists(_volbreak(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, D.ro, D.L[:, 0], D.L[:, 3], p["k"], p["s"], p["R"], p["tf"], S(p["w1"]), p["hold"], p["stop"]).tolist())
GRID_VOLBREAK = grid(k=(0.2, 0.3, 0.45, 0.6), s=(0.2, 0.35), R=(1.0, 2.0, 50.0), tf=(0, 1), w1=(1200, 1500), hold=(400,), stop=(0, 1))


def pivots(D, kind):
    H, L, C = D.L[:, 0], D.L[:, 3], D.pdc
    P = (H + L + C) / 3
    if kind == "R1S1": return 2 * P - L, 2 * P - H
    if kind == "R2S2": return P + (H - L), P - (H - L)
    if kind == "CAM3": return C + (H - L) * 1.1 / 4, C - (H - L) * 1.1 / 4
    if kind == "CAM4": return C + (H - L) * 1.1 / 2, C - (H - L) * 1.1 / 2
    return P, P

def gen_pivfade(D, p):
    LH, LL = pivots(D, p["piv"])
    return ev_from_lists(_lfade(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, LH, LL, S(p["w0"]), S(p["w1"]), p["sweep"], p["conf"], p["tg"], p["R"], p["tf"], p["hold"], D.vwap).tolist())
def gen_pivbreak(D, p):
    LH, LL = pivots(D, p["piv"])
    return ev_from_lists(_lretest(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, LH, LL, S(p["w0"]), S(p["w1"]), p["bk"], p["s"], p["R"], p["tf"], 60, p["hold"]).tolist())
GRID_PIVFADE = grid(piv=("R1S1", "R2S2", "CAM3", "PIVOT"), w0=(930, 1000), w1=(1300, 1530), sweep=(0.0, 0.03), conf=(3, 10), tg=(0, 1), R=(1.0, 2.0), tf=(0, 1), hold=(240,))
GRID_PIVBREAK = grid(piv=("R1S1", "CAM4", "R2S2"), w0=(930, 1000), w1=(1300, 1500), bk=(0.03, 0.1), s=(0.1, 0.2), R=(0.5, 1.0, 2.0), tf=(0, 1), hold=(240,))


def round_levels(D, step):
    pc = D.pdc; return np.ceil(pc / step) * step, np.floor(pc / step) * step
def gen_round(D, p):
    LH, LL = round_levels(D, p["step"])
    if p["mode"] == "fade":
        return ev_from_lists(_lfade(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, LH, LL, S(p["w0"]), S(p["w1"]), 0.0, p["conf"], 0, p["R"], p["tf"], p["hold"], D.vwap).tolist())
    return ev_from_lists(_lretest(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, LH, LL, S(p["w0"]), S(p["w1"]), 0.03, 0.15, p["R"], p["tf"], 60, p["hold"]).tolist())
GRID_ROUND = grid(step=(100.0, 250.0, 500.0), mode=("fade", "break"), w0=(930, 1000), w1=(1300, 1530), conf=(3, 10), R=(0.5, 1.0, 2.0), tf=(0, 1), hold=(240,))


def week_levels(D):
    dd = pd.to_datetime(pd.Series(D.daydate).astype(str), format="%Y%m%d", errors="coerce")
    iso = dd.dt.isocalendar(); wk = (iso.year.astype("float") * 100 + iso.week.astype("float")).to_numpy()
    rth = (D.om >= 570) & (D.om < 960)
    df = pd.DataFrame(dict(day=D.day[rth], h=D.h[rth], l=D.l[rth]))
    g = df.groupby("day").agg(h=("h", "max"), l=("l", "min")).reindex(range(D.nd)); g["wk"] = wk
    w = g.groupby("wk").agg(h=("h", "max"), l=("l", "min")).shift(1)
    return g.wk.map(w.h).to_numpy().astype(np.float64), g.wk.map(w.l).to_numpy().astype(np.float64)
def gen_week(D, p):
    if not hasattr(D, "_wkl"): D._wkl = week_levels(D)
    LH, LL = D._wkl
    if p["mode"] == "fade":
        return ev_from_lists(_lfade(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, LH, LL, S(p["w0"]), S(p["w1"]), p["sweep"], 10, 0, p["R"], p["tf"], p["hold"], D.vwap).tolist())
    return ev_from_lists(_lretest(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, LH, LL, S(p["w0"]), S(p["w1"]), 0.05, 0.2, p["R"], p["tf"], 60, p["hold"]).tolist())
GRID_WEEK = grid(mode=("fade", "break"), w0=(930, 1000), w1=(1300, 1530), sweep=(0.0, 0.05), R=(0.5, 1.0, 2.0), tf=(0, 1), hold=(240, 400))


@njit(cache=True)
def _div(o, h, l, c, sme, last, day, atr, trend, w0, w1, rsi_n, lb, R, tf, hold, extreme):
    n = len(c); out = np.zeros((n // 4 + 10, 8)); k = 0; cur = -1; cnt = 0
    up = 0.0; dn = 0.0; rsi = np.full(n, 50.0); al = 1.0 / rsi_n
    for i in range(1, n):
        ch = c[i] - c[i - 1]; up = (1 - al) * up + al * max(ch, 0.0); dn = (1 - al) * dn + al * max(-ch, 0.0)
        rsi[i] = 100 - 100 / (1 + up / dn) if dn > 0 else 50.0
    for i in range(lb + 2, n):
        d = day[i]
        if d != cur: cur = d; cnt = 0
        if sme[i] < w0 or sme[i] >= w1 or cnt >= 2 or day[i - lb] != d: continue
        a = atr[d]
        if a <= 0: continue
        hh = -1e18; ll = 1e18; ih = -1; il = -1
        for j in range(i - lb, i):
            if h[j] > hh: hh = h[j]; ih = j
            if l[j] < ll: ll = l[j]; il = j
        s = 0
        if h[i] > hh and rsi[i] < rsi[ih] - extreme and c[i] < o[i]: s = -1
        elif l[i] < ll and rsi[i] > rsi[il] + extreme and c[i] > o[i]: s = 1
        if s == 0: continue
        if tf == 1 and s != trend[d]: continue
        sl = (h[i] + 0.02 * a) if s == -1 else (l[i] - 0.02 * a)
        risk = (c[i] - sl) * s
        if risk <= 0 or risk > 0.5 * a: continue
        out[k, 0] = last[i]; out[k, 1] = s; out[k, 2] = 0; out[k, 3] = c[i]; out[k, 4] = sl; out[k, 5] = c[i] + s * R * risk; out[k, 6] = last[i]; out[k, 7] = hold
        k += 1; cnt += 1
    return out[:k]
def gen_div(D, p):
    B = D.bars(p["tf5"])
    return ev_from_lists(_div(B["o"], B["h"], B["l"], B["c"], B["sme"], B["last"], B["day"], D.atr, D.trend, S(p["w0"]), S(p["w1"]), p["rsi"], p["lb"], p["R"], p["tf"], p["hold"], p["ex"]).tolist())
GRID_DIV = grid(tf5=(5, 15), rsi=(6, 14), lb=(12, 24), R=(1.0, 2.0, 3.0), tf=(0, 1), w0=(1000,), w1=(1500,), hold=(120, 400), ex=(2.0, 5.0))


@njit(cache=True)
def _onfade(o, h, l, c, sm, ds, de, atr, trend, ro, pdc, x, T, s_k, tgmode, R, tf, hold):
    out = np.zeros((len(ds), 8)); k = 0
    for d in range(len(ds)):
        r = ro[d]
        if r < 0 or atr[d] <= 0 or np.isnan(pdc[d]): continue
        a = atr[d]; mv = (o[r] - pdc[d]) / a
        if abs(mv) < x: continue
        s = -1 if mv > 0 else 1
        if tf == 1 and s != trend[d]: continue
        j = r + T
        if j > de[d]: continue
        sl = c[j] - s * s_k * a
        tp = pdc[d] if tgmode == 1 else c[j] + s * R * s_k * a
        if (tp - c[j]) * s <= 0: continue
        out[k, 0] = j; out[k, 1] = s; out[k, 2] = 0; out[k, 3] = c[j]; out[k, 4] = sl; out[k, 5] = tp; out[k, 6] = j; out[k, 7] = hold; k += 1
    return out[:k]
def gen_onfade(D, p):
    return ev_from_lists(_onfade(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, D.ro, D.pdc, p["x"], p["T"], p["s"], p["tg"], p["R"], p["tf"], p["hold"]).tolist())
GRID_ONFADE = grid(x=(0.15, 0.3, 0.5), T=(0, 5, 15, 30), s=(0.15, 0.25, 0.4), tg=(0, 1), R=(0.5, 1.0), tf=(0, 1), hold=(60, 240))


@njit(cache=True)
def _insday(o, h, l, c, sm, ds, de, atr, trend, ro, pdh, pdl, ppdh, ppdl, w1, R, tf, hold, cap):
    out = np.zeros((len(ds), 8)); k = 0
    for d in range(len(ds)):
        r = ro[d]
        if r < 0 or atr[d] <= 0 or np.isnan(ppdh[d]) or np.isnan(pdh[d]): continue
        if not (pdh[d] < ppdh[d] and pdl[d] > ppdl[d]): continue
        a = atr[d]
        for i in range(r, de[d] + 1):
            if sm[i] >= w1: break
            s = 0
            if h[i] >= pdh[d] + TICK: s = 1
            elif l[i] <= pdl[d] - TICK: s = -1
            if s == 0: continue
            if tf == 1 and s != trend[d]: break
            px = pdh[d] + TICK if s == 1 else pdl[d] - TICK
            dist = min(pdh[d] - pdl[d], cap * a)
            out[k, 0] = i - 1; out[k, 1] = s; out[k, 2] = 2; out[k, 3] = px; out[k, 4] = px - s * dist; out[k, 5] = px + s * R * dist; out[k, 6] = i; out[k, 7] = hold; k += 1
            break
    return out[:k]
def gen_insday(D, p):
    pdh, pdl = D.L[:, 0], D.L[:, 3]
    return ev_from_lists(_insday(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, D.ro, pdh, pdl, np.r_[np.nan, pdh[:-1]], np.r_[np.nan, pdl[:-1]], S(p["w1"]), p["R"], p["tf"], p["hold"], p["cap"]).tolist())
GRID_INSDAY = grid(w1=(1200, 1500), R=(0.5, 1.0, 2.0), tf=(0, 1), hold=(240, 400), cap=(0.25, 0.5))

FAMILIES2 = {"VOL_BREAK": (gen_volbreak, GRID_VOLBREAK, 1), "PIVOT_FADE": (gen_pivfade, GRID_PIVFADE, 2), "PIVOT_BREAK": (gen_pivbreak, GRID_PIVBREAK, 2),
             "ROUND_NUM": (gen_round, GRID_ROUND, 2), "WEEK_LEVEL": (gen_week, GRID_WEEK, 2), "RSI_DIV": (gen_div, GRID_DIV, 2),
             "ON_INVENTORY": (gen_onfade, GRID_ONFADE, 1), "INSIDE_DAY": (gen_insday, GRID_INSDAY, 1)}
