import numpy as np, pandas as pd
def vwap_side(d, t):
    om, day, h, l, c, v, o = d["om"], d["dayid"], d["h"], d["l"], d["c"], np.maximum(d["v"], 1e-9), d["o"]
    m = (om >= 570) & (om < t)
    df = pd.DataFrame(dict(date=d["date"][m], tp=((h + l + c) / 3 * v)[m], v=v[m], o=o[m], c=c[m]))
    g = df.groupby("date").agg(tp=("tp", "sum"), v=("v", "sum"), o=("o", "first"), c=("c", "last"))
    g["agree"] = np.sign(g.c - g.tp / g.v) == np.sign(g.c - g.o)
    return g.agree
