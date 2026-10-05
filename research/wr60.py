"""Search for a long-side momentum-continuation system with WR >= 60% and PF >= 1.3 (after costs), NQ 2020-01 -> 2026-09.
Base signal = Momentum Sequence (bearish main candle + N rising bullish candles above its low), the only user-supplied
idea that showed a real edge. Added: daily-trend / VWAP filters, session window with 15:55 flatten (prop-compatible),
stop scaling, fixed-R target, optional break-even, time stop.
Fills: next-bar-open market entry +1 tick, stops at level/open -1 tick, targets need 1-tick trade-through, stop first,
target never on the entry bar. $1 RT per MNQ. P&L per 1 MNQ."""
import sys, itertools
import numpy as np, pandas as pd
from numba import njit

TICK, SLIP, PV, COMM = 0.25, 0.25, 2.0, 1.0
import os
z = np.load("data/" + os.environ.get("NQ_DATA", "nq_1m.npz"))
EP, OM, DATE, DAY = z["epoch"], z["om"], z["date"], z["dayid"]
O, H, L, C, V = z["o"], z["h"], z["l"], z["c"], z["v"]


def daily_info():
    """Per trading date: prev RTH close, SMA20 of RTH closes (both known at today's open), ATR14 of RTH days."""
    rth = (OM >= 570) & (OM < 960)
    df = pd.DataFrame(dict(date=DATE[rth], h=H[rth], l=L[rth], c=C[rth]))
    d = df.groupby("date").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    pc = d.c.shift(1)
    tr = np.maximum(d.h - d.l, np.maximum((d.h - pc).abs(), (d.l - pc).abs()))
    d["atr"] = tr.ewm(alpha=1 / 14, adjust=False).mean().shift(1)
    d["sma20"] = d.c.rolling(20).mean().shift(1)
    d["sma50"] = d.c.rolling(50).mean().shift(1)
    d["pc"] = pc
    return d


def build(tf):
    g = EP // tf
    df = pd.DataFrame(dict(g=g, o=O, h=H, l=L, c=C, v=V, om=OM, date=DATE, day=DAY))
    a = df.groupby(["day", "g"], sort=True).agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"),
                                                  v=("v", "sum"), om=("om", "first"), date=("date", "first")).reset_index()
    di = daily_info()
    m = a.date.map(di.pc); s20 = a.date.map(di.sma20); s50 = a.date.map(di.sma50); atr = a.date.map(di.atr)
    # RTH vwap (from 09:30), NaN outside RTH
    rth = (a.om >= 570) & (a.om < 960)
    tp = (a.h + a.l + a.c) / 3 * a.v.clip(lower=1e-9)
    grp = a.date.where(rth, -1)
    vw = tp.where(rth, 0).groupby(grp).cumsum() / a.v.clip(lower=1e-9).where(rth, 0).groupby(grp).cumsum()
    vw[~rth] = np.nan
    return dict(o=a.o.to_numpy(), h=a.h.to_numpy(), l=a.l.to_numpy(), c=a.c.to_numpy(), om=a.om.to_numpy().astype(np.int64),
                date=a.date.to_numpy(), day=a.day.to_numpy().astype(np.int64),
                up20=(m > s20).fillna(False).to_numpy(), up50=(m > s50).fillna(False).to_numpy(),
                atr=atr.fillna(0).to_numpy(), vwap=vw.to_numpy(), tf=tf)


@njit(cache=True)
def sim(o, h, l, c, om, day, allow, N, R, stop_k, be_r, max_bars, win_s, win_e, flat, min_risk, out):
    n = len(c); pos = 0; k = 0; entry = 0.0; sl = 0.0; tp = 0.0; eb = 0; pend = False; psl = 0.0; risk = 0.0
    be_done = False
    for i in range(N + 1, n):
        if pend:
            pend = False
            if day[i] == day[i - 1] and om[i] < flat:
                entry = o[i] + SLIP; risk = entry - psl
                if risk > 0:
                    pos = 1; sl = psl; tp = entry + R * risk; eb = i; be_done = False
        if pos == 1:
            ex = 0.0; done = False
            if o[i] <= sl and i > eb:
                ex = o[i] - SLIP; done = True
            elif l[i] <= sl:
                ex = sl - SLIP; done = True
            elif i > eb and h[i] >= tp + TICK:
                ex = max(o[i], tp); done = True
            elif day[i] != day[eb] or om[i] + 0 >= flat or (max_bars > 0 and i - eb >= max_bars):
                ex = c[i] - SLIP; done = True
            if done:
                out[k, 0] = ex - entry; out[k, 1] = eb; out[k, 2] = risk; out[k, 3] = i; k += 1; pos = 0
            elif be_r > 0 and not be_done and h[i] >= entry + be_r * risk:
                sl = entry + TICK; be_done = True
        if pos == 0 and not pend and allow[i] and om[i] >= win_s and om[i] < win_e:
            m = i - N
            if c[m] < o[m] and day[m] == day[i]:
                ok = True
                for j in range(N):
                    b = i - j
                    if c[b] <= o[b] or l[b] <= l[m]:
                        ok = False; break
                    if j < N - 1 and c[b] <= c[b - 1]:
                        ok = False; break
                if ok:
                    dist = (c[i] - l[m]) * stop_k
                    if dist >= min_risk:
                        pend = True; psl = c[i] - dist
    return k


