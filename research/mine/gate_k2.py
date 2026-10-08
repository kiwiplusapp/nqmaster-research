"""Final policy with the NQ part at 1 or 2 contracts (gold WinRate x2): HI = Ultra+night, LO = Estable (no x2), gate at C."""
import sys, itertools, numpy as np, pandas as pd
sys.path.insert(0, ".")
import fast1c as F
from gate84 import gated, summ
from gate_lo import UA, GW
from acct_policy import hiatr
LO = ["C61:CRT11", "N:ENG0610", "N:LATEFH", "U1:ORB90", "U1:MSEQ", "U:ON07", "U:REV06", "W:VOLB_tf1", "WR1:VW13b"]
HOY = ["G:ENG0408", "G:OD1030", "G:SVWAP22", "N:LATE15", "N:LF0430", "N:LF06", "N:NF05", "U:ICTF", "WR:CRT11", "WR:MOM11", "WR:MSEQ", "WR:MSEQS", "WR:ORB60", "WR:ORB90", "WR:REV06", "WR:VOLB_tf1", "WR:VW13", "WR:VW13b"]
def comb(nq, wn, gold, wg, per):
    Ls, Cs, nd = F.DATA[per]; L = np.zeros((nd, 1440), np.float32); c = np.zeros(nd)
    for k in nq:
        if k in F.KEYS: L += wn * Ls[k]; c += wn * Cs[k]
    for k in gold: L += wg * Ls[k]; c += wg * Cs[k]
    return L.min(1).astype(np.float64), c
rows = []
cases = [("HOY 1c", HOY, HOY, 1, 1, 0), ("HOY 2c", HOY, HOY, 2, 2, 0)]
cases += [(f"Ultra/Estable NQ {k}c, oro {g}x, C{C}", UA, LO, k, g, C) for k, g, C in itertools.product((1, 2), (1, 2), (1200, 1500, 1800))]
for nm, hi, lo, k, g, C in cases:
    for per in F.PERS:
        if nm.startswith("HOY"):
            lH, cH = comb([x for x in hi if not x.startswith("G:")], k, [x for x in hi if x.startswith("G:")], g, per); lL, cL = lH, cH
        else:
            lH, cH = comb(hi, k, GW, g, per); lL, cL = comb(lo, k, GW, g, per)
        o = gated(lH, cH, lL, cL, float(C), 120); m = len(o); atr = hiatr(per)[:m]
        for fn, mask in (("todos", np.ones(m, bool)), ("ATR<1.15", atr < 1.15)):
            rows.append(dict(caso=nm, per=per, arranque=fn, **summ(o[mask])))
R = pd.DataFrame(rows); R.to_csv("gate_k2.csv", index=False); pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
print(R.pivot_table(index=["caso", "arranque"], columns="per", values=["aprueba", "mediana", "p20"]).round(1).to_string())
