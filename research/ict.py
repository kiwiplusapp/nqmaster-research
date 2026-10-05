"""ICT reversal model (Dhesi-style): liquidity sweep -> CISD / IFVG inversion -> entry (market, FVG, CISD retest,
IFVG retest) -> fixed-R target. Bar-by-bar state machine, no look-ahead.
Liquidity levels per session day (known before use): previous RTH high/low (PDH/PDL), overnight high/low 18:00-09:29
(ONH/ONL), London 02:00-05:00 high/low. A level only counts the first time it is taken, and only if it was not already
taken before the window opened.
Bearish (mirror for bullish):
  sweep  : high > untaken level inside the window; track the extreme.
  CISD   : a close below the OPEN of the first candle of the bullish run that made the extreme (within K bars).
  IFVG   : alternative trigger - a bullish FVG formed in the 20 bars before the extreme is closed through (inverted).
  entry  : 0 market next open | 1 limit at the proximal edge of the newest bearish FVG after the extreme |
           2 limit at the CISD level | 3 limit at the inverted FVG edge. Limits live M bars, cancelled if the extreme is exceeded.
  stop   : extreme + 1 tick; target: R x risk. Flat at 15:55 ET. One position at a time, max N trades/day.
Costs: market/stop fills +1 tick, limits need a 1-tick trade-through, $1 RT per MNQ; stop first inside a bar."""
import os, sys, itertools
import numpy as np, pandas as pd
from numba import njit

TICK, SLIP, PV, COMM = 0.25, 0.25, 2.0, 1.0


def load(name):
    z = np.load("data/" + name)
    return {k: z[k] for k in z.files}


def bars(d, tf):
    if tf == 1:
        return dict(o=d["o"], h=d["h"], l=d["l"], c=d["c"], om=d["om"].astype(np.int64), day=d["dayid"].astype(np.int64), date=d["date"])
    g = d["epoch"] // tf
    df = pd.DataFrame(dict(g=g, o=d["o"], h=d["h"], l=d["l"], c=d["c"], om=d["om"], day=d["dayid"], date=d["date"]))
    a = df.groupby(["day", "g"], sort=True).agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"),
                                                  om=("om", "first"), date=("date", "first")).reset_index()
    return dict(o=a.o.to_numpy(), h=a.h.to_numpy(), l=a.l.to_numpy(), c=a.c.to_numpy(), om=a.om.to_numpy().astype(np.int64),
                day=a.day.to_numpy().astype(np.int64), date=a.date.to_numpy())


def day_levels(d):
    """levels[day, k]: 0 PDH 1 ONH 2 LonH 3 PDL 4 ONL 5 LonL ; plus ATRd and trend per day."""
    om, day, h, l, c = d["om"], d["dayid"], d["h"], d["l"], d["c"]
    nd = int(day.max()) + 1
    df = pd.DataFrame(dict(day=day, om=om, h=h, l=l, c=c))
    rth = df[(df.om >= 570) & (df.om < 960)].groupby("day").agg(h=("h", "max"), l=("l", "min"), c=("c", "last")).reindex(range(nd))
    on = df[(df.om >= 1080) | (df.om < 570)].groupby("day").agg(h=("h", "max"), l=("l", "min")).reindex(range(nd))
    lon = df[(df.om >= 120) & (df.om < 300)].groupby("day").agg(h=("h", "max"), l=("l", "min")).reindex(range(nd))
    L = np.full((nd, 6), np.nan)
    L[:, 0] = rth.h.shift(1).to_numpy(); L[:, 3] = rth.l.shift(1).to_numpy()
    L[:, 1] = on.h.to_numpy(); L[:, 4] = on.l.to_numpy()
    L[:, 2] = lon.h.to_numpy(); L[:, 5] = lon.l.to_numpy()
    pc = rth.c.shift(1)
    tr = np.maximum(rth.h - rth.l, np.maximum((rth.h - pc).abs(), (rth.l - pc).abs()))
    atr = tr.ewm(alpha=1 / 14, adjust=False, ignore_na=True).mean().shift(1).fillna(0).to_numpy()
    sma = rth.c.rolling(20, min_periods=20).mean().shift(1)
    trend = np.sign((pc - sma).fillna(0)).to_numpy().astype(np.int64)
    return L, atr, trend


