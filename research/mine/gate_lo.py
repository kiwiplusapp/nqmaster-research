"""Simplest implementable ESTABLE (LO gear) for policy A-oro2 (HI = Ultra+night, gold WinRate x2 always, gate C=1200). -> printed"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
import fast1c as F
from gate84 import gated, summ
from gate_final import combo, UA, GW, EST
from acct_policy import hiatr
LOS = {"Estable exacto (busqueda)": EST,
       "Estable sin x2": ["C61:CRT11", "N:ENG0610", "N:LATEFH", "U1:ORB90", "U1:MSEQ", "U:ON07", "U:REV06", "W:VOLB_tf1", "WR1:VW13b"],
       "Estable sin x2 + VW13 x2": ["C61:CRT11", "N:ENG0610", "N:LATEFH", "U1:ORB90", "U1:MSEQ", "U:ON07", "U:REV06", "W:VOLB_tf1", "WR1:VW13b", "WR:VW13"],
       "Estable con x2": ["U:CRT11", "N:ENG0610", "N:LATEFH", "U:ORB90", "U:MSEQ", "U:ON07", "U:REV06", "W:VOLB_tf1", "WR:VW13b", "WR:VW13"],
       "SAFE actual de NQMaster": [k.replace("U1:ICT", "U1:ICTF") for k in ["U1:ORB60", "U1:ORB90", "U1:MSEQ", "U:MSEQS", "U1:CRT11", "U1:ICT", "U1:MOM13", "U:VW13", "U:ON07", "U:REV06", "N:LATE15", "N:ENG0610", "N:LATEFH", "N:NF05", "N:LF06", "N:LF0430"]]}
if __name__ == "__main__":      # analysis only when run directly (other scripts import the helpers)
    rows = []
    for nm, lo in LOS.items():
        for per in F.PERS:
            lH, cH = combo(UA, GW, 2, per); lL, cL = combo(lo, GW, 2, per)
            o = gated(lH, cH, lL, cL, 1200.0, 120); m = len(o); atr = hiatr(per)[:m]
            for fn, mask in (("todos", np.ones(m, bool)), ("ATR<1.15", atr < 1.15)):
                rows.append(dict(estable=nm, per=per, arranque=fn, **summ(o[mask])))
    R = pd.DataFrame(rows); pd.set_option("display.width", 250)
    print(R.pivot_table(index=["estable", "arranque"], columns="per", values=["aprueba", "mediana"]).round(1).to_string())
