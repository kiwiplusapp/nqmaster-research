"""High-WR intraday families on 5m signals, executed on 1m bars (for more trades/day without lowering WR).
Families: RSI2 pullback, EMA20 pullback, VWAP touch, new-HOD/LOD continuation. Direction filter: daily trend (SMA20),
intraday trend (price vs RTH open & VWAP), or both. Bracket: stop sk*ATRd, target R*stop, max hold H min, flat 15:55,
up to K trades/day, one at a time. Costs: 1 tick slip entry/stop, target needs 1-tick trade-through, $1 RT.
Selection on CFD 2020-23 only; CFD 2024-26 and REAL MNQ 2024-26 are checks."""
import sys, itertools, numpy as np, pandas as pd
from numba import njit
from ict import load, day_levels
TICK, SLIP = 0.25, 0.25


@njit(cache=True)
def execute(o, h, l, c, om, day, atr, sig, sk, R, H, K, ws, we, out):
    n = len(c); k = 0; pos = 0; e = 0.0; sl = 0.0; tp = 0.0; eb = 0; cur = -1; ntd = 0
    for i in range(1, n):
        if day[i] != cur: cur = day[i]; ntd = 0
        if pos != 0:
            ex = np.nan
            if pos == 1:
                if l[i] <= sl: ex = min(o[i], sl) - SLIP
                elif h[i] >= tp + TICK: ex = max(o[i], tp)
            else:
                if h[i] >= sl: ex = max(o[i], sl) + SLIP
                elif l[i] <= tp - TICK: ex = min(o[i], tp)
            if np.isnan(ex) and (i - eb >= H or om[i] >= 955 or day[i + 1 if i + 1 < n else i] != day[i]):
                ex = c[i] - pos * SLIP
            if not np.isnan(ex):
                out[k, 0] = pos * (ex - e); out[k, 1] = eb; out[k, 2] = pos; out[k, 3] = i; k += 1; pos = 0
            continue
        s = sig[i]
        if s == 0 or ntd >= K or om[i] < ws or om[i] >= we: continue
        a = atr[day[i]]
        if a <= 0: continue
        pos = s; e = o[i] + s * SLIP; rk = sk * a; sl = e - s * rk; tp = e + s * R * rk; eb = i; ntd += 1
        # same-bar stop check (stop first)
        if (s == 1 and l[i] <= sl) or (s == -1 and h[i] >= sl):
            out[k, 0] = -rk - SLIP; out[k, 1] = eb; out[k, 2] = s; out[k, 3] = i; k += 1; pos = 0
    return k


