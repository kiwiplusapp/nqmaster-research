"""r8: independent check of normalised/100 == dollars/(2 x ATR) on trades with both versions."""
import os, sys, pickle, numpy as np, pandas as pd
M = "/home/user/nqmaster-research/research/mine"; sys.path.insert(0, M); sys.path.insert(0, os.path.dirname(M)); os.chdir(M)
from wrq_lib import getD
D = getD("nqdb.npz"); atr = pd.Series(D.atr, index=D.daydate)
C = pickle.load(open("cand16_trades.pkl", "rb")); R, N = C["UltraR"]
key = ["date", "mod", "tin", "d", "fi"]
J = R.merge(N, on=key, suffixes=("_r", "_n"))
print("cand16 UltraR: real", len(R), "norm", len(N), "matched", len(J), "| real trades from", R.date.min())
J["atrD"] = atr.reindex(J.date).to_numpy()
print("atr col real == day atr:", np.allclose(J.atr_r, J.atrD), " atr_n == atr_r:", np.allclose(J.atr_n, J.atr_r))
J["zr"] = J.u_r / (2 * J.atrD); J["zn"] = J.u_n / 100.0
for lo, hi in ((20180101, 20200101), (20200101, 20240101), (20240101, 20991231)):
    S = J[(J.date >= lo) & (J.date < hi)]
    print(f"  {lo}-{hi}: n {len(S)}  sum zr {S.zr.sum():.2f} sum zn {S.zn.sum():.2f} ratio zr/zn {S.zr.sum()/S.zn.sum():.3f}  corr {np.corrcoef(S.zr, S.zn)[0,1]:.4f}  "
          f"median per-trade diff (zn-zr) {np.median(S.zn - S.zr):.4f}  median gross-cost gap 2.4/ATR-0.00345 {np.median(2.4/S.atrD - 0.00345):.4f}")
# per-module ratio 2020-26
S = J[J.date >= 20200101]
g = S.groupby("mod_x" if "mod_x" in S else "mod").agg(n=("zr", "size"), zr=("zr", "sum"), zn=("zn", "sum")); g["ratio"] = g.zr / g.zn
print(g.round(3).to_string())
# trades_db: four six-year modules
NEW = {"SO04": ("CLOCK_ANCHOR", 1527), "RV11": ("RVOL_DRIVE", 4226), "ORFAIL": ("OR_FAIL", 142), "CAM3": ("PIVOT_FADE", 365)}
TR = {}
for f in ("trades_db_old.pkl", "trades_db_new.pkl"): TR.update(pickle.load(open(f, "rb")))
for nm, k in NEW.items():
    r, n = TR[k]["real"], TR[k]["norm"]; j = r.merge(n, on=["date", "fi", "d"], suffixes=("_r", "_n"))
    j["a"] = atr.reindex(j.date).to_numpy(); j["zr"] = j.usd_r / (2 * j.a); j["zn"] = j.usd_n / 100
    for lo, hi in ((20100101, 20200101), (20200101, 20991231)):
        s = j[(j.date >= lo) & (j.date < hi)]
        print(f"{nm} {lo//10000}-{hi//10000-1 if hi<20990000 else 2026}: real {((r.date>=lo)&(r.date<hi)).sum()} norm {((n.date>=lo)&(n.date<hi)).sum()} matched {len(s)} ratio zr/zn {s.zr.sum()/s.zn.sum():.3f} corr {np.corrcoef(s.zr, s.zn)[0,1]:.4f}"
              f" | gross check: (usd_r + 4.8)/(2a) vs usd_n/100 + 0.345%: ratio {((s.usd_r+4.8)/(2*s.a)).sum()/((s.usd_n/100+0.00345)).sum():.4f}")
    print(f"   real trades on days ATR<150 in 2020-26: {((r.date>=20200101) & (atr.reindex(r.date).to_numpy()<150)).sum()}")
