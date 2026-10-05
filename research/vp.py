"""Volume-profile levels (prior RTH day POC / VAH / VAL / LVN) and level-reaction setups on NQ.
Profile: each 1-min RTH bar's volume spread uniformly over its range in bins of BIN points. VA = 70% around the POC.
Setups (next RTH day, 09:30 -> 15:55):
  A 'VA rejection' (responsive): first test of VAH from below (VAL from above) that closes back inside the value area
     by >= rej x ATRd -> fade toward the POC. Stop beyond the test extreme. Target POC or R multiple.
  B 'VA acceptance' (initiative): RTH opens outside value in the trend direction -> limit at the VA edge (retest),
     stop k x ATRd beyond, target R.
  C 'LVN reaction': first touch of the nearest prior-day LVN in the direction of the open drive -> continuation.
Costs: 1 tick slippage on market/stop fills, $1 RT, stop first. Result in points (per 1 MNQ: usd = pts*2 - 1)."""
import sys, itertools, numpy as np, pandas as pd
from numba import njit
from ict import load, day_levels
TICK, SLIP = 0.25, 0.25


def profiles(d, BIN):
    om, day, h, l, v = d["om"], d["dayid"], d["h"], d["l"], np.maximum(d["v"], 1e-9)
    nd = int(day.max()) + 1
    POC = np.full(nd, np.nan); VAH = np.full(nd, np.nan); VAL = np.full(nd, np.nan); LVN = [[] for _ in range(nd)]
    rth = np.where((om >= 570) & (om < 960))[0]
    starts = np.r_[0, np.where(np.diff(day[rth]) != 0)[0] + 1]; ends = np.r_[starts[1:], len(rth)]
    for s, e in zip(starts, ends):
        idx = rth[s:e]; dd = day[idx[0]]
        lo = np.floor(l[idx].min() / BIN) * BIN; hi = np.ceil(h[idx].max() / BIN) * BIN
        nb = int(round((hi - lo) / BIN)) + 1
        if nb < 5 or nb > 5000: continue
        prof = np.zeros(nb)
        a = ((l[idx] - lo) / BIN).astype(int); b = ((h[idx] - lo) / BIN).astype(int)
        for i0, i1, vol in zip(a, b, v[idx]):
            prof[i0:i1 + 1] += vol / (i1 - i0 + 1)
        p = int(prof.argmax()); tot = prof.sum(); lo_i = hi_i = p; acc = prof[p]
        while acc < 0.7 * tot and (lo_i > 0 or hi_i < nb - 1):
            up = prof[hi_i + 1] if hi_i < nb - 1 else -1; dn = prof[lo_i - 1] if lo_i > 0 else -1
            if up >= dn: hi_i += 1; acc += up
            else: lo_i -= 1; acc += dn
        POC[dd] = lo + (p + 0.5) * BIN; VAH[dd] = lo + (hi_i + 1) * BIN; VAL[dd] = lo + lo_i * BIN
        sm = np.convolve(prof, np.ones(3) / 3, mode="same"); med = np.median(prof[lo_i:hi_i + 1])
        for i in range(max(1, lo_i), min(nb - 1, hi_i + 1)):
            if sm[i] < sm[i - 1] and sm[i] <= sm[i + 1] and sm[i] < 0.35 * med:
                LVN[dd].append(lo + (i + 0.5) * BIN)
    # shift to "prior day" arrays aligned on the trading day that uses them
    P = np.full((nd, 3), np.nan); LV = np.full((nd, 8), np.nan)
    have = np.where(~np.isnan(POC))[0]
    for k in range(1, len(have)):
        cur, prev = have[k], have[k - 1]
        P[cur] = (POC[prev], VAH[prev], VAL[prev])
        for j, x in enumerate(sorted(LVN[prev])[:8]): LV[cur, j] = x
    return P, LV


