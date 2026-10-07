"""150K plan (eval 6c / funded 3c, final + night modules) year by year: one account slot started on the first trading day of each calendar
year (2020-2023 on CFD, 2024-2026 on real MNQ/MGC), run 12 months (2026: to the end of the data); plus the average over every start day
inside that year (starts every 3 days). -> year150.csv"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
import prof_grid_lib
import lc_lib as L
from acct_life import CFG
from acct_lab import Z
from acct_policy import vec
from acct_bigger import life_q, ACC
NIGHT = ["N:NF05", "N:LF06", "N:LF0430"]
E = L.define("Y_E", CFG["UA_FULL_GR"] + NIGHT); F = tuple(L.define("Y_" + x, CFG[x] + NIGHT) for x in ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR"))
T, D, Q, CAP, FEE = ACC["150K"]; ek, fk = 6, 3; rows = []
for per, years in (("IS", (2020, 2021, 2022, 2023)), ("REAL", (2024, 2025, 2026))):
    days = np.asarray(Z(per)["days"]); ev = vec(per, E, 0.0, 0.4667 * T / ek); fv = [vec(per, c, 0.0, 0.0) for c in F]
    LO = ek * ev[0]; CL = ek * ev[1]; f0 = fk * np.array([v[0] for v in fv]); f1 = fk * np.array([v[1] for v in fv])
    for y in years:
        idx = np.nonzero((days >= y * 10000) & (days < (y + 1) * 10000))[0]
        if len(idx) == 0: continue
        s0 = idx[0]; H = min(252, len(days) - s0 - 1)
        sl = slice(s0, s0 + H + 1); out = np.zeros((2, 6))
        life_q(LO[sl].copy(), CL[sl].copy(), f0[:, sl].copy(), f1[:, sl].copy(), 1687.5, 3375.0, 6000.0, T, D, Q, CAP, FEE, H, H, out)
        # all starts inside the year (each run H days, bounded by the data)
        res = []
        for s in idx[::3]:
            h = min(252, len(days) - s - 1)
            if h < 120: break
            o = np.zeros((2, 6)); sl2 = slice(s, s + h + 1)
            life_q(LO[sl2].copy(), CL[sl2].copy(), f0[:, sl2].copy(), f1[:, sl2].copy(), 1687.5, 3375.0, 6000.0, T, D, Q, CAP, FEE, h, h, o); res.append(o[0, 0] / h * 21)
        rows.append(dict(anio=y, datos="CFD" if per == "IS" else "real", meses=round(H / 21, 1), mes_inicio_enero=round(out[0, 0] / H * 21), evals=int(out[0, 1]), pasan=int(out[0, 2]),
                         quemadas=int(out[0, 3]), cobros=int(out[0, 4]), mes_prom_todos_los_inicios=round(np.mean(res)) if res else np.nan, peor_inicio=round(np.min(res)) if res else np.nan))
R = pd.DataFrame(rows); R.to_csv("year150.csv", index=False); pd.set_option("display.width", 200); print(R.to_string(index=False))
