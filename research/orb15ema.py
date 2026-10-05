"""15-min opening range breakout, then 2-min EMA(20) pullback confirmation (user idea).
OR = 09:30-09:45 ET. On 2-min bars after 09:45: first close beyond the OR sets the direction (long above / short below).
Then wait for the pullback to interact with the 2-min EMA20 (low <= EMA for longs) and a confirmation:
  conf 0: the touch bar closes back above the EMA (rejection)  -> enter next bar open
  conf 1: a later bar closes above the touch bar's high        -> enter next bar open
Stop: 0 touch-bar extreme | 1 OR midpoint | 2 opposite OR side. Target R x risk. Entries until win_end, flat 15:55.
Optional invalidation: a close back inside the OR cancels the setup. Filters: daily trend, pullback day (prior-day move
with trend < 0.44 ATR). Up to max_tr trades per day (re-arm after exit)."""
import sys, itertools, numpy as np, pandas as pd
from numba import njit
from ict import load, bars, day_levels
TICK, SLIP = 0.25, 0.25


@njit(cache=True)
def sim(o, h, l, c, ema, om, day, atr, trend, pb, conf, smode, R, win_end, inval, filt, mx, max_tr, out):
    n = len(c); k = 0; i = 0
    while i < n:
        d = day[i]; j = i
        while j < n and day[j] == d: j += 1
        nxt = j; a = atr[d]
        if a <= 0: i = nxt; continue
        orh = -1e18; orl = 1e18
        for q in range(i, nxt):
            if om[q] >= 570 and om[q] < 585:
                orh = max(orh, h[q]); orl = min(orl, l[q])
        if orh < -1e17: i = nxt; continue
        dirn = 0; touch = -1; ntr = 0; pos = 0; q = i
        entry = 0.0; sl = 0.0; tp = 0.0; eb = 0
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
                    out[k, 0] = pos * (ex - entry); out[k, 1] = eb; out[k, 2] = abs(entry - sl); k += 1; pos = 0; touch = -1
                q += 1; continue
            if m < 585 or m >= win_end or ntr >= max_tr: q += 1; continue
            if dirn == 0:
                if c[q] > orh: dirn = 1
                elif c[q] < orl: dirn = -1
                if dirn != 0:
                    t = trend[d]
                    if (filt >= 1 and dirn != t) or (filt == 2 and not pb[d]): ntr = max_tr
                q += 1; continue
            if inval == 1 and ((dirn == 1 and c[q] < orh) or (dirn == -1 and c[q] > orl)):
                touch = -1; q += 1; continue
            sig = False
            if touch < 0:
                if (dirn == 1 and l[q] <= ema[q] and c[q] > orl) or (dirn == -1 and h[q] >= ema[q] and c[q] < orh):
                    touch = q
                    if conf == 0 and ((dirn == 1 and c[q] > ema[q]) or (dirn == -1 and c[q] < ema[q])): sig = True
            else:
                if conf == 0:
                    if (dirn == 1 and l[q] <= ema[q] and c[q] > ema[q]) or (dirn == -1 and h[q] >= ema[q] and c[q] < ema[q]):
                        touch = q; sig = True
                else:
                    if (dirn == 1 and c[q] > h[touch]) or (dirn == -1 and c[q] < l[touch]): sig = True
                    elif (dirn == 1 and l[q] < l[touch]) or (dirn == -1 and h[q] > h[touch]): touch = q
            if sig and q + 1 < nxt:
                e = o[q + 1] + dirn * SLIP
                if smode == 0: stop = (l[touch] - TICK) if dirn == 1 else (h[touch] + TICK)
                elif smode == 1: stop = (orh + orl) / 2
                else: stop = (orl - TICK) if dirn == 1 else (orh + TICK)
                risk = (e - stop) * dirn
                if risk > 0 and risk <= mx * a:
                    pos = dirn; entry = e; sl = stop; tp = e + dirn * R * risk; eb = q + 1; ntr += 1
                touch = -1
            q += 1
        i = nxt
    return k


