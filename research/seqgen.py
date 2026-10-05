"""Generalised momentum-sequence scan, long AND short, several timeframes, to build a higher-frequency portfolio.
Short side = the long logic applied to the negated price series (high <-> -low), so both sides share one engine.
Selection is done on IN-SAMPLE 2020-2023 only; 2024-01 -> 2026-09 is reported untouched as out-of-sample.
Fills: next-bar-open market +1 tick, stop at level/open -1 tick, target needs 1-tick trade-through and never on the
entry bar, stop first. $1 RT per MNQ. P&L per 1 MNQ."""
import sys, itertools
import numpy as np, pandas as pd
from numba import njit

TICK, SLIP, PV, COMM = 0.25, 0.25, 2.0, 1.0
z = np.load("data/nq_1m.npz")
EP, OM, DATE, DAY = z["epoch"], z["om"], z["date"], z["dayid"]
O, H, L, C, V = z["o"], z["h"], z["l"], z["c"], z["v"]


def daily():
    rth = (OM >= 570) & (OM < 960)
    df = pd.DataFrame(dict(date=DATE[rth], o=O[rth], h=H[rth], l=L[rth], c=C[rth]))
    d = df.groupby("date").agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"))
    out = pd.DataFrame(index=d.index)
    out["pc"] = d.c.shift(1)
    for k in (10, 20, 50):
        out[f"sma{k}"] = d.c.rolling(k).mean().shift(1)
    out["rth_open"] = d.o
    return out


def build(tf):
    g = EP // tf
    df = pd.DataFrame(dict(g=g, o=O, h=H, l=L, c=C, om=OM, date=DATE, day=DAY))
    a = df.groupby(["day", "g"], sort=True).agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"),
                                                  om=("om", "first"), date=("date", "first")).reset_index()
    di = daily()
    B = dict(o=a.o.to_numpy(), h=a.h.to_numpy(), l=a.l.to_numpy(), c=a.c.to_numpy(), om=a.om.to_numpy().astype(np.int64),
             date=a.date.to_numpy(), day=a.day.to_numpy().astype(np.int64))
    pc = a.date.map(di.pc).to_numpy()
    for k in (10, 20, 50):
        s = a.date.map(di[f"sma{k}"]).to_numpy()
        B[f"up{k}"] = np.nan_to_num(pc - s, nan=0.0) > 0
        B[f"dn{k}"] = np.nan_to_num(pc - s, nan=0.0) < 0
    ro = a.date.map(di.rth_open).to_numpy()
    rth = (B["om"] >= 570) & (B["om"] < 960)
    B["above_open"] = rth & (B["c"] > np.nan_to_num(ro, nan=1e18))
    B["below_open"] = rth & (B["c"] < np.nan_to_num(ro, nan=-1e18))
    B["all"] = np.ones(len(B["c"]), bool)
    return B


@njit(cache=True)
def sim(o, h, l, c, om, day, allow, N, need_main, R, stop_k, win_s, win_e, flat, out):
    n = len(c); pos = 0; k = 0; entry = 0.0; sl = 0.0; tp = 0.0; eb = 0; pend = False; psl = 0.0; risk = 0.0
    for i in range(N + 1, n):
        if pend:
            pend = False
            if day[i] == day[i - 1] and om[i] < flat:
                entry = o[i] + SLIP; risk = entry - psl
                if risk > 0:
                    pos = 1; sl = psl; tp = entry + R * risk; eb = i
        if pos == 1:
            ex = 0.0; done = False
            if o[i] <= sl and i > eb:
                ex = o[i] - SLIP; done = True
            elif l[i] <= sl:
                ex = sl - SLIP; done = True
            elif i > eb and h[i] >= tp + TICK:
                ex = max(o[i], tp); done = True
            elif day[i] != day[eb] or om[i] >= flat:
                ex = c[i] - SLIP; done = True
            if done:
                out[k, 0] = ex - entry; out[k, 1] = eb; out[k, 2] = risk; k += 1; pos = 0
        if pos == 0 and not pend and allow[i] and om[i] >= win_s and om[i] < win_e:
            m = i - N
            if day[m] != day[i]:
                continue
            if need_main and not (c[m] < o[m]):
                continue
            ok = True
            for j in range(N):
                b = i - j
                if c[b] <= o[b] or l[b] <= l[m]:
                    ok = False; break
                if j < N - 1 and c[b] <= c[b - 1]:
                    ok = False; break
            if ok:
                dist = (c[i] - l[m]) * stop_k
                if dist > 0:
                    pend = True; psl = c[i] - dist
    return k


def run(B, d, filt, intra, N, need_main, R, sk, ws, we, fl=955):
    if d == 1:
        o, h, l, c = B["o"], B["h"], B["l"], B["c"]
        allow = B[filt.replace("X", "up")] if filt != "all" else B["all"]
        if intra: allow = allow & B["above_open"]
    else:
        o, h, l, c = -B["o"], -B["l"], -B["h"], -B["c"]
        allow = B[filt.replace("X", "dn")] if filt != "all" else B["all"]
        if intra: allow = allow & B["below_open"]
    out = np.zeros((len(c) // 3, 3))
    k = sim(o, h, l, c, B["om"], B["day"], allow, N, need_main, R, sk, ws, we, fl, out)
    return out[:k, 0], B["date"][out[:k, 1].astype(np.int64)], out[:k, 1].astype(np.int64)


def st(pts, dates, lo, hi):
    m = (dates >= lo) & (dates <= hi); u = pts[m] * PV - COMM
    if len(u) < 10:
        return len(u), np.nan, np.nan, 0.0
    w = u[u > 0].sum(); l = -u[u <= 0].sum()
    return len(u), (u > 0).mean() * 100, (w / l if l > 0 else 9.9), u.sum()


if __name__ == "__main__":
    tf = int(sys.argv[1])
    B = build(tf)
    wins = {"rth": (570, 945), "1000": (600, 945), "1030": (630, 945), "am": (570, 720)}
    rows = []
    for d, filt, intra, (wn, (ws, we)), N, nm, R, sk in itertools.product(
            (1, -1), ("all", "X10", "X20", "X50"), (False, True), wins.items(), (3, 4, 5, 6), (True, False),
            (0.4, 0.5, 0.6, 0.75), (1.5, 2.0, 2.5, 3.0)):
        pts, dates, _ = run(B, d, filt, intra, N, nm, R, sk, ws, we)
        r = dict(tf=tf, d=d, filt=filt, intra=intra, win=wn, N=N, main=nm, R=R, sk=sk)
        for nmp, lo, hi in (("is", 20200101, 20231231), ("oos", 20240101, 20991231)):
            n, wr, pf, net = st(pts, dates, lo, hi)
            r[f"{nmp}_n"] = n; r[f"{nmp}_wr"] = wr; r[f"{nmp}_pf"] = pf; r[f"{nmp}_net"] = net
        yp = [st(pts, dates, y * 10000 + 101, y * 10000 + 1231)[2] for y in range(2020, 2024)]
        r["is_minyr"] = np.nanmin(yp) if not all(np.isnan(yp)) else np.nan
        rows.append(r)
    g = pd.DataFrame(rows)
    g.to_csv(f"seqgen_tf{tf}.csv", index=False)
    print(tf, len(g), "done")
