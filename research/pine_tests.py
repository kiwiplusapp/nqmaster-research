"""Backtests of two user-supplied TradingView strategies on NQ 1m data (2020-01 -> 2026-09), resampled.
A) NASDAQ 100 Peak Hours Strategy (EMA9/21 + RSI + VWAP + ATR filter, GMT-5 fixed 09:30-11:30 window).
B) Momentum Sequence Strategy [Herman] (main candle + N consecutive opposite candles, SL at main candle, TP k*R).
Fills: market orders at next bar open + 1 tick; stops at level (or open if gapped) - 1 tick; limits need 1-tick
trade-through (or open if gapped). Stop assumed before target inside a bar. Costs $1 RT per MNQ. P&L per 1 MNQ."""
import sys
import numpy as np, pandas as pd
from numba import njit

TICK, SLIP, PV, COMM = 0.25, 0.25, 2.0, 1.0

z = np.load("data/nq_1m.npz")
EP = z["epoch"]; O, H, L, C, V = z["o"], z["h"], z["l"], z["c"], z["v"]; DAYID = z["dayid"]; DATE = z["date"]


def bars(tf):
    if tf == 1:
        return dict(o=O, h=H, l=L, c=C, v=V, ep=EP, day=DAYID, date=DATE)
    g = EP // tf
    df = pd.DataFrame(dict(g=g, o=O, h=H, l=L, c=C, v=V, ep=EP, day=DAYID, date=DATE))
    a = df.groupby(["day", "g"], sort=True).agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"),
                                                  v=("v", "sum"), ep=("ep", "first"), date=("date", "first")).reset_index()
    return {k: a[k].to_numpy() for k in ["o", "h", "l", "c", "v", "ep", "day", "date"]}


def ema(x, n):
    return pd.Series(x).ewm(span=n, adjust=False).mean().to_numpy()


def rma(x, n):
    return pd.Series(x).ewm(alpha=1.0 / n, adjust=False).mean().to_numpy()


# ------------------------------------------------------------------ A) Peak Hours
@njit(cache=True)
def sim_peak(o, h, l, c, atr, longc, shortc, revL, revS, trail_mult, out):
    n = len(c); pos = 0; entry = 0.0; k = 0
    lentry_bar = -1; sentry_bar = -1; lentry_px = np.nan; sentry_px = np.nan
    pend = 0            # pending market action at next open: 1 go long, -1 go short, 2 close
    be_on = False; be_px = 0.0; ext = 0.0; entry_bar = 0
    for i in range(1, n):
        # 1) market orders at the open
        if pend != 0:
            px = o[i]
            if pos != 0 and (pend == 2 or pend == -pos):
                ex = px - pos * SLIP
                out[k, 0] = pos * (ex - entry); out[k, 1] = entry_bar; out[k, 2] = i; out[k, 3] = pos; k += 1
                pos = 0
            if pend == 1 or pend == -1:
                if pos == 0:
                    pos = pend; entry = px + pos * SLIP; be_on = False; ext = entry; entry_bar = i
            pend = 0
        # 2) stops intrabar (levels known from previous bar close)
        if pos != 0:
            a = atr[i - 1]
            st = c[i - 1] - pos * 0.5 * a
            act = 1.5 * a * trail_mult; off = act / 2.0
            if pos == 1:
                if be_on and be_px > st:
                    st = be_px
                if ext - entry >= act and ext - off > st:
                    st = ext - off
                if l[i] <= st:
                    ex = min(o[i], st) - SLIP
                    out[k, 0] = ex - entry; out[k, 1] = entry_bar; out[k, 2] = i; out[k, 3] = 1; k += 1; pos = 0
                else:
                    ext = max(ext, h[i])
            else:
                if be_on and be_px < st:
                    st = be_px
                if entry - ext >= act and ext + off < st:
                    st = ext + off
                if h[i] >= st:
                    ex = max(o[i], st) + SLIP
                    out[k, 0] = entry - ex; out[k, 1] = entry_bar; out[k, 2] = i; out[k, 3] = -1; k += 1; pos = 0
                else:
                    ext = min(ext, l[i])
        # 3) bar-close logic (Pine order)
        if longc[i]:
            lentry_bar = i; lentry_px = c[i]
            if pos != 1:
                pend = 1
        if shortc[i]:
            sentry_bar = i; sentry_px = c[i]
            if pos != -1:
                pend = -1
        if pos == 1 and c[i] > lentry_px + 1.5 * atr[i]:
            be_on = True; be_px = lentry_px
        if pos == -1 and c[i] < sentry_px - 1.5 * atr[i]:
            be_on = True; be_px = sentry_px
        if lentry_bar >= 0 and i - lentry_bar >= 20:
            if pos == 1:
                pend = 2
            lentry_bar = -1
        if sentry_bar >= 0 and i - sentry_bar >= 20:
            if pos == -1:
                pend = 2
            sentry_bar = -1
        if pos == 1 and revL[i]:
            pend = 2
        if pos == -1 and revS[i]:
            pend = 2
    return k


