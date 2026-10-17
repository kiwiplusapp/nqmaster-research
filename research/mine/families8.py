"""Batch 8 (2026-10-17, real Databento NQ futures 2010-26): four families never mined in this project.
  NDAY_BRK  intraday breakout of the prior N COMPLETE RTH days' high / low (N 3/5/10/20): a 1m or 5m close beyond the level
            + bk x daily ATR inside a window, optional daily-trend filter; market entry at the next bar, or a resting limit
            at the level ("retest", valid E minutes). Stop: level - sk ATR, or a fixed k ATR. Target R or time only (15:55).
            One signal per side per day (max 2 trades a day).
  ZMR       midday z-score mean reversion (11:00-14:30, 1m): z = (close - mean of the last W closes) / std; first bar with
            |z| >= zt after a reset (|z| < zt) -> fade toward the mean, any side or only when the fade is WITH the daily trend;
            stop k ATR; target the W-mean or R x stop; hold <= 90 / 180 min; max 2 a day.
  LEG2      first-leg continuation: by T the RTH move (close - RTH open) >= x ATR; wait for a pullback >= p of the leg
            from its extreme (the pullback must start within P minutes after T); stop entry 1 tick beyond the high / low of
            the last 5 one-minute bars (the recent swing), re-issued on every deeper pullback bar, valid E minutes; stop at
            the pullback extreme (skip if > 0.3 ATR); target 1R / 2R / measured move (leg length); flat 15:55; 1 a day.
  EXH1      exhaustion-bar fade (09:34-15:30, 1m or 5m bars): bar range >= m x the median range of the last 60 bars of the
            same timeframe, close within 25% of the bar extreme, after >= kc consecutive bars the same way; fade at the next
            bar, stop 1 tick beyond the bar extreme (skip if > 0.25 ATR), target 0.5R / 1R / bar midpoint, hold 30 / 60 min,
            with / against / any daily trend; max 2 a day.
All signals use bars up to the signal bar; entries from the next bar (core.execute, $1.90 + 1 tick per side). Levels for
NDAY_BRK come from complete prior RTH sessions only (last RTH bar open >= 15:59), like families5._daily."""
import numpy as np, pandas as pd
from numba import njit
from core import S, TICK, ev_from_lists
from families import grid, idx_at


# ---------------------------------------------------------------- NDAY_BRK
def _nday_levels(D, N):
    """Per day d: max high / min low of the last N COMPLETE RTH sessions strictly before d (NaN if fewer than N)."""
    key = f"_ndlv{N}"
    if hasattr(D, key): return getattr(D, key)
    rth = (D.om >= 570) & (D.om < 960)
    df = pd.DataFrame(dict(day=D.day[rth], h=D.h[rth], l=D.l[rth], om=D.om[rth]))
    g = df.groupby("day"); H = g.h.max(); L = g.l.min(); last = g.om.last()
    ok = last >= 959
    Hc = H[ok]; Lc = L[ok]                                           # complete days only, ascending day id
    HN = Hc.rolling(N, min_periods=N).max(); LN = Lc.rolling(N, min_periods=N).min()      # window ending AT that complete day
    idx = range(D.nd)
    HN = HN.reindex(idx).ffill().shift(1).to_numpy(float)            # day d -> value at the last complete day <= d-1
    LN = LN.reindex(idx).ffill().shift(1).to_numpy(float)
    setattr(D, key, (HN, LN)); return HN, LN


