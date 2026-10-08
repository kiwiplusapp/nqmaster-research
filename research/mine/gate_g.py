"""Daily profit stop (EvalProfitStop) on the final 1-contract policy: HI = Ultra+night, LO = Estable (no x2), gold WinRate x2, C=1200."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
import fast1c as F
from gate84b import gear, summ
from gate_lo import combo, UA, GW
from acct_policy import hiatr
LO = ["C61:CRT11", "N:ENG0610", "N:LATEFH", "U1:ORB90", "U1:MSEQ", "U:ON07", "U:REV06", "W:VOLB_tf1", "WR1:VW13b"]
rows = []
for G in (0, 700, 1000, 1400):
    for per in F.PERS:
        lH, cH = combo(UA, GW, 2, per); lL, cL = combo(LO, GW, 2, per)
        o = gear(lH, cH, lL, cL, lH, cH, 1200.0, 1e9, float(G), 120); m = len(o); atr = hiatr(per)[:m]
        for fn, mask in (("todos", np.ones(m, bool)), ("ATR<1.15", atr < 1.15)):
            rows.append(dict(G=G, per=per, arranque=fn, **summ(o[mask])))
R = pd.DataFrame(rows); pd.set_option("display.width", 250)
print(R.pivot_table(index=["G", "arranque"], columns="per", values=["aprueba", "mediana", "p30"]).round(1).to_string())
