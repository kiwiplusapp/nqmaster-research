"""'Tradefather' bank level + momentum leg candle, mechanised, on NQ.
Bank level  : the last N bars formed a sideways zone whose high-low range <= zk x ATR(14 bars).
Leg candle  : the current bar closes beyond the zone with range >= lk x ATR (momentum), same colour as the break.
Entry       : next bar open in the break direction (optionally only with the daily trend). Window = ET minutes [ws, we).
Stop        : 'zone' = opposite side of the zone, 'leg' = extreme of the leg candle.
Exit modes  : 0 fixed R target | 1 breakeven at +1R then chandelier trail (extreme - tr x ATR), no target
              | 2 same as 1 + scale-in: add a 2nd unit at +1R. Flat at flat_om. Max 2 trades/day, one at a time.
Costs: 1 tick slippage on entries/stops, $1.90 RT per MNQ unit; stop first inside a bar."""
import sys, itertools, numpy as np, pandas as pd
from numba import njit
from ict import load, bars, day_levels
TICK, SLIP = 0.25, 0.25


@njit(cache=True)
def atr_bars(h, l, c, n):
    out = np.zeros(len(c)); a = 0.0
    for i in range(len(c)):
        tr = h[i] - l[i] if i == 0 else max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
        a = tr if i == 0 else (a * (n - 1) + tr) / n
        out[i] = a
    return out


@njit(cache=True)
def sim(o, h, l, c, om, day, atr, trend, N, zk, lk, smode, emode, R, trail, ws, we, flat, tf_only, out):
    n = len(c); k = 0; pos = 0; entry = 0.0; sl = 0.0; tp = 0.0; eb = 0; units = 1; add_px = 0.0; e2 = 0.0; ext = 0.0; rk = 0.0
    cur = -1; ntd = 0
    for i in range(N + 2, n):
        if day[i] != cur: cur = day[i]; ntd = 0
        m = om[i]
        if pos != 0:
            done = False; ex = 0.0
            # stop
            if (pos == 1 and l[i] <= sl) or (pos == -1 and h[i] >= sl):
                ex = (min(o[i], sl) if pos == 1 else max(o[i], sl)) - pos * SLIP if i > eb else sl - pos * SLIP; done = True
            elif emode == 0 and i > eb and ((pos == 1 and h[i] >= tp + TICK) or (pos == -1 and l[i] <= tp - TICK)):
                ex = tp; done = True
            elif day[i] != day[eb] or m >= flat:
                ex = c[i] - pos * SLIP; done = True
            if done:
                pnl = pos * (ex - entry)
                if units == 2: pnl += pos * (ex - e2)
                out[k, 0] = pnl; out[k, 1] = eb; out[k, 2] = rk; out[k, 3] = units; k += 1; pos = 0
                continue
            if emode >= 1:
                ext = max(ext, h[i]) if pos == 1 else min(ext, l[i])
                if (pos == 1 and ext >= entry + rk) or (pos == -1 and ext <= entry - rk):
                    be = entry + pos * TICK
                    if (pos == 1 and be > sl) or (pos == -1 and be < sl): sl = be
                    if emode == 2 and units == 1:
                        units = 2; e2 = entry + pos * rk + pos * SLIP
                    tr_stop = ext - pos * trail * atr[i]
                    if (pos == 1 and tr_stop > sl) or (pos == -1 and tr_stop < sl): sl = tr_stop
            continue
        if ntd >= 2 or m < ws or m >= we: continue
        zh = h[i - N]; zl = l[i - N]
        for j in range(i - N, i):
            if day[j] != day[i]: zh = -1.0; break
            zh = max(zh, h[j]); zl = min(zl, l[j])
        if zh < 0: continue
        a = atr[i - 1]
        if a <= 0 or zh - zl > zk * a: continue
        if h[i] - l[i] < lk * a: continue
        d = 0
        if c[i] > zh and c[i] > o[i]: d = 1
        elif c[i] < zl and c[i] < o[i]: d = -1
        if d == 0: continue
        if tf_only and d != trend[day[i]]: continue
        if i + 1 >= n or day[i + 1] != day[i]: continue
        e = o[i + 1] + d * SLIP
        stop = (zl - TICK if d == 1 else zh + TICK) if smode == 0 else (l[i] - TICK if d == 1 else h[i] + TICK)
        r = (e - stop) * d
        if r <= 0: continue
        pos = d; entry = e; sl = stop; rk = r; tp = e + d * R * r; eb = i + 1; units = 1; ext = e; ntd += 1
    return k


