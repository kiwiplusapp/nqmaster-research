"""Gold intraday drift by ET clock hour (open of hour -> open of next hour), in daily-ATR units, per period.
Also session blocks: Asia 18:00-03:00, London 03:00-08:20, COMEX AM 08:20-10:00, NY 10:00-13:30, late 13:30-16:55."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
from core import Data, S
def hourly(D, lo, hi):
    df = pd.DataFrame(dict(day=D.day, date=D.date, sm=D.sm, o=D.o, c=D.c))
    df = df[(df.date >= lo) & (df.date < hi)]
    df["atr"] = D.atr[df.day.to_numpy()]
    df = df[df.atr > 0]
    df["blk"] = df.sm // 60
    g = df.groupby(["day", "blk"]).agg(o=("o", "first"), c=("c", "last"), atr=("atr", "first"))
    g["r"] = (g.c - g.o) / g.atr
    t = g.groupby("blk").r.agg(["mean", "std", "size"])
    t["t"] = t["mean"] / t["std"] * np.sqrt(t["size"]); t["pos"] = g.groupby("blk").r.apply(lambda x: (x > 0).mean())
    t.index = [f"{(18 + b) % 24:02d}:00" for b in t.index]
    return t
def blocks(D, lo, hi):
    BL = {"Asia 18-03": (S(1800), S(300)), "Londres 03-08:20": (S(300), S(820)), "COMEX 08:20-10": (S(820), S(1000)), "NY 10-13:30": (S(1000), S(1330)), "Tarde 13:30-16:55": (S(1330), S(1655))}
    df = pd.DataFrame(dict(day=D.day, date=D.date, sm=D.sm, o=D.o, c=D.c)); df = df[(df.date >= lo) & (df.date < hi)]
    out = {}
    for nm, (a, b) in BL.items():
        x = df[(df.sm >= a) & (df.sm < b)].groupby("day").agg(o=("o", "first"), c=("c", "last"))
        A = D.atr[x.index.to_numpy()]; r = (x.c - x.o).to_numpy() / np.where(A > 0, A, np.nan)
        r = r[np.isfinite(r)]
        out[nm] = dict(mean=round(r.mean(), 4), t=round(r.mean() / r.std() * np.sqrt(len(r)), 2), pos=round((r > 0).mean(), 3), n=len(r))
    return pd.DataFrame(out).T
X = Data("xau_hd.npz"); M = Data("mgc_fut.npz")
P = [("IS 2020-23", X, 20200201, 20240101), ("C24 2024-26", X, 20240101, 30000000), ("REAL MGC", M, 20240201, 30000000)]
pd.set_option("display.width", 250)
H = pd.concat({nm: hourly(D, lo, hi)[["mean", "t", "pos"]] for nm, D, lo, hi in P}, axis=1).round(3)
print(H.to_string())
for nm, D, lo, hi in P: print("\n", nm); print(blocks(D, lo, hi).to_string())
print("cost per round trip in ATR units (MGC: $3.90 / ($4 x ATR)): IS %.4f  C24 %.4f  REAL %.4f" % tuple(3.9 / (4 * np.nanmedian(D.atr[D.atr > 0][(D.daydate[D.atr > 0] >= lo) & (D.daydate[D.atr > 0] < hi)])) for _, D, lo, hi in P))