@njit(cache=True)
def sim(o, h, l, c, om, day, P, LV, atr, trend, setup, rej, sk, R, tgt_poc, bias, last_entry, out):
    n = len(c); k = 0; i = 0
    while i < n:
        d = day[i]; j = i
        while j < n and day[j] == d: j += 1
        nxt = j; a = atr[d]
        poc, vah, val = P[d, 0], P[d, 1], P[d, 2]
        if a <= 0 or np.isnan(poc): i = nxt; continue
        q = i
        while q < nxt and om[q] < 570: q += 1
        if q >= nxt: i = nxt; continue
        ro = o[q]; pos = 0; entry = 0.0; sl = 0.0; tp = 0.0; eb = 0; done = False
        touchedH = False; touchedL = False; ext = 0.0; lim = np.nan; ldir = 0
        if setup == 1:
            if ro > vah and (bias == 0 or trend[d] == 1): lim = vah; ldir = 1
            elif ro < val and (bias == 0 or trend[d] == -1): lim = val; ldir = -1
        lvl = np.nan
        while q < nxt:
            m = om[q]
            if pos != 0:
                ex = np.nan
                if pos == 1:
                    if l[q] <= sl: ex = (min(o[q], sl) if q > eb else sl) - SLIP
                    elif q > eb and h[q] >= tp + TICK: ex = max(o[q], tp)
                else:
                    if h[q] >= sl: ex = (max(o[q], sl) if q > eb else sl) + SLIP
                    elif q > eb and l[q] <= tp - TICK: ex = min(o[q], tp)
                if np.isnan(ex) and m >= 955: ex = c[q] - pos * SLIP
                if not np.isnan(ex):
                    out[k, 0] = pos * (ex - entry); out[k, 1] = eb; out[k, 2] = abs(entry - sl); out[k, 3] = pos; k += 1; pos = 0; done = True
                q += 1; continue
            if done or m >= last_entry: q += 1; continue
            if setup == 0:
                # VAH test from below then close back inside by rej*ATR -> short
                if not touchedH and h[q] >= vah and o[q] < vah:
                    touchedH = True; ext = h[q]
                if touchedH:
                    ext = max(ext, h[q])
                    if c[q] <= vah - rej * a and (bias == 0 or trend[d] == -1):
                        if q + 1 < nxt:
                            e = o[q + 1] - SLIP; stop = ext + TICK; risk = stop - e
                            t = poc if tgt_poc else e - R * risk
                            if risk > 0 and risk <= sk * a and t < e:
                                pos = -1; entry = e; sl = stop; tp = t; eb = q + 1
                        touchedH = False; touchedL = True  # one attempt per side
                if not touchedL and l[q] <= val and o[q] > val:
                    touchedL = True; ext = l[q]
                elif touchedL and pos == 0 and not done and ext < 1e17 and l[q] <= val:
                    pass
                if touchedL and pos == 0 and ext > 0 and ext <= val:
                    ext = min(ext, l[q])
                    if c[q] >= val + rej * a and (bias == 0 or trend[d] == 1):
                        if q + 1 < nxt:
                            e = o[q + 1] + SLIP; stop = ext - TICK; risk = e - stop
                            t = poc if tgt_poc else e + R * risk
                            if risk > 0 and risk <= sk * a and t > e:
                                pos = 1; entry = e; sl = stop; tp = t; eb = q + 1
                        ext = 1e18
            elif setup == 1:
                if ldir != 0 and ((ldir == 1 and l[q] <= lim - TICK) or (ldir == -1 and h[q] >= lim + TICK)):
                    e = min(lim, o[q]) if ldir == 1 else max(lim, o[q])
                    stop = e - ldir * sk * a; risk = sk * a
                    pos = ldir; entry = e; sl = stop; tp = e + ldir * R * risk; eb = q; ldir = 0
                    if (pos == 1 and l[q] <= sl) or (pos == -1 and h[q] >= sl):
                        out[k, 0] = -(risk + SLIP); out[k, 1] = eb; out[k, 2] = risk; out[k, 3] = pos; k += 1; pos = 0; done = True
            else:
                # setup 2: LVN continuation in the direction of the first 15-min drive
                if m >= 585 and np.isnan(lvl):
                    drv = 1 if c[q - 1] > ro else -1
                    if bias == 1 and drv != trend[d]: done = True; q += 1; continue
                    best = np.nan
                    for z in range(8):
                        x = LV[d, z]
                        if np.isnan(x): continue
                        if drv == 1 and x < c[q - 1] and (np.isnan(best) or x > best): best = x
                        if drv == -1 and x > c[q - 1] and (np.isnan(best) or x < best): best = x
                    if np.isnan(best): done = True; q += 1; continue
                    lvl = best; ldir = drv
                if not np.isnan(lvl) and ldir != 0:
                    if (ldir == 1 and l[q] <= lvl - TICK) or (ldir == -1 and h[q] >= lvl + TICK):
                        e = min(lvl, o[q]) if ldir == 1 else max(lvl, o[q]); risk = sk * a
                        pos = ldir; entry = e; sl = e - ldir * risk; tp = e + ldir * R * risk; eb = q; ldir = 0
                        if (pos == 1 and l[q] <= sl) or (pos == -1 and h[q] >= sl):
                            out[k, 0] = -(risk + SLIP); out[k, 1] = eb; out[k, 2] = risk; out[k, 3] = pos; k += 1; pos = 0; done = True
            q += 1
        i = nxt
    return k


