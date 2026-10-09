"""Start-day filters on the cushion-gated policies (Lucid Flex 50K, exact dense grids, 1 contract):
  ATR: start only if today's daily ATR / its 60-day median < 1.15 (calm regime)
  COLD: start only if the HI set made <= 0 over the previous 10 trading days (no chasing a hot streak)
Pass / median days among the starts that the filter allows, and the share of days allowed. -> gate_start.csv"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
import fast1c as F
from gate84 import vecs, gated, summ
from gate84b import SETS
from acct_policy import hiatr
PERS = F.PERS
POL = [("HOY", "HOY", "HOY", 0), ("HOY/ESTABLE 900", "HOY", "ESTABLE", 900), ("HOY/ESTABLE 1200", "HOY", "ESTABLE", 1200),
       ("RAPIDO/ESTABLE 1200", "RAPIDO", "ESTABLE", 1200), ("RAPIDO/ESTABLE 1500", "RAPIDO", "ESTABLE", 1500)]
rows = []
for nm, h, l, C in POL:
    for per in PERS:
        lH, cH = vecs(SETS[h], per); lL, cL = vecs(SETS[l], per)
        o = gated(lH, cH, lL, cL, float(C), 120); m = len(o)
        atr = hiatr(per)[:m]; prev = pd.Series(cH).rolling(10).sum().shift(1).to_numpy()[:m]
        for fn, mask in (("todos", np.ones(m, bool)), ("ATR<1.15", atr < 1.15), ("racha floja", prev <= 0), ("ambos", (atr < 1.15) & (prev <= 0))):
            s = summ(o[mask]); rows.append(dict(politica=nm, per=per, filtro=fn, dias_ok=100 * mask.mean(), **s))
R = pd.DataFrame(rows); R.to_csv("gate_start.csv", index=False)
pd.set_option("display.width", 250)
P = R.pivot_table(index=["politica", "filtro"], columns="per", values=["aprueba", "mediana", "dias_ok"]).round(1)
print(P.to_string())
