"""CUSUM edge monitor calibration for GoldMaster (WinRate, Robust). z = daily P&L per MGC / (10 x daily ATR in gold dollars)
(= research pv 4 x ATR in x2.5 points). k = half the 2020-26 mean; h = smallest multiple of sd with false-alarm probability
<= 2%/year on block-bootstrapped 2020-26 and no alarm on 2020-26 nor on real MGC 2024-26. Also replay 2010-19 (regime check)."""
import sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, ".")
from core import Data
from robust_monitor import cusum_first, boot_idx
from gold_port import conflict_filter
T = pickle.load(open("gold_curated_trades.pkl", "rb"))
PROF = {"WinRate": ["OD1030", "ENG0408", "SVWAP22"], "Robust": ["OD1030", "ENG0408", "SVWAP22", "ASIA1R", "ENG0206"]}
DL, DM = Data("xau_long.npz"), Data("mgc_fut.npz")
def atr_by_date(D):
    s = pd.Series(D.atr, index=D.daydate); return s[~s.index.duplicated(keep="last")]
AL, AM = atr_by_date(DL), atr_by_date(DM)
def zser(mods, pers, A, days_src):
    F = conflict_filter(pd.concat([T[m][p] for m in mods for p in pers], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True))
    days = np.array(sorted(d for d in days_src if F.date.min() <= d <= F.date.max()))
    pnl = F.u.groupby(F.date).sum().reindex(days, fill_value=0.0); a = A.reindex(days).replace(0, np.nan).ffill().bfill()
    return (pnl / (4.0 * a)).to_numpy()
out = {}
for nm, mods in PROF.items():
    z = zser(mods, ("IS", "C24"), AL, AL.index[(AL.index >= 20200201)]); zr = zser(mods, ("REAL",), AM, AM.index[AM.index >= 20240201])
    zo = zser(mods, ("2010-14", "2015-19"), AL, AL.index[(AL.index >= 20100201) & (AL.index < 20200101)])
    mu, sd = z.mean(), z.std(); k = mu / 2
    I = boot_idx(len(z), 800, 2000)
    for hs in (6, 8, 10, 12, 15, 18, 22, 26, 30):
        h = hs * sd; fa = np.mean([0 < cusum_first(z[I[b]], k, h) <= 252 for b in range(800)])
        dead = np.median([(lambda t: t if t > 0 else 2000)(cusum_first(z[I[b]] - mu, k, h)) for b in range(800)])
        hist = cusum_first(z, k, h); real = cusum_first(zr, k, h); old = cusum_first(zo, k, h)
        print(f"{nm:8s} h={hs:2d}sd falsa alarma/año {100 * fa:4.1f}%  detecta ventaja muerta ~{dead:4.0f} días  alarma 2020-26: {hist > 0}  MGC: {real > 0}  2010-19: día {old}")
        if fa <= 0.02 and hist < 0 and real < 0 and nm not in out: out[nm] = dict(k=k, h=h, hs=hs, mu=mu, sd=sd, dead=dead, old=old)
print(out); pickle.dump(out, open("gold_monitor.pkl", "wb"))
