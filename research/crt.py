"""Candle Range Theory (CRT) backtest on NQ 1m.
Candle 1 = previous HTF candle (range H1/L1). Candle 2 = the HTF candle that SWEEPS one side (trades beyond H1 or L1)
and CLOSES back inside the candle-1 range. Trade at the open of candle 3 toward the other side:
  bearish CRT: high2 > H1, L1 < close2 < H1  -> SHORT, stop = high2 + 1 tick
  bullish CRT: low2 < L1, L1 < close2 < H1   -> LONG,  stop = low2 - 1 tick
Targets: fixed k*R, or the opposite extreme of candle 1 (classic CRT). Flat by 16:50 ET (end of the Globex day).
Fills: market entry at the next 1m open +1 tick, stop at level/open -1 tick, target needs 1-tick trade-through and
not on the entry bar, stop first. $1 RT per MNQ. Result per 1 MNQ and in R."""
import sys, itertools, os
import numpy as np, pandas as pd
from numba import njit

TICK, SLIP, PV, COMM = 0.25, 0.25, 2.0, 1.0
DATA = os.environ.get("NQ_DATA", "nq_1m.npz")
z = np.load("data/" + DATA)
EP, OM, DATE, DAY = z["epoch"], z["om"].astype(np.int64), z["date"], z["dayid"].astype(np.int64)
O, H, L, C = z["o"], z["h"], z["l"], z["c"]


def daily_trend_atr():
    rth = (OM >= 570) & (OM < 960)
    df = pd.DataFrame(dict(date=DATE[rth], h=H[rth], l=L[rth], c=C[rth]))
    d = df.groupby("date").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    pc = d.c.shift(1)
    tr = np.maximum(d.h - d.l, np.maximum((d.h - pc).abs(), (d.l - pc).abs()))
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean().shift(1)
    sma = d.c.rolling(20).mean().shift(1)
    t = np.sign((pc - sma).fillna(0))
    dates = z["dates"]
    return (pd.Series(atr).reindex(dates).fillna(0).to_numpy(), pd.Series(t).reindex(dates).fillna(0).to_numpy().astype(np.int64))


ATRD, TREND = daily_trend_atr()


def candle_ids(p):
    et_off = ((OM - (EP % 1440)) % 1440)            # ET minus UTC in minutes, mod 1440
    et_ep = EP + np.where(et_off > 720, et_off - 1440, et_off)
    if p == "D":
        return DAY.copy(), OM.copy()
    if p == 240:
        return (et_ep - 18 * 60) // 240, OM.copy()   # 18,22,02,06,10,14 ET
    return et_ep // p, OM.copy()


@njit(cache=True)
def sim(o, h, l, c, om, day, cid, atrd, trend, win_lo, win_hi, bias, tgt_mode, R, min_rng, max_risk, min_close_frac, flat_om, out):
    """win_lo/win_hi: allowed ET minute window for the OPEN time of candle 2 (om of its first bar; wrap if lo>hi).
    bias: 0 none, 1 with daily trend only, -1 against. tgt_mode 0 = fixed R, 1 = opposite extreme of candle 1."""
    n = len(c); k = 0
    h1 = 0.0; l1 = 0.0; have1 = False
    h2 = -1e18; l2 = 1e18; c2 = 0.0; o2m = 0; start2 = 0
    pos = 0; entry = 0.0; sl = 0.0; tp = 0.0; eb = 0; rk = 0.0
    for i in range(n):
        # ---- manage open position on this bar
        if pos != 0:
            done = False; ex = 0.0
            if pos == 1:
                if i > eb and o[i] <= sl:
                    ex = o[i] - SLIP; done = True
                elif l[i] <= sl:
                    ex = sl - SLIP; done = True
                elif i > eb and h[i] >= tp + TICK:
                    ex = max(o[i], tp); done = True
            else:
                if i > eb and o[i] >= sl:
                    ex = o[i] + SLIP; done = True
                elif h[i] >= sl:
                    ex = sl + SLIP; done = True
                elif i > eb and l[i] <= tp - TICK:
                    ex = min(o[i], tp); done = True
            if not done and (day[i] != day[eb] or om[i] == flat_om):
                ex = c[i] - pos * SLIP; done = True
            if done:
                out[k, 0] = pos * (ex - entry); out[k, 1] = eb; out[k, 2] = rk; out[k, 3] = pos; out[k, 4] = i; k += 1
                pos = 0
        # ---- candle bookkeeping
        if i == 0 or cid[i] != cid[i - 1]:
            if i > 0:
                # candle 2 just closed at bar i-1 -> evaluate CRT with candle 1
                if have1 and pos == 0 and day[i] == day[i - 1]:
                    ok_win = (om2_in(o2m, win_lo, win_hi))
                    a = atrd[day[i]]
                    rng1 = h1 - l1
                    if ok_win and a > 0 and rng1 >= min_rng * a and om[i] != flat_om:
                        d = 0
                        if h2 > h1 and c2 < h1 and c2 > l1 and l2 >= l1:
                            if (h1 - c2) >= min_close_frac * rng1:
                                d = -1
                        elif l2 < l1 and c2 > l1 and c2 < h1 and h2 <= h1:
                            if (c2 - l1) >= min_close_frac * rng1:
                                d = 1
                        t = trend[day[i]]
                        if d != 0 and (bias == 0 or (bias == 1 and d == t) or (bias == -1 and d == -t)):
                            e = o[i] + d * SLIP
                            stop = (l2 - TICK) if d == 1 else (h2 + TICK)
                            risk = (e - stop) * d
                            if risk > 0 and risk <= max_risk * a:
                                if tgt_mode == 0:
                                    tgt = e + d * R * risk
                                else:
                                    tgt = h1 if d == 1 else l1
                                if (tgt - e) * d > 0:
                                    pos = d; entry = e; sl = stop; tp = tgt; eb = i; rk = risk
                                    # position opened at bar i open: check this bar for stop immediately
                                    if pos == 1 and l[i] <= sl:
                                        out[k, 0] = (sl - SLIP) - entry; out[k, 1] = eb; out[k, 2] = rk; out[k, 3] = 1; out[k, 4] = i; k += 1; pos = 0
                                    elif pos == -1 and h[i] >= sl:
                                        out[k, 0] = entry - (sl + SLIP); out[k, 1] = eb; out[k, 2] = rk; out[k, 3] = -1; out[k, 4] = i; k += 1; pos = 0
                # shift candle 2 -> candle 1 (only if same trading day stream is continuous)
                h1 = h2; l1 = l2; have1 = start2 >= 0 and h2 > -1e17
            h2 = h[i]; l2 = l[i]; c2 = c[i]; o2m = om[i]; start2 = i
        else:
            if h[i] > h2: h2 = h[i]
            if l[i] < l2: l2 = l[i]
            c2 = c[i]
    return k


