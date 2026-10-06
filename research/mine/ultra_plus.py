"""More trades per day without lowering WR / PF: marginal test of extra modules on Ultra (corrected ICT x2), conflict filter.
Extras: ENG0610 NQ (ENGULF_4H 1172), LATE15 (LATE_MOM 762, already in NQMaster), LATE_FH (LATE_MOM 1107), LATE759 (LATE_MOM 759),
VW13b (WR70Plus VW13 at 0.15 ATR with x2 at 0.30, replacing VW13), gold WinRate / Robust (GoldMaster)."""
import os, sys, pickle, itertools, numpy as np, pandas as pd
sys.path.insert(0, ".")
from gold_port import conflict_filter
from ict_redo import ictf, metrics
T = pickle.load(open("robust_trades.pkl", "rb")); GC = pickle.load(open("gold_curated_trades.pkl", "rb"))
TR = {}
for f in ("trades_b3.pkl", "trades_b4.pkl"): TR.update(pickle.load(open(f, "rb")))
def mined(key, per, name):
    df = TR[key]["mnq" if per == "REAL" else "nq"]
    lo, hi = (20240201, 3e7) if per == "REAL" else ((20200201, 20240101) if per == "IS" else (20240101, 3e7))
    from news import NEWS
    df = df[(df.date >= lo) & (df.date < hi) & ~df.date.isin(NEWS["FOMC"])]
    return pd.DataFrame(dict(date=df.date.to_numpy(), mod=name, tin=df.tin.to_numpy(), tout=df.tout.to_numpy(), d=df.d.to_numpy(), u=df.usd.to_numpy(), w=1.0))
EXTRA = {"ENG0610nq": ("ENGULF_4H", 1172), "LATE15": ("LATE_MOM", 762), "LATE_FH": ("LATE_MOM", 1107), "LATE759": ("LATE_MOM", 759)}
rows = []
for per in ("IS", "C24", "REAL"):
    F, days = T["Ultra"][per]; base = pd.concat([F[F["mod"] != "ICT"][["date", "mod", "tin", "tout", "d", "u", "w"]], ictf(per, 2.0)], ignore_index=True)
    W = T["WR70Plus"][per][0]; vw13b = W[W["mod"] == "VW13b"][["date", "mod", "tin", "tout", "d", "u", "w"]]
    ex = {k: mined(v, per, k) for k, v in EXTRA.items()}
    gw = pd.concat([GC[m][per] for m in ("OD1030", "ENG0408", "SVWAP22")]).assign(mod="GOLD"); gr = pd.concat([GC[m][per] for m in ("OD1030", "ENG0408", "SVWAP22", "ASIA1R", "ENG0206")]).assign(mod="GOLD")
    combos = {"Ultra": [], "+VW13b (en vez de VW13)": ["vw13b"], "+LATE15": ["LATE15"], "+ENG0610nq": ["ENG0610nq"], "+LATE_FH": ["LATE_FH"],
              "+LATE15 +ENG0610nq": ["LATE15", "ENG0610nq"], "+LATE15 +ENG0610nq +VW13b": ["LATE15", "ENG0610nq", "vw13b"],
              "+LATE15 +ENG0610nq +VW13b +LATE_FH": ["LATE15", "ENG0610nq", "vw13b", "LATE_FH"],
              "+oro WinRate": ["gw"], "+oro Robust": ["gr"], "+LATE15 +ENG0610nq +VW13b +oro Robust": ["LATE15", "ENG0610nq", "vw13b", "gr"]}
    for nm, add in combos.items():
        b = base[base["mod"] != "VW13"] if "vw13b" in add else base
        parts = [b] + [vw13b if a == "vw13b" else (gw if a == "gw" else (gr if a == "gr" else ex[a])) for a in add]
        nq = conflict_filter(pd.concat([p for p in parts if not (p["mod"] == "GOLD").all()], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True))
        gold = [p for p in parts if (p["mod"] == "GOLD").all()]
        X = pd.concat([nq] + gold, ignore_index=True)
        rows.append(dict(per=per, set=nm, **metrics(X, days)))
M = pd.DataFrame(rows); pd.set_option("display.width", 250); pd.set_option("display.max_rows", 100)
print(M.pivot_table(index="set", columns="per", values=["tpd", "wr", "pf", "sharpe", "mo"], aggfunc="first").to_string())
M.to_csv("ultra_plus.csv", index=False)
