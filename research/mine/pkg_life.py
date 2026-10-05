import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); RES = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, RES)
from final_pkg import pkg_base, base, cand_trades, conflict_filter, get
os.chdir(RES)
from pa_subsets import build, life2
from evalfast import stats
VW = get("CLOCK_ANCHOR", "{'anc': 'VWAP', 'T': 1300, 'x': 0.3, 'mode': 1, 's': 0.15, 'R': 0.5, 'tg': 0, 'tf': 1, 'hold': 120}")
rows = []
for per in ("IS", "C24", "REAL"):
    tag = "mnq_fut" if per == "REAL" else "nq_1m"
    B, days = base(per)
    P = pkg_base(per, True)
    P = conflict_filter(pd.concat([P, cand_trades(VW, per, "VW13", 1.0)], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True))
    for nm, F in (("MaxPlus", B), ("MaxPlus2", P)):
        path = build(tag, F, days)
        e4 = stats(path, k1=4); e2 = stats(path, k1=2); L = life2(path, path, 4)
        rows.append(dict(per=per, v=nm, eval4=f"{e4['pass_']}/{e4['bust']}", eval4_days_to_PA=e4["days_to_PA"], eval2=f"{e2['pass_']}/{e2['bust']}", net_mo=L["net_mo"], p10=L["p10_mo"], payouts=L["payouts_yr"], pa_busts=L["PA_busts_yr"]))
        print(rows[-1], flush=True)
print(pd.DataFrame(rows).to_string(index=False))
