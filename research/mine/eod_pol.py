"""Robust sizing-policy search for the 2026 Apex 50K plans (INTRA D2000, EOD D2000 DLL1000 pause/fail). Objective: max of the
minimum pass rate over IS / C24 / REAL (no period is privileged)."""
import os, sys, pickle, itertools, numpy as np, pandas as pd
sys.path.insert(0, ".")
from eod_eval import stats_eval, RES
PROF = {"Ultra": pickle.load(open(os.path.join(RES, "mine", "ultra_paths.pkl"), "rb")), "WR70Plus": pickle.load(open(os.path.join(RES, "mine", "wr70plus_paths.pkl"), "rb"))}
PLANS = {"INTRA2000": (2000.0, False, 0.0, False), "EOD_pausa": (2000.0, True, 1000.0, False), "EOD_quema": (2000.0, True, 1000.0, True)}
G = list(itertools.product((1, 2, 3), (4, 6, 8, 10, 12, 99), (1000.0, 1500.0, 2000.0), (1, 2, 3, 4), (0.0, 400.0, 600.0, 800.0)))
G = [g for g in G if not (g[1] == 99 and (g[2] != 1000.0 or g[3] != g[0]))]
rows = []
for prof, PP in PROF.items():
    for plan, (D, eod, dll, fail) in PLANS.items():
        for k0, dlate, lg, kl, dl in G:
            r = dict(prof=prof, plan=plan, k0=k0, d_late=dlate, lg=lg, k_late=kl, dl=dl)
            for per in ("IS", "C24", "REAL"):
                P = PP[per]
                p, b, p14, du = stats_eval(P["day"], P["fav"], P["adv"], P["rel"], P["ndays"], 3000.0, D, 21, eod, dll, fail, k0, dlate, lg, kl, dl)
                r.update({f"{per}_pass": round(100 * p, 1), f"{per}_bust": round(100 * b, 1), f"{per}_p14": round(100 * p14, 1), f"{per}_days": round(du, 1)})
            rows.append(r)
        print(prof, plan, flush=True)
X = pd.DataFrame(rows); X["minpass"] = X[["IS_pass", "C24_pass", "REAL_pass"]].min(axis=1); X["avgpass"] = X[["IS_pass", "C24_pass", "REAL_pass"]].mean(axis=1)
X.to_csv("eod_pol.csv", index=False); pd.set_option("display.width", 300)
for (prof, plan), g in X.groupby(["prof", "plan"]):
    print("\n==", prof, plan)
    print(g.sort_values(["minpass", "avgpass"], ascending=False).head(6)[["k0", "d_late", "lg", "k_late", "dl", "IS_pass", "C24_pass", "REAL_pass", "REAL_bust", "IS_p14", "C24_p14", "REAL_p14", "REAL_days"]].to_string(index=False))
