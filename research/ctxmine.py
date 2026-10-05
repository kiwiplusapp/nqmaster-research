"""Context-filtered clock miner. Base: at clock time t, direction = sign(close[t-1] - ref) (or reverse); bracket stop sk*ATRd,
target R*stop, max hold H, flat 15:55 (tmom.sim with no trend filter). Each trade gets day/time context features, and every
filter combination is scored. Selection must use IS (CFD 2020-23) only; C24 (CFD 2024-26) and REAL (MNQ 2024-26) are checks.
Features (all known before the entry bar):
  tr  : trade dir vs daily trend (SMA20 of RTH closes)         -> +1 with / -1 against
  vw  : trade dir vs side of RTH VWAP at t-1 (RTH times only)  -> +1 / -1 (0 before RTH)
  gp  : trade dir vs RTH gap (RTH open - prior RTH close)      -> +1 / -1 (0 before RTH)
  on  : trade dir vs overnight move (09:29 close - 18:00 open) -> +1 / -1 (RTH times) ; before RTH: vs session move so far
  pb  : pullback day (prior-day move with trend < 0.44 ATR)    -> 1 / 0
  pd  : trade dir vs prior RTH day direction                   -> +1 / -1"""
import sys, itertools, numpy as np, pandas as pd
import tmom
from ict import load, day_levels


def day_feats(D, X):
    L, atr, trend = X
    om, day, o, h, l, c = D["om"], D["dayid"], D["o"], D["h"], D["l"], D["c"]
    v = np.maximum(D["v"], 1e-9)
    df = pd.DataFrame(dict(day=day, om=om, o=o, c=c, pv=(h + l + c) / 3 * v, v=v))
    r = df[(df.om >= 570) & (df.om < 960)]
    g = r.groupby("day").agg(ro=("o", "first"), rc=("c", "last"), rlast=("om", "last"))
    nd = int(day.max()) + 1
    g = g.reindex(range(nd))
    so = df.groupby("day").o.first().reindex(range(nd))
    pre = df[(df.om < 570) | (df.om >= 1080)].groupby("day").c.last().reindex(range(nd))
    pc = g.rc.shift(1)
    full = g.rlast >= 959
    fc = g.rc.where(full)
    prevmove = (fc.shift(1) - fc.shift(2)) / pd.Series(atr) * pd.Series(trend)
    F = pd.DataFrame(dict(ro=g.ro, pc=pc, so=so, onc=pre, trend=trend, atr=atr, pb=(prevmove < 0.44).astype(int), pdd=np.sign(pc - g.rc.shift(2))))
    return F, df


def vwap_at(df, t):
    m = (df.om >= 570) & (df.om < t)
    s = df[m].groupby("day").agg(pv=("pv", "sum"), v=("v", "sum"), c=("c", "last"))
    return np.sign(s.c - s.pv / s.v)


def trades(D, X, F, df, t, L, rev, sk, R, H):
    x = tmom.run(D, X, t, L, rev, sk, R, H, 0)
    if not len(x): return x
    dd = D["dayid"][x.bi]; x["day"] = dd; f = F.loc[dd].reset_index(drop=True)
    d = x.d.to_numpy()
    x["tr"] = np.sign(d * f.trend.to_numpy())
    rth = 570 <= t < 960
    if rth:
        vw = vwap_at(df, t).reindex(dd).to_numpy(); x["vw"] = np.nan_to_num(np.sign(d * vw))
        x["gp"] = np.nan_to_num(np.sign(d * (f.ro - f.pc).to_numpy()))
        x["on"] = np.nan_to_num(np.sign(d * (f.onc - f.so).to_numpy()))
    else:
        x["vw"] = 0; x["gp"] = 0; x["on"] = 0
    x["pb"] = f.pb.to_numpy(); x["pd"] = np.nan_to_num(np.sign(d * f.pdd.to_numpy()))
    return x


def pf(u): return u[u > 0].sum() / -u[u <= 0].sum() if (u <= 0).any() and len(u) >= 30 else np.nan


FILT = list(itertools.product((0, 1, -1), (0, 1, -1), (0, 1, -1), (0, 1, -1), (0, 1, 2), (0, 1, -1)))   # tr vw gp on pb pd
TIMES = [0, 60, 120, 180, 240, 300, 360, 420, 480, 540, 600, 630, 660, 690, 720, 750, 780, 810, 840, 870, 900, 930]
if __name__ == "__main__":
    part, nparts = int(sys.argv[1]), int(sys.argv[2])
    S = {}
    for n in ("nq_1m.npz", "mnq_fut.npz"):
        D = load(n); X = day_levels(D); F, df = day_feats(D, X); S[n] = (D, X, F, df)
    grid = [g for g in itertools.product(TIMES, (-2, -1, 30, 60), (0, 1), (0.15, 0.25), (0.3, 0.6, 1.0), (60, 100000)) if not (g[1] == -2 and not 570 < g[0] < 960)]
    rows = []
    for gi, (t, L, rev, sk, R, H) in enumerate(grid):
        if gi % nparts != part: continue
        T = {}
        for n, (D, X, F, df) in S.items():
            x = trades(D, X, F, df, t, L, rev, sk, R, H)
            if n == "nq_1m.npz":
                T["IS"] = x[(x.date >= 20200201) & (x.date < 20240101)]; T["C24"] = x[x.date >= 20240101]
            else:
                T["REAL"] = x[x.date >= 20240201]
        for ft in FILT:
            if ft[1] or ft[2] or ft[3]:
                if not 570 < t < 960: continue
            r = dict(t=t, L=L, rev=rev, sk=sk, R=R, H=H, tr=ft[0], vw=ft[1], gp=ft[2], on=ft[3], pb=ft[4], pd=ft[5])
            ok = True
            for p, x in T.items():
                m = np.ones(len(x), bool)
                for col, val in zip(("tr", "vw", "gp", "on", "pd"), (ft[0], ft[1], ft[2], ft[3], ft[5])):
                    if val: m &= (x[col].to_numpy() == val)
                if ft[4] == 1: m &= x.pb.to_numpy() == 1
                elif ft[4] == 2: m &= x.pb.to_numpy() == 0
                u = x.usd.to_numpy()[m]
                if p == "IS" and len(u) < 200: ok = False; break
                r[p + "_n"] = len(u); r[p + "_wr"] = round(100 * (u > 0).mean(), 1) if len(u) else np.nan; r[p + "_pf"] = round(pf(u), 3) if len(u) else np.nan
            if ok: rows.append(r)
    pd.DataFrame(rows).to_csv(f"ctx_{part}.csv", index=False); print(part, len(rows), "done")
