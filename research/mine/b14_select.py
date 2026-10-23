"""Batch 14 selection (2026-10-23, Franklin NY-open bias rule, families14.py). Mined with the default periods:
MINE_TAG=b14 python3 run_mine_db.py FRANKLIN -> results_b14.csv (T1 2020-23 / T2 2024-26 real $ per MNQ; A 2010-14 / B 2015-19 norm).
PROTOCOL (fixed before the portfolio step; no win-rate floor because the rule itself sets none):
  s1 T1 n >= 100, PF >= 1.30 | s2 T2 PF >= 1.20 | s3 A >= 1.00 and B >= 1.00 | s4 T2 with +4 ticks per side ($3.00 per trade) PF >= 1.10
  s5 plateau: >= 2/3 of the one-step numeric neighbours (st, R) with T1 PF >= 1.15 | s6 one representative per signal (lon, cmp, ent):
  best T1 PF | portfolio: b11_select.portfolio_test (ultra_d4 + candidate, conflict_filter; T1p 2020-10-15..2022, T2p 2023..):
  Sharpe up in both, max DD / worst month <= +5%, corr < 0.3.  -> b14_select.json"""
import os, sys, json, pickle, ast, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from b11_select import pf, portfolio_test, cand_frame
from families14 import GRID_FRANKLIN

R = pd.read_csv(os.path.join(HERE, "results_b14.csv")); T = pickle.load(open(os.path.join(HERE, "trades_b14.pkl"), "rb"))
R = R.sort_values("j").reset_index(drop=True); OUT = {"cells": len(R)}
s1 = R[(R.T1_n >= 100) & (R.T1_pf >= 1.30)]; s2 = s1[s1.T2_pf >= 1.20]; s3 = s2[(s2.A_pf >= 1.0) & (s2.B_pf >= 1.0)]
def plus4(j):
    tr = T[("FRANKLIN", j)]["real"]; u = tr.usd[tr.date >= 20240101].to_numpy() - 3.0; return pf(u)
s3 = s3.assign(T2_pf4=[plus4(j) for j in s3.j]); s4 = s3[s3.T2_pf4 >= 1.10]
idx = {repr(g): j for j, g in enumerate(GRID_FRANKLIN)}; pfT1 = dict(zip(R.j, R.T1_pf))
def plateau(j):
    p = GRID_FRANKLIN[j]; nb = []
    for k, vals in (("st", [0.15, 0.25, 0.40]), ("R", [1.0, 2.0, 0.0])):
        if p[k] not in vals: continue
        i = vals.index(p[k])
        for di in (-1, 1):
            if 0 <= i + di < len(vals): q = dict(p); q[k] = vals[i + di]; nb.append(idx[repr(q)])
    ok = [pfT1.get(x, 0) >= 1.15 for x in nb]
    return len(nb) >= 2 and np.mean(ok) >= 2 / 3
s5 = s4[[plateau(j) for j in s4.j]]
s5 = s5.assign(sig=[repr({k: GRID_FRANKLIN[j][k] for k in ("lon", "cmp", "ent")}) for j in s5.j])
s6 = s5.sort_values("T1_pf", ascending=False).groupby("sig").head(1)
OUT["stages"] = dict(s1=len(s1), s2=len(s2), s3=len(s3), s4=len(s4), s5=len(s5), s6=len(s6))
OUT["base_rate_T2"] = round(float((R.T2_pf >= 1.2).mean()), 3); OUT["P_T2_given_T1"] = round(float((s1.T2_pf >= 1.2).mean()), 3)
cols = ["j", "params", "T1_n", "T1_wr", "T1_pf", "T2_n", "T2_wr", "T2_pf", "T2_pf4", "A_pf", "B_pf"]
OUT["survivors"] = s6[cols].to_dict("records")
print(OUT["stages"], "base", OUT["base_rate_T2"], "P(T2|T1)", OUT["P_T2_given_T1"]); print(s6[cols].to_string())
OUT["portfolio"] = []
for r in s6.itertuples():
    tr = T[("FRANKLIN", r.j)]["real"]; c = cand_frame(tr, f"FRK{r.j}")
    res = portfolio_test([c], f"FRANKLIN #{r.j}"); OUT["portfolio"].append(res)
    print(r.j, "corr", res.get("corr"), "delta", res.get("delta"), flush=True)
json.dump(OUT, open(os.path.join(HERE, "b14_select.json"), "w"), indent=1, default=str)
