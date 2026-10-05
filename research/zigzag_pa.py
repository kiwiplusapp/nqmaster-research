"""[RS] ZigZag PA Strategy V4.1 (Pine v1/v2) replicated on NQ 1m data 2020-01 -> 2026-09.
ZigZag from 60m bars, harmonic patterns on the last 5 pivots, entry when close is inside the 0.236 fib of the last leg,
exit (market, next open) when high/low touches fib 0.618 (TP) or fib -0.236 (SL).
mode 'honest': the 60m pivot is known only after that hour closes (what you get live).
mode 'leak'  : the pivot of the hour currently forming is used at its first bar (Pine v1/v2 security() on history)."""
import sys
import numpy as np, pandas as pd
from numba import njit
from pine_tests import bars, stats, PERIODS, SLIP, PV, COMM


def hour_zigzag():
    b = bars(60)
    o, h, l, c = b["o"], b["h"], b["l"], b["c"]
    n = len(c); zz = np.full(n, np.nan); dirn = 0
    for i in range(1, n):
        up1, dn1 = c[i - 1] >= o[i - 1], c[i - 1] <= o[i - 1]
        up, dn = c[i] >= o[i], c[i] <= o[i]
        prev_dir = dirn
        dirn = -1 if (up1 and dn) else (1 if (dn1 and up) else dirn)
        if up1 and dn and prev_dir != -1:
            zz[i] = max(h[i], h[i - 1])
        elif dn1 and up and prev_dir != 1:
            zz[i] = min(l[i], l[i - 1])
    return b["ep"] // 60, zz


@njit(cache=True)
def rng(v, lo, hi):
    return v >= lo and v <= hi


@njit(cache=True)
def any_pattern(x, a, b, c, d, mode):
    if x == a or a == b or b == c:
        return False
    if not ((mode == 1 and d < c) or (mode == -1 and d > c)):
        return False
    xab = abs(b - a) / abs(x - a); xad = abs(a - d) / abs(x - a); abc = abs(b - c) / abs(a - b); bcd = abs(c - d) / abs(b - c)
    if rng(abc, 0.382, 0.886) and rng(bcd, 1.13, 2.618): return True                                    # ABCD
    if rng(xab, 0.382, 0.5) and rng(abc, 0.382, 0.886) and rng(bcd, 1.618, 2.618) and xad <= 0.618: return True  # Bat
    if xab <= 0.382 and rng(abc, 0.382, 0.886) and rng(bcd, 2.0, 3.618) and xad <= 1.13: return True      # AltBat
    if xab <= 0.786 and rng(abc, 0.382, 0.886) and rng(bcd, 1.618, 2.618) and rng(xad, 1.27, 1.618): return True  # Butterfly
    if rng(xab, 0.5, 0.618) and rng(abc, 0.382, 0.886) and rng(bcd, 1.13, 2.618) and rng(xad, 0.75, 0.875): return True  # Gartley
    if rng(xab, 0.5, 0.875) and rng(abc, 0.382, 0.886) and rng(bcd, 2.0, 5.0) and rng(xad, 1.382, 5.0): return True  # Crab
    if rng(xab, 0.5, 0.875) and rng(abc, 1.13, 1.618) and rng(bcd, 1.27, 2.24) and rng(xad, 0.886, 1.13): return True  # Shark
    if rng(xab, 1.13, 1.618) and rng(abc, 1.618, 2.24) and rng(bcd, 0.5, 0.625) and rng(xad, 0.0, 0.236): return True  # 5-O
    if rng(xab, 1.27, 1.618) and rng(abc, 0.0, 5.0) and rng(bcd, 1.27, 1.618) and rng(xad, 0.0, 5.0): return True  # Wolf
    if rng(xab, 2.0, 10.0) and rng(abc, 0.9, 1.1) and rng(bcd, 0.236, 0.88) and rng(xad, 0.9, 1.1): return True  # HnS
    if rng(xab, 0.382, 0.618) and rng(abc, 0.382, 0.618) and rng(bcd, 0.382, 0.618) and rng(xad, 0.236, 0.764): return True  # ConTria
    if rng(xab, 1.236, 1.618) and rng(abc, 1.0, 1.618) and rng(bcd, 1.236, 2.0) and rng(xad, 2.0, 2.236): return True  # ExpTria
    if rng(xab, 0.5, 0.886) and rng(abc, 1.0, 2.618) and rng(bcd, 1.618, 2.618) and rng(xad, 0.886, 1.0): return True  # AntiBat
    if rng(xab, 0.236, 0.886) and rng(abc, 1.13, 2.618) and rng(bcd, 1.0, 1.382) and rng(xad, 0.5, 0.886): return True  # AntiButterfly
    if rng(xab, 0.5, 0.886) and rng(abc, 1.0, 2.618) and rng(bcd, 1.5, 5.0) and rng(xad, 1.0, 5.0): return True  # AntiGartley
    if rng(xab, 0.25, 0.5) and rng(abc, 1.13, 2.618) and rng(bcd, 1.618, 2.618) and rng(xad, 0.5, 0.75): return True  # AntiCrab
    if rng(xab, 0.382, 0.875) and rng(abc, 0.5, 1.0) and rng(bcd, 1.25, 2.618) and rng(xad, 0.5, 1.25): return True  # AntiShark
    return False


