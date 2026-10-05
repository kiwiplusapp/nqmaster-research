"""Robustness lab, step 1: trade sets for the profiles under audit (1-lot units, FOMC skipped, $1.90 RT + 1 tick slippage).
Ultra (eval profile), WR70Plus (funded profile), Core6 (only the modules that survived 11 years, default variants, no filters).
Periods: IS = CFD 2020-23, C24 = CFD 2024-26, REAL = MNQ futures 2024-26. Output robust_trades.pkl {prof: {per: (F, days)}}."""
import os, sys, pickle, ast, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
import final_pkg
from final_pkg import pkg_base, base, cand_trades, conflict_filter, get
from families2 import FAMILIES2
from core import Data, run_events
exec(open("wr70_eval.py").read().split("rows = []")[0])          # build(), CANDS, A
def gtr(ps):
    gen, grid, md = FAMILIES2["VOL_BREAK"]; p = ast.literal_eval(ps); out = {}
    for key, nm in (("nq", "nq_1m.npz"), ("mnq", "mnq_fut.npz")):
        D = final_pkg._D.get(key) or Data(nm); final_pkg._D[key] = D
        df = run_events(D, gen(D, p), flat=955, maxday=md); df["tin"] = D.sm[df.fi.to_numpy().astype(int)]; df["tout"] = D.sm[df.xi.to_numpy().astype(int)] + 1
        out[key] = df[["date", "usd", "tin", "tout", "d"]]
    return out
VW = get("CLOCK_ANCHOR", "{'anc': 'VWAP', 'T': 1300, 'x': 0.3, 'mode': 1, 's': 0.15, 'R': 0.5, 'tg': 0, 'tf': 1, 'hold': 120}")
VB = gtr("{'k': 0.45, 's': 0.35, 'R': 2.0, 'tf': 0, 'w1': 1500, 'hold': 400, 'stop': 0}")
COLS = ["date", "mod", "tin", "tout", "d", "u", "w"]
OUT = {"Ultra": {}, "WR70Plus": {}, "Core6": {}}
for per in ("IS", "C24", "REAL"):
    days = np.array(base(per)[1])
    U = conflict_filter(pd.concat([pkg_base(per, True), cand_trades(VW, per, "VW13", 1.0), cand_trades(VB, per, "VOLB", 1.0)], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True))
    OUT["Ultra"][per] = (U[COLS].reset_index(drop=True), days)
for tag, lo in (("nq_1m", 20200201), ("mnq_fut", 20240201)):
    X = build(tag, CANDS["WR70-A"], True); X = X[X.date >= lo]
    alld = np.array(sorted(A[tag][(A[tag].date >= lo)].date.unique()))
    core = {"ICT": 1.0, "MSEQ": 0.5, "CRT11": 2.0, "LON": 2.0, "ORB60": 0.6, "VOLB_tf0": 2.0}
    C = A[tag]; C = pd.concat([C[(C["mod"] == m) & (C["var"] == v)] for m, v in core.items()], ignore_index=True); C = C[C.date >= lo]
    C = conflict_filter(C.sort_values(["date", "tin"]).reset_index(drop=True))
    parts = (("IS", 0, 20240101), ("C24", 20240101, 3e7)) if tag == "nq_1m" else (("REAL", 0, 3e7),)
    for per, a, b in parts:
        days = alld[(alld >= a) & (alld < b)]
        OUT["WR70Plus"][per] = (X[(X.date >= a) & (X.date < b)][COLS].reset_index(drop=True), days)
        OUT["Core6"][per] = (C[(C.date >= a) & (C.date < b)][COLS].reset_index(drop=True), days)
pickle.dump(OUT, open("robust_trades.pkl", "wb"))
for p, d in OUT.items():
    for per, (F, days) in d.items():
        x = F.u * F.w; dd = x.groupby(F.date).sum().reindex(days, fill_value=0)
        print(p, per, len(F), "tpd", round(len(F) / len(days), 2), "WR", round(100 * (F.u > 0).mean(), 1), "PF", round(x[x > 0].sum() / -x[x <= 0].sum(), 3), "Sharpe", round(dd.mean() / dd.std() * 252 ** .5, 2), "$/mo", round(dd.mean() * 21))
