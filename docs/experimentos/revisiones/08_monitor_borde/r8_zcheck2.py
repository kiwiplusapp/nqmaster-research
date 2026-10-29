import os, sys, pickle, numpy as np, pandas as pd
M = "/home/user/nqmaster-research/research/mine"; sys.path.insert(0, M); sys.path.insert(0, os.path.dirname(M)); os.chdir(M)
from wrq_lib import getD
from news import NEWS
D = getD("nqdb.npz"); atr = pd.Series(D.atr, index=D.daydate)
C = pickle.load(open("cand16_trades.pkl", "rb")); R, N = C["UltraR"]
J = R.merge(N, on=["date", "mod", "tin", "d", "fi"], suffixes=("_r", "_n")); J["a"] = atr.reindex(J.date).to_numpy()
J["zr"] = J.u_r / (2 * J.a); J["zn"] = J.u_n / 100.0
def fit(x, y): b, a = np.polyfit(x, y, 1); return b, a
S = J[J.date >= 20200101]; b, a = fit(S.zn, S.zr); print(f"cand16 UltraR 2020-26: slope zr~zn {b:.4f} intercept {a:.4f}; zr/zn per trade median (|zn|>0.2) {np.median((S.zr/S.zn)[S.zn.abs()>0.2]):.4f}")
TR = {}
for f in ("trades_db_old.pkl", "trades_db_new.pkl"): TR.update(pickle.load(open(f, "rb")))
NEW = {"SO04": ("CLOCK_ANCHOR", 1527), "RV11": ("RVOL_DRIVE", 4226), "ORFAIL": ("OR_FAIL", 142), "CAM3": ("PIVOT_FADE", 365)}
for nm, k in NEW.items():
    r, n = TR[k]["real"], TR[k]["norm"]; j = r.merge(n, on=["date", "fi", "d"], suffixes=("_r", "_n")); j["a"] = atr.reindex(j.date).to_numpy()
    j["zr"] = j.usd_r / (2 * j.a); j["zn"] = j.usd_n / 100
    for lo, hi in ((20100101, 20200101), (20200101, 20991231)):
        s = j[(j.date >= lo) & (j.date < hi)]; b, a = fit(s.zn, s.zr)
        print(f"{nm} {lo//10000}-: slope {b:.4f} intercept {a:.4f} median per-trade ratio (|zn|>0.2) {np.median((s.zr/s.zn)[s.zn.abs()>0.2]):.4f}  mean |zr| {s.zr.abs().mean():.3f}")
days = np.array(sorted(set(D.daydate[(D.ro >= 0)]))); days = days[(days >= 20100701) & ~np.isin(days, list(NEWS["FOMC"]))]
a = atr.reindex(days).to_numpy()
for lo, hi in ((20200101, 20240101), (20240101, 20991231)):
    m = (days >= lo) & (days < hi); print(f"days {lo//10000}-: {m.sum()}, ATR<150: {(m & (a < 150)).sum()}")
lo = days[(days >= 20200101) & (a < 150)]; print("ATR<150 days 2020+: first/last", lo[:5], lo[-5:])