def run_peak(tf, trail_mult):
    b = bars(tf); o, h, l, c, v, ep = b["o"], b["h"], b["l"], b["c"], b["v"], b["ep"]
    e21, e9 = ema(c, 21), ema(c, 9)
    d = np.diff(c, prepend=c[0])
    rsi = 100 - 100 / (1 + rma(np.maximum(d, 0), 14) / np.maximum(rma(np.maximum(-d, 0), 14), 1e-12))
    pc = np.roll(c, 1)
    tr = np.maximum(h - l, np.maximum(abs(h - pc), abs(l - pc))); atr = rma(tr, 14)
    volf = atr > pd.Series(atr).rolling(20).mean().to_numpy()
    hlc3 = (h + l + c) / 3; vv = np.maximum(v, 1e-9)
    day = b["day"]
    vwap = pd.Series(hlc3 * vv).groupby(day).cumsum().to_numpy() / pd.Series(vv).groupby(day).cumsum().to_numpy()
    ldir = e21 > ema(np.roll(e21, 1), 3); sdir = e9 > ema(np.roll(e9, 1), 3)
    est = ((ep % 1440) - 300) % 1440          # bar open time in fixed GMT-5
    base = (est >= 480) & (est <= 960) & volf & (est >= 570) & (est <= 690)
    longc = (c > e9) & (e9 > e21) & ldir & sdir & (rsi > 50) & (c > vwap) & base
    shortc = (c < e9) & (e9 < e21) & ~ldir & ~sdir & (rsi < 50) & (c < vwap) & base
    revL = (e9 < e21) & ~ldir; revS = (e9 > e21) & ~sdir
    out = np.zeros((len(c), 4)); k = sim_peak(o, h, l, c, atr, longc, shortc, revL, revS, trail_mult, out)
    return trades(out[:k], b)


# ------------------------------------------------------------------ B) Momentum Sequence
@njit(cache=True)
def sim_seq(o, h, l, c, N, R, side, out):
    n = len(c); pos = 0; k = 0; entry = 0.0; sl = 0.0; tp = 0.0; fill_bar = -1; pend = 0; psl = 0.0; ptp = 0.0
    for i in range(N + 1, n):
        if pend != 0:
            pos = pend; entry = o[i] + pos * SLIP; sl = psl; tp = ptp; fill_bar = i; pend = 0
        elif pos != 0:   # Pine places the exit on the fill bar's close -> active from the next bar
            done = False; ex = 0.0
            if pos == 1:
                if l[i] <= sl:
                    ex = min(o[i], sl) - SLIP; done = True
                elif h[i] >= tp + TICK or o[i] >= tp:
                    ex = max(o[i], tp); done = True
            else:
                if h[i] >= sl:
                    ex = max(o[i], sl) + SLIP; done = True
                elif l[i] <= tp - TICK or o[i] <= tp:
                    ex = min(o[i], tp); done = True
            if done:
                out[k, 0] = pos * (ex - entry); out[k, 1] = fill_bar; out[k, 2] = i; out[k, 3] = pos; out[k, 4] = abs(entry - sl); k += 1
                pos = 0
        if pos == 0 and pend == 0:
            m = i - N
            if side >= 0 and c[m] < o[m]:
                ok = True
                for j in range(N):
                    b = i - j
                    if c[b] <= o[b] or l[b] <= l[m]:
                        ok = False
                    if j < N - 1 and c[b] <= c[b - 1]:
                        ok = False
                if ok:
                    pend = 1; psl = l[m]; ptp = c[i] + (c[i] - l[m]) * R
            if pend == 0 and side <= 0 and c[m] > o[m]:
                ok = True
                for j in range(N):
                    b = i - j
                    if c[b] >= o[b] or h[b] >= h[m]:
                        ok = False
                    if j < N - 1 and c[b] >= c[b - 1]:
                        ok = False
                if ok:
                    pend = -1; psl = h[m]; ptp = c[i] - (h[m] - c[i]) * R
    return k


