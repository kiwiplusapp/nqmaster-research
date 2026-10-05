import numpy as np, pandas as pd
from wr60 import build, sim, PV, COMM
B = build(5)
def run(N=5, R=0.5, sk=1.75, ws=630, we=945, fl=955, vw=False):
    al = B["up20"].copy()
    if vw: al &= B["c"] > np.nan_to_num(B["vwap"], nan=1e18)
    out = np.zeros((len(B["c"]) // 3, 3))
    k = sim(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], al, N, R, sk, 0.0, 0, ws, we, fl, 0.0, out)
    df = pd.DataFrame(dict(pts=out[:k, 0], risk=out[:k, 2], date=B["date"][out[:k, 1].astype(np.int64)]))
    return df
def rep(df, label, extra_slip=0.0):
    pts = df.pts - extra_slip - extra_slip * (df.pts < 0)
    u = pts * PV - COMM
    d = pd.DataFrame(dict(date=df.date, u=u))
    daily = d.groupby("date").u.sum(); eq = daily.cumsum(); dd = (eq.cummax() - eq).max()
    w = u[u > 0]; l = u[u <= 0]
    streak = mx = 0
    for x in u:
        streak = streak + 1 if x <= 0 else 0; mx = max(mx, streak)
    print(f"\n== {label}")
    print(f"trades {len(u)}  per week {len(u)/(6.73*52):.2f}  WR {100*(u>0).mean():.1f}%  PF {w.sum()/-l.sum():.2f}  net ${u.sum():,.0f}"
          f"  avg win ${w.mean():.0f}  avg loss ${l.mean():.0f}  maxDD ${dd:,.0f}  worst day ${daily.min():.0f}  max consec losses {mx}"
          f"  median risk {df.risk.median():.0f} pts (${df.risk.median()*2:.0f}/MNQ)")
    y = d.assign(y=d.date // 10000).groupby("y").u
    print(pd.DataFrame(dict(n=y.size(), wr=y.apply(lambda s: round(100*(s>0).mean(),1)), pf=y.apply(lambda s: round(s[s>0].sum()/-s[s<=0].sum(),2)), net=y.sum().round())).T.to_string())
    for lo, hi, nm in ((20240925, 20260125, "IS 2y-split"), (20260126, 20991231, "OOS 2026")):
        s = u[(df.date >= lo) & (df.date <= hi)]
        print(f"{nm}: n {len(s)} WR {100*(s>0).mean():.1f}% PF {s[s>0].sum()/-s[s<=0].sum():.2f} net ${s.sum():,.0f}")
    mo = d.assign(m=d.date // 100).groupby("m").u.sum()
    print(f"months positive {100*(mo>0).mean():.0f}%  worst month ${mo.min():,.0f}  best ${mo.max():,.0f}")
a = run(); a.to_pickle("wr60_A.pkl")
rep(a, "A: up20, 10:30-15:45, N=5, TP 0.5R, stop 1.75x")
rep(a, "A with 2 ticks slippage per side", 0.25)
b = run(N=4, R=0.75, sk=2.5); rep(b, "B: up20, 10:30-15:45, N=4, TP 0.75R, stop 2.5x")
rep(b, "B with 2 ticks slippage", 0.25)