def prep(D):
    L, atr, trend = day_levels(D)
    n = len(D["c"]); idx = np.arange(n)
    df = pd.DataFrame(dict(o=D["o"], h=D["h"], l=D["l"], c=D["c"], v=np.maximum(D["v"], 1e-9) if "v" in D else 1.0, om=D["om"], day=D["dayid"], g=D["epoch"] // 5, i=idx))
    rth = (df.om >= 570) & (df.om < 960)
    tp = (df.h + df.l + df.c) / 3
    df["pv"] = np.where(rth, tp * df.v, 0.0); df["vv"] = np.where(rth, df.v, 0.0)
    df["vwap"] = df.groupby("day").pv.cumsum() / df.groupby("day").vv.cumsum().replace(0, np.nan)
    ro = df[rth].groupby("day").o.first(); df["ropen"] = df.day.map(ro)
    B = df.groupby(["day", "g"], sort=True).agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"), om=("om", "first"),
                                                last=("i", "last"), vwap=("vwap", "last"), ropen=("ropen", "first")).reset_index()
    B["nxt"] = B["last"] + 1
    B["trend"] = trend[B.day.to_numpy()]
    B["atr"] = atr[B.day.to_numpy()]
    d = B.c.diff(); up = d.clip(lower=0); dn = (-d).clip(lower=0)
    rs = up.ewm(alpha=0.5, adjust=False).mean() / dn.ewm(alpha=0.5, adjust=False).mean().replace(0, np.nan)
    B["rsi2"] = (100 - 100 / (1 + rs)).fillna(50)
    B["e20"] = B.c.ewm(span=20, adjust=False).mean(); B["e50"] = B.c.ewm(span=50, adjust=False).mean()
    B["hod"] = B[B.om >= 570].groupby("day").h.cummax(); B["lod"] = B[B.om >= 570].groupby("day").l.cummin()
    B["phod"] = B.groupby("day").hod.shift(1); B["plod"] = B.groupby("day").lod.shift(1)
    B["dist"] = ((B.c - B.vwap) / B.atr)
    B["mx"] = B.groupby("day").dist.cummax(); B["mn"] = B.groupby("day").dist.cummin()
    return D, atr, B


def signals(B, fam, p, dm):
    it = np.sign(B.c - B.ropen) * (np.sign(B.c - B.vwap) == np.sign(B.c - B.ropen))
    if dm == 0: dirn = B.trend
    elif dm == 1: dirn = it
    else: dirn = B.trend.where(B.trend == it, 0)
    if fam == "RSI2":
        lng = B.rsi2 < p; sht = B.rsi2 > 100 - p
    elif fam == "EMA":
        lng = (B.e20 > B.e50) & (B.l <= B.e20) & (B.c > B.e20) & (B.c > B.o)
        sht = (B.e20 < B.e50) & (B.h >= B.e20) & (B.c < B.e20) & (B.c < B.o)
    elif fam == "VWT":
        lng = (B.mx.shift(1) >= p) & (B.l <= B.vwap) & (B.c > B.vwap); sht = (B.mn.shift(1) <= -p) & (B.h >= B.vwap) & (B.c < B.vwap)
    elif fam == "HOD":
        lng = (B.c > B.phod) & (B.c > B.o); sht = (B.c < B.plod) & (B.c < B.o)
    s = np.where(lng & (dirn == 1), 1, np.where(sht & (dirn == -1), -1, 0))
    return s


def run(D, atr, B, fam, p, dm, sk, R, H, K, ws, we):
    s = signals(B, fam, p, dm)
    sig = np.zeros(len(D["c"]) + 1, np.int64)
    m = (s != 0) & (B.nxt.to_numpy() < len(D["c"]))
    sig[B.nxt.to_numpy()[m]] = s[m]
    out = np.zeros((40000, 4))
    k = execute(D["o"], D["h"], D["l"], D["c"], D["om"].astype(np.int64), D["dayid"].astype(np.int64), atr, sig, sk, R, H, K, ws, we, out)
    ei = out[:k, 1].astype(np.int64)
    return pd.DataFrame(dict(date=D["date"][ei], usd=out[:k, 0] * 2 - 1, d=out[:k, 2], tin=D["om"][ei], xi=out[:k, 3].astype(np.int64)))


def pf(u): return u[u > 0].sum() / -u[u <= 0].sum() if (u <= 0).any() and len(u) > 20 else np.nan


FAMS = [("RSI2", 5), ("RSI2", 10), ("RSI2", 20), ("EMA", 0), ("VWT", 0.3), ("VWT", 0.6), ("HOD", 0)]
if __name__ == "__main__":
    S = {n: prep(load(n)) for n in ("nq_1m.npz", "mnq_fut.npz")}
    rows = []
    for (fam, p), dm, sk, R, H, K, (ws, we) in itertools.product(FAMS, (0, 1, 2), (0.1, 0.15, 0.2), (0.3, 0.5), (30, 120), (1, 2, 3), ((600, 900), (630, 945))):
        r = dict(fam=fam, p=p, dm=dm, sk=sk, R=R, H=H, K=K, win=f"{ws}-{we}")
        for n, (D, atr, B) in S.items():
            df = run(D, atr, B, fam, p, dm, sk, R, H, K, ws, we)
            parts = [("IS", df[(df.date >= 20200201) & (df.date < 20240101)]), ("C24", df[df.date >= 20240101])] if n == "nq_1m.npz" else [("REAL", df[df.date >= 20240201])]
            for lab, x in parts:
                r[lab + "_n"] = len(x); r[lab + "_wr"] = round(100 * (x.usd > 0).mean(), 1) if len(x) else np.nan; r[lab + "_pf"] = round(pf(x.usd), 3)
        rows.append(r)
    g = pd.DataFrame(rows); g.to_csv("intra_map.csv", index=False)
    h = g[(g.IS_wr >= 68) & (g.IS_n >= 400)].sort_values("IS_pf", ascending=False)
    print(h.head(40).to_string(index=False))
    print(g.groupby("fam")[["IS_pf", "C24_pf", "REAL_pf", "IS_wr"]].median().round(3).to_string())
