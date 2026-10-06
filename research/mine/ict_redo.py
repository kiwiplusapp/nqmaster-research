"""Re-evaluate Ultra with the CORRECTED ICT (ict_fix: fill-then-stop when the bar hits the limit and the sweep extreme).
1) trade-level portfolio metrics (conflict filter) for ICT x2 (as NQMaster), x1, off, original x2 (biased research);
2) adds dense grids 'U:ICTF' (w=2) and 'U1:ICTF' (w=1) to research/tmp/dense/<per>.npz for the account simulations."""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, ".")
from dense_build import dense
from gold_port import conflict_filter
T = pickle.load(open("robust_trades.pkl", "rb")); K = pd.read_pickle("ict_fix_trades.pkl")
RES = os.path.dirname(os.getcwd()); DN = os.path.join(RES, "tmp", "dense")
def ictf(per, w):
    tag = "mnq_fut.npz" if per == "REAL" else "nq_1m.npz"; df = K[(tag, "corregido", 1.0)]
    lo, hi = (20240201, 3e7) if per == "REAL" else ((20200201, 20240101) if per == "IS" else (20240101, 3e7))
    df = df[(df.date >= lo) & (df.date < hi)]
    return pd.DataFrame(dict(date=df.date.to_numpy(), mod="ICT", tin=df.tin.to_numpy(), tout=df.tout.to_numpy(), d=df.d.to_numpy(), u=df.usd.to_numpy(), w=w))
def metrics(F, days):
    x = F.u * F.w; d = x.groupby(F.date).sum().reindex(days, fill_value=0.0)
    return dict(tpd=round(len(F) / len(days), 2), wr=round(100 * (F.u > 0).mean(), 1), pf=round(x[x > 0].sum() / -x[x <= 0].sum(), 3), sharpe=round(d.mean() / d.std() * 252 ** .5, 2), mo=round(d.mean() * 21))
rows = []
for per in ("IS", "C24", "REAL"):
    F, days = T["Ultra"][per]; F = F[["date", "mod", "tin", "tout", "d", "u", "w"]]; rest = F[F["mod"] != "ICT"]
    V = {"ICT original x2 (sesgado)": F, "ICT corregido x2 (NQMaster hoy)": conflict_filter(pd.concat([rest, ictf(per, 2.0)], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True)),
         "ICT corregido x1": conflict_filter(pd.concat([rest, ictf(per, 1.0)], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True)), "sin ICT": rest}
    for nm, X in V.items(): rows.append(dict(per=per, ver=nm, **metrics(X, days)))
    # dense grids for the corrected ICT
    z = dict(np.load(os.path.join(DN, f"{per}.npz")))
    for key, w in (("U:ICTF", 2.0), ("U1:ICTF", 1.0)):
        L, R = dense(ictf(per, w), "nq", per, z["days"]); z[key + "|L"] = L; z[key + "|R"] = R
    np.savez(os.path.join(DN, f"{per}.npz"), **z); print(per, "dense updated", flush=True)
M = pd.DataFrame(rows); pd.set_option("display.width", 220)
print(M.pivot_table(index="ver", columns="per", values=["tpd", "wr", "pf", "sharpe", "mo"], aggfunc="first").to_string())
meta = pickle.load(open(os.path.join(DN, "meta.pkl"), "rb"))
for per in meta: meta[per] = sorted(set(meta[per]) | {"U:ICTF", "U1:ICTF"})
pickle.dump(meta, open(os.path.join(DN, "meta.pkl"), "wb"))
