import numpy as np, pandas as pd, tmom, intra
from ict import load, day_levels
from news import NEWS
exec(open("conflict.py").read().split("for tag, lo, split")[0])
def sm(om): return (np.asarray(om) - 1080) % 1440
def vwap_side(d, t):
    om, h, l, c, v, o = d["om"], d["h"], d["l"], d["c"], np.maximum(d["v"], 1e-9), d["o"]
    m = (om >= 570) & (om < t)
    df = pd.DataFrame(dict(date=d["date"][m], tp=((h + l + c) / 3 * v)[m], v=v[m], o=o[m], c=c[m]))
    g = df.groupby("date").agg(tp=("tp", "sum"), v=("v", "sum"), o=("o", "first"), c=("c", "last"))
    return np.sign(g.c - g.tp / g.v) == np.sign(g.c - g.o)
res = []
for tag, lo, split in (("nq_1m", 20200201, 20240101), ("mnq_fut", 20240201, None)):
    D = load(tag + ".npz"); X = day_levels(D); S = intra.prep(D)
    V = pd.read_pickle(f"variants_{tag}.pkl"); V = V[V["mod"] != "GOLD"]
    new = []
    df = tmom.run(D, X, 690, -2, 0, 0.25, 0.3, 100000, 0); df = df[df.date.map(vwap_side(D, 690)) == True]
    new.append(pd.DataFrame(dict(date=df.date, mod="MOM1130", var=0.3, usd=df.usd, tin=sm(690), tout=sm(D["om"][df.xi]) + 1, d=df.d)))
    for sk in (0.15, 0.2):
        df = intra.run(D, S[1], S[2], "RSI2", 10, 2, sk, 0.3, 120, 3, 630, 945)
        new.append(pd.DataFrame(dict(date=df.date, mod=f"RSI2_{sk}", var=0.3, usd=df.usd, tin=sm(df.tin), tout=sm(D["om"][df.xi]) + 1, d=df.d)))
    V = pd.concat([V] + new, ignore_index=True); V["fomc"] = V.date.isin(NEWS["FOMC"]); V = V[(V.date >= lo) & ~V.fomc]
    base = {k: v for k, v in PROFILES["MAX_SHARPE"].items() if k != "GOLD"}
    combos = {"BASE": base, "+MOM1130": {**base, "MOM1130": 0.3}, "+RSI2_.15": {**base, "RSI2_0.15": 0.3}, "+RSI2_.20": {**base, "RSI2_0.2": 0.3},
              "+MOM1130+RSI2_.15": {**base, "MOM1130": 0.3, "RSI2_0.15": 0.3}}
    for cn, prof in combos.items():
        F = conflict_filter(pick(V, prof).reset_index(drop=True))
        parts = [("IS", F[F.date < split]), ("C24", F[F.date >= split])] if split else [("REAL", F)]
        for lab, x in parts:
            days = np.array(sorted(V[(V.date < split) if lab == "IS" else (V.date >= (split or 0))].date.unique()))
            s = stats(x, days); res.append(dict(combo=cn, per=lab, sharpe=round(s[0], 2), wr=round(s[1], 1), pf=round(s[2], 3), tpd=round(s[3], 2), usd_month=round(s[4] / len(days) * 21)))
r = pd.DataFrame(res); print(r.pivot(index="combo", columns="per", values=["tpd", "wr", "pf", "sharpe", "usd_month"]).to_string())