def stats(pts, dates, lo=None, hi=None):
    msk = np.ones(len(pts), bool)
    if lo: msk &= dates >= lo
    if hi: msk &= dates <= hi
    u = pts[msk] * PV - COMM
    if len(u) < 20:
        return dict(n=len(u), wr=0, pf=0, net=0)
    w = u[u > 0].sum(); ls = -u[u <= 0].sum()
    return dict(n=len(u), wr=round((u > 0).mean() * 100, 1), pf=round(w / ls, 3) if ls else 99, net=round(u.sum()))


YEARS = [(20200101, 20201231), (20210101, 20211231), (20220101, 20221231), (20230101, 20231231),
         (20240101, 20241231), (20250101, 20251231), (20260101, 20261231)]


def run_grid(tf):
    B = build(tf)
    filt = {"none": np.ones(len(B["c"]), bool), "up20": B["up20"], "up50": B["up50"],
            "up20_vwap": B["up20"] & (B["c"] > np.nan_to_num(B["vwap"], nan=1e18)),
            "vwap": B["c"] > np.nan_to_num(B["vwap"], nan=1e18)}
    sessions = {"rth": (570, 945, 955), "am": (570, 720, 955), "open2h": (600, 690, 955)}
    rows = []
    for (fn, allow), (sn, (ws, we, fl)), N, R, sk, be, mb, mr in itertools.product(
            filt.items(), sessions.items(), (3, 4, 5, 6), (0.5, 0.6, 0.75, 1.0, 1.5), (1.0, 1.5, 2.0), (0.0, 0.5),
            (0, 12, 24), (0.0, 0.03)):
        out = np.zeros((len(B["c"]) // 3, 3))
        minr = mr * np.median(B["atr"][B["atr"] > 0])
        k = sim(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], allow, N, R, sk, be, mb, ws, we, fl, minr, out)
        pts = out[:k, 0]; dates = B["date"][out[:k, 1].astype(np.int64)]
        f = stats(pts, dates); a = stats(pts, dates, None, 20231231); b = stats(pts, dates, 20240101)
        yp = []
        for lo, hi in YEARS:
            s = stats(pts, dates, lo, hi); yp.append(s["pf"])
        rows.append(dict(tf=tf, filt=fn, sess=sn, N=N, R=R, stop_k=sk, be=be, max_bars=mb, min_risk=mr,
                         n=f["n"], per_day=round(f["n"] / 1700, 2), wr=f["wr"], pf=f["pf"], net=f["net"],
                         is_wr=a["wr"], is_pf=a["pf"], oos_n=b["n"], oos_wr=b["wr"], oos_pf=b["pf"], oos_net=b["net"],
                         min_year_pf=min(yp), yrs_pf=" ".join(f"{x:.2f}" for x in yp)))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    tf = int(sys.argv[1])
    g = run_grid(tf)
    g.to_csv(f"wr60_tf{tf}.csv", index=False)
    ok = g[(g.is_wr >= 60) & (g.oos_wr >= 60) & (g.is_pf >= 1.3) & (g.oos_pf >= 1.3)]
    print(tf, "configs", len(g), "pass both:", len(ok))
    print(ok.sort_values("min_year_pf", ascending=False).head(25).to_string(index=False))
    print("\nTop by min(IS_pf, OOS_pf) with WR>=60 both:")
    g2 = g[(g.is_wr >= 60) & (g.oos_wr >= 60)].copy(); g2["mpf"] = g2[["is_pf", "oos_pf"]].min(axis=1)
    print(g2.sort_values("mpf", ascending=False).head(15).to_string(index=False))
