"""Validate the oil candidates (IS & C24 PF >= 1.2) on WTI 2011-2019 (histdata), cost-normalised to the 2024-26 cost/ATR ratio."""
import sys, ast, numpy as np, pandas as pd
sys.path.insert(0, ".")
from core import Data, run_events, split_stats
from run_mine import FAMILIES
R = pd.read_csv("results_oil.csv"); ok = R[(R.IS_n >= 100) & (R.C24_n >= 60) & (R.IS_pf >= 1.15) & (R.C24_pf >= 1.15)]
D = Data("wti_long.npz"); A = D.atr[D.atr > 0]; dd = D.daydate[D.atr > 0]
ratio = 3.9 / (4 * np.median(A[dd >= 20240101])); print("2024-26 cost ratio (ATR units): %.4f" % ratio)
rows = []
for r in ok.itertuples():
    gen, grid, md = FAMILIES[r.fam]; p = ast.literal_eval(r.params)
    df = run_events(D, gen(D, p), flat=1010, maxday=md, slip=0.0, norm_cost=ratio)
    s = split_stats("wti_long", df); rows.append(dict(fam=r.fam, j=r.j, params=r.params, IS_pf=r.IS_pf, C24_pf=r.C24_pf, G1_n=s["G1_n"], G1_pf=s["G1_pf"], G2_n=s["G2_n"], G2_pf=s["G2_pf"]))
pd.set_option("display.width", 250); print(pd.DataFrame(rows).sort_values("G2_pf", ascending=False).to_string(index=False))