def run_seq(tf, N, R, side):
    b = bars(tf)
    out = np.zeros((len(b["c"]), 5)); k = sim_seq(b["o"], b["h"], b["l"], b["c"], N, R, side, out)
    return trades(out[:k], b)


def trades(a, b):
    df = pd.DataFrame(dict(pts=a[:, 0], date=b["date"][a[:, 1].astype(int)]))
    df["usd"] = df.pts * PV - COMM
    return df


def stats(df, lo=None, hi=None):
    if lo:
        df = df[df.date >= lo]
    if hi:
        df = df[df.date <= hi]
    if len(df) == 0:
        return dict(n=0)
    u = df.usd; w = u[u > 0].sum(); ls = -u[u <= 0].sum()
    daily = df.groupby("date").usd.sum(); eq = daily.cumsum(); dd = (eq.cummax() - eq).max()
    return dict(n=len(df), per_day=round(len(df) / max(df.date.nunique(), 1), 1), wr=round((u > 0).mean() * 100, 1),
                pf=round(w / ls, 2) if ls else 99, net=round(u.sum()), avg=round(u.mean(), 2), dd=round(dd))


PERIODS = [("2020-26", None, None), ("2020-23", None, 20231231), ("2024", 20240101, 20241231), ("2025", 20250101, 20251231),
           ("IS 24/09-26/01", 20240925, 20260125), ("OOS 26/01-26/09", 20260126, None)]


def table(df, label):
    rows = []
    for name, lo, hi in PERIODS:
        s = stats(df, lo, hi); s["period"] = name; rows.append(s)
    print(f"\n=== {label}"); print(pd.DataFrame(rows).set_index("period").to_string()); sys.stdout.flush()


if __name__ == "__main__":
    if sys.argv[1] == "A":
        for tf in (1, 5, 15):
            for tm, nm in ((0.25, "trail en ticks (como esta escrito)"), (1.0, "trail en puntos")):
                table(run_peak(tf, tm), f"PEAK HOURS tf={tf}m {nm}")
    else:
        for tf in (1, 5, 15):
            table(run_seq(tf, 5, 1.5, 1), f"MOMENTUM SEQ default tf={tf}m N=5 1.5R long-only")
        cache = {tf: bars(tf) for tf in (1, 3, 5, 15)}
        rows = []
        for tf in (1, 3, 5, 15):
            b = cache[tf]
            for N in (2, 3, 4, 5):
                for R in (0.5, 1.0, 1.5, 2.0):
                    for side in (1, -1, 0):
                        out = np.zeros((len(b["c"]), 5)); k = sim_seq(b["o"], b["h"], b["l"], b["c"], N, R, side, out)
                        df = trades(out[:k], b)
                        a = stats(df, 20240925, 20260125); b2 = stats(df, 20260126, None); f = stats(df)
                        rows.append(dict(tf=tf, N=N, R=R, side=side, full_n=f.get("n"), full_pf=f.get("pf"), full_wr=f.get("wr"),
                                         is_n=a.get("n"), is_pf=a.get("pf"), is_wr=a.get("wr"), is_net=a.get("net"),
                                         oos_n=b2.get("n"), oos_pf=b2.get("pf"), oos_wr=b2.get("wr"), oos_net=b2.get("net")))
        g = pd.DataFrame(rows); g.to_csv("pine_seq_grid.csv", index=False)
        print("\n=== GRID top 15 by IS PF (min 100 IS trades)")
        print(g[g.is_n >= 100].sort_values("is_pf", ascending=False).head(15).to_string(index=False))
        print("\nconfigs:", len(g), " full PF>1.1:", int((g.full_pf > 1.1).sum()),
              " IS&OOS PF>1.2:", int(((g.oos_pf > 1.2) & (g.is_pf > 1.2)).sum()))
