"""2026-10-15 'best system' layer test: what should NQMaster DO when the edge monitor (CUSUM, Ultra k 0.0758 / h 18.57, calibrated
on 2020-26 real so that it never fires there) raises an alarm? The 2010-19 years are out of sample for the calibration and are a
period where Ultra's edge was weak (cost-normalised PF ~1.0-1.2), i.e. the situation the monitor exists for.
Policies (each day's P&L = sum of the active modules' trades of that day; z = day P&L / (2 x ATR)):
  A  always Ultra (alarm = alert only, today's default)
  P  on alarm pause all entries for L trading days, then reset the CUSUM and resume Ultra
  W  on alarm switch to the walk-forward 'review set' (modules whose last-5-year cost-normalised PF > 1.05, past data only) for
     L days, then reset and resume Ultra
  D  on alarm switch to Durable (NF05 CRT11 VOLB MSEQS ORB60 ORB90; composition chosen on 2010-26 -> in-sample, reported only)
  Y  yearly review only (every January the review set; robust16.py) -- no monitor
  YM yearly review + monitor action W
L = 63 / 126 / 252. Periods: 2013-19 cost-normalised (norm $), 2020-23 and 2024-26 real $. -> os_adapt.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from wrq_lib import getD
from news import NEWS
DUR = ["NF05", "CRT11", "VOLB", "MSEQS", "ORB60", "ORB90"]
K, H = 0.0758, 18.57
pf = lambda x: float(x[x > 0].sum() / -x[x <= 0].sum()) if (x <= 0).any() else np.nan


def review_set(N, mods, d):
    """modules with cost-normalised PF > 1.05 over the 5 years before date d (>= 20 trades); unknown modules stay on"""
    lo = d - 50000; T = N[(N.date >= lo) & (N.date < d)]; out = []
    for m in mods:
        t = T[T["mod"] == m].x
        if len(t) < 20 or pf(t.to_numpy()) > 1.05: out.append(m)
    return out


def run(M, Mn, atr, days, mods, N, pol, L):
    """M: day x module P&L used for the result; Mn: same in normalised $ (for z); returns daily P&L array, alarms, days off"""
    n = len(days); out = np.zeros(n); s = 0.0; until = -1; fb = None; alarms = 0; off = 0; yset = None; yr = None
    col = {m: i for i, m in enumerate(mods)}; Mv = M.to_numpy(); Zv = Mn.to_numpy()
    for t in range(n):
        y = days[t] // 10000
        if pol in ("Y", "YM") and y != yr: yr = y; yset = [col[m] for m in review_set(N, mods, y * 10000 + 101)]
        base = yset if pol in ("Y", "YM") else list(range(len(mods)))
        if t < until:
            act = fb; off += 1
        else:
            act = base
        out[t] = Mv[t, act].sum() if len(act) else 0.0
        if pol in ("A", "P", "W", "D", "YM") and t >= until:
            z = Zv[t, act].sum() / (2.0 * atr[t])
            s = max(0.0, s + K - z)
            if s > H:
                alarms += 1; s = 0.0
                if pol == "P": fb = []; until = t + 1 + L
                elif pol in ("W", "YM"): fb = [col[m] for m in review_set(N, mods, int(days[t]))]; until = t + 1 + L
                elif pol == "D": fb = [col[m] for m in DUR if m in col]; until = t + 1 + L
    return out, alarms, off


def stats(x):
    eq = np.cumsum(x); dd = float((np.maximum.accumulate(eq) - eq).max())
    return dict(net=round(float(x.sum())), sharpe=round(float(x.mean() / x.std() * np.sqrt(252)), 2) if x.std() > 0 else 0.0, maxdd=round(dd))


if __name__ == "__main__":
    C = pickle.load(open("cand16_trades.pkl", "rb")); Q = pickle.load(open("ultraq_trades.pkl", "rb"))["UltraQ"]
    R, N = C["UltraR"]; R = pd.concat([R, Q[0][Q[0]["mod"] == "CPI09"]], ignore_index=True); N = pd.concat([N, Q[1][Q[1]["mod"] == "CPI09"]], ignore_index=True)
    for X in (R, N): X["x"] = X.u * X.w
    D = getD("nqdb.npz")
    days = np.array(sorted(set(D.daydate[(D.ro >= 0)]))); days = days[(days >= 20100701) & ~np.isin(days, list(NEWS["FOMC"]))]
    atr = pd.Series(D.atr, index=D.daydate).groupby(level=0).last().reindex(days).to_numpy()
    mods = sorted(set(N["mod"]) | set(R["mod"]))
    Mn = N.pivot_table(index="date", columns="mod", values="x", aggfunc="sum").reindex(index=days, columns=mods, fill_value=0.0).fillna(0.0)
    Mr = R.pivot_table(index="date", columns="mod", values="x", aggfunc="sum").reindex(index=days, columns=mods, fill_value=0.0).fillna(0.0)
    Mmix = Mn.copy(); Mmix.loc[days >= 20200101] = Mr.loc[days >= 20200101]          # norm before 2020, real after
    PER = {"2013-19 norm": (20130101, 20200101), "2020-23 real": (20200101, 20240101), "2024-26 real": (20240101, 20991231)}
    OUT = {}; rows = []
    pols = [("A", 0), ("Y", 0)] + [(p, L) for p in ("P", "W", "D", "YM") for L in (63, 126, 252)]
    for pol, L in pols:
        x, al, off = run(Mmix, Mmix, atr, days, mods, N, pol, L)
        key = pol + (f"{L}" if L else ""); rec = dict(alarms=al, days_off=off)
        for nm, (lo, hi) in PER.items():
            m = (days >= lo) & (days < hi); rec[nm] = stats(x[m])
        yrs = {int(y): round(float(x[(days // 10000) == y].sum())) for y in range(2011, 2027)}
        rec["neg_years_2011_19"] = int(sum(v < 0 for y, v in yrs.items() if y < 2020)); rec["years"] = yrs
        OUT[key] = rec
        print(f"{key:6s} alarms {al:2d} off {off:4d} | " + " | ".join(f"{nm}: ${r['net']:>7,} Sh {r['sharpe']:5.2f} DD {r['maxdd']:>6,}" for nm, r in ((k, rec[k]) for k in PER)) +
              f" | neg yrs 2011-19 {rec['neg_years_2011_19']}", flush=True)
    # when did the monitor fire under A (alert only)?
    s = 0.0; fires = []
    for t in range(len(days)):
        s = max(0.0, s + K - Mmix.to_numpy()[t].sum() / (2 * atr[t]))
        if s > H: fires.append(int(days[t])); s = 0.0
    OUT["alarm_dates_ultra"] = fires; print("alarm dates (Ultra, reset after each):", fires)
    json.dump(OUT, open("os_adapt.json", "w"), indent=1)
