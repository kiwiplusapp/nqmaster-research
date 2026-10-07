"""Overnight NQ modules from the gold G_DRIVE family (gnq_check.py: add Sharpe in IS / C24 / REAL, robust to +4 ticks, 2015-19 PF > 1):
  NF05   (G_DRIVE 2836): 20:00 -> 05:00 move >= 0.35 ATR -> FADE, any direction, stop 0.2 ATR, target 2R, max 240 min   (2015-19 PF 1.61)
  LF0315 (G_DRIVE 2933): 03:00 -> 03:15 move >= 0.10 ATR -> FADE, any direction, stop 0.2 ATR, target 2R, max 600 min   (2015-19 PF 1.15)
  NM22   (G_DRIVE 2130): 20:00 -> 22:00 move >= 0.20 ATR -> continuation, any direction, stop beyond the window extreme (cap 0.35 ATR),
         target 0.5R, max 240 min (2015-19 PF 1.09)
1) trade-level portfolio metrics with Ultra (conflict filter), 2) dense grids N:NF05 / N:LF0315 / N:NM22 for the account sims,
3) lifecycle $/month per account: 50K (eval 2c / funded 2c) and 150K (eval 6c / funded 3c), history / +1 tick / 1,000 bootstrap years."""
import os, sys, ast, pickle, numpy as np, pandas as pd
sys.path.insert(0, ".")
from core import Data, run_events
from run_mine import FAMILIES
from gold_port import conflict_filter
from gnq_check import ultra, U
from news import NEWS
from dense_build import dense
FOMC = set(NEWS["FOMC"])
NEW = {"NF05": ("G_DRIVE", 2836), "LF0315": ("G_DRIVE", 2933), "NM22": ("G_DRIVE", 2130)}
R = pd.read_csv("results_gnq.csv")
Dn, Dr = Data("nq_1m.npz"), Data("mnq_fut.npz")
def new_trades(per, name):
    fam, j = NEW[name]; gen, grid, md = FAMILIES[fam]; p = ast.literal_eval(R[(R.fam == fam) & (R.j == j)].params.iat[0])
    D = Dr if per == "REAL" else Dn
    df = run_events(D, gen(D, p), flat=955, maxday=md, slip=0.25); df["tin"] = D.sm[df.fi.to_numpy().astype(int)]; df["tout"] = D.sm[df.xi.to_numpy().astype(int)] + 1
    lo, hi = (20200201, 20240101) if per == "IS" else ((20240101, 3e7) if per == "C24" else (20240201, 3e7))
    df = df[(df.date >= lo) & (df.date < hi) & ~df.date.isin(FOMC)]
    return pd.DataFrame(dict(date=df.date.to_numpy(), mod=name, tin=df.tin.to_numpy(), tout=df.tout.to_numpy(), d=df.d.to_numpy(), u=df.usd.to_numpy(), w=1.0))
NT = {(per, n): new_trades(per, n) for per in ("IS", "C24", "REAL") for n in NEW}
def metrics(X, days):
    x = X.u * X.w; d = x.groupby(X.date).sum().reindex(days, fill_value=0.0)
    return dict(tpd=round(len(X) / len(days), 2), wr=round(100 * (X.u > 0).mean(), 1), pf=round(x[x > 0].sum() / -x[x <= 0].sum(), 3), sharpe=round(d.mean() / d.std() * 252 ** .5, 2), mo=round(d.mean() * 21))
rows = []
combos = {"Ultra": [], "+NF05": ["NF05"], "+LF0315": ["LF0315"], "+NM22": ["NM22"], "+NF05+LF0315": ["NF05", "LF0315"], "+NF05+LF0315+NM22": ["NF05", "LF0315", "NM22"]}
for per in ("IS", "C24", "REAL"):
    Ux, days = U[per]
    for nm, add in combos.items():
        X = conflict_filter(pd.concat([Ux] + [NT[(per, a)] for a in add]).sort_values(["date", "tin"]).reset_index(drop=True))
        rows.append(dict(per=per, set=nm, **metrics(X, days)))
    for n in NEW:
        x = NT[(per, n)]; rows.append(dict(per=per, set="solo " + n, **metrics(x, days)))
M = pd.DataFrame(rows); pd.set_option("display.width", 250)
print(M.pivot_table(index="set", columns="per", values=["tpd", "wr", "pf", "sharpe", "mo"], aggfunc="first").to_string(), flush=True)
M.to_csv("gnq_port.csv", index=False)
# ---- dense grids (append; builders are import-safe now)
RES = os.path.dirname(os.getcwd()); DN = os.path.join(RES, "tmp", "dense")
meta = pickle.load(open(os.path.join(DN, "meta.pkl"), "rb"))
for per in ("IS", "C24", "REAL"):
    z = dict(np.load(os.path.join(DN, f"{per}.npz")))
    for n in NEW:
        L, Rr = dense(NT[(per, n)], "nq", per, z["days"]); z["N:" + n + "|L"] = L; z["N:" + n + "|R"] = Rr
    np.savez(os.path.join(DN, f"{per}.npz"), **z); meta[per] = sorted(set(meta[per]) | {"N:" + n for n in NEW}); print(per, "dense +", list(NEW), flush=True)
pickle.dump(meta, open(os.path.join(DN, "meta.pkl"), "wb"))
