"""Edge-monitor CUSUM recalibration (2026-10-12) for the new default Ultra (cand16 'UltraR') and the new Durable profile
(hist_profiles 'Durable6'), same method as robust_monitor.py: z = day $ per base contract / (2 x daily ATR points),
k = mean(z) / 2, h = smallest multiple of sd(z) with P(false alarm within 1 year) <= 5% on 10-day block bootstrap of the
2020-26 real days and no alarm on the 2020-26 history; delay to detect a dead edge (mean -> 0). -> monitor_recal.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from numba import njit
from wrq_lib import getD
from news import NEWS


@njit(cache=True)
def first_alarm(x, k, h):
    s = 0.0
    for t in range(len(x)):
        s = max(0.0, s + k - x[t])
        if s > h: return t + 1
    return -1


def zser(X, days, atr):
    d = (X.u * X.w).groupby(X.date).sum().reindex(days, fill_value=0.0).to_numpy()
    return d / (2.0 * atr)


if __name__ == "__main__":
    D = getD("nqdb.npz"); rng = np.random.default_rng(5)
    days = np.array(sorted(set(D.daydate[(D.ro >= 0)]))); days = days[(days >= 20200101) & ~np.isin(days, list(NEWS["FOMC"]))]
    atr = pd.Series(D.atr, index=D.daydate).groupby(level=0).last().reindex(days).to_numpy(); m = atr >= 150; days = days[m]; atr = atr[m]
    SETS = {"Ultra (new)": pickle.load(open("cand16_trades.pkl", "rb"))["UltraR"][0], "Durable": pickle.load(open("hist_profiles_trades.pkl", "rb"))["Durable6"][0],
            "WR70Plus (new)": pickle.load(open("cand16_trades.pkl", "rb"))["WR70R"][0], "Ultra (old, check)": pickle.load(open("cand16_trades.pkl", "rb"))["Ultra"][0]}
    OUT = {}; B = 3000; H = 756; L = 10
    for name, X in SETS.items():
        z = zser(X[X.date.isin(days)], days, atr); mu = float(z.mean()); sd = float(z.std()); k = mu / 2
        idx = np.array([np.concatenate([np.arange(s, s + L) for s in rng.integers(0, len(z) - L, H // L + 1)])[:H] for _ in range(B)])
        res = None
        for hs in np.arange(4.0, 40.0, 0.5):
            h = hs * sd
            a = np.array([first_alarm(z[ix], k, h) for ix in idx])
            fa1 = float(((a > 0) & (a <= 252)).mean()); fa3 = float(((a > 0) & (a <= 756)).mean()); hist = first_alarm(z, k, h)
            if fa1 <= 0.05 and hist < 0:
                dead = np.array([first_alarm(z[ix] - mu, k, h) for ix in idx[:1000]]); neg = np.array([first_alarm(z[ix] - 1.5 * mu, k, h) for ix in idx[:1000]])
                res = dict(k=round(k, 4), h=round(h, 2), h_sd=float(hs), mean_z=round(mu, 4), P_false_1y=round(fa1, 3), P_false_3y=round(fa3, 3),
                           median_days_to_detect_dead_edge=float(np.median(np.where(dead > 0, dead, 999))), median_days_negative_edge=float(np.median(np.where(neg > 0, neg, 999))))
                break
        OUT[name] = res; print(name, res, flush=True)
    json.dump(OUT, open("monitor_recal.json", "w"), indent=1)