def run(d, P, LV, X, setup, rej, sk, R, tgt_poc, bias, last_entry):
    L, atr, trend = X
    out = np.zeros((5000, 4))
    k = sim(d["o"], d["h"], d["l"], d["c"], d["om"].astype(np.int64), d["dayid"].astype(np.int64), P, LV, atr, trend, setup, rej, sk, R, tgt_poc, bias, last_entry, out)
    return pd.DataFrame(dict(pts=out[:k, 0], date=d["date"][out[:k, 1].astype(np.int64)], d=out[:k, 3]))


def pf(u): return u[u > 0].sum() / -u[u <= 0].sum() if (u <= 0).any() and len(u) > 10 else np.nan


if __name__ == "__main__":
    rows = []
    S = {}
    for n in ("nq_1m.npz", "mnq_fut.npz"):
        d = load(n); X = day_levels(d); P, LV = profiles(d, 5.0); S[n] = (d, P, LV, X)
    grid = [(0, rej, sk, R, tp, b, le) for rej, sk, R, tp, b, le in itertools.product((0.0, 0.03, 0.06), (0.1, 0.2, 0.35), (1.0, 2.0), (0, 1), (0, 1, -1), (720, 900))]
    grid += [(1, 0, sk, R, 0, b, le) for sk, R, b, le in itertools.product((0.05, 0.1, 0.2), (0.5, 1.0, 2.0, 3.0), (0, 1), (720, 900))]
    grid += [(2, 0, sk, R, 0, b, le) for sk, R, b, le in itertools.product((0.05, 0.1, 0.2), (0.5, 1.0, 2.0, 3.0), (0, 1), (720, 900))]
    for setup, rej, sk, R, tpoc, b, le in grid:
        if setup == 0 and b == -1: b = 0
        r = dict(setup=setup, rej=rej, sk=sk, R=R, tgt_poc=tpoc, bias=b, last=le)
        for n, (d, P, LV, X) in S.items():
            df = run(d, P, LV, X, setup, rej, sk, R, tpoc, b, le); u = df.pts * 2 - 1
            if n == "nq_1m.npz":
                for lab, m in (("is", df.date < 20240101), ("c24", df.date >= 20240101)):
                    r[lab + "_n"] = int(m.sum()); r[lab + "_wr"] = round(100 * (u[m] > 0).mean(), 1) if m.sum() else np.nan; r[lab + "_pf"] = round(pf(u[m]), 3)
            else:
                m = df.date >= 20240201; r["fut_n"] = int(m.sum()); r["fut_wr"] = round(100 * (u[m] > 0).mean(), 1) if m.sum() else np.nan; r["fut_pf"] = round(pf(u[m]), 3)
        rows.append(r)
    g = pd.DataFrame(rows).drop_duplicates(); g.to_csv("vp_scan.csv", index=False)
    for s in (0, 1, 2):
        h = g[(g.setup == s) & (g.is_n >= 150)]
        if len(h) == 0: continue
        print(f"\nSETUP {s}: median PF IS {h.is_pf.median():.2f} C24 {h.c24_pf.median():.2f} FUT {h.fut_pf.median():.2f}")
        h = h.assign(m=h[["is_pf", "c24_pf", "fut_pf"]].min(axis=1))
        print(h.sort_values("m", ascending=False).head(8).to_string(index=False))
