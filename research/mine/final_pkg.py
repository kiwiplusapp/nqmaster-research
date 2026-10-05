import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from port_test import base, cand_trades, metrics, conflict_filter
R1 = pd.read_csv("results_b1.csv"); TR = pickle.load(open("trades_b1.pkl", "rb"))
from core import Data, run_events
from families import FAMILIES
import ast
_D = {}
def get(fam, ps):
    gen, grid, md = FAMILIES[fam]; p = ast.literal_eval(ps); out = {}
    for key, nm in (("nq", "nq_1m.npz"), ("mnq", "mnq_fut.npz")):
        if key not in _D: _D[key] = Data(nm)
        D = _D[key]; df = run_events(D, gen(D, p), flat=955, maxday=md)
        df["tin"] = D.sm[df.fi.to_numpy().astype(int)]; df["tout"] = D.sm[df.xi.to_numpy().astype(int)] + 1
        out[key] = df[["date", "usd", "tin", "tout", "d"]]
    return out
VW13a = get("CLOCK_ANCHOR", "{'anc': 'VWAP', 'T': 1300, 'x': 0.3, 'mode': 1, 's': 0.15, 'R': 0.5, 'tg': 0, 'tf': 1, 'hold': 120}")
VW13b = get("CLOCK_ANCHOR", "{'anc': 'VWAP', 'T': 1300, 'x': 0.15, 'mode': 1, 's': 0.15, 'R': 0.5, 'tg': 0, 'tf': 1, 'hold': 120}")
sel = pickle.load(open("filt_sel.pkl", "rb")); BF = pickle.load(open("base_feats.pkl", "rb"))
def pkg_base(per, cap):
    F = BF[per][0].copy(); b = pd.Series(1.0, index=F.index); keep = pd.Series(True, index=F.index)
    for r, k in sel:
        x = F[r["feat"]]; m = ((F["mod"] == r["mod"]) & ((x < r["hi"]) if r["bucket"].startswith("low") else (x >= r["lo"]))).fillna(False)
        if k == "boost": b[m] = 2.0
        else: keep &= ~m
    w = F.w * b
    if cap: w = np.minimum(w, np.maximum(F.w, 2.0))       # never above x2 of the 1-unit size (ICT keeps its x2)
    F["w"] = w; return F[keep][["date", "mod", "tin", "tout", "d", "u", "w"]]
def run(per, cap, vw, period=None, rules=True):
    if rules: B = pkg_base(per, cap); days = base(per)[1]
    else: B, days = base(per)
    A = B
    if vw is not None:
        A = conflict_filter(pd.concat([B, cand_trades(vw, per, "VW13", 1.0)], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True))
    if period == "2024-25": A = A[A.date < 20260101]; days = days[days < 20260101]
    if period == "2026": A = A[A.date >= 20260101]; days = days[days >= 20260101]
    return metrics(A, days)
if __name__ == "__main__":
    C = {"base (MaxPlus+conf)": dict(rules=False, cap=False, vw=None), "reglas (sin tope)": dict(rules=True, cap=False, vw=None), "reglas (tope x2)": dict(rules=True, cap=True, vw=None),
         "reglas tope x2 + VW13 x0.30": dict(rules=True, cap=True, vw=VW13a), "reglas tope x2 + VW13 x0.15": dict(rules=True, cap=True, vw=VW13b)}
    rows = []
    for per, period in (("IS", None), ("C24", None), ("REAL", None), ("C24", "2026"), ("REAL", "2026")):
        for nm, kw in C.items():
            r = run(per, kw["cap"], kw["vw"], period, kw["rules"]); r.update(per=f"{per} {period or 'all'}", combo=nm); rows.append(r)
    g = pd.DataFrame(rows); pd.set_option("display.width", 250)
    order = ["IS all", "C24 all", "REAL all", "C24 2026", "REAL 2026"]
    for c in ("wr", "pf", "sharpe", "mo", "maxdd", "tpd"):
        print(c); print(g.pivot(index="combo", columns="per", values=c).reindex(list(C))[order].to_string())
