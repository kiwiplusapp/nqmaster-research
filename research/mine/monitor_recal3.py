"""2026-10-19: edge-monitor k / h for the 2027 default (Ultra + the durable six-year modules SO04 / RV11 / ORFAIL / CAM3, six_oos.py).
Same method as monitor_recal2.py (k = mean z / 2, h = smallest multiple of sd(z) with P(false alarm within 1 year) <= 5% on 10-day block
bootstrap AND no alarm in the 2020-26 history; warning level P(false warning in 1 year) <= 25%). z = day $ per base contract / (2 x ATR).
-> monitor_recal3.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from wrq_lib import getD
from news import NEWS
from monitor_recal2 import calib
from audit16_stats import load
NEW = {"SO04": ("CLOCK_ANCHOR", 1527), "RV11": ("RVOL_DRIVE", 4226), "ORFAIL": ("OR_FAIL", 142), "CAM3": ("PIVOT_FADE", 365)}
if __name__ == "__main__":
    D = getD("nqdb.npz"); rng = np.random.default_rng(5)
    days = np.array(sorted(set(D.daydate[(D.ro >= 0)]))); days = days[(days >= 20200101) & ~np.isin(days, list(NEWS["FOMC"]))]
    atr = pd.Series(D.atr, index=D.daydate).groupby(level=0).last().reindex(days).to_numpy(); m = atr >= 150; days = days[m]; atr = atr[m]
    sets, cur = load(); TR = {}
    for f in ("trades_db_old.pkl", "trades_db_new.pkl"): TR.update(pickle.load(open(os.path.join(HERE, f), "rb")))
    parts = [cur[0][["date", "mod", "u", "w"]]]
    for nm, key in NEW.items():
        t = TR[key]["real"]; parts.append(pd.DataFrame(dict(date=t.date.to_numpy(), mod=nm, u=t.usd.to_numpy(), w=1.0)))
    X = pd.concat(parts, ignore_index=True); X = X[X.date.isin(days)]
    z = (X.u * X.w).groupby(X.date).sum().reindex(days, fill_value=0.0).to_numpy() / (2.0 * atr)
    OUT = {"Ultra + durable four": calib(z, rng)}; print(OUT, flush=True)
    json.dump(OUT, open(os.path.join(HERE, "monitor_recal3.json"), "w"), indent=1)
