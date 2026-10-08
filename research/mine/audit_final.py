"""AUDIT step 9: pruned-profile candidates suggested by the audit (removal of modules with weak evidence) and forward 'haircut' scenarios.
Each set: IS / C24 / REAL / last 6 months (2026-04..09) metrics, 2015-19 cost-normalised PF of the module set, +1 tick per side,
+1 tick with 35% / 50% of the edge removed (constant deduction per weighted trade), block-bootstrap P(losing 6-month window) and
max drawdown p95 (1 base contract) under the 'realistic' haircut. (Approximation: removing a module does not re-admit trades the
conflict filter had blocked.)  -> audit_final.csv"""
import pickle, numpy as np, pandas as pd
from audit_port import st, daily, pf1519, boot_idx
A = pickle.load(open("audit_trades.pkl", "rb")); P = A["prof"]
SETS = {
    "Ultra (current)": ("Ultra", []),
    "Ultra -MOM1030 -ON07 -MOM13": ("Ultra", ["MOM1030", "ON07", "MOM13"]),
    "Ultra -MOM1030 -ON07 -MOM13 -LATEFH -ENG10": ("Ultra", ["MOM1030", "ON07", "MOM13", "LATEFH", "ENG10"]),
    "Ultra -MOM1030 -ON07 -MOM13 -LATEFH -ENG10 -ORB90": ("Ultra", ["MOM1030", "ON07", "MOM13", "LATEFH", "ENG10", "ORB90"]),
    "WR70N (current)": ("WR70N", []),
    "WR70N -VOLB": ("WR70N", ["VOLB"]),
    "WR70N -VOLB -ORB90": ("WR70N", ["VOLB", "ORB90"]),
    "GoldRB (current)": ("GoldRB", []),
    "GoldWR (current)": ("GoldWR", []),
    "Gold OD1030+ASIA1R": ("GoldRB", ["ENG0408", "SVWAP22", "ENG0206"]),
}
if __name__ == "__main__":
    rows = []
    for nm, (prof, rem) in SETS.items():
        r = dict(set=nm)
        for per in ("IS", "C24", "REAL"):
            F, D = P[prof][per]; F = F[~F["mod"].isin(rem)]; s = st(F, D)
            for k in ("tpd", "wr", "pf", "sharpe", "mo", "maxdd"): r[f"{per}_{k}"] = s[k]
            if per != "IS":
                s6 = st(F[F.date >= 20260401], D[D >= 20260401]); r[f"{per}_L6_pf"] = s6["pf"]; r[f"{per}_L6_mo"] = s6["mo"]
        if prof in ("Ultra", "WR70N"): r["L1519_pf_set"] = pf1519(prof, [m for m in P[prof]["REAL"][0]["mod"].unique() if m not in rem])
        F, D = P[prof]["REAL"]; F = F[~F["mod"].isin(rem)]; tick = 2.0 if prof.startswith("Gold") else 1.0
        mean_tr = float(((F.u - tick) * F.w).sum() / F.w.sum())
        for tag, keep in (("+1t", 1.0), ("+1t x0.65", 0.65), ("+1t x0.5", 0.5)):
            s = st(F.assign(u=F.u - tick - (1 - keep) * mean_tr), D)
            for k in ("wr", "pf", "sharpe", "mo"): r[f"REAL {tag} {k}"] = s[k]
            if tag == "+1t x0.65":
                d = daily(F.assign(u=F.u - tick - 0.35 * mean_tr), D).to_numpy(); I = boot_idx(len(d), 2000)[:, :252]; Pm = d[I]; eq = Pm.cumsum(1)
                cs = np.concatenate([np.zeros((Pm.shape[0], 1)), eq], 1); win = cs[:, 126:] - cs[:, :-126]
                r["x0.65 P(6m window loss)"] = round(float((win < 0).mean()), 3); r["x0.65 P(year loss)"] = round(float((eq[:, -1] < 0).mean()), 3)
                r["x0.65 maxDD p95"] = round(float(np.percentile((np.maximum.accumulate(np.maximum(eq, 0), 1) - eq).max(1), 95)))
        rows.append(r); print(nm, "done", flush=True)
    O = pd.DataFrame(rows); O.to_csv("audit_final.csv", index=False); pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60)
    print(O.T.to_string())
