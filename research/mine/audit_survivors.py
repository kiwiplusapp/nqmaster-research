"""AUDIT step 7: do the mined families show PERSISTENCE, or are the survivors what chance predicts?
For each family of the strategy miner (results_*.csv; CFD IS 2020-23, CFD C24 2024-26, MNQ REAL 2024-26):
  eligible = IS_n >= 100 and C24_n >= 60; survivor rule used by the project = IS PF >= 1.25 and C24 PF >= 1.25 and REAL PF >= 1.15.
  expected survivors if 2020-23 and 2024-26 were independent = N_elig x P(IS pass) x P(C24 & REAL pass)  (C24 and REAL are the same
  period on two feeds, so they are taken jointly). Ratio observed / expected > 1 = persistence beyond chance.
  Spearman(IS PF, C24 PF) over eligible configs.
  2015-19 (cost-normalised, nqhd_long): PF >= 1.0 / >= 1.1 share of survivors vs of all eligible configs (base rate).
  (results_*longnorm.csv where available; NQ_DRIVE / G_DRIVE / G_ORB on NQ re-run here for survivors + 400 random eligible configs.)
Output: audit_survivors.csv"""
import os, sys, ast, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
from core import Data, run_events
from run_mine import FAMILIES
rng = np.random.default_rng(5)
SRC = [("results_all.csv", "results_longnorm.csv"), ("results_b3.csv", "results_b3longnorm.csv"), ("results_b4.csv", "results_b4longnorm.csv"),
       ("results_gnq.csv", None), ("results_nqdrive.csv", None)]
def pfu(u):
    u = np.asarray(u); gl = -u[u <= 0].sum(); return float(u[u > 0].sum() / gl) if gl > 0 and len(u) >= 20 else np.nan
if __name__ == "__main__":
    DL = None; rows = []
    for f, lf in SRC:
        R = pd.read_csv(f)
        if lf: Lg = pd.read_csv(lf)[["fam", "j", "TR_n", "TR_pf"]]; R = R.merge(Lg, on=["fam", "j"], how="left")
        for fam, g in R.groupby("fam"):
            E = g[(g.IS_n >= 100) & (g.C24_n >= 60)].copy()
            if len(E) < 30: continue
            pi = (E.IS_pf >= 1.25).mean(); po = ((E.C24_pf >= 1.25) & (E.REAL_pf >= 1.15)).mean()
            surv = E[(E.IS_pf >= 1.25) & (E.C24_pf >= 1.25) & (E.REAL_pf >= 1.15)]
            r = dict(file=f, fam=fam, eligible=len(E), P_IS=round(pi, 3), P_OOS=round(po, 3), survivors=len(surv), expected=round(len(E) * pi * po, 1),
                     ratio=round(len(surv) / max(len(E) * pi * po, 0.1), 2), spearman_IS_C24=round(float(E[["IS_pf", "C24_pf"]].corr(method="spearman").iloc[0, 1]), 3),
                     spearman_IS_REAL=round(float(E[["IS_pf", "REAL_pf"]].corr(method="spearman").iloc[0, 1]), 3), median_IS=round(float(E.IS_pf.median()), 3), median_C24=round(float(E.C24_pf.median()), 3))
            if "TR_pf" not in E.columns or E.TR_pf.isna().all():          # re-run 2015-19 for survivors + a random sample
                if fam not in FAMILIES: rows.append(r); continue
                if DL is None: DL = Data("nqhd_long.npz")
                gen, grid, md = FAMILIES[fam]; samp = pd.concat([surv, E.sample(min(400, len(E)), random_state=3)]).drop_duplicates("j")
                tr = {}
                for j in samp.j:
                    df = run_events(DL, gen(DL, grid[j]), flat=955, maxday=md, slip=0.0, norm_cost=0.00345); df = df[(df.date >= 20150201) & (df.date < 20200101)]
                    tr[j] = pfu(df.usd)
                E["TR_pf"] = E.j.map(tr); surv = surv.assign(TR_pf=surv.j.map(tr)); base = E[E.j.isin(E.sample(min(400, len(E)), random_state=3).j)]
            else:
                surv = E[E.j.isin(surv.j)]; base = E
            s = surv.TR_pf.dropna(); b = base.TR_pf.dropna()
            r.update(surv_1519_n=len(s), surv_1519_median=round(float(s.median()), 3) if len(s) else np.nan, surv_1519_ge1=round(float((s >= 1.0).mean()), 2) if len(s) else np.nan,
                     surv_1519_ge11=round(float((s >= 1.1).mean()), 2) if len(s) else np.nan, base_1519_median=round(float(b.median()), 3), base_1519_ge1=round(float((b >= 1.0).mean()), 2),
                     base_1519_ge11=round(float((b >= 1.1).mean()), 2))
            rows.append(r); print(r, flush=True)
    O = pd.DataFrame(rows); O.to_csv("audit_survivors.csv", index=False)
    tot = O[["eligible", "survivors", "expected"]].sum(); print("TOTAL", tot.to_dict(), "ratio", round(tot.survivors / tot.expected, 2))
    pd.set_option("display.width", 250); print(O.drop(columns=["file"]).to_string(index=False))
