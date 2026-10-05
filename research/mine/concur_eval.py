"""Does a cap on simultaneous open positions (units) raise the Apex 50K eval pass rate (open-equity trailing) for Ultra?
First-come: a trade is skipped if the open units at its entry minute + its own weight exceed K. Policy = recommended EvalMode
(2 lots, 3 from session 12 if < $2,000, DLL $800) and fixed 2."""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
import final_pkg
from final_pkg import pkg_base, base, cand_trades, conflict_filter, get
from families2 import FAMILIES2
from core import Data, run_events
from evalpol import stats_pol
from apex50_stats import pa_runs
import ast
def gtr(ps):
    gen, grid, md = FAMILIES2["VOL_BREAK"]; p = ast.literal_eval(ps); out = {}
    for key, nm in (("nq", "nq_1m.npz"), ("mnq", "mnq_fut.npz")):
        D = final_pkg._D.get(key) or Data(nm); final_pkg._D[key] = D
        df = run_events(D, gen(D, p), flat=955, maxday=md); df["tin"] = D.sm[df.fi.to_numpy().astype(int)]; df["tout"] = D.sm[df.xi.to_numpy().astype(int)] + 1
        out[key] = df[["date", "usd", "tin", "tout", "d"]]
    return out
VW = get("CLOCK_ANCHOR", "{'anc': 'VWAP', 'T': 1300, 'x': 0.3, 'mode': 1, 's': 0.15, 'R': 0.5, 'tg': 0, 'tf': 1, 'hold': 120}")
VB = gtr("{'k': 0.45, 's': 0.35, 'R': 2.0, 'tf': 0, 'w1': 1500, 'hold': 400, 'stop': 0}")
os.chdir(RES)
from pa_subsets import build as bpath
def cap(F, K):
    if K is None: return F
    keep = []
    for d, g in F.groupby("date", sort=False):
        open_ = []
        for r in g.itertuples():
            open_ = [(t, w) for t, w in open_ if t > r.tin]
            u = sum(w for _, w in open_)
            if u + r.w <= K: keep.append(r.Index); open_.append((r.tout, r.w))
    return F.loc[keep]
rows = []
for K in (None, 4, 3, 2, 1):
    r = dict(K=K or "sin tope")
    for per in ("IS", "C24", "REAL"):
        tag = "mnq_fut" if per == "REAL" else "nq_1m"; days = base(per)[1]
        PU = conflict_filter(pd.concat([pkg_base(per, True), cand_trades(VW, per, "VW13", 1.0), cand_trades(VB, per, "VOLB", 1.0)], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True))
        PU = cap(PU, K); Q = bpath(tag, PU, days)
        x = PU.u * PU.w; dd = x.groupby(PU.date).sum().reindex(days, fill_value=0)
        p, b, p14, du = stats_pol(Q["day"], Q["fav"], Q["adv"], Q["rel"], Q["ndays"], 3000.0, 2500.0, 21, 2, 0.0, 2, 0.0, 2, 12, 2000.0, 3, 800.0, 0.0)
        p2, b2, _, _ = stats_pol(Q["day"], Q["fav"], Q["adv"], Q["rel"], Q["ndays"], 3000.0, 2500.0, 21, 2, 0.0, 2, 0.0, 2, 99, 0.0, 2, 0.0, 0.0)
        pa = pa_runs(Q, 1, 0.0, 400.0); full = pa[~pa.truncated]
        r.update({f"{per}_tpd": round(len(PU) / len(days), 2), f"{per}_pf": round(x[x > 0].sum() / -x[x <= 0].sum(), 3), f"{per}_mo": round(dd.mean() * 21),
                  f"{per}_pass_pol": round(100 * p, 1), f"{per}_bust_pol": round(100 * b, 1), f"{per}_pass_k2": round(100 * p2, 1), f"{per}_PA_Ecash": round(full.cash.mean())})
    rows.append(r); print(r, flush=True)
G = pd.DataFrame(rows); G.to_csv(os.path.join(RES, "mine", "concur_eval.csv"), index=False); pd.set_option("display.width", 300)
for k in ("tpd", "pf", "mo", "pass_pol", "bust_pol", "pass_k2", "PA_Ecash"):
    print(k); print(G[["K"] + [f"{p}_{k}" for p in ("IS", "C24", "REAL")]].to_string(index=False))
