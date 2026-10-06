"""Contracts per module in each phase (Lucid Flex 50K), EQ2-style gating with cushion thresholds scaled by the size.
Eval: FULLG (Ultra + gold Robust) at ek contracts. Funded: SAFE < 750*fk <= NOB < 1500*fk <= FULL at fk contracts, payout at X.
Ranked by the WORST period $/month per account slot (12-month lifecycle, fees included)."""
import sys, itertools, numpy as np, pandas as pd
sys.path.insert(0, ".")
from acct_size import life_g, eval_stats
from acct_life import stack
pd.set_option("display.width", 260); pd.set_option("display.max_rows", 200)
T, D, Q, CAP, FEE = 3000.0, 2000.0, 150.0, 2000.0, 105.2
rows = []
ARR = {}
for per in ("IS", "C24", "REAL"):
    ARR[per] = (stack(per, ("FULLG",) * 3, 0.0), stack(per, ("SAFE", "NOB", "FULL"), 0.0), stack(per, ("ULTRA",) * 3, 0.0))
for ek, fk, X, sc in itertools.product((1, 2, 3), (1, 2, 3), (3000.0, 4000.0, 5000.0), (0.5, 1.0)):
    r = dict(ek=ek, fk=fk, X=X, cushion=f"{int(750 * fk * sc)}/{int(1500 * fk * sc)}")
    for per in ("IS", "C24", "REAL"):
        (elo, ecl), (flo, fcl), _ = ARR[per]
        out = np.zeros((1000, 6)); m = life_g(elo, ecl, float(ek), 0.0, 0.0, flo, fcl, float(fk), 750.0 * fk * sc, 1500.0 * fk * sc, X, T, D, Q, CAP, FEE, 252, 3, out); L = out[:m]
        o = np.zeros((2000, 2)); n = eval_stats(elo, ecl, float(ek), 0.0, 0.0, T, D, o); e = o[:n]; ok = e[:, 0] == 1; done = e[:, 0] != 0
        r.update({f"{per}_mo": round(L[:, 0].mean() / 12), f"{per}_p10": round(np.percentile(L[:, 0], 10) / 12), f"{per}_evals": round(L[:, 1].mean(), 1),
                  f"{per}_fbust": round(L[:, 3].mean(), 2), f"{per}_pass": round(100 * ok.sum() / max(done.sum(), 1)), f"{per}_days": float(np.median(e[ok, 1])) if ok.any() else np.nan})
    rows.append(r)
G = pd.DataFrame(rows); P = ("IS", "C24", "REAL")
G["worst"] = G[[f"{p}_mo" for p in P]].min(axis=1); G["mean"] = G[[f"{p}_mo" for p in P]].mean(axis=1).round(); G["p10min"] = G[[f"{p}_p10" for p in P]].min(axis=1)
G["fees_yr"] = (G[[f"{p}_evals" for p in P]].mean(axis=1) * FEE).round()
G.to_csv("acct_k.csv", index=False)
cols = ["ek", "fk", "X", "cushion", "worst", "mean", "p10min", "fees_yr"] + [f"{p}_mo" for p in P] + [f"{p}_pass" for p in P] + [f"{p}_days" for p in P] + [f"{p}_fbust" for p in P]
print(G.sort_values("worst", ascending=False)[cols].head(25).to_string(index=False))
print(G[(G.ek == 1) & (G.fk == 1) & (G.X == 4000.0) & (G.cushion == "750/1500")][cols].to_string(index=False))
