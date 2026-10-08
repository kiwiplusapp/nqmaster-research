"""Structural versions of the RAPIDO/ESTABLE gating that map onto the existing NQMaster Ultra profile (HI) plus one new SAFE
definition (LO), gold constant in both gears (GoldMaster unchanged). Exact dense grids, Lucid Flex 50K, 1 contract. -> gate_struct.csv"""
import sys, itertools, numpy as np, pandas as pd
sys.path.insert(0, ".")
import fast1c as F
import prof_grid_lib  # noqa: F401
from acct_life import CFG
from gate84 import vecs, gated, summ
from gate84b import SETS
from acct_policy import hiatr
PERS = F.PERS
NIGHT = ["N:NF05", "N:LF06", "N:LF0430"]; GW = ["G:OD1030", "G:ENG0408", "G:SVWAP22"]; GR = GW + ["G:ASIA1R", "G:ENG0206"]
UA = [k.replace("U:ICT", "U:ICTF").replace("ICTFF", "ICTF") for k in CFG["UA_FULL"]] + NIGHT
EST_NQ = [k for k in SETS["ESTABLE"] if not k.startswith("G:")]; RAP_NQ = [k for k in SETS["RAPIDO"] if not k.startswith("G:")]
EST_NQ_ULTRA = ["U1:CRT11", "U1:ORB90", "U1:MSEQ", "U:ON07", "U:REV06", "W:VOLB_tf1", "WR1:VW13b", "N:ENG0610", "N:LATEFH"]   # same modules, Ultra variants
PAIRS = {"RAPIDO/ESTABLE (busqueda, oro cambia)": (SETS["RAPIDO"], SETS["ESTABLE"]),
         "RAPIDO/ESTABLE NQ + oro Robust fijo": (RAP_NQ + GR, EST_NQ + GR),
         "RAPIDO/ESTABLE NQ + oro WinRate fijo": (RAP_NQ + GW, EST_NQ + GW),
         "Ultra+noche / ESTABLE NQ + oro Robust": (UA + GR, EST_NQ + GR),
         "Ultra+noche / ESTABLE NQ + oro WinRate": (UA + GW, EST_NQ + GW),
         "Ultra+noche / ESTABLE (variantes Ultra) + oro Robust": (UA + GR, EST_NQ_ULTRA + GR),
         "Ultra+noche / ESTABLE (variantes Ultra) + oro WinRate": (UA + GW, EST_NQ_ULTRA + GW)}
rows = []
for (nm, (hi, lo)), C in itertools.product(PAIRS.items(), (900, 1200, 1500)):
    hi = [k for k in hi if k in F.KEYS]; lo = [k for k in lo if k in F.KEYS]
    for per in PERS:
        lH, cH = vecs(hi, per); lL, cL = vecs(lo, per)
        o = gated(lH, cH, lL, cL, float(C), 120); m = len(o); atr = hiatr(per)[:m]
        for fn, mask in (("todos", np.ones(m, bool)), ("ATR<1.15", atr < 1.15)):
            rows.append(dict(par=nm, C=C, per=per, arranque=fn, **summ(o[mask])))
R = pd.DataFrame(rows); R.to_csv("gate_struct.csv", index=False)
pd.set_option("display.width", 260)
P = R.pivot_table(index=["par", "C", "arranque"], columns="per", values=["aprueba", "mediana"]).round(1)
P[("oos", "aprueba")] = P[[("aprueba", "C24"), ("aprueba", "REAL")]].mean(1); P[("oos", "mediana")] = P[[("mediana", "C24"), ("mediana", "REAL")]].mean(1)
print(P.to_string())