@njit(cache=True)
def om2_in(m, lo, hi):
    if lo <= hi:
        return m >= lo and m < hi
    return m >= lo or m < hi


def run(p, win, bias, tgt_mode, R, min_rng, max_risk, min_close_frac=0.0, flat_om=1010):
    cid, _ = candle_ids(p)
    out = np.zeros((len(C) // 20 + 1000, 5))
    k = sim(O, H, L, C, OM, DAY, cid, ATRD, TREND, win[0], win[1], bias, tgt_mode, R, min_rng, max_risk, min_close_frac, flat_om, out)
    o = out[:k]
    df = pd.DataFrame(dict(pts=o[:, 0], risk=o[:, 2], d=o[:, 3], date=DATE[o[:, 1].astype(np.int64)], t_in=OM[o[:, 1].astype(np.int64)]))
    df["usd"] = df.pts * PV - COMM
    df["R"] = (df.pts - COMM / PV) / df.risk
    return df


def st(df, lo, hi):
    s = df[(df.date >= lo) & (df.date <= hi)]
    if len(s) < 15:
        return len(s), np.nan, np.nan, np.nan
    u = s.usd; w = u[u > 0].sum(); l = -u[u <= 0].sum()
    return len(s), round((u > 0).mean() * 100, 1), round(w / l, 3) if l > 0 else 9.9, round(s.R.mean(), 3)


WINDOWS = {"all": (0, 1440), "ny_am": (480, 720), "ny_open": (540, 660), "ny_pm": (720, 960), "london": (120, 420),
           "asia": (1080, 120), "rth": (570, 960)}

if __name__ == "__main__":
    split_is = (20200101, 20231231); split_oos = (20240101, 20991231)
    if len(sys.argv) > 2:
        split_is = (int(sys.argv[2]), int(sys.argv[3])); split_oos = (int(sys.argv[3]) + 1, 20991231)
    P = sys.argv[1]
    p = "D" if P == "D" else int(P)
    rows = []
    for (wn, win), bias, (tm, R), mr, mx, mcf in itertools.product(
            WINDOWS.items(), (0, 1, -1), ((0, 1.0), (0, 1.5), (0, 2.0), (0, 3.0), (1, 0)), (0.0, 0.1, 0.25), (0.1, 0.25, 1.0), (0.0, 0.25)):
        df = run(p, win, bias, tm, R, mr, mx, mcf)
        a = st(df, *split_is); b = st(df, *split_oos)
        rows.append(dict(p=P, win=wn, bias=bias, tgt=("opp" if tm else f"{R}R"), min_rng=mr, max_risk=mx, mcf=mcf,
                         is_n=a[0], is_wr=a[1], is_pf=a[2], is_R=a[3], oos_n=b[0], oos_wr=b[1], oos_pf=b[2], oos_R=b[3]))
    g = pd.DataFrame(rows)
    g.to_csv(f"crt_{P}_{DATA.split('.')[0]}.csv", index=False)
    print(P, len(g), "done")