def run(B, trend, N, zk, lk, smode, emode, R, trail, ws, we, flat, tf_only):
    atr = atr_bars(B["h"], B["l"], B["c"], 14)
    out = np.zeros((len(B["c"]) // 5, 4))
    k = sim(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], atr, trend, N, zk, lk, smode, emode, R, trail, ws, we, flat, tf_only, out)
    df = pd.DataFrame(dict(pts=out[:k, 0], date=B["date"][out[:k, 1].astype(np.int64)], units=out[:k, 3]))
    df["usd"] = df.pts * 2 - 1.9 * df.units
    return df


def pf(u): return u[u > 0].sum() / -u[u <= 0].sum() if (u <= 0).any() and len(u) > 10 else np.nan


if __name__ == "__main__":
    tf = int(sys.argv[1])
    S = {}
    for n in ("nq_1m.npz", "mnq_fut.npz"):
        d = load(n); B = bars(d, tf); L, atr_d, trend = day_levels(d); S[n] = (B, trend)
    rows = []
    for N, zk, lk, sm, em, R, trail, (ws, we), tfo in itertools.product((10, 20), (2.0, 3.0), (1.0, 1.5), (0, 1), (0, 1, 2), (2.0,), (2.0, 3.0),
                                                                        ((480, 600), (570, 690), (570, 900)), (0, 1)):
        if em == 0 and trail == 3.0: continue
        r = dict(tf=tf, N=N, zk=zk, lk=lk, stop="zone" if sm == 0 else "leg", exit=["2R", "BE+trail", "BE+trail+scale"][em], trail=trail, win=f"{ws}-{we}", trend_only=tfo)
        for n, (B, trend) in S.items():
            df = run(B, trend, N, zk, lk, sm, em, R, trail, ws, we, 720 if we <= 690 else 955, tfo)
            if n == "nq_1m.npz":
                for p, x in (("IS", df[df.date < 20240101]), ("C24", df[df.date >= 20240101])):
                    r[p + "_n"] = len(x); r[p + "_wr"] = round(100 * (x.usd > 0).mean(), 1) if len(x) else np.nan; r[p + "_pf"] = round(pf(x.usd), 2)
            else:
                x = df[df.date >= 20240201]; r["REAL_n"] = len(x); r["REAL_wr"] = round(100 * (x.usd > 0).mean(), 1) if len(x) else np.nan; r["REAL_pf"] = round(pf(x.usd), 2)
        rows.append(r)
    g = pd.DataFrame(rows); g.to_csv(f"tradefather_tf{tf}.csv", index=False)
    h = g[g.IS_n >= 150]
    print(f"tf{tf}: {len(g)} configs | median PF IS {h.IS_pf.median():.2f} C24 {h.C24_pf.median():.2f} REAL {h.REAL_pf.median():.2f}")
    print(h.groupby("exit")[["IS_pf", "C24_pf", "REAL_pf", "IS_wr", "REAL_wr"]].median().round(2).to_string())
    sel = h[h.IS_pf >= 1.2]; print(f"IS-selected (PF>=1.2): {len(sel)} -> REAL median {sel.REAL_pf.median():.2f}, C24 median {sel.C24_pf.median():.2f}")
    h = h.assign(m=h[["IS_pf", "C24_pf", "REAL_pf"]].min(axis=1))
    print(h.sort_values("m", ascending=False).head(10).to_string(index=False))
