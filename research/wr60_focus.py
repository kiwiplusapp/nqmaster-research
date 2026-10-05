import numpy as np, pandas as pd, itertools
from wr60 import build, sim, PV, COMM
B = build(5)
filt = {"up20": B["up20"], "up20_vwap": B["up20"] & (B["c"] > np.nan_to_num(B["vwap"], nan=1e18))}
sess = {"rth": (570, 945, 955), "rth_1030": (630, 945, 955), "to14": (570, 840, 955)}
def trades(allow, N, R, sk, ws, we, fl):
    out = np.zeros((len(B["c"]) // 3, 3))
    k = sim(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], allow, N, R, sk, 0.0, 0, ws, we, fl, 0.0, out)
    df = pd.DataFrame(dict(pts=out[:k, 0], risk=out[:k, 2], date=B["date"][out[:k, 1].astype(np.int64)]))
    df["usd"] = df.pts * PV - COMM
    return df
def m(df):
    if len(df) < 15: return dict(n=len(df), wr=np.nan, pf=np.nan)
    u = df.usd; w = u[u > 0].sum(); l = -u[u <= 0].sum()
    return dict(n=len(u), wr=round((u > 0).mean()*100, 1), pf=round(w/l, 2), net=round(u.sum()))
rows = []
for (fn, al), (sn, (ws, we, fl)), N, R, sk in itertools.product(filt.items(), sess.items(), (4, 5, 6), (0.5, 0.6, 0.75), (1.75, 2.0, 2.5, 3.0)):
    df = trades(al, N, R, sk, ws, we, fl)
    f = m(df); a = m(df[df.date < 20240101]); b = m(df[df.date >= 20240101]); c2 = m(df[(df.date >= 20240925) & (df.date <= 20260125)]); d2 = m(df[df.date >= 20260126])
    yp = [m(df[(df.date >= y*10000) & (df.date < (y+1)*10000)])["pf"] for y in range(2020, 2027)]
    rows.append(dict(filt=fn, sess=sn, N=N, R=R, sk=sk, n=f["n"], wr=f["wr"], pf=f["pf"], net=f.get("net"),
                     is_pf=a["pf"], is_wr=a["wr"], oos_pf=b["pf"], oos_wr=b["wr"], p2is=c2["pf"], p2oos=d2["pf"], p2oos_wr=d2["wr"],
                     risk_pts=round(df.risk.median(), 1), yrs=" ".join(f"{x:.2f}" for x in yp), minyr=np.nanmin(yp)))
g = pd.DataFrame(rows); g.to_csv("wr60_focus.csv", index=False)
ok = g[(g.wr >= 60) & (g.is_wr >= 58) & (g.oos_wr >= 58) & (g.pf >= 1.3)]
print(ok.sort_values("minyr", ascending=False).head(30).to_string(index=False))
