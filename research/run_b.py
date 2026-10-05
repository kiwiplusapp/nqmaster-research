import pickle, numpy as np, pandas as pd
from life25b import lifecycle
MP = pickle.load(open("minute_paths.pkl", "rb"))
E = dict(k1=4)
PAS = {"B=0 (actual)": dict(k1=1), "B=500": dict(k1=1, B=500.0), "B=1000": dict(k1=1, B=1000.0), "B=1500": dict(k1=1, B=1500.0),
       "B=1000 + 2 contr si colchon>=$2500": dict(mode=4, k1=1, k2=2, C=2500, B=1000.0), "B=1500 + 2 contr si colchon>=$3000": dict(mode=4, k1=1, k2=2, C=3000, B=1500.0)}
rows = []
for per in ("REAL", "C24", "IS"):
    for pn, p in PAS.items():
        r = lifecycle(MP[per]["ALL"], E, p); r.update(per=per, pa=pn); rows.append(r)
g = pd.DataFrame(rows)
for c in ("net_mo", "p10_mo", "payouts_yr", "PA_busts_yr", "evals_yr"):
    print(c); print(g.pivot(index="pa", columns="per", values=c).reindex(list(PAS)).to_string())