@njit(cache=True)
def sim(o, h, l, c, om, day, L, lvl_mask, atr, trend, win_s, win_e, K, emode, R, bias, max_risk, M, max_day, flat, out):
    n = len(c); k = 0
    cur = -1; taken = np.zeros(6, np.bool_); ntd = 0
    # state for each side: 0 bear (from highs), 1 bull (from lows)
    act = np.zeros(2, np.bool_); ext = np.zeros(2); exti = np.zeros(2, np.int64)
    pend = 0; plim = 0.0; pstop = 0.0; pexp = 0; pdir = 0; pext = 0.0
    pos = 0; entry = 0.0; sl = 0.0; tp = 0.0; eb = 0; rk = 0.0
    for i in range(2, n):
        d = day[i]
        if d != cur:
            cur = d; ntd = 0; act[:] = False; pend = 0
            for q in range(6):
                taken[q] = (not lvl_mask[q]) or np.isnan(L[d, q])
        m = om[i]
        # ---- manage position
        if pos != 0:
            done = False; ex = 0.0
            if pos == 1:
                if i > eb and o[i] <= sl: ex = o[i] - SLIP; done = True
                elif l[i] <= sl: ex = sl - SLIP; done = True
                elif i > eb and h[i] >= tp + TICK: ex = max(o[i], tp); done = True
            else:
                if i > eb and o[i] >= sl: ex = o[i] + SLIP; done = True
                elif h[i] >= sl: ex = sl + SLIP; done = True
                elif i > eb and l[i] <= tp - TICK: ex = min(o[i], tp); done = True
            if not done and (day[i] != day[eb] or m >= flat):
                ex = c[i] - pos * SLIP; done = True
            if done:
                out[k, 0] = pos * (ex - entry); out[k, 1] = eb; out[k, 2] = rk; out[k, 3] = pos; out[k, 4] = i; k += 1; pos = 0
        # ---- pending limit
        if pend != 0 and pos == 0:
            if i > pexp or (pdir == -1 and h[i] > pext) or (pdir == 1 and l[i] < pext) or m >= flat:
                pend = 0
            elif (pdir == -1 and h[i] >= plim + TICK) or (pdir == 1 and l[i] <= plim - TICK):
                fill = max(plim, o[i]) if pdir == -1 else min(plim, o[i])
                risk = (pstop - fill) * (-pdir)
                if risk > 0:
                    pos = pdir; entry = fill; sl = pstop; rk = risk; tp = fill + pos * R * risk; eb = i; ntd += 1
                    if (pos == -1 and h[i] >= sl) or (pos == 1 and l[i] <= sl):
                        out[k, 0] = -(rk + SLIP); out[k, 1] = eb; out[k, 2] = rk; out[k, 3] = pos; out[k, 4] = i; k += 1; pos = 0
                pend = 0
        inwin = m >= win_s and m < win_e
        # ---- levels taken outside the window are consumed
        for q in range(6):
            if not taken[q]:
                if q < 3 and h[i] > L[d, q] and not inwin:
                    taken[q] = True
                elif q >= 3 and l[i] < L[d, q] and not inwin:
                    taken[q] = True
        if not inwin:
            act[:] = False
            continue
        # ---- sweeps
        for q in range(6):
            if taken[q]:
                continue
            if q < 3 and h[i] > L[d, q]:
                taken[q] = True
                if not act[0] or h[i] > ext[0]:
                    act[0] = True; ext[0] = h[i]; exti[0] = i
            elif q >= 3 and l[i] < L[d, q]:
                taken[q] = True
                if not act[1] or l[i] < ext[1]:
                    act[1] = True; ext[1] = l[i]; exti[1] = i
        for s in range(2):
            if not act[s]:
                continue
            dirn = -1 if s == 0 else 1
            # extend the extreme
            if s == 0 and h[i] > ext[0]:
                ext[0] = h[i]; exti[0] = i
            if s == 1 and l[i] < ext[1]:
                ext[1] = l[i]; exti[1] = i
            if i - exti[s] > K:
                act[s] = False; continue
            # CISD level: open of the first candle of the run into the extreme
            j = exti[s]
            if s == 0:
                if c[j] <= o[j]: j -= 1
                while j > 0 and day[j] == d and c[j] > o[j] and c[j - 1] > o[j - 1]: j -= 1
            else:
                if c[j] >= o[j]: j -= 1
                while j > 0 and day[j] == d and c[j] < o[j] and c[j - 1] < o[j - 1]: j -= 1
            cisd = o[j]
            trig = False; ifvg_edge = np.nan
            if i > exti[s]:
                if s == 0 and c[i] < cisd: trig = True
                if s == 1 and c[i] > cisd: trig = True
                if emode == 3:
                    trig = False
                    # newest opposite FVG formed in the 20 bars up to the extreme, inverted by this close
                    b = exti[s]
                    while b >= exti[s] - 20 and b >= 2 and day[b] == d:
                        if s == 0 and l[b] > h[b - 2]:
                            if c[i] < h[b - 2] and c[i - 1] >= h[b - 2]:
                                trig = True; ifvg_edge = h[b - 2]
                            break
                        if s == 1 and h[b] < l[b - 2]:
                            if c[i] > l[b - 2] and c[i - 1] <= l[b - 2]:
                                trig = True; ifvg_edge = l[b - 2]
                            break
                        b -= 1
            if not trig:
                continue
            act[s] = False
            if pos != 0 or pend != 0 or ntd >= max_day or m + 1 >= flat:
                continue
            t = trend[d]
            if bias == 1 and dirn != t: continue
            if bias == -1 and dirn == t: continue
            stop = ext[s] + TICK if s == 0 else ext[s] - TICK
            a = atr[d]
            if a <= 0: continue
            if emode == 0:
                if i + 1 >= n or day[i + 1] != d: continue
                e = o[i + 1] + dirn * SLIP
                risk = (stop - e) * (-dirn)
                if risk <= 0 or risk > max_risk * a: continue
                pos = dirn; entry = e; sl = stop; rk = risk; tp = e + dirn * R * risk; eb = i + 1; ntd += 1
                # position starts next bar; handled by the manager on bar i+1 (eb = i+1)
            else:
                lim = np.nan
                if emode == 1:
                    b = i
                    while b >= exti[s] + 2:
                        if s == 0 and h[b] < l[b - 2]:
                            lim = h[b]; break
                        if s == 1 and l[b] > h[b - 2]:
                            lim = l[b]; break
                        b -= 1
                elif emode == 2:
                    lim = cisd
                else:
                    lim = ifvg_edge
                if np.isnan(lim): continue
                if (s == 0 and lim > c[i]) or (s == 1 and lim < c[i]):
                    risk = (stop - lim) * (-dirn)
                    if risk <= 0 or risk > max_risk * a: continue
                    pend = dirn; plim = lim; pstop = stop; pexp = i + M; pdir = dirn; pext = ext[s]
    return k


