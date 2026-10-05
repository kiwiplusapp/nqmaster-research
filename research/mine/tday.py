"""TDAY module: at time T (10:30 default) compute the trend-day probability (logistic model fitted on CFD 2020-23 only, features known
at T); if p >= threshold, enter in the direction of the move since the RTH open, stop = k*ATR (or beyond the day's opposite
extreme), exit 15:55 or target R*risk. Tested on CFD 2020-23 (in-sample for the model), CFD 2024-26, MNQ real 2024-26 and
2015-19 (CFD, cost-normalised, out-of-sample in time for the model)."""
import os, sys, itertools, pickle, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
from core import Data, S, ev_from_lists, run_events
from news import NEWS
exec(open("trendday_pred.py", encoding="utf8").read().split("# bucket Ultra trades")[0])      # IS/C24/RE tables, model m, Z, FEATS, day_table
DL = Data("nqhd_long.npz"); TL = day_table(DL); T1519 = TL[(TL.date >= 20150101) & (TL.date < 20200101)]
def events(D, Tab, thr, k, stopmode, R):
    p = m.predict_proba(Z(Tab))[:, 1]; ev = []
    for (dd, row), pp in zip(Tab.iterrows(), p):
        if pp < thr or row.date in NEWS["FOMC"]: continue
        d = int(row.day); a = D.ro[d]; e = D.de[d]; sm = D.sm[a:e + 1]
        i = a + np.searchsorted(sm, S(1030)) - 1
        if i <= a: continue
        s = 1 if D.c[i] > D.o[a] else -1; A = D.atr[d]; px = D.c[i]
        if stopmode == 0: sl = px - s * k * A
        else:
            ext = D.l[a:i + 1].min() if s == 1 else D.h[a:i + 1].max(); sl = ext - s * 0.25
            if (px - sl) * s > 0.6 * A: continue
        tp = px + s * R * abs(px - sl)
        ev.append([i, s, 0, px, sl, tp, i, 400])
    return ev_from_lists(ev)
def pf(u): return round(float(u[u > 0].sum() / -u[u <= 0].sum()), 3) if (u <= 0).any() else np.nan
pIS = m.predict_proba(Z(IS))[:, 1]
rows = []
for qthr, k, stopmode, R in itertools.product((0.5, 0.667, 0.8), (0.2, 0.3, 0.45), (0, 1), (1.0, 2.0, 99.0)):
    if stopmode == 1 and k != 0.2: continue
    thr = float(np.quantile(pIS, qthr)); r = dict(q=qthr, thr=round(thr, 3), stop=("ATR %.2f" % k) if stopmode == 0 else "extremo del día", R=R)
    for lab, D, Tab, norm in (("IS", DN, IS, False), ("C24", DN, C24, False), ("REAL", DM, RE, False), ("y1519", DL, T1519, True)):
        df = run_events(D, events(D, Tab, thr, k, stopmode, R), flat=955, maxday=1, slip=0.0 if norm else 0.25, norm_cost=0.00345 if norm else None)
        u = df.usd.to_numpy(); r[lab + "_n"] = len(u); r[lab + "_pf"] = pf(u); r[lab + "_wr"] = round(100 * (u > 0).mean(), 1) if len(u) else np.nan
        if not norm: r[lab + "_avg"] = round(float(u.mean()), 1) if len(u) else np.nan
    rows.append(r); print(r, flush=True)
G = pd.DataFrame(rows); G.to_csv("tday.csv", index=False); pd.set_option("display.width", 260)
G["minpf"] = G[["IS_pf", "C24_pf", "REAL_pf", "y1519_pf"]].min(axis=1)
print(G.sort_values("minpf", ascending=False).to_string(index=False))
