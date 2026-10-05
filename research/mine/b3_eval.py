"""Apex 50K impact of the batch-3 modules (ENGULF_4H, EMA9_VWAP) on the eval profile (Ultra, recommended policy) and the
funded profile (WR70Plus, 1 lot, DLL 400). Minute-path eval/PA simulation identical to evalpol.py / apex50_stats.py."""
import os, sys, pickle, ast, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
import final_pkg
from final_pkg import pkg_base, base, cand_trades, conflict_filter, get
from families2 import FAMILIES2
from families3 import FAMILIES3
from core import Data, run_events
from evalpol import stats_pol
from apex50_stats import pa_runs
exec(open("wr70_eval.py").read().split("rows = []")[0])          # build(), CANDS, A (WR70Plus pipeline)
from news import NEWS
def gtr(fams, fam, j=None, ps=None):
    gen, grid, md = fams[fam]; p = grid[j] if j is not None else ast.literal_eval(ps); out = {}
    for key, nm in (("nq", "nq_1m.npz"), ("mnq", "mnq_fut.npz")):
        D = final_pkg._D.get(key) or Data(nm); final_pkg._D[key] = D
        df = run_events(D, gen(D, p), flat=955, maxday=md); df["tin"] = D.sm[df.fi.to_numpy().astype(int)]; df["tout"] = D.sm[df.xi.to_numpy().astype(int)] + 1
        out[key] = df[["date", "usd", "tin", "tout", "d"]]
    return out
VW = get("CLOCK_ANCHOR", "{'anc': 'VWAP', 'T': 1300, 'x': 0.3, 'mode': 1, 's': 0.15, 'R': 0.5, 'tg': 0, 'tf': 1, 'hold': 120}")
VB = gtr(FAMILIES2, "VOL_BREAK", ps="{'k': 0.45, 's': 0.35, 'R': 2.0, 'tf': 0, 'w1': 1500, 'hold': 400, 'stop': 0}")
NEW = {f"{f}#{j}": gtr(FAMILIES3, f, j) for f, j in (("ENGULF_4H", 253), ("ENGULF_4H", 349), ("ENGULF_4H", 411), ("EMA9_VWAP", 679), ("EMA9_VWAP", 721))}
os.chdir(RES)
from pa_subsets import build as bpath
def ultra_paths(extra):
    P = {}
    for per in ("IS", "C24", "REAL"):
        tag = "mnq_fut" if per == "REAL" else "nq_1m"; days = base(per)[1]
        parts = [pkg_base(per, True), cand_trades(VW, per, "VW13", 1.0), cand_trades(VB, per, "VOLB", 1.0)] + [cand_trades(NEW[x], per, x, 1.0) for x in extra]
        PU = conflict_filter(pd.concat(parts, ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True))
        P[per] = bpath(tag, PU, days)
    return P
def wr70_paths(extra):
    P = {}
    for tag, lo in (("nq_1m", 20200201), ("mnq_fut", 20240201)):
        X = build(tag, CANDS["WR70-A"], True)[["date", "mod", "tin", "tout", "d", "u", "w"]]
        for x in extra:
            df = NEW[x]["mnq" if tag == "mnq_fut" else "nq"]; df = df[~df.date.isin(NEWS["FOMC"])]
            X = pd.concat([X, pd.DataFrame(dict(date=df.date, mod=x, tin=df.tin, tout=df.tout, d=df.d, u=df.usd - 0.9, w=1.0))], ignore_index=True)
        if extra: X = conflict_filter(X.sort_values(["date", "tin"]).reset_index(drop=True))
        X = X[X.date >= lo]; alld = np.array(sorted(A[tag][(A[tag].date >= lo)].date.unique()))
        for per, m, days in ((("IS", X.date < 20240101, alld[alld < 20240101]), ("C24", X.date >= 20240101, alld[alld >= 20240101])) if tag == "nq_1m" else (("REAL", X.date >= 0, alld),)):
            P[per] = bpath(tag, X[m], days)
    return P
rows = []
for prof, fn, extras in (("Ultra", ultra_paths, ([], ["ENGULF_4H#253"], ["ENGULF_4H#349"], ["ENGULF_4H#253", "EMA9_VWAP#679"], ["ENGULF_4H#411", "EMA9_VWAP#721"])),
                         ("WR70Plus", wr70_paths, ([], ["ENGULF_4H#253"], ["ENGULF_4H#411"], ["ENGULF_4H#411", "EMA9_VWAP#721"], ["ENGULF_4H#253", "EMA9_VWAP#679"]))):
    for ex in extras:
        P = fn(ex); r = dict(prof=prof, add="+".join(ex) or "BASE")
        for per in ("IS", "C24", "REAL"):
            Q = P[per]
            p, b, p14, du = stats_pol(Q["day"], Q["fav"], Q["adv"], Q["rel"], Q["ndays"], 3000.0, 2500.0, 21, 2, 0.0, 2, 0.0, 2, 12, 2000.0, 3, 800.0, 0.0)
            p2, b2, p142, du2 = stats_pol(Q["day"], Q["fav"], Q["adv"], Q["rel"], Q["ndays"], 3000.0, 2500.0, 21, 2, 0.0, 2, 0.0, 2, 99, 0.0, 2, 0.0, 0.0)
            pa = pa_runs(Q, 1, 0.0, 400.0); full = pa[~pa.truncated]
            r.update({f"{per}_pass_pol": round(100 * p, 1), f"{per}_p14_pol": round(100 * p14, 1), f"{per}_pass_k2": round(100 * p2, 1),
                      f"{per}_PA_Ecash": round(full.cash.mean()), f"{per}_PA_bust": round(100 * (full.status == -1).mean(), 1), f"{per}_PA_any": round(100 * (full.n >= 1).mean(), 1)})
        rows.append(r); print(r, flush=True)
G = pd.DataFrame(rows); G.to_csv(os.path.join(RES, "mine", "b3_eval.csv"), index=False); pd.set_option("display.width", 300)
for k in ("pass_pol", "p14_pol", "pass_k2", "PA_Ecash", "PA_bust", "PA_any"):
    print(k); print(G[["prof", "add"] + [f"{p}_{k}" for p in ("IS", "C24", "REAL")]].to_string(index=False))
