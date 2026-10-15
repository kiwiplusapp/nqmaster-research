"""2026-10-16 C5: edge-monitor recalibration for the CURRENT defaults. The CUSUM z in NQMaster is the day's $ per BASE contract /
(2 x ATR); since 2026-10-15 MOM1030 and CPI09 trade x4 and CPI09 is in Ultra / UltraQ / WR70Plus, so the daily z distribution changed
and the k / h of monitor_recal.py (calibrated without them) are stale. Same method as monitor_recal.py (fixed in advance):
  k = mean(z) / 2; h = smallest multiple of sd(z) with P(false alarm within 1 year) <= 5% on 10-day block bootstrap of the 2020-26
  real days AND no alarm anywhere in the 2020-26 history.
New: a fast WARNING level (alert only, no action) = smallest h_w with P(false warning within 1 year) <= 25%.
Also re-checks the built-in fallback table (robust16 rule: module off when its last-5-year cost-normalised PF <= 1.05).
-> monitor_recal2.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from wrq_lib import getD
from news import NEWS
from monitor_recal import first_alarm
from audit16_stats import load
pf = lambda x: float(x[x > 0].sum() / -x[x <= 0].sum()) if (x <= 0).any() else np.inf


def calib(z, rng, B=3000, H=756, L=10):
    mu = float(z.mean()); sd = float(z.std()); k = mu / 2
    idx = np.array([np.concatenate([np.arange(s, s + L) for s in rng.integers(0, len(z) - L, H // L + 1)])[:H] for _ in range(B)])
    out = {}
    for hs in np.arange(2.0, 40.0, 0.5):
        h = hs * sd; a = np.array([first_alarm(z[ix], k, h) for ix in idx])
        fa1 = float(((a > 0) & (a <= 252)).mean()); hist = first_alarm(z, k, h)
        if "warn" not in out and fa1 <= 0.25:
            dead = np.array([first_alarm(z[ix] - mu, k, h) for ix in idx[:1000]])
            out["warn"] = dict(h=round(h, 2), h_sd=float(hs), P_false_1y=round(fa1, 3), median_days_dead_edge=float(np.median(np.where(dead > 0, dead, 999))))
        if fa1 <= 0.05 and hist < 0:
            dead = np.array([first_alarm(z[ix] - mu, k, h) for ix in idx[:1000]]); neg = np.array([first_alarm(z[ix] - 1.5 * mu, k, h) for ix in idx[:1000]])
            out["alarm"] = dict(k=round(k, 4), h=round(h, 2), h_sd=float(hs), mean_z=round(mu, 4), P_false_1y=round(fa1, 3),
                                P_false_3y=round(float(((a > 0) & (a <= 756)).mean()), 3),
                                median_days_dead_edge=float(np.median(np.where(dead > 0, dead, 999))), median_days_negative_edge=float(np.median(np.where(neg > 0, neg, 999))))
            break
    return out


if __name__ == "__main__":
    D = getD("nqdb.npz"); rng = np.random.default_rng(5)
    days = np.array(sorted(set(D.daydate[(D.ro >= 0)]))); days = days[(days >= 20200101) & ~np.isin(days, list(NEWS["FOMC"]))]
    atr = pd.Series(D.atr, index=D.daydate).groupby(level=0).last().reindex(days).to_numpy(); m = atr >= 150; days = days[m]; atr = atr[m]
    sets, cur = load()
    C = pickle.load(open(os.path.join(HERE, "cand16_trades.pkl"), "rb")); Q = pickle.load(open(os.path.join(HERE, "ultraq_trades.pkl"), "rb"))["UltraQ"]
    cpi = Q[0][Q[0]["mod"] == "CPI09"].assign(w=4.0)
    x4 = lambda X: X.assign(w=np.where(X["mod"].isin(["MOM1030", "CPI09"]), 4.0, X.w))
    SETS = {"Ultra (x4 + CPI09)": cur[0], "UltraQ (x4)": x4(Q[0]), "WR70Plus (+CPI09 x4)": pd.concat([C["WR70R"][0], cpi], ignore_index=True),
            "Durable": sets["Durable"][0], "Ultra old calibration check (UltraR x1)": C["UltraR"][0]}
    OUT = {}
    for name, X in SETS.items():
        X = X[X.date.isin(days)]; z = (X.u * X.w).groupby(X.date).sum().reindex(days, fill_value=0.0).to_numpy() / (2.0 * atr)
        OUT[name] = calib(z, rng); print(name, OUT[name], flush=True)
    # fallback table check (robust16 rule) on the current set, cost-normalised
    N = cur[1].assign(x=lambda d: d.u * d.w, y=lambda d: d.date // 10000); mods = sorted(N["mod"].unique()); tab = {}
    for y in range(2020, 2028):
        T = N[(N.y >= y - 5) & (N.y < y)]
        tab[y] = [m for m in mods if (T["mod"] == m).sum() >= 20 and pf(T[T["mod"] == m].x.to_numpy()) <= 1.05]
    OUT["fallback_table_recomputed"] = tab; print(tab)
    json.dump(OUT, open(os.path.join(HERE, "monitor_recal2.json"), "w"), indent=1)
