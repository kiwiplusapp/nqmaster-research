import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from port_test import base, cand_trades, metrics, conflict_filter
R1 = pd.read_csv("results_b1.csv"); R2 = pd.read_csv("results_b2.csv")
TR = {**pickle.load(open("trades_b1.pkl", "rb")), **pickle.load(open("trades_b2.pkl", "rb"))}
def get(R, fam, ps): return TR[(fam, int(R[(R.fam == fam) & (R.params == ps)].j.iloc[0]))]
VOLB = get(R2, "VOL_BREAK", "{'k': 0.45, 's': 0.35, 'R': 2.0, 'tf': 1, 'w1': 1500, 'hold': 400, 'stop': 0}")
VOLB50 = get(R2, "VOL_BREAK", "{'k': 0.45, 's': 0.35, 'R': 50.0, 'tf': 1, 'w1': 1500, 'hold': 400, 'stop': 0}")
SOPEN = get(R1, "CLOCK_ANCHOR", "{'anc': 'SOPEN', 'T': 800, 'x': 0.35, 'mode': 1, 's': 0.25, 'R': 0.5, 'tg': 0, 'tf': 1, 'hold': 330}")
VW13 = get(R1, "CLOCK_ANCHOR", "{'anc': 'VWAP', 'T': 1300, 'x': 0.15, 'mode': 1, 's': 0.15, 'R': 0.5, 'tg': 0, 'tf': 1, 'hold': 120}")
sel = pickle.load(open("filt_sel.pkl", "rb")); BF = pickle.load(open("base_feats.pkl", "rb"))
def boosted_base(per):
    F = BF[per][0].copy(); b = pd.Series(1.0, index=F.index)
    for r, k in sel:
        if k != "boost": continue
        x = F[r["feat"]]; m = (F["mod"] == r["mod"]) & ((x < r["hi"]) if r["bucket"].startswith("low") else (x >= r["lo"]))
        b[m.fillna(False)] = 2.0
    F["w"] = F.w * b; return F[["date", "mod", "tin", "tout", "d", "u", "w"]]
def run(per, cands, boost=False, period=None):
    B, days = base(per)
    if boost: B = boosted_base(per)
    parts = [B] + [cand_trades(tr, per, nm, w) for nm, tr, w in cands]
    A = pd.concat(parts, ignore_index=True)
    if cands: A = conflict_filter(A.sort_values(["date", "tin"]).reset_index(drop=True))
    if period == "2024-25": A = A[A.date < 20260101]; days = days[days < 20260101]
    if period == "2026": A = A[A.date >= 20260101]; days = days[days >= 20260101]
    return metrics(A, days)
COMBOS = {"base": ([], False), "+VOLB": ([("VOLB", VOLB, 1.0)], False), "+VOLB(no tgt)": ([("VOLB", VOLB50, 1.0)], False),
          "+SOPEN+VW13": ([("SOPEN", SOPEN, 1.0), ("VW13", VW13, 1.0)], False),
          "+VOLB+SOPEN+VW13": ([("VOLB", VOLB, 1.0), ("SOPEN", SOPEN, 1.0), ("VW13", VW13, 1.0)], False),
          "boosts": ([], True), "boosts+VOLB+SOPEN+VW13": ([("VOLB", VOLB, 1.0), ("SOPEN", SOPEN, 1.0), ("VW13", VW13, 1.0)], True)}
rows = []
for per, period in (("IS", None), ("C24", "2024-25"), ("REAL", "2024-25"), ("C24", "2026"), ("REAL", "2026")):
    for nm, (cands, bo) in COMBOS.items():
        r = run(per, cands, bo, period); r.update(per=f"{per} {period or '2020-23'}", combo=nm); rows.append(r)
g = pd.DataFrame(rows); pd.set_option("display.width", 250)
order = ["IS 2020-23", "C24 2024-25", "REAL 2024-25", "C24 2026", "REAL 2026"]
for c in ("wr", "pf", "sharpe", "mo", "maxdd", "tpd"):
    print(c); print(g.pivot(index="combo", columns="per", values=c).reindex(list(COMBOS))[order].to_string())
