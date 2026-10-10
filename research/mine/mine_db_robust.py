"""Second look at the 16-year mining: configs with PF >= 1.2 in ALL four periods (A 2010-14 norm, B 2015-19 norm, T1 2020-23 real,
T2 2024-26 real; n >= 100 in T1). For each: parameter neighbourhood (median PF of the configs that differ in one parameter) and
value for the Ultra portfolio (daily P&L added at 1 contract: Sharpe change in T1 / T2 real and in A / B normalised; correlation).
-> mine_db_robust.json"""
import os, sys, ast, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from mine_db_select import load
from wrq_lib import getD


def sharpe(x): return float(x.mean() / x.std() * np.sqrt(252)) if x.std() > 0 else np.nan


def neighbours(R, row):
    p = ast.literal_eval(row.params); same = R[R.fam == row.fam]
    P = same.params.apply(ast.literal_eval)
    out = []
    for k in p:
        m = P.apply(lambda q: all(q[x] == p[x] for x in p if x != k) and q[k] != p[k])
        out.append(same[m.to_numpy()])
    N = pd.concat(out) if out else same.iloc[:0]
    return dict(n=int(len(N)), **{c: round(float(N[c].median()), 3) for c in ("T1_pf", "T2_pf", "B_pf", "A_pf")},
                share_all4_above_1=round(float(((N[["T1_pf", "T2_pf", "B_pf", "A_pf"]] > 1).all(axis=1)).mean()), 3))


if __name__ == "__main__":
    R, T = load()
    ok = ((R[["T1_pf", "T2_pf", "B_pf", "A_pf"]] >= 1.2).all(axis=1)) & (R.T1_n >= 100)
    C = R[ok].copy()
    TR = pickle.load(open(os.path.join(HERE, "db_long_trades.pkl"), "rb"))
    Xr, Xn = TR["Ultra"]
    D = getD("nqdb.npz")
    days = np.array(sorted(set(D.daydate[D.ro >= 0]))); days = days[days >= 20100607]
    atr_d = pd.Series(D.atr, index=D.daydate).groupby(level=0).last().reindex(days).to_numpy()
    Ur = (Xr[Xr.atr >= 150].u * Xr[Xr.atr >= 150].w).groupby(Xr[Xr.atr >= 150].date).sum().reindex(days, fill_value=0.0)
    Un = (Xn.u * Xn.w).groupby(Xn.date).sum().reindex(days, fill_value=0.0)
    PER = (("A", 20100601, 20150101, "norm"), ("B", 20150101, 20200101, "norm"), ("T1", 20200101, 20240101, "real"), ("T2", 20240101, 20991231, "real"))
    rows = []
    for _, r in C.iterrows():
        k = (r.fam, int(r.j))
        if k not in T: continue
        rec = dict(fam=r.fam, j=int(r.j), params=r.params, wr=f"{r.A_wr}/{r.B_wr}/{r.T1_wr}/{r.T2_wr}", pf=f"{r.A_pf}/{r.B_pf}/{r.T1_pf}/{r.T2_pf}",
                   trades_per_year=round(float(r.T1_n) / 4, 1), neighbours=neighbours(R, r))
        for lab, lo, hi, view in PER:
            m = (days >= lo) & (days < hi)
            if view == "real": m &= atr_d >= 150
            tr = T[k][view]; x = tr.groupby("date").usd.sum().reindex(days, fill_value=0.0)
            U = Ur if view == "real" else Un
            rec[lab] = dict(corr=round(float(np.corrcoef(U[m], x[m])[0, 1]), 3), sh_ultra=round(sharpe(U[m]), 2), sh_plus=round(sharpe(U[m] + x[m]), 2),
                            per_month=round(float(x[m].mean() * 21)) if view == "real" else None)
            rec[lab]["dSharpe"] = round(rec[lab]["sh_plus"] - rec[lab]["sh_ultra"], 3)
        rows.append(rec)
        print(json.dumps(rec), flush=True)
    json.dump(rows, open(os.path.join(HERE, "mine_db_robust.json"), "w"), indent=1, default=str)
