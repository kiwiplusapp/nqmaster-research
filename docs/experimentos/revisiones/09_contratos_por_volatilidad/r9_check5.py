"""r9_check5: alineacion de fechas campana vs nqdb (dia de semana; |P&L| contra el rango RTH del mismo dia y de los vecinos) y ATR al abrir."""
import os, sys, numpy as np, pandas as pd
MINE = "/home/user/nqmaster-research/research/mine"; os.chdir(MINE); sys.path.insert(0, MINE)
import prop_wf as P, objective as O, exp09_volsize as X
days, M, FU, PER = O.setup(); D = X.getD("nqdb.npz")
wd = pd.to_datetime(pd.Series(days).astype(str)).dt.dayofweek; print("dias de semana campana:", wd.value_counts().sort_index().to_dict())
rth = (D.om >= 570) & (D.om < 960); df = pd.DataFrame(dict(day=D.day[rth], h=D.h[rth], l=D.l[rth]))
rng = df.groupby("day").agg(h=("h", "max"), l=("l", "min")); r = (rng.h - rng.l).reindex(range(D.nd)).to_numpy()
rs = pd.Series(r, index=D.daydate).groupby(level=0).last()
FIN = M[(0, 4)][2]; a = np.abs(FIN)
pos = rs.index.get_indexer(days)
for lag in (-1, 0, 1):
    x = rs.to_numpy()[pos + lag]; ok = ~np.isnan(x); print(f"corr(|P&L dia t|, rango RTH t{lag:+d}) = {np.corrcoef(a[ok], x[ok])[0,1]:.3f}")
atr = X.atr_days(days)
# ATR del dia t debe depender solo de rangos hasta t-1: recomputar desde TR con shift y comparar
print("ATR min/max campana:", atr.min().round(1), atr.max().round(1))
