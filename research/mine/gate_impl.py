"""Cushion gating that NQMaster ALREADY implements (PropMode Eval, EvalCushionFull = C): FULL profile while cushion >= C, SAFE
below (no x2 boosts; VOLB, LON, MOM1030, MOM11 off; everything else incl. night modules stays). Gold (GoldMaster) runs its profile
all the time. vs the searched RAPIDO/ESTABLE pair. Exact dense grids, Lucid Flex 50K, 1 contract, starts: all days and ATR < 1.15.
-> gate_impl.csv"""
import sys, itertools, numpy as np, pandas as pd
sys.path.insert(0, ".")
import fast1c as F
import prof_grid_lib  # noqa: F401  (defines CFG profile lists)
from acct_life import CFG
from gate84 import vecs, gated, summ
from gate84b import SETS
from acct_policy import hiatr
PERS = F.PERS
NIGHT = ["N:NF05", "N:LF06", "N:LF0430"]; GW = ["G:OD1030", "G:ENG0408", "G:SVWAP22"]; GR = GW + ["G:ASIA1R", "G:ENG0206"]
fix = lambda ks: [k.replace("U:ICT", "U:ICTF").replace("U1:ICT", "U1:ICTF").replace("WR:ICT", "U:ICTF").replace("WR1:ICT", "U1:ICTF").replace("ICTFF", "ICTF") for k in ks]
UA_FULL = fix(CFG["UA_FULL"]) + NIGHT; UA_SAFE = fix(CFG["UA_SAFE"]) + NIGHT
WR_FULL = fix(CFG["WR_FULL"]) + NIGHT + ["N:LATE15"]; WR_SAFE = fix(CFG["WR_SAFE"]) + NIGHT + ["N:LATE15"]
PAIRS = {"Ultra FULL/SAFE + oro Robust": (UA_FULL + GR, UA_SAFE + GR), "Ultra FULL/SAFE + oro WinRate": (UA_FULL + GW, UA_SAFE + GW),
         "WR70Plus FULL/SAFE + oro WinRate": (WR_FULL + GW, WR_SAFE + GW), "WR70Plus FULL/SAFE + oro Robust": (WR_FULL + GR, WR_SAFE + GR),
         "RAPIDO/ESTABLE (busqueda)": (SETS["RAPIDO"], SETS["ESTABLE"])}
rows = []
for (nm, (hi, lo)), C in itertools.product(PAIRS.items(), (0, 600, 900, 1200, 1500)):
    hi = [k for k in hi if k in F.KEYS]; lo = [k for k in lo if k in F.KEYS]
    for per in PERS:
        lH, cH = vecs(hi, per); lL, cL = vecs(lo, per)
        o = gated(lH, cH, lL, cL, float(C), 120); m = len(o); atr = hiatr(per)[:m]
        for fn, mask in (("todos", np.ones(m, bool)), ("ATR<1.15", atr < 1.15)):
            rows.append(dict(par=nm, C=C, per=per, arranque=fn, **summ(o[mask])))
R = pd.DataFrame(rows); R.to_csv("gate_impl.csv", index=False)
pd.set_option("display.width", 260)
P = R.pivot_table(index=["par", "C", "arranque"], columns="per", values=["aprueba", "mediana"]).round(1)
P[("oos", "aprueba")] = P[[("aprueba", "C24"), ("aprueba", "REAL")]].mean(1); P[("oos", "mediana")] = P[[("mediana", "C24"), ("mediana", "REAL")]].mean(1)
print(P.to_string())
