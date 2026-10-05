"""Finer lifecycle grid around the robust zone + surface smoothness. Ranking uses the WORST period (min of IS / C24 / REAL $/month),
so a policy only scores well if it works in calm 2020-23 and in volatile 2024-26."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
from acct_life import run_life, CFG
pd.set_option("display.width", 300); pd.set_option("display.max_rows", 300)
PER = ("IS", "C24", "REAL")
EVAL = {"Ultra": (("ULTRA",) * 3, 0, 0, 0.0), "FULL": (("FULL",) * 3, 0, 0, 0.0), "FULLG": (("FULLG",) * 3, 0, 0, 0.0)}
for C in (300, 600, 900):
    for DL in (0.0, 1000.0):
        EVAL[f"S<{C}<=FG DL{int(DL)}"] = (("SAFE", "SAFE", "FULLG"), C, C, DL)
FUND = {}
for c1 in (500, 750, 1000, 1250, 1500):
    for hi in ("FULL", "FULLG"):
        FUND[f"S<{c1}<={hi}"] = (("SAFE", "SAFE", hi), c1, c1, 0.0)
    FUND[f"S<{c1}<=NOB<{c1 + 1500}<=FULL"] = (("SAFE", "NOB", "FULL"), c1, c1 + 1500, 0.0)
FUND["Ultra"] = (("ULTRA",) * 3, 0, 0, 0.0)
rows = []
for en in ("Ultra", "FULLG", "S<600<=FG DL0", "S<600<=FG DL1000", "S<300<=FG DL0"):
    for fn, fu in FUND.items():
        for X in (3000.0, 4000.0, 5000.0, 6000.0):
            r = dict(eval=en, fund=fn, X=X)
            for per in PER: r.update({f"{per}_{k}": v for k, v in run_life(per, EVAL[en], fu, 0.0, X).items()})
            rows.append(r)
    print(en, flush=True)
G = pd.DataFrame(rows); G["worst_mo"] = G[[f"{p}_mo" for p in PER]].min(axis=1); G["mean_mo"] = G[[f"{p}_mo" for p in PER]].mean(axis=1)
G["worst_p10"] = G[[f"{p}_p10" for p in PER]].min(axis=1); G.to_csv("acct_life2.csv", index=False)
cols = ["eval", "fund", "X", "worst_mo", "mean_mo", "worst_p10"] + [f"{p}_{k}" for k in ("mo", "fbust") for p in PER]
print(G.sort_values("worst_mo", ascending=False)[cols].head(30).to_string(index=False))
print("\nsurface (eval S<600<=FG DL0, fund S<c1<=FULL): worst-period $/month by c1 x X")
s = G[(G["eval"] == "S<600<=FG DL0") & G.fund.str.match(r"S<\d+<=FULL$")].copy(); s["c1"] = s.fund.str.extract(r"S<(\d+)").astype(int)
print(s.pivot_table(index="c1", columns="X", values="worst_mo").to_string())
print(s.pivot_table(index="c1", columns="X", values="mean_mo").to_string())
print("BASE:"); print(G[(G["eval"] == "Ultra") & (G.fund == "Ultra") & (G.X == 5000.0)][cols].to_string(index=False))
