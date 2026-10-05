"""CRT deep-dive on hourly candles with limit-entry refinements. entry_mode 0 = market at candle-3 open,
1 = limit at the swept level (H1 short / L1 long), 2 = limit at 50% of candle-2 wick beyond candle 1.
Limit valid until candle 3 ends; fill needs a 1-tick trade-through. Stop beyond the candle-2 extreme, target k*R."""
import sys, itertools
import numpy as np, pandas as pd
from numba import njit
from crt import O, H, L, C, OM, DAY, DATE, ATRD, TREND, candle_ids, TICK, SLIP, PV, COMM, st

@njit(cache=True)
def sim(o, h, l, c, om, day, cid, atrd, trend, c2_hours_mask, bias, R, min_rng, max_risk, mcf, emode, flat_om, out):
    n = len(c); k = 0
    h1 = 0.0; l1 = 0.0; have1 = False; h2 = -1e18; l2 = 1e18; c2 = 0.0; o2m = 0
    pos = 0; entry = 0.0; sl = 0.0; tp = 0.0; eb = 0; rk = 0.0
    pend = 0; plim = 0.0; psl = 0.0; pexp = -1
    for i in range(n):
        newc = i == 0 or cid[i] != cid[i - 1]
        # pending limit order
        if pend != 0 and pos == 0:
            if cid[i] != pexp or day[i] != day[eb]:
                pend = 0
            else:
                if (pend == -1 and h[i] >= plim + TICK) or (pend == 1 and l[i] <= plim - TICK):
                    fill = max(plim, o[i]) if pend == -1 else min(plim, o[i])
                    pos = pend; entry = fill; sl = psl; rk = (sl - entry) * (-pos); tp = entry + pos * R * rk; eb = i; pend = 0
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
            if not done and (day[i] != day[eb] or om[i] == flat_om):
                ex = c[i] - pos * SLIP; done = True
            if done:
                out[k, 0] = pos * (ex - entry); out[k, 1] = eb; out[k, 2] = rk; out[k, 3] = pos; out[k, 4] = i; k += 1; pos = 0
        if newc:
            if i > 0 and have1 and pos == 0 and pend == 0 and day[i] == day[i - 1] and om[i] != flat_om:
                hr = (o2m // 60) % 24
                a = atrd[day[i]]; rng1 = h1 - l1
                if c2_hours_mask[hr] and a > 0 and rng1 >= min_rng * a:
                    d = 0
                    if h2 > h1 and c2 < h1 and c2 > l1 and l2 >= l1 and (h1 - c2) >= mcf * rng1: d = -1
                    elif l2 < l1 and c2 > l1 and c2 < h1 and h2 <= h1 and (c2 - l1) >= mcf * rng1: d = 1
                    t = trend[day[i]]
                    if d != 0 and (bias == 0 or (bias == 1 and d == t) or (bias == -1 and d == -t)):
                        stop = (l2 - TICK) if d == 1 else (h2 + TICK)
                        if emode == 0:
                            e = o[i] + d * SLIP; risk = (e - stop) * d
                            if risk > 0 and risk <= max_risk * a:
                                pos = d; entry = e; sl = stop; rk = risk; tp = e + d * R * risk; eb = i
                                if (pos == 1 and l[i] <= sl) or (pos == -1 and h[i] >= sl):
                                    out[k, 0] = -rk - SLIP; out[k, 1] = eb; out[k, 2] = rk; out[k, 3] = pos; out[k, 4] = i; k += 1; pos = 0
                        else:
                            if d == -1:
                                lim = h1 if emode == 1 else (max(h1, c2) + h2) / 2.0
                            else:
                                lim = l1 if emode == 1 else (min(l1, c2) + l2) / 2.0
                            risk = (lim - stop) * d
                            if risk > 0 and risk <= max_risk * a:
                                pend = d; plim = lim; psl = stop; pexp = cid[i]; eb = i
            h1 = h2; l1 = l2; have1 = h2 > -1e17
            h2 = h[i]; l2 = l[i]; c2 = c[i]; o2m = om[i]
        else:
            if h[i] > h2: h2 = h[i]
            if l[i] < l2: l2 = l[i]
            c2 = c[i]
    return k

def run(p, hours, bias, R, min_rng, max_risk, mcf, emode, flat_om=1010):
    cid, _ = candle_ids(p)
    mask = np.zeros(24, np.bool_); mask[list(hours)] = True
    out = np.zeros((len(C) // 20 + 1000, 5))
    k = sim(O, H, L, C, OM, DAY, cid, ATRD, TREND, mask, bias, R, min_rng, max_risk, mcf, emode, flat_om, out)
    o = out[:k]
    df = pd.DataFrame(dict(pts=o[:, 0], risk=o[:, 2], d=o[:, 3], date=DATE[o[:, 1].astype(np.int64)], xi=o[:, 4].astype(np.int64)))
    df["usd"] = df.pts * PV - COMM; df["R"] = (df.pts - COMM / PV) / df.risk
    return df

if __name__ == "__main__":
    rows = []
    HOURS = {"8-11": (8, 9, 10, 11), "8": (8,), "9": (9,), "10": (10,), "11": (11,), "9-10": (9, 10), "2-5": (2, 3, 4, 5), "12-15": (12, 13, 14, 15)}
    for p in (60, 30):
        for (hn, hrs), bias, R, mr, mx, mcf, em in itertools.product(HOURS.items(), (0, 1), (1.5, 2.0, 2.5, 3.0), (0.0, 0.1), (0.15, 0.25, 0.5), (0.0, 0.25), (0, 1, 2)):
            df = run(p, hrs, bias, R, mr, mx, mcf, em)
            a = st(df, 20200101, 20231231); b = st(df, 20240101, 20991231)
            yp = [st(df, y * 10000 + 101, y * 10000 + 1231)[2] for y in range(2020, 2027)]
            rows.append(dict(p=p, hours=hn, bias=bias, R=R, min_rng=mr, max_risk=mx, mcf=mcf, emode=em, is_n=a[0], is_wr=a[1], is_pf=a[2],
                             oos_n=b[0], oos_wr=b[1], oos_pf=b[2], minyr=np.nanmin(yp) if not np.all(np.isnan(yp)) else np.nan, yrs=" ".join(f"{x:.2f}" for x in yp)))
        print(p, "done"); sys.stdout.flush()
    g = pd.DataFrame(rows); g.to_csv("crt2.csv", index=False)
    s = g[(g.is_n >= 80) & (g.is_pf >= 1.3)]
    print("IS-selected", len(s), "of", len(g), "| OOS PF median %.2f, share OOS>=1.3: %.2f" % (s.oos_pf.median(), (s.oos_pf >= 1.3).mean()))
    print(s.sort_values("is_pf", ascending=False).head(30).to_string(index=False))
