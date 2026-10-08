"""S&P (MES) candidates from the full miner run (results_es.csv: IS = CFD 2020-23, C24 = CFD 2024-26, both PF >= 1.2, n >= 80/50)
-> robustness filter like the NQ night modules:
  2015-19 cost-normalised (es_long.npz, cost = 1.274% of daily ATR = the 2024-26 MES cost share) PF >= 1.1,
  +4 ticks per side (slip 1.25 points) on 2020-23 and 2024-26 PF >= 1.1.
-> es_check.csv (all candidates with the extra columns), trades of survivors in es_survivors.pkl"""
import sys, ast, pickle, numpy as np, pandas as pd
sys.path.insert(0, ".")
from core import Data, run_events, split_stats
from run_mine import FAMILIES

def pf(u):
    u = np.asarray(u); gl = -u[u <= 0].sum(); return round(u[u > 0].sum() / gl, 3) if gl > 0 else np.nan

if __name__ == "__main__":
    R = pd.read_csv("results_es.csv")
    C = R[(R.IS_n >= 80) & (R.C24_n >= 50) & (R.IS_pf >= 1.2) & (R.C24_pf >= 1.2)].copy()
    print(len(C), "candidates", flush=True)
    DL = Data("es_long.npz"); DH = Data("es_hd.npz"); rows = []; keep = {}
    for r in C.itertuples():
        gen, grid, maxday = FAMILIES[r.fam]; p = grid[r.j]
        a = run_events(DL, gen(DL, p), flat=955, maxday=maxday, slip=0.0, norm_cost=0.01274)
        tr = a[a.date < 20200101].usd; t1 = a[(a.date >= 20200201) & (a.date < 20240101)].usd; t2 = a[a.date >= 20240101].usd
        b = run_events(DH, gen(DH, p), flat=955, maxday=maxday, slip=1.25)
        s1 = b[(b.date >= 20200201) & (b.date < 20240101)].usd; s2 = b[b.date >= 20240101].usd
        row = dict(fam=r.fam, j=r.j, params=r.params, IS_pf=r.IS_pf, C24_pf=r.C24_pf, IS_wr=r.IS_wr, C24_wr=r.C24_wr, IS_n=r.IS_n, C24_n=r.C24_n,
                   TR_n=len(tr), TR_pf=pf(tr), T1n_pf=pf(t1), T2n_pf=pf(t2), IS4_pf=pf(s1), C244_pf=pf(s2))
        row["ok"] = bool(row["TR_n"] >= 60 and (row["TR_pf"] or 0) >= 1.1 and (row["IS4_pf"] or 0) >= 1.1 and (row["C244_pf"] or 0) >= 1.1)
        rows.append(row)
        if row["ok"]:
            d = run_events(DH, gen(DH, p), flat=955, maxday=maxday, slip=0.25)
            d["tin"] = DH.sm[d.fi.to_numpy().astype(int)]; d["tout"] = DH.sm[d.xi.to_numpy().astype(int)] + 1
            keep[(r.fam, r.j)] = d[["date", "usd", "tin", "tout", "d"]]
    X = pd.DataFrame(rows); X.to_csv("es_check.csv", index=False); pickle.dump(keep, open("es_survivors.pkl", "wb"))
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 120)
    print(X.sort_values(["ok", "TR_pf"], ascending=False)[["fam", "j", "IS_pf", "C24_pf", "TR_n", "TR_pf", "IS4_pf", "C244_pf", "IS_wr", "C24_wr", "ok", "params"]].head(40).to_string(index=False))
    print("survivors:", int(X.ok.sum()))