def prep(name, tf=2):
    d = load(name); B = bars(d, tf); L, atr, trend = day_levels(d)
    B["ema"] = pd.Series(B["c"]).ewm(span=20, adjust=False).mean().to_numpy()
    # pullback day flag from RTH closes
    om, day, c = d["om"], d["dayid"], d["c"]
    nd = int(day.max()) + 1
    cl = pd.Series(c[(om == 959)], index=day[(om == 959)]).reindex(range(nd))
    pc = cl.shift(1); pc2 = cl.shift(2)
    pr = ((pc - pc2) / np.where(atr > 0, atr, np.nan)) * trend
    pb = (pr < 0.44).fillna(False).to_numpy()
    return B, atr, trend, pb


def run(P, conf, smode, R, win_end, inval, filt, mx, max_tr):
    B, atr, trend, pb = P
    out = np.zeros((20000, 3))
    k = sim(B["o"], B["h"], B["l"], B["c"], B["ema"], B["om"], B["day"], atr, trend, pb, conf, smode, R, win_end, inval, filt, mx, max_tr, out)
    df = pd.DataFrame(dict(pts=out[:k, 0], date=B["date"][out[:k, 1].astype(np.int64)], risk=out[:k, 2]))
    df["usd"] = df.pts * 2 - 1
    return df


def pf(s): return s[s > 0].sum() / -s[s <= 0].sum() if (s <= 0).any() else 9.0


if __name__ == "__main__":
    S = {n: prep(n) for n in ("nq_1m.npz", "mnq_fut.npz")}
    rows = []
    for conf, sm, R, we, inv, filt, mx, mt in itertools.product((0, 1), (0, 1, 2), (1.0, 1.5, 2.0, 3.0), (660, 720, 810), (0, 1), (0, 1, 2), (0.1, 0.2, 0.35), (1, 2)):
        r = dict(conf=conf, stop=sm, R=R, win_end=we, inval=inv, filt=filt, mx=mx, max_tr=mt)
        for n, P in S.items():
            df = run(P, conf, sm, R, we, inv, filt, mx, mt)
            if n == "nq_1m.npz":
                for nm, s in (("is", df[df.date < 20240101]), ("c24", df[df.date >= 20240101])):
                    r[nm + "_n"] = len(s); r[nm + "_wr"] = round(100 * (s.usd > 0).mean(), 1) if len(s) else np.nan; r[nm + "_pf"] = round(pf(s.usd), 3) if len(s) > 10 else np.nan
            else:
                s = df[df.date >= 20240201]; r["fut_n"] = len(s); r["fut_wr"] = round(100 * (s.usd > 0).mean(), 1) if len(s) else np.nan; r["fut_pf"] = round(pf(s.usd), 3) if len(s) > 10 else np.nan
                s = df[df.date >= 20260101]; r["f26_n"] = len(s); r["f26_pf"] = round(pf(s.usd), 3) if len(s) > 10 else np.nan
        rows.append(r)
    g = pd.DataFrame(rows); g.to_csv("orb15ema.csv", index=False)
    h = g[g.is_n >= 200]
    print("configs", len(g), "| median PF IS %.3f C24 %.3f FUT %.3f" % (h.is_pf.median(), h.c24_pf.median(), h.fut_pf.median()))
    sel = h[h.is_pf >= 1.2]; print("IS-selected", len(sel), "-> FUT median %.2f, share >=1.2 %.2f" % (sel.fut_pf.median(), (sel.fut_pf >= 1.2).mean()))
    g["m"] = g[["is_pf", "c24_pf", "fut_pf"]].min(axis=1)
    print(g[(g.is_n >= 200) & (g.fut_n >= 100)].sort_values("m", ascending=False).head(15).to_string(index=False))
