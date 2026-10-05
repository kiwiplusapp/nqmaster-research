"""London breakout + FVG return (LozTradez-style) on NQ. Range = [range_start, 03:00 ET). After 03:00 a bar CLOSES
beyond the range -> direction. Entry: 0 market at next open | 1 limit at the proximal edge of the first FVG (3-bar gap)
formed in the breakout direction after the break (valid until the entry deadline). Stop: 0 FVG origin (first-bar
extreme of the gap) | 1 range midpoint | 2 opposite side of the range. Target R x risk. Exit at the deadline.
One trade per session. Costs as elsewhere (1 tick slippage, $1 RT per MNQ, stop first)."""
import sys, itertools
import numpy as np, pandas as pd
from numba import njit
from ict import load, bars, day_levels
TICK, SLIP = 0.25, 0.25


@njit(cache=True)
def sim(o, h, l, c, om, day, atr, trend, rs, re, win_e, ent_e, emode, smode, R, max_risk, exit_om, bias, out):
    n = len(c); k = 0; i = 0
    while i < n:
        d = day[i]; j = i
        while j < n and day[j] == d: j += 1
        nxt = j
        a = atr[d]
        if a <= 0: i = nxt; continue
        # sequential clock inside the Globex day: minutes since 18:00
        rh = -1e18; rl = 1e18; q = i; dirn = 0; bq = -1
        def_ok = True
        while q < nxt:
            m = (om[q] - 1080) % 1440
            if m >= (rs - 1080) % 1440 and m < (re - 1080) % 1440:
                rh = max(rh, h[q]); rl = min(rl, l[q])
            elif m >= (re - 1080) % 1440:
                break
            q += 1
        if rh < -1e17 or rl > 1e17: i = nxt; continue
        # breakout search
        while q < nxt:
            m = (om[q] - 1080) % 1440
            if m >= (win_e - 1080) % 1440: break
            if c[q] > rh: dirn = 1; bq = q; break
            if c[q] < rl: dirn = -1; bq = q; break
            q += 1
        if dirn == 0 or (bias == 1 and dirn != trend[d]) or (bias == -1 and dirn == trend[d]): i = nxt; continue
        entry = np.nan; eb = -1; stop = np.nan
        if emode == 0:
            if bq + 1 < nxt:
                eb = bq + 1; entry = o[eb] + dirn * SLIP
                if smode == 1: stop = (rh + rl) / 2
                elif smode == 2: stop = rl if dirn == 1 else rh
                else: stop = l[bq] - TICK if dirn == 1 else h[bq] + TICK
        else:
            # find first FVG in breakout direction formed at/after the break, then wait for the retrace
            lim = np.nan; org = np.nan; q = bq
            while q < nxt:
                m = (om[q] - 1080) % 1440
                if m >= (ent_e - 1080) % 1440: break
                if np.isnan(lim) and q >= 2:
                    if dirn == 1 and l[q] > h[q - 2]: lim = l[q]; org = l[q - 2] - TICK
                    if dirn == -1 and h[q] < l[q - 2]: lim = h[q]; org = h[q - 2] + TICK
                    q += 1; continue
                if not np.isnan(lim):
                    if (dirn == 1 and l[q] <= lim - TICK) or (dirn == -1 and h[q] >= lim + TICK):
                        eb = q; entry = min(lim, o[q]) if dirn == 1 else max(lim, o[q])
                        if smode == 1: stop = (rh + rl) / 2
                        elif smode == 2: stop = rl if dirn == 1 else rh
                        else: stop = org
                        break
                q += 1
        if eb < 0 or np.isnan(entry): i = nxt; continue
        risk = (entry - stop) * dirn
        if risk <= 0 or risk > max_risk * a: i = nxt; continue
        tp = entry + dirn * R * risk; ex = np.nan; q = eb
        while q < nxt:
            m = (om[q] - 1080) % 1440
            if dirn == 1:
                if l[q] <= stop: ex = (min(o[q], stop) if q > eb else stop) - SLIP; break
                if q > eb and h[q] >= tp + TICK: ex = max(o[q], tp); break
            else:
                if h[q] >= stop: ex = (max(o[q], stop) if q > eb else stop) + SLIP; break
                if q > eb and l[q] <= tp - TICK: ex = min(o[q], tp); break
            if m >= (exit_om - 1080) % 1440: ex = c[q] - dirn * SLIP; break
            q += 1
        if np.isnan(ex): ex = c[nxt - 1] - dirn * SLIP
        out[k, 0] = dirn * (ex - entry); out[k, 1] = eb; out[k, 2] = risk; out[k, 3] = dirn; out[k, 4] = min(q, nxt - 1); k += 1
        i = nxt
    return k


def run(B, atr, trend, rs, re, win_e, ent_e, emode, smode, R, mx, exit_om, bias):
    out = np.zeros((4000, 5))
    k = sim(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], atr, trend, rs, re, win_e, ent_e, emode, smode, R, mx, exit_om, bias, out)
    df = pd.DataFrame(dict(pts=out[:k, 0], date=B["date"][out[:k, 1].astype(np.int64)], risk=out[:k, 2], d=out[:k, 3], xi=out[:k, 4].astype(np.int64)))
    df["usd"] = df.pts * 2 - 1
    return df


def pf(s): return s[s > 0].sum() / -s[s <= 0].sum() if (s <= 0).any() else 9.0


if __name__ == "__main__":
    tf = int(sys.argv[1])
    sets = {}
    for n in ("nq_1m.npz", "mnq_fut.npz"):
        d = load(n); B = bars(d, tf); L, atr, trend = day_levels(d); sets[n] = (B, atr, trend)
    rows = []
    for rs, (we, ee), em, sm, R, mx, xo, bias in itertools.product((1080, 1200, 0, 120), ((300, 360), (360, 480), (480, 540)), (0, 1), (0, 1, 2),
                                                                  (1.0, 1.5, 2.0, 3.0), (0.1, 0.25), (570, 660, 955), (0, 1)):
        r = dict(tf=tf, rs=rs, win_e=we, ent_e=ee, em=em, sm=sm, R=R, mx=mx, exit=xo, bias=bias)
        for n, (B, atr, trend) in sets.items():
            df = run(B, atr, trend, rs, 180, we, ee, em, sm, R, mx, xo, bias)
            if n == "nq_1m.npz":
                for nm, s in (("is", df[df.date < 20240101]), ("c24", df[df.date >= 20240101])):
                    r[nm + "_n"] = len(s); r[nm + "_wr"] = round(100 * (s.usd > 0).mean(), 1) if len(s) else np.nan; r[nm + "_pf"] = round(pf(s.usd), 3) if len(s) > 10 else np.nan
            else:
                s = df[df.date >= 20240201]; r["fut_n"] = len(s); r["fut_wr"] = round(100 * (s.usd > 0).mean(), 1) if len(s) else np.nan; r["fut_pf"] = round(pf(s.usd), 3) if len(s) > 10 else np.nan
        rows.append(r)
    g = pd.DataFrame(rows); g.to_csv(f"london_tf{tf}.csv", index=False); print(tf, len(g), "done")