@njit(cache=True)
def sim(o, h, l, c, sz, ew, tpr, slr, out):
    n = len(c); piv = np.full(5, np.nan); npiv = 0; pos = 0; entry = 0.0; eb = 0; k = 0; pend = 0
    for i in range(n):
        if pend != 0:
            if pos != 0 and (pend == 2 or pend == -pos):
                ex = o[i] - pos * SLIP
                out[k, 0] = pos * (ex - entry); out[k, 1] = eb; k += 1; pos = 0
            if (pend == 1 or pend == -1) and pos == 0:
                pos = pend; entry = o[i] + pos * SLIP; eb = i
            pend = 0
        if not np.isnan(sz[i]) and sz[i] != 0:
            for j in range(4):
                piv[j] = piv[j + 1]
            piv[4] = sz[i]; npiv += 1
        if npiv < 5:
            continue
        x, a, b, cc, d = piv[0], piv[1], piv[2], piv[3], piv[4]
        fr = abs(d - cc)
        sgn = -1.0 if d > cc else 1.0
        f_ew = d + sgn * fr * ew; f_tp = d + sgn * fr * tpr; f_sl = d + sgn * fr * slr
        buy = any_pattern(x, a, b, cc, d, 1) and c[i] <= f_ew
        sel = any_pattern(x, a, b, cc, d, -1) and c[i] >= f_ew
        # Pine order: entry buy, close buy, entry sell, close sell (last call wins for the next open)
        if buy and pos != 1:
            pend = 1
        if pos == 1 and (h[i] >= f_tp or l[i] <= f_sl):
            pend = 2
        if sel and pos != -1:
            pend = -1
        if pos == -1 and (l[i] <= f_tp or h[i] >= f_sl):
            pend = 2
    return k


def run(chart_tf, mode, ew=0.236, tpr=0.618, slr=-0.236):
    hk, zz = hour_zigzag()
    b = bars(chart_tf); key = b["ep"] // 60
    first = np.r_[True, key[1:] != key[:-1]]
    pos = np.searchsorted(hk, key)                      # index of the hour bar containing this chart bar
    pos = np.clip(pos, 0, len(hk) - 1)
    src = pos - 1 if mode == "honest" else pos           # honest: last CLOSED hour
    sz = np.where(first & (src >= 0), zz[np.clip(src, 0, None)], np.nan)
    out = np.zeros((len(b["c"]), 2)); k = sim(b["o"], b["h"], b["l"], b["c"], sz, ew, tpr, slr, out)
    df = pd.DataFrame(dict(pts=out[:k, 0], date=b["date"][out[:k, 1].astype(int)]))
    df["usd"] = df.pts * PV - COMM
    return df


if __name__ == "__main__":
    for tf in (5, 15):
        for mode in ("leak", "honest"):
            rows = []
            df = run(tf, mode)
            for name, lo, hi in PERIODS:
                s = stats(df, lo, hi); s["period"] = name; rows.append(s)
            print(f"\n=== ZigZag PA chart {tf}m, pivots 60m, {mode}")
            print(pd.DataFrame(rows).set_index("period").to_string()); sys.stdout.flush()
