"""Does adding more curated gold modules (LATE1430, DRIVE11, ASIA05) to the final profile raise $/month per Lucid 50K slot?
Final profile = eval UA+GR fixed 2 contracts (profit stop 1400), funded UA gating + GR. -> gold_extra_lc.csv"""
import sys; sys.path.insert(0, ".")
import pandas as pd
import lc_lib as L
from acct_life import CFG
base_e = "UA_FULL_GR"; base_f = ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR")
C = {"final": (base_e, base_f, L.FIXED2)}
for tag, extra in {"+LATE1430": ["G:LATE1430"], "+DRIVE11": ["G:DRIVE11"], "+ASIA05": ["G:ASIA05"], "+LATE1430+DRIVE11": ["G:LATE1430", "G:DRIVE11"]}.items():
    e = L.define(base_e + tag, CFG[base_e] + extra); f = tuple(L.define(x + tag, CFG[x] + extra) for x in base_f)
    C["final " + tag] = (e, f, L.FIXED2)
    C["solo fondeada " + tag] = (base_e, f, L.FIXED2)
R, S = L.run(C); R.to_csv("gold_extra_lc.csv", index=False)
pd.set_option("display.width", 250)
print(R.pivot_table(index="cand", columns=["per", "test"], values="mo").round(0).to_string()); print(S.sort_values("mean9", ascending=False).to_string())
