"""Protocol for the NQ_DRIVE survivors (results_nqdrive.csv, anchors every hour): best-IS config per (A, T, mode) cluster with
IS & C24 PF >= 1.25 and REAL >= 1.15 -> 2015-19 cost-normalised PF, +2/+4 ticks, correlation and Sharpe change vs Ultra + NF05
(conflict filter). -> nqdrive_check.csv"""
import sys, ast, numpy as np, pandas as pd
sys.path.insert(0, ".")
from core import Data, run_events, split_stats
from families_gold import gen_drive
from gold_port import conflict_filter
from gnq_check import U, trades, pf, sharpe, D_is, D_re, D_lg
from news import NEWS
FOMC = set(NEWS["FOMC"])
NF = dict(A=2000, T=540, x=0.35, mode=-1, tf=0, k=0.2, stop=0, R=2.0, hold=240)
def per_slice(df, per):
    lo, hi = (20200201, 20240101) if per == "IS" else ((20240101, 3e7) if per == "C24" else (20240201, 3e7))
    df = df[(df.date >= lo) & (df.date < hi) & ~df.date.isin(FOMC)]
    return pd.DataFrame(dict(date=df.date, mod="X", tin=df.tin, tout=df.tout, d=df.d, u=df.usd, w=1.0))
BASE = {}
for per, D in (("IS", D_is), ("C24", D_is), ("REAL", D_re)):
    nf = per_slice(trades(D, gen_drive, NF, 1), per).assign(mod="NF05"); Ux, days = U[per]
    BASE[per] = (pd.concat([Ux, nf]), days)
if __name__ == "__main__":
    R = pd.read_csv("results_nqdrive.csv")
    ok = R[(R.IS_n >= 100) & (R.C24_n >= 60) & (R.IS_pf >= 1.25) & (R.C24_pf >= 1.25) & (R.REAL_pf >= 1.15)].copy()
    ok["p"] = ok.params.map(ast.literal_eval); ok["key"] = ok.p.map(lambda d: (d["A"], d["T"], d["mode"]))
    reps = ok.sort_values("IS_pf", ascending=False).groupby("key").head(1)
    rows = []
    for r in reps.itertuples():
        p = r.p; row = dict(j=r.j, params=r.params, IS_pf=r.IS_pf, C24_pf=r.C24_pf, REAL_pf=r.REAL_pf, IS_n=r.IS_n, IS_wr=r.IS_wr)
        lg = trades(D_lg, gen_drive, p, 1, slip=0.0, nc=0.00345); s = split_stats("nqhd_long", lg); row["L1519_pf"] = s.get("TR_pf"); row["L1519_n"] = s.get("TR_n")
        for extra in (2, 4): x = trades(D_re, gen_drive, p, 1, slip=0.25 * (1 + extra)); row[f"REAL_slip+{extra}"] = pf(x.usd)
        for per, D in (("IS", D_is), ("C24", D_is), ("REAL", D_re)):
            new = per_slice(trades(D, gen_drive, p, 1), per).assign(mod="NEW"); Bx, days = BASE[per]
            s0, d0 = sharpe(conflict_filter(Bx.sort_values(["date", "tin"]).reset_index(drop=True)), days)
            s1, _ = sharpe(conflict_filter(pd.concat([Bx, new]).sort_values(["date", "tin"]).reset_index(drop=True)), days)
            row[f"{per}_corr"] = round(np.corrcoef(new.groupby("date").u.sum().reindex(days, fill_value=0.0), d0)[0, 1], 3); row[f"{per}_dSh"] = round(s1 - s0, 3)
        rows.append(row); print(row, flush=True)
    O = pd.DataFrame(rows); O.to_csv("nqdrive_check.csv", index=False); pd.set_option("display.width", 300); pd.set_option("display.max_colwidth", 90)
    print(O.to_string(index=False))
