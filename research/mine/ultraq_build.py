"""2026-10-14 UltraQ = Ultra (cand16 UltraWR rebuild: no ON07 / LON / ICT) without the wide VW13 lot (Vw13Wide false: VW13 only at
>= 0.30 ATR, 1 lot) + CPI09 (cpi_lab.py). Saves real and cost-normalised trade lists (ultraq_trades.pkl) and calibrates the
edge-monitor CUSUM exactly like monitor_recal.py. -> ultraq_trades.pkl, ultraq_monitor.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from core import Data
from ultra_q2 import cpi09_trades
from monitor_recal import first_alarm, zser
from wrq_lib import getD
from news import NEWS

if __name__ == "__main__":
    C = pickle.load(open("cand16_trades.pkl", "rb")); cr, cn = cpi09_trades(Data("nqdb.npz"))
    W, WN = C["UltraWR"]; cols = ["date", "mod", "tin", "tout", "d", "u", "w"]
    Q = pd.concat([W[W["mod"] != "VW13b"][cols], cr[cols]], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True)
    QN = pd.concat([WN[WN["mod"] != "VW13b"][cols], cn[cols]], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True)
    pickle.dump({"UltraQ": (Q, QN)}, open("ultraq_trades.pkl", "wb"))
    D = getD("nqdb.npz"); rng = np.random.default_rng(5)
    days = np.array(sorted(set(D.daydate[(D.ro >= 0)]))); days = days[(days >= 20200101) & ~np.isin(days, list(NEWS["FOMC"]))]
    atr = pd.Series(D.atr, index=D.daydate).groupby(level=0).last().reindex(days).to_numpy(); m = atr >= 150; days = days[m]; atr = atr[m]
    z = zser(Q[Q.date.isin(days)], days, atr); mu = float(z.mean()); sd = float(z.std()); k = mu / 2; B = 3000; H = 756; L = 10
    idx = np.array([np.concatenate([np.arange(s, s + L) for s in rng.integers(0, len(z) - L, H // L + 1)])[:H] for _ in range(B)])
    res = None
    for hs in np.arange(4.0, 40.0, 0.5):
        h = hs * sd; a = np.array([first_alarm(z[ix], k, h) for ix in idx])
        fa1 = float(((a > 0) & (a <= 252)).mean())
        if fa1 <= 0.05 and first_alarm(z, k, h) < 0:
            dead = np.array([first_alarm(z[ix] - mu, k, h) for ix in idx[:1000]])
            res = dict(k=round(k, 4), h=round(h, 2), P_false_1y=round(fa1, 3), median_days_to_detect_dead_edge=float(np.median(np.where(dead > 0, dead, 999)))); break
    print(res); json.dump(res, open("ultraq_monitor.json", "w"), indent=1)
