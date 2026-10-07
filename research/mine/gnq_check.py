"""Gold-derived families (G_DRIVE, G_ORB) mined on NQ (results_gnq.csv). For each cluster (fam, A, T, mode) with IS & C24 PF >= 1.25
and REAL >= 1.15, take the config with the best IS PF (IS-only choice), then: 2015-19 regime test on nqhd_long (cost-normalised
0.345% ATR), slippage stress on REAL (+2 / +4 ticks per side), daily correlation with the Ultra portfolio, and the portfolio Sharpe
with / without it (conflict filter, IS / C24 / REAL). -> gnq_check.csv"""
import os, sys, ast, pickle, numpy as np, pandas as pd
sys.path.insert(0, ".")
from core import Data, run_events, split_stats
from run_mine import FAMILIES
from gold_port import conflict_filter
from ict_redo import ictf
from ultra_plus_lib import mined
R = pd.read_csv("results_gnq.csv")
ok = R[(R.IS_n >= 100) & (R.C24_n >= 60) & (R.IS_pf >= 1.25) & (R.C24_pf >= 1.25) & (R.REAL_pf >= 1.15)].copy()
ok["p"] = ok.params.map(ast.literal_eval)
ok["key"] = ok.apply(lambda r: (r.fam, r.p["A"], r.p["T"], r.p.get("mode", 0)), axis=1)
reps = ok.sort_values("IS_pf", ascending=False).groupby("key").head(1)
D_is = Data("nq_1m.npz"); D_re = Data("mnq_fut.npz"); D_lg = Data("nqhd_long.npz")
T = pickle.load(open("robust_trades.pkl", "rb"))
def ultra(per):
    F = T["Ultra"][per][0]; W = T["WR70Plus"][per][0]
    X = pd.concat([F[(F["mod"] != "ICT") & (F["mod"] != "VW13")], ictf(per, 2.0), W[W["mod"] == "VW13b"].assign(mod="VW13"),
                   mined(("LATE_MOM", 762), per, "LATE15"), mined(("ENGULF_4H", 1172), per, "ENG10"), mined(("LATE_MOM", 1107), per, "LATEFH")])
    return X[["date", "mod", "tin", "tout", "d", "u", "w"]], T["Ultra"][per][1]
U = {p: ultra(p) for p in ("IS", "C24", "REAL")}
def trades(D, gen, p, md, slip=0.25, nc=None):
    df = run_events(D, gen(D, p), flat=955, maxday=md, slip=slip, norm_cost=nc)
    if len(df): df["tin"] = D.sm[df.fi.to_numpy().astype(int)]; df["tout"] = D.sm[df.xi.to_numpy().astype(int)] + 1
    return df
def pf(u): u = np.asarray(u); gl = -u[u <= 0].sum(); return round(u[u > 0].sum() / gl, 3) if gl > 0 else np.nan
def sharpe(X, days):
    d = (X.u * X.w).groupby(X.date).sum().reindex(days, fill_value=0.0); return d.mean() / d.std() * 252 ** .5, d
if __name__ == "__main__":
    rows = []
    for r in reps.itertuples():
        gen, grid, md = FAMILIES[r.fam]; p = r.p; row = dict(fam=r.fam, j=r.j, params=r.params, IS_pf=r.IS_pf, C24_pf=r.C24_pf, REAL_pf=r.REAL_pf, IS_n=r.IS_n, IS_wr=r.IS_wr)
        lg = trades(D_lg, gen, p, md, slip=0.0, nc=0.00345); s = split_stats("nqhd_long", lg) if len(lg) else {}
        row.update({"L1519_n": s.get("TR_n"), "L1519_pf": s.get("TR_pf"), "L2023_pf_norm": s.get("T1_pf")})          # 2015-19 regime test (cost-normalised)
        re = trades(D_re, gen, p, md)
        for extra in (2, 4):
            x = trades(D_re, gen, p, md, slip=0.25 * (1 + extra)); row[f"REAL_pf_slip+{extra}"] = pf(x.usd) if len(x) else np.nan
        for per, D in (("IS", D_is), ("C24", D_is), ("REAL", D_re)):
            x = trades(D, gen, p, md) if per != "REAL" else re
            lo, hi = (20200201, 20240101) if per == "IS" else ((20240101, 3e7) if per == "C24" else (20240201, 3e7))
            x = x[(x.date >= lo) & (x.date < hi)]
            new = pd.DataFrame(dict(date=x.date, mod="NEW", tin=x.tin, tout=x.tout, d=x.d, u=x.usd, w=1.0))
            Ux, days = U[per]; s0, d0 = sharpe(conflict_filter(Ux.sort_values(["date", "tin"]).reset_index(drop=True)), days)
            X1 = conflict_filter(pd.concat([Ux, new]).sort_values(["date", "tin"]).reset_index(drop=True)); s1, _ = sharpe(X1, days)
            nd = new.groupby("date").u.sum().reindex(days, fill_value=0.0)
            row[f"{per}_corr"] = round(np.corrcoef(nd, d0)[0, 1], 3); row[f"{per}_dSharpe"] = round(s1 - s0, 3); row[f"{per}_kept"] = int((X1["mod"] == "NEW").sum())
        rows.append(row); print(row, flush=True)
    O = pd.DataFrame(rows); O.to_csv("gnq_check.csv", index=False); pd.set_option("display.width", 300); pd.set_option("display.max_colwidth", 70)
    print(O.drop(columns=["params"]).to_string(index=False)); print(O[["fam", "j", "params"]].to_string(index=False))