@njit(cache=True)
def _ndbrk(o, h, l, c, sm, ro, de, atr, trend, HN, LN, bk, tfb, w0, w1, tf, stopm, sk, R, ent, E):
    nd = len(ro); out = np.zeros((nd * 2, 8)); n = 0
    for d in range(nd):
        r = ro[d]; A = atr[d]
        if r < 0 or A <= 0 or np.isnan(HN[d]) or np.isnan(LN[d]): continue
        up = HN[d] + bk * A; dn = LN[d] - bk * A
        doneL = False; doneS = False
        for j in range(r, de[d] + 1):
            if sm[j] < w0: continue
            if sm[j] >= w1: break
            if tfb == 5 and (sm[j] - sm[r]) % 5 != 4: continue        # 5-minute closes only
            s = 0
            if (not doneL) and c[j] > up and (tf == 0 or trend[d] == 1): s = 1
            elif (not doneS) and c[j] < dn and (tf == 0 or trend[d] == -1): s = -1
            if s == 0: continue
            if s == 1: doneL = True
            else: doneS = True
            lvl = HN[d] if s == 1 else LN[d]
            if ent == 0:
                px = c[j]; t = 0; ex = j
            else:
                px = lvl; t = 1; ex = j + E
            sl = (lvl - s * sk * A) if stopm == 0 else (px - s * sk * A)
            risk = (px - sl) * s
            if risk < 0.03 * A or risk > 0.5 * A: continue
            tp = px + s * R * risk if R < 50 else px + s * 50 * A
            out[n, 0] = j; out[n, 1] = s; out[n, 2] = t; out[n, 3] = px; out[n, 4] = sl; out[n, 5] = tp; out[n, 6] = ex; out[n, 7] = 400; n += 1
            if doneL and doneS: break
    return out[:n]


ND_WIN = {"am": (935, 1130), "day": (935, 1500)}
ND_STOP = {"lvl0.1": (0, 0.1), "fix0.2": (1, 0.2), "fix0.3": (1, 0.3)}


def gen_ndbrk(D, p):
    HN, LN = _nday_levels(D, p["N"]); w0, w1 = ND_WIN[p["win"]]; stopm, sk = ND_STOP[p["stop"]]
    ent = 0 if p["ent"] == "mkt" else 1; E = 60
    return ev_from_lists(_ndbrk(D.o, D.h, D.l, D.c, D.sm, D.ro, D.de, D.atr, D.trend, HN, LN, p["bk"], p["tfb"], S(w0), S(w1), p["tf"],
                                stopm, sk, p["R"], ent, E).tolist())


GRID_NDBRK = (grid(ent=("mkt",), N=(3, 5, 10, 20), bk=(0.0, 0.05, 0.10), tfb=(1, 5), win=tuple(ND_WIN), tf=(0, 1), stop=tuple(ND_STOP), R=(0.5, 1.0, 2.0, 99.0)) +
              grid(ent=("rt60",), N=(3, 5, 10, 20), bk=(0.0, 0.10), tfb=(1,), win=tuple(ND_WIN), tf=(0, 1), stop=("lvl0.1", "fix0.2"), R=(0.5, 1.0, 2.0)))


