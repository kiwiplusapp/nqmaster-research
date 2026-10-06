"""ICT research fill bias: original sim cancels the pending limit when the bar also exceeds the sweep extreme (optimistic);
ict_fix assumes fill-then-stop in that bar (pessimistic). Compare by period and the effect on Ultra (ICT weight x2)."""
import os, sys, numpy as np, pandas as pd
import ict, ict_fix
from news import NEWS
def sm(om): return (np.asarray(om) - 1080) % 1440
rows = []; KEEP = {}
for tag in ("nq_1m.npz", "mnq_fut.npz"):
    D = ict.load(tag); Bi = ict.bars(D, 5); L, atr, trend = ict.day_levels(D)
    for nm, mod in (("original", ict), ("corregido", ict_fix)):
        for R in (0.5, 0.75, 1.0):
            df = mod.run(Bi, L, atr, trend, np.array([1] * 6, np.bool_), (570, 630), 4, 2, R, 1, 0.25); df = df[~df.date.isin(NEWS["FOMC"])]
            KEEP[(tag, nm, R)] = pd.DataFrame(dict(date=df.date, usd=df.usd, tin=sm(Bi["om"][df.bi]), tout=sm(Bi["om"][df.xi]) + 5, d=df.d))
            parts = (("IS", (df.date >= 20200201) & (df.date < 20240101)), ("C24", df.date >= 20240101)) if tag.startswith("nq") else (("REAL", df.date >= 20240201),)
            for lab, m in parts:
                u = df.usd[m]; rows.append(dict(ver=nm, R=R, per=lab, n=int(m.sum()), wr=round(100 * (u > 0).mean(), 1), pf=round(u[u > 0].sum() / -u[u <= 0].sum(), 3), net=round(u.sum())))
R_ = pd.DataFrame(rows); pd.set_option("display.width", 200)
print(R_.pivot_table(index=["R", "ver"], columns="per", values=["n", "wr", "pf"], aggfunc="first").to_string())
pd.to_pickle(KEEP, "mine/ict_fix_trades.pkl")
