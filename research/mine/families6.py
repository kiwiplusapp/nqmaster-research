"""Batch 6 (2026-10-16): 'NexGenAlgo System 1 - Trend-Pullback Buy-Stop' as described by Federico.
  Trend   : EMA3 > EMA7 > EMA50 on the bar timeframe (mirror for shorts).
  Vol     : ATR(14) flat or falling (atrm 0 = no check, 1 = ATR <= ATR 1 bar ago, 2 = ATR <= ATR 3 bars ago).
  Candle 1: a bar against the trend (bearish in an uptrend); pt 0 = any such bar, 1 = its low reaches EMA3, 2 = its low reaches EMA7.
  Entry   : buy stop 1 tick above candle-1 high, valid exp bars; stop 1 tick below its low; target R x risk (spec 2R).
  Window  : signal bar inside win ('all' 19:00-15:45 = 1 h after the 18:00 Globex reopen, 'night' 19:00-09:29, 'rth' 09:30-15:45);
            flat 15:55 (core). Side: long (spec), short (mirror), both.
EMAs / ATR run continuously over the tf bars (like a chart). Execution = core.execute (same costs as every other family)."""
import numpy as np
from numba import njit
from core import S, TICK, ev_from_lists
from families import grid

WIN = {"all": (1900, 1545), "night": (1900, 929), "rth": (930, 1545)}


@njit(cache=True)
def _ema(x, n):
    a = 2.0 / (n + 1); out = np.empty_like(x); out[0] = x[0]
    for i in range(1, len(x)): out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out


@njit(cache=True)
def _atr(h, l, c, n):
    out = np.empty_like(c); out[0] = h[0] - l[0]
    for i in range(1, len(c)):
        tr = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
        out[i] = out[i - 1] + (tr - out[i - 1]) / n
    return out


@njit(cache=True)
def _nga(o, h, l, c, sme, last, day, e3, e7, e50, atr, w0, w1, atrm, pt, exp, side, R, tf, minrisk):
    nb = len(c); out = np.zeros((nb, 8)); n = 0
    for t in range(60, nb):
        s = sme[t]
        if not (s >= w0 and s <= w1): continue
        if atrm == 1 and atr[t] > atr[t - 1]: continue
        if atrm == 2 and atr[t] > atr[t - 3]: continue
        for d in (1, -1):
            if side != 0 and d != side: continue
            if d == 1:
                if not (e3[t] > e7[t] and e7[t] > e50[t]): continue
                if not (c[t] < o[t]): continue
                if pt == 1 and l[t] > e3[t]: continue
                if pt == 2 and l[t] > e7[t]: continue
                px = h[t] + TICK; sl = l[t] - TICK
            else:
                if not (e3[t] < e7[t] and e7[t] < e50[t]): continue
                if not (c[t] > o[t]): continue
                if pt == 1 and h[t] < e3[t]: continue
                if pt == 2 and h[t] < e7[t]: continue
                px = l[t] - TICK; sl = h[t] + TICK
            risk = (px - sl) * d
            if risk < minrisk: continue
            out[n, 0] = last[t]; out[n, 1] = d; out[n, 2] = 2; out[n, 3] = px; out[n, 4] = sl; out[n, 5] = px + d * R * risk
            out[n, 6] = last[t] + exp * tf; out[n, 7] = 1440; n += 1
    return out[:n]


def gen_nga(D, p):
    B = D.bars(p["tf"]); key = f"_nga{p['tf']}"
    if not hasattr(D, key):
        setattr(D, key, (_ema(B["c"], 3), _ema(B["c"], 7), _ema(B["c"], 50), _atr(B["h"], B["l"], B["c"], 14)))
    e3, e7, e50, atr = getattr(D, key); w0, w1 = WIN[p["win"]]
    return ev_from_lists(_nga(B["o"], B["h"], B["l"], B["c"], B["sme"], B["last"], B["day"], e3, e7, e50, atr, S(w0), S(w1),
                              p["atrm"], p["pt"], p["exp"], p["side"], p["R"], p["tf"], 2 * TICK).tolist())


GRID_NGA = grid(tf=(5, 15, 60), atrm=(0, 1, 2), pt=(0, 1, 2), exp=(1, 3), win=tuple(WIN), side=(1, -1, 0), R=(1.0, 1.5, 2.0))
FAMILIES6 = {"NGA_PB": (gen_nga, GRID_NGA, 20)}