# ---------------------------------------------------------------- ZMR
def _zfeat(D, W):
    key = f"_z{W}"
    if hasattr(D, key): return getattr(D, key)
    s = pd.Series(D.c); mean = s.rolling(W, min_periods=W).mean(); sd = s.rolling(W, min_periods=W).std(ddof=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        z = (D.c - mean.to_numpy()) / sd.to_numpy()
    z = np.where(np.isfinite(z), z, 0.0)
    out = (np.ascontiguousarray(z), np.ascontiguousarray(mean.to_numpy(float)))
    setattr(D, key, out); return out


@njit(cache=True)
def _zmr(c, sm, day, atr, trend, z, mean, w0, w1, zt, side, k, tg, R, hold):
    n = len(c); nd = day[-1] + 1; out = np.zeros((nd * 10 + 10, 8)); m = 0
    cur = -1; armed = True; cnt = 0
    for i in range(n):
        d = day[i]
        if d != cur: cur = d; armed = True; cnt = 0
        if sm[i] < w0 or sm[i] >= w1: continue
        zz = z[i]
        if abs(zz) < zt: armed = True; continue
        if not armed: continue
        armed = False
        A = atr[d]
        if A <= 0 or cnt >= 10 or np.isnan(mean[i]): continue
        s = -1 if zz > 0 else 1
        if side == 1 and s != trend[d]: continue
        px = c[i]; sl = px - s * k * A
        if tg == 0: tp = mean[i]
        else: tp = px + s * R * k * A
        if (tp - px) * s < 0.02 * A: continue
        out[m, 0] = i; out[m, 1] = s; out[m, 2] = 0; out[m, 3] = px; out[m, 4] = sl; out[m, 5] = tp; out[m, 6] = i; out[m, 7] = hold; m += 1; cnt += 1
    return out[:m]


ZTG = {"mean": (0, 0.0), "R0.5": (1, 0.5), "R1": (1, 1.0), "R2": (1, 2.0)}


def gen_zmr(D, p):
    z, mean = _zfeat(D, p["W"]); tg, R = ZTG[p["tg"]]
    return ev_from_lists(_zmr(D.c, D.sm, D.day, D.atr, D.trend, z, mean, S(1100), S(1430), p["zt"], p["side"], p["k"], tg, R, p["hold"]).tolist())


GRID_ZMR = grid(W=(30, 60, 120), zt=(2.0, 2.5, 3.0), side=(0, 1), k=(0.15, 0.25, 0.35), tg=tuple(ZTG), hold=(90, 180))


# ---------------------------------------------------------------- LEG2
@njit(cache=True)
def _leg2(o, h, l, c, sm, ro, de, atr, trend, eT, x, p, P, tg, tf, E, wend):
    nd = len(ro); out = np.zeros((nd * 30, 8)); n = 0
    for d in range(nd):
        r = ro[d]; e = eT[d]; A = atr[d]
        if r < 0 or e < 0 or A <= 0 or e - 1 <= r + 4: continue
        i = e - 1; mv = c[i] - o[r]
        if abs(mv) < x * A: continue
        s = 1 if mv > 0 else -1
        if tf == 1 and s != trend[d]: continue
        ext = h[r] if s == 1 else l[r]
        for j in range(r, i + 1):
            if s == 1 and h[j] > ext: ext = h[j]
            if s == -1 and l[j] < ext: ext = l[j]
        detected = False; pbx = 0.0; leg = 0.0; det_sm = 0; cnt = 0
        for j in range(e, de[d] + 1):
            if sm[j] >= wend: break
            if not detected:
                if sm[j] >= sm[e] + P: break                          # the pullback must start within P minutes
                if s == 1 and h[j] > ext: ext = h[j]
                if s == -1 and l[j] < ext: ext = l[j]
                leg = (ext - o[r]) * s
                if leg < x * A: continue
                depth = (ext - l[j]) if s == 1 else (h[j] - ext)
                if depth >= p * leg:
                    detected = True; pbx = l[j] if s == 1 else h[j]; det_sm = sm[j]
                else: continue
            else:
                if sm[j] >= det_sm + 120 or cnt >= 30: break
                if s == 1 and l[j] < pbx: pbx = l[j]
                elif s == -1 and h[j] > pbx: pbx = h[j]
                else: continue                                        # only a deeper pullback bar re-issues the order
            if (pbx - o[r]) * s <= 0: break                            # full retrace: leg failed
            hi = -1e18; lo = 1e18
            for q in range(j - 4, j + 1):
                if h[q] > hi: hi = h[q]
                if l[q] < lo: lo = l[q]
            px = (hi + TICK) if s == 1 else (lo - TICK); sl = pbx
            risk = (px - sl) * s
            if risk < 0.03 * A or risk > 0.3 * A: continue
            if tg == 0: tp = px + s * risk
            elif tg == 1: tp = px + s * 2.0 * risk
            else: tp = px + s * leg
            out[n, 0] = j; out[n, 1] = s; out[n, 2] = 2; out[n, 3] = px; out[n, 4] = sl; out[n, 5] = tp; out[n, 6] = j + E; out[n, 7] = 400; n += 1; cnt += 1
    return out[:n]


LTG = {"R1": 0, "R2": 1, "MM": 2}


def gen_leg2(D, p):
    eT = idx_at(D.sm, D.ds, D.de, S(p["T"]))
    return ev_from_lists(_leg2(D.o, D.h, D.l, D.c, D.sm, D.ro, D.de, D.atr, D.trend, eT, p["x"], p["p"], p["P"], LTG[p["tg"]], p["tf"], p["E"], S(1500)).tolist())


GRID_LEG2 = grid(T=(1015, 1030, 1100), x=(0.25, 0.4, 0.6), p=(0.3, 0.5, 0.7), P=(60, 120), tg=tuple(LTG), tf=(0, 1), E=(30, 90))


# ---------------------------------------------------------------- EXH1
def _exh_bars(D, tfb):
    key = f"_exh{tfb}"
    if hasattr(D, key): return getattr(D, key)
    if tfb == 1:
        B = dict(o=D.o, h=D.h, l=D.l, c=D.c, last=np.arange(D.n), day=D.day, sme=D.sm)
    else:
        b = D.bars(5); B = dict(o=b["o"], h=b["h"], l=b["l"], c=b["c"], last=b["last"], day=b["day"], sme=b["sme"])
    rg = B["h"] - B["l"]
    med = pd.Series(rg).rolling(60, min_periods=30).median().shift(1).to_numpy(float)
    B["med"] = np.where(np.isfinite(med), med, np.nan)
    setattr(D, key, B); return B


@njit(cache=True)
def _exh(o, h, l, c, sme, day, last, atr, trend, med, w0, w1, m, kc, tg, hold, tf):
    nb = len(c); nd = day[-1] + 1; out = np.zeros((nd * 10 + 10, 8)); n = 0
    cur = -1; run = 0; pdir = 0; cnt = 0
    for b in range(nb):
        d = day[b]
        if d != cur: cur = d; run = 0; pdir = 0; cnt = 0
        bd = 1 if c[b] > o[b] else (-1 if c[b] < o[b] else 0)
        if bd != 0 and bd == pdir: run += 1
        elif bd != 0: run = 1
        else: run = 0
        pdir = bd
        if bd == 0 or sme[b] < w0 or sme[b] >= w1 or run < kc or cnt >= 10: continue
        md = med[b]
        if not (md > 0): continue
        rg = h[b] - l[b]
        if rg < m * md or rg <= 0: continue
        tail = (h[b] - c[b]) if bd == 1 else (c[b] - l[b])
        if tail > 0.25 * rg: continue
        A = atr[d]
        if A <= 0: continue
        s = -bd
        if tf == 1 and s != trend[d]: continue
        if tf == -1 and s != -trend[d]: continue
        px = c[b]; sl = (h[b] + TICK) if s == -1 else (l[b] - TICK)
        risk = (px - sl) * s
        if risk < 0.03 * A or risk > 0.25 * A: continue
        if tg == 0: tp = px + s * 0.5 * risk
        elif tg == 1: tp = px + s * risk
        else: tp = (h[b] + l[b]) / 2
        if (tp - px) * s <= TICK: continue
        out[n, 0] = last[b]; out[n, 1] = s; out[n, 2] = 0; out[n, 3] = px; out[n, 4] = sl; out[n, 5] = tp; out[n, 6] = last[b]; out[n, 7] = hold; n += 1; cnt += 1
    return out[:n]


ETG = {"R0.5": 0, "R1": 1, "mid": 2}


def gen_exh(D, p):
    B = _exh_bars(D, p["tfb"])
    return ev_from_lists(_exh(B["o"], B["h"], B["l"], B["c"], B["sme"], B["day"], B["last"], D.atr, D.trend, B["med"], S(934), S(1530),
                              p["m"], p["kc"], ETG[p["tg"]], p["hold"], p["tf"]).tolist())


GRID_EXH = grid(tfb=(1, 5), m=(2.0, 2.5, 3.5, 5.0), kc=(2, 3, 5), tg=tuple(ETG), hold=(30, 60), tf=(1, -1, 0))

FAMILIES8 = {"NDAY_BRK": (gen_ndbrk, GRID_NDBRK, 2), "ZMR": (gen_zmr, GRID_ZMR, 2), "LEG2": (gen_leg2, GRID_LEG2, 1), "EXH1": (gen_exh, GRID_EXH, 2)}
# categorical parameters (not a "step" for the plateau test)
CATEGORICAL8 = {"ent", "tfb", "win", "tf", "stop", "side", "tg"}
