import pickle, numpy as np, pandas as pd
B = pickle.load(open("base_feats.pkl", "rb"))
FE = ["vw", "open", "rng", "pos", "trend", "gap", "pdret", "m30", "ret5", "atr", "pd", "svw"]
def pf(x): 
    l = -x[x <= 0].sum(); return x[x > 0].sum() / l if l > 0 and len(x) >= 25 else np.nan
rows = []
IS = B["IS"][0]
for m in sorted(IS["mod"].unique()):
    for f in FE:
        xi = IS[IS["mod"] == m][f].dropna()
        if len(xi) < 90: continue
        for qlo, qhi, lab in ((0, 1 / 3, "low33"), (2 / 3, 1, "high33"), (0, 0.2, "low20"), (0.8, 1, "high20")):
            lo = -np.inf if qlo == 0 else xi.quantile(qlo); hi = np.inf if qhi == 1 else xi.quantile(qhi)
            r = dict(mod=m, feat=f, bucket=lab, lo=lo, hi=hi)
            for per in ("IS", "C24", "REAL"):
                F = B[per][0]; G = F[F["mod"] == m]; x = (G.u * G.w)
                inb = (G[f] >= lo) & (G[f] < hi) if qhi < 1 else (G[f] >= lo)
                if qlo == 0: inb = G[f] < hi
                r[per + "_n"] = int(inb.sum()); r[per + "_pf_in"] = pf(x[inb]); r[per + "_pf_out"] = pf(x[~inb & G[f].notna()]); r[per + "_wr_in"] = 100 * (G.u[inb] > 0).mean()
            rows.append(r)
R = pd.DataFrame(rows); R.to_csv("filt_mine.csv", index=False)
drop = R[(R.IS_n >= 40) & (R.IS_pf_in < 1.0) & (R.IS_pf_out > 1.2)]
boost = R[(R.IS_n >= 40) & (R.IS_pf_in > 1.9)]
pd.set_option("display.width", 250)
cols = ["mod", "feat", "bucket", "IS_n", "IS_pf_in", "IS_pf_out", "C24_n", "C24_pf_in", "C24_pf_out", "REAL_n", "REAL_pf_in", "REAL_pf_out"]
print("DROP candidates chosen on IS:", len(drop), "| survive (C24 & REAL in-bucket PF < out-bucket PF and < 1.1):",
      int(((drop.C24_pf_in < drop.C24_pf_out) & (drop.REAL_pf_in < drop.REAL_pf_out) & (drop.C24_pf_in < 1.1) & (drop.REAL_pf_in < 1.1)).sum()))
print(drop[cols].round(2).to_string(index=False))
print("\nBOOST candidates chosen on IS:", len(boost), "| survive (C24 & REAL in-bucket PF > 1.6):", int(((boost.C24_pf_in > 1.6) & (boost.REAL_pf_in > 1.6)).sum()))
print(boost[cols].round(2).to_string(index=False))
