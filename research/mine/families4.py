"""Batch 4: late-session intraday momentum (Gao, Han, Li & Zhou 2018 'Market intraday momentum': the first half-hour return,
measured from the previous close, predicts the last half-hour return). Entries 14:30-15:30 ET, exit 15:55 (or stop / target).
Signals (information up to the bar before entry):
  FH   sign(close 10:00 - prior RTH close)          (first half hour incl. the overnight gap)
  RTH  sign(close T-1 - RTH open)
  DAY  sign(close T-1 - prior RTH close)
  L30  sign(close T-1 - close T-31)
  VW   sign(close T-1 - RTH VWAP)
  FHRTH FH and RTH agree
Threshold: |signal move| >= x * daily ATR."""
import numpy as np
from numba import njit
from core import S, ev_from_lists
from families import grid
SIGS = {"FH": 0, "RTH": 1, "DAY": 2, "L30": 3, "VW": 4, "FHRTH": 5}

@njit(cache=True)
def _late(c, sm, ro, de, pdc, vwap, atr, trend, T, sig, x, tfl, k, R):
    nd = len(ro); out = np.zeros((nd, 8)); n = 0
    for d in range(nd):
        a = ro[d]
        if a < 0 or atr[d] <= 0 or np.isnan(pdc[d]): continue
        A = atr[d]
        e = -1
        for q in range(a, de[d] + 1):
            if sm[q] == T: e = q; break
        if e < 0 or e - 1 < a: continue
        i = e - 1
        # 10:00 close index (bar starting 09:59)
        j10 = -1
        for q in range(a, e):
            if sm[q] == S0959: j10 = q; break
        mv = 0.0
        if sig == 0 or sig == 5:
            if j10 < 0: continue
            mv = c[j10] - pdc[d]
        elif sig == 1: mv = c[i] - c[a]
        elif sig == 2: mv = c[i] - pdc[d]
        elif sig == 3:
            if i - 30 < a: continue
            mv = c[i] - c[i - 30]
        elif sig == 4:
            if np.isnan(vwap[i]): continue
            mv = c[i] - vwap[i]
        s = 1 if mv > 0 else (-1 if mv < 0 else 0)
        if s == 0 or abs(mv) < x * A: continue
        if sig == 5:
            m2 = c[i] - c[a]
            if (1 if m2 > 0 else -1) != s or abs(m2) < x * A: continue
        if tfl == 1 and s != trend[d]: continue
        sl = c[i] - s * k * A; tp = c[i] + s * R * k * A
        out[n, 0] = i; out[n, 1] = s; out[n, 2] = 0; out[n, 3] = c[i]; out[n, 4] = sl; out[n, 5] = tp; out[n, 6] = i; out[n, 7] = 400; n += 1
    return out[:n]
S10 = S(1000); S0959 = S(959)

def gen_late(D, p):
    return ev_from_lists(_late(D.c, D.sm, D.ro, D.de, D.pdc, D.vwap, D.atr.astype(np.float64), D.trend, S(p["T"]), SIGS[p["sig"]], p["x"], p["tf"], p["k"], p["R"]).tolist())
GRID_LATE = grid(T=(1430, 1500, 1515, 1530), sig=list(SIGS), x=(0.0, 0.1, 0.25, 0.5), tf=(0, 1), k=(0.1, 0.2, 0.3, 1.0), R=(0.5, 1.0, 99.0))
FAMILIES4 = {"LATE_MOM": (gen_late, GRID_LATE, 1)}
