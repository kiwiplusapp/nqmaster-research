"""Gold-specific families, anchored on gold's own session clocks (ET): Globex open 18:00, Asia 20:00, London 03:00,
COMEX open 08:20, NY equities 09:30. Flat 16:50 ET.
G_DRIVE : move from the anchor open to anchor+T (close of the bar before) >= x*ATR -> continuation (mode 1) or fade (-1),
          market entry, stop k*ATR (stop=0) or beyond the window's opposite extreme capped at k*ATR (stop=1), target R*risk.
G_ORB   : opening range [anchor, anchor+T); first breakout (stop order 1 tick beyond) within W minutes after the range,
          stop at the opposite side capped at cap*ATR, target R*risk; optional trend filter; ambiguous bars skipped."""
import numpy as np
from numba import njit
from core import S, ev_from_lists
from families import grid
FLAT_G = 1010                                     # 16:50 ET (om minutes)

@njit(cache=True)
def _drive(o, h, l, c, sm, ds, de, atr, trend, A, T, x, mode, tf, k, stop, R, hold):
    out = np.zeros((len(ds), 8)); n = 0
    for d in range(len(ds)):
        if ds[d] < 0 or atr[d] <= 0: continue
        a = -1; e = -1
        for q in range(ds[d], de[d] + 1):
            if a < 0 and sm[q] >= A: a = q
            if sm[q] >= A + T: e = q; break
        if a < 0 or e < 0 or e - 1 < a or sm[a] > A + 5: continue
        i = e - 1; mv = c[i] - o[a]; Av = atr[d]
        if abs(mv) < x * Av or mv == 0: continue
        s = 1 if mv > 0 else -1
        if mode == -1: s = -s
        if tf == 1 and s != trend[d]: continue
        px = c[i]
        if stop == 0: risk = k * Av
        else:
            hi = h[a]; lo = l[a]
            for q in range(a, i + 1):
                hi = max(hi, h[q]); lo = min(lo, l[q])
            risk = (px - lo) if s == 1 else (hi - px)
            risk = min(risk + 0.25, k * Av)
            if risk <= 0.5: continue
        out[n, 0] = i; out[n, 1] = s; out[n, 2] = 0; out[n, 3] = px; out[n, 4] = px - s * risk; out[n, 5] = px + s * R * risk; out[n, 6] = i; out[n, 7] = hold; n += 1
    return out[:n]
def gen_drive(D, p):
    return ev_from_lists(_drive(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr.astype(np.float64), D.trend, S(p["A"]), p["T"], p["x"], p["mode"], p["tf"], p["k"], p["stop"], p["R"], p["hold"]).tolist())
GRID_DRIVE = (grid(A=(1800, 2000), T=(30, 60, 120, 240, 540), x=(0.1, 0.2, 0.35), mode=(1, -1), tf=(0, 1), k=(0.2, 0.35), stop=(0, 1), R=(0.5, 1.0, 2.0), hold=(240, 600)) +
              grid(A=(300,), T=(15, 30, 60, 120, 320), x=(0.1, 0.2, 0.35), mode=(1, -1), tf=(0, 1), k=(0.2, 0.35), stop=(0, 1), R=(0.5, 1.0, 2.0), hold=(240, 600)) +
              grid(A=(820, 930), T=(10, 15, 30, 60, 90), x=(0.1, 0.2, 0.35), mode=(1, -1), tf=(0, 1), k=(0.2, 0.35), stop=(0, 1), R=(0.5, 1.0, 2.0), hold=(240, 600)))

@njit(cache=True)
def _orb(o, h, l, c, sm, ds, de, atr, trend, A, T, W, cap, R, tf, hold):
    out = np.zeros((len(ds), 8)); n = 0
    for d in range(len(ds)):
        if ds[d] < 0 or atr[d] <= 0: continue
        a = -1; e = -1
        for q in range(ds[d], de[d] + 1):
            if a < 0 and sm[q] >= A: a = q
            if sm[q] >= A + T: e = q; break
        if a < 0 or e < 0 or sm[a] > A + 5: continue
        rh = h[a]; rl = l[a]
        for q in range(a, e):
            rh = max(rh, h[q]); rl = min(rl, l[q])
        b = -1; s = 0
        for q in range(e, de[d] + 1):
            if sm[q] >= A + T + W: break
            up = h[q] >= rh + 0.25; dn = l[q] <= rl - 0.25
            if up and dn: break
            if up: b = q; s = 1; break
            if dn: b = q; s = -1; break
        if b < 0 or s == 0: continue
        if tf == 1 and s != trend[d]: continue
        lvl = rh + 0.25 if s == 1 else rl - 0.25
        risk = min(rh - rl + 0.5, cap * atr[d])
        out[n, 0] = b - 1; out[n, 1] = s; out[n, 2] = 2; out[n, 3] = lvl; out[n, 4] = lvl - s * risk; out[n, 5] = lvl + s * R * risk; out[n, 6] = b; out[n, 7] = hold; n += 1
    return out[:n]
def gen_orb(D, p):
    return ev_from_lists(_orb(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr.astype(np.float64), D.trend, S(p["A"]), p["T"], p["W"], p["cap"], p["R"], p["tf"], p["hold"]).tolist())
GRID_GORB = (grid(A=(1800, 2000), T=(60, 120, 240, 420), W=(120, 360), cap=(0.25, 0.4, 0.6), R=(0.5, 1.0, 2.0), tf=(0, 1), hold=(240, 600)) +
             grid(A=(300,), T=(15, 30, 60), W=(60, 180), cap=(0.25, 0.4, 0.6), R=(0.5, 1.0, 2.0), tf=(0, 1), hold=(240, 600)) +
             grid(A=(820, 930), T=(10, 15, 30, 60), W=(60, 180), cap=(0.25, 0.4, 0.6), R=(0.5, 1.0, 2.0), tf=(0, 1), hold=(240, 600)))
# NQ_DRIVE (2026-10-07): the same anchored drive on NQ with anchors every hour of the Globex day not covered by GRID_DRIVE
GRID_NQDRIVE = grid(A=(1900, 2100, 2200, 2300, 0, 100, 200, 400, 500, 600, 700, 1000, 1100, 1200, 1300, 1400), T=(15, 30, 60, 120, 240),
                    x=(0.1, 0.2, 0.35), mode=(1, -1), tf=(0, 1), k=(0.2, 0.35), stop=(0,), R=(0.5, 1.0, 2.0), hold=(240,))
FAMILIES_GOLD = {"G_DRIVE": (gen_drive, GRID_DRIVE, 1), "G_ORB": (gen_orb, GRID_GORB, 1), "NQ_DRIVE": (gen_drive, GRID_NQDRIVE, 1)}
