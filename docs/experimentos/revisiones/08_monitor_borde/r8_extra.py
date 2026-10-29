"""r8: bootstrap of W252-A in 2013-19, review set at 2027-01-01 vs NQMaster table, mean z with current lists, low-ATR trades P&L."""
import os, sys, json, numpy as np, pandas as pd
M = "/home/user/nqmaster-research/research/mine"; sys.path.insert(0, M); sys.path.insert(0, os.path.dirname(M)); os.chdir(M)
import exp08_monitor as E
from os_adapt import review_set, stats, pf
days, atr, mods, Mv, N, post = E.build(with_new=True)
xa = E.run(days, atr, mods, Mv, N, post, "A", E.K, E.Hh, E.HW)[0]; xw = E.run(days, atr, mods, Mv, N, post, "W252", E.K, E.Hh, E.HW)[0]
m = (days >= 20130101) & (days < 20200101); d = (xw - xa)[m]; nz = d != 0
print(f"2013-19: days with W252 != A: {nz.sum()} of {m.sum()}; sum diff {d.sum():.0f}; mean/day in windows {d[nz].mean():.2f} sd {d[nz].std():.1f} t~{d[nz].mean()/d[nz].std()*np.sqrt(nz.sum()):.2f}")
rng = np.random.default_rng(8); dd = d[nz]; L = 20; B = 5000; S = []
for _ in range(B):
    st = rng.integers(0, len(dd) - L, len(dd) // L + 1); S.append(np.concatenate([dd[s:s + L] for s in st])[:len(dd)].sum())
S = np.array(S); print(f"block bootstrap (20 d) of the in-window differences: P(sum>0) {np.mean(S>0):.3f}, 90% CI [{np.percentile(S,5):.0f}, {np.percentile(S,95):.0f}]")
# Sharpe difference bootstrap on paired 2013-19 daily series
xa13, xw13 = xa[m], xw[m]; T = len(xa13); SD = []
for _ in range(2000):
    st = rng.integers(0, T - L, T // L + 1); ix = np.concatenate([np.arange(s, s + L) for s in st])[:T]
    a, w = xa13[ix], xw13[ix]; SD.append(w.mean() / w.std() * np.sqrt(252) - a.mean() / a.std() * np.sqrt(252))
SD = np.array(SD); print(f"paired block bootstrap Sharpe(W252)-Sharpe(A) 2013-19: obs {xw13.mean()/xw13.std()*np.sqrt(252)-xa13.mean()/xa13.std()*np.sqrt(252):.3f}, P(>0) {np.mean(SD>0):.3f}, 90% CI [{np.percentile(SD,5):.3f}, {np.percentile(SD,95):.3f}]")
# review set at 2027-01-01 and today, vs NQMaster table (2027: REV06 off)
for dte in (20270101, 20261029, 20260101):
    rs = review_set(N, mods, dte); off = sorted(set(mods) - set(rs)); print(f"review set at {dte}: OFF = {off}")
T5 = N[(N.date >= 20220101) & (N.date < 20270101)]
print("PF 2022-26 (norm, x=u*w) of the four six-year modules and REV06:", {mm: round(pf(T5[T5['mod'] == mm].x.to_numpy()), 3) for mm in ("SO04", "RV11", "ORFAIL", "CAM3", "REV06", "LF06", "VW13")})
# mean z with current lists on the monitor_recal3 sample (2020-26, ATR>=150)
k = (days >= 20200101) & (atr >= 150); z = Mv[k].sum(1) / (2 * atr[k]); print(f"mean z 2020-26 ATR>=150 current lists: {z.mean():.4f} (monitor_recal3 mean_z 0.1797 -> k {z.mean()/2:.4f} vs 0.0899); sd {z.std():.4f} (h 26.93 = 36.5 sd -> {36.5*z.std():.2f})")
lo = (days >= 20200101) & (atr < 150); print(f"2020-21 ATR<150 days: {lo.sum()}, P&L on those days (all policies) {Mv[lo].sum():.0f}; CUSUM drift added ~ {lo.sum()*E.K - (Mv[lo].sum(1)/(2*atr[lo])).sum():.2f}")
# mean corrected z by year 2010-19 vs k
for y in range(2011, 2020):
    mm = (days // 10000) == y; print(y, f"mean z {(Mv[mm].sum(1)/100).mean():.3f}", end=" | ")
print()
# CUSUM path under WH: s at 2020-01-01