def run(B, L, atr, trend, lvl_mask, win, K, emode, R, bias, max_risk, M=20, max_day=3, flat=955):
    out = np.zeros((len(B["c"]) // 10 + 1000, 5))
    k = sim(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], L, lvl_mask, atr, trend, win[0], win[1], K, emode, R, bias, max_risk, M, max_day, flat, out)
    o = out[:k]
    df = pd.DataFrame(dict(pts=o[:, 0], risk=o[:, 2], d=o[:, 3], date=B["date"][o[:, 1].astype(np.int64)], bi=o[:, 1].astype(np.int64), xi=o[:, 4].astype(np.int64)))
    df["usd"] = df.pts * PV - COMM
    df["R"] = (df.pts - COMM / PV) / df.risk
    return df


def st(df, lo, hi):
    s = df[(df.date >= lo) & (df.date <= hi)]
    if len(s) < 20:
        return len(s), np.nan, np.nan, np.nan
    u = s.usd; w = u[u > 0].sum(); l = -u[u <= 0].sum()
    return len(s), round((u > 0).mean() * 100, 1), round(w / l, 3) if l > 0 else 9.9, round(s.R.mean(), 3)


LEVELS = {"all": [1, 1, 1, 1, 1, 1], "pd_on": [1, 1, 0, 1, 1, 0], "pd": [1, 0, 0, 1, 0, 0], "on": [0, 1, 0, 0, 1, 0], "on_lon": [0, 1, 1, 0, 1, 1]}
WINS = {"nyam": (570, 690), "ny_open": (570, 630), "ny_mid": (600, 720), "pm": (810, 930)}

if __name__ == "__main__":
    tf = int(sys.argv[1])
    sets = {}
    for name in ("nq_1m.npz", "mnq_fut.npz"):
        d = load(name); B = bars(d, tf); L, atr, trend = day_levels(d)
        sets[name] = (B, L, atr, trend)
    rows = []
    for (ln, lm), (wn, win), K, em, R, bias, mx in itertools.product(LEVELS.items(), WINS.items(), (10, 20, 40) if tf == 1 else (4, 8),
                                                                      (0, 1, 2, 3), (1.0, 1.5, 2.0, 3.0), (0, 1, -1), (0.1, 0.25)):
        r = dict(tf=tf, lv=ln, win=wn, K=K, em=em, R=R, bias=bias, mx=mx)
        for name, (B, L, atr, trend) in sets.items():
            df = run(B, L, atr, trend, np.array(lm, np.bool_), win, K, em, R, bias, mx)
            tag = "cfd" if name.startswith("nq_1m") else "fut"
            if tag == "cfd":
                a = st(df, 20200101, 20231231); b = st(df, 20240101, 20991231)
                r.update(is_n=a[0], is_wr=a[1], is_pf=a[2], is_R=a[3], cfd24_n=b[0], cfd24_wr=b[1], cfd24_pf=b[2])
            else:
                b = st(df, 20240201, 20991231)
                r.update(fut_n=b[0], fut_wr=b[1], fut_pf=b[2], fut_R=b[3])
        rows.append(r)
    g = pd.DataFrame(rows); g.to_csv(f"ict_tf{tf}.csv", index=False)
    print(tf, len(g), "done")
