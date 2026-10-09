"""Companion to eval20.py: Lucid 50K pass WITHOUT a time limit (Lucid Flex evals have none) vs within 20 / 30 / 40 trading days,
for fixed sizes and 'start small, size up if behind' policies. Starts with >= 150 trading days of future data. -> eval20_life.csv"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
from eval20 import mats, stats
PROF = {"WR70Plus+noche": "E_WRN", "WR70Plus+noche+oro WinRate": "E_WRN_GW", "Ultra+noche+oro Robust": "E_UAN_GR"}
POL = {"1 fijo": (1, 1, 0.0, 999, 1, 0.0), "2 fijo": (2, 2, 0.0, 999, 2, 0.0), "1->2 dia10 si <2100": (1, 1, 0.0, 10, 2, 2100.0),
       "1->2 dia15 si <2100": (1, 1, 0.0, 15, 2, 2100.0), "1->2 dia20 si <2100": (1, 1, 0.0, 20, 2, 2100.0), "2->1 si colchon<1000": (2, 1, 1000.0, 999, 2, 0.0)}
rows = []
for per in ("IS", "C24", "REAL"):
    for pn, cfg in PROF.items():
        LO, CL = mats(per, cfg, 1400.0, 2)
        for poln, p in POL.items():
            o = stats(LO, CL, 3000.0, 2000.0, 0.5, 400, *p, 150); ps = o[:, 0] == 1
            rows.append(dict(per=per, perfil=pn, politica=poln, aprueba=100 * ps.mean(), quema=100 * (o[:, 0] == -1).mean(),
                             d20=100 * (ps & (o[:, 1] <= 20)).mean(), d30=100 * (ps & (o[:, 1] <= 30)).mean(), d40=100 * (ps & (o[:, 1] <= 40)).mean(),
                             mediana=float(np.median(o[ps, 1]))))
R = pd.DataFrame(rows); R.to_csv("eval20_life.csv", index=False)
pd.set_option("display.width", 250)
S = R.groupby(["perfil", "politica"]).agg(aprueba=("aprueba", "mean"), aprueba_min=("aprueba", "min"), d20=("d20", "mean"), d30=("d30", "mean"), d40=("d40", "mean"), mediana=("mediana", "mean"), quema=("quema", "mean"))
print(S.round(1).to_string())
print(R.pivot_table(index=["perfil", "politica"], columns="per", values=["aprueba", "d20"]).round(0).to_string())
