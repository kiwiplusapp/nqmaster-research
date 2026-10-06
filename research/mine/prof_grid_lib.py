"""Best prop profile: eval profile x funded profile x contracts x payout threshold, 12-month lifecycle per Lucid 50K slot.
History + 500 block-bootstrap years per combo. Run per period: python prof_grid.py IS|C24|REAL -> prof_grid_<per>.csv"""
import sys, itertools, numpy as np, pandas as pd
sys.path.insert(0, ".")
from acct_lab import META
from acct_size import life_g
from acct_life import stack, CFG
per = sys.argv[1] if len(sys.argv) > 1 and __name__ == "__main__" else None
U = [m for m in META["IS"] if m.startswith("U:") and m not in ("U:ICT", "U:VW13", "U:ICTF")]
NEWM = ["N:LATE15", "N:ENG0610", "N:LATEFH"]
CFG["UA_FULL"] = U + ["U:ICTF", "W:VW13b"] + NEWM
CFG["UA_NOB"] = [("U1:" + m[2:]) if ("U1:" + m[2:]) in META["IS"] else m for m in U] + ["U1:ICTF", "W:VW13b"] + NEWM
CFG["UA_SAFE"] = ["U1:ORB60", "U1:ORB90", "U1:MSEQ", "U:MSEQS", "U1:CRT11", "U1:ICTF", "U1:MOM13", "U:VW13", "U:ON07", "U:REV06"] + NEWM
WRm = sorted(m[3:] for m in META["IS"] if m.startswith("WR:"))
CFG["WR_FULL"] = ["WR:" + m for m in WRm]; CFG["WR_NOB"] = ["WR1:" + m for m in WRm]; CFG["WR_SAFE"] = ["WR1:" + m for m in WRm if m not in ("MOM11", "VOLB_tf1")]
C6m = sorted(m[3:] for m in META["IS"] if m.startswith("C6:"))
CFG["C6_FULL"] = ["C6:" + m for m in C6m]; CFG["C6_NOB"] = ["C61:" + m for m in C6m]; CFG["C6_SAFE"] = ["C61:" + m for m in C6m if m not in ("VOLB_tf0", "LON")]
GW = ["G:OD1030", "G:ENG0408", "G:SVWAP22"]; GR = GW + ["G:ASIA1R", "G:ENG0206"]
for b in ("UA", "WR", "C6"):
    for lvl in ("FULL", "NOB", "SAFE"):
        CFG[f"{b}_{lvl}_GW"] = CFG[f"{b}_{lvl}"] + GW; CFG[f"{b}_{lvl}_GR"] = CFG[f"{b}_{lvl}"] + GR
    CFG[f"{b}_FULL_none"] = CFG[f"{b}_FULL"]
EVAL = {"UA+GR": "UA_FULL_GR", "UA+GW": "UA_FULL_GW", "UA": "UA_FULL_none", "WR+GW": "WR_FULL_GW", "WR+GR": "WR_FULL_GR", "C6+GR": "C6_FULL_GR"}
FUND = {f"{b} gating +{g}": ((f"{b}_SAFE_{g}", f"{b}_NOB_{g}", f"{b}_FULL_{g}"), 750.0, 1500.0) for b in ("UA", "WR", "C6") for g in ("GW", "GR") if not (b == "C6" and g == "GR")}
FUND.update({"UA full +GW": (("UA_FULL_GW",) * 3, 0.0, 0.0), "WR full +GW": (("WR_FULL_GW",) * 3, 0.0, 0.0)})
