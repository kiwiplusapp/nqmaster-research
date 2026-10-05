"""Final numbers for the GoldMaster profiles (1 MGC per module, real $ costs: $1.90 RT + 1 tick per side, FOMC skipped, conflict filter)."""
import sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, ".")
from gold_port import conflict_filter, metrics, DAYS
T = pickle.load(open("gold_curated_trades.pkl", "rb"))
PROF = {"WinRate": ["OD1030", "ENG0408", "SVWAP22"], "Balanced": ["OD1030", "ENG0408", "SVWAP22", "ENG0610"], "Robust": ["OD1030", "ENG0408", "SVWAP22", "ASIA1R", "ENG0206"]}
rows = []; out = {}
for nm, mods in PROF.items():
    for per in ("IS", "C24", "REAL"):
        F = conflict_filter(pd.concat([T[m][per] for m in mods], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True))
        m = metrics(F, DAYS[per]); x = F.u; dd = x.groupby(F.date).sum()
        m.update(net=round(x.sum()), net_nocomm=round((x + 1.9).sum()), worst_day=round(dd.min()), months_pos=round(100 * (dd.groupby(dd.index // 100).sum() > 0).mean()))
        rows.append(dict(profile=nm, per=per, **m)); out[(nm, per)] = F
    for per in ("2010-14", "2015-19"):
        F = conflict_filter(pd.concat([T[m][per] for m in mods], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True)); x = F.u
        rows.append(dict(profile=nm, per=per + " (costo normalizado)", n=len(F), wr=round(100 * (x > 0).mean(), 1), pf=round(x[x > 0].sum() / -x[x <= 0].sum(), 3)))
G = pd.DataFrame(rows); pd.set_option("display.width", 250); print(G.to_string(index=False))
for nm in PROF:
    F = out[(nm, "REAL")]; print("\n", nm, "MGC by module:"); print(F.groupby("mod").u.agg(n="size", wr=lambda x: round(100 * (x > 0).mean(), 1), pf=lambda x: round(x[x > 0].sum() / -x[x <= 0].sum(), 2), net="sum").round(0).to_string())
pickle.dump(out, open("gold_final_trades.pkl", "wb")); G.to_csv("gold_final.csv", index=False)
