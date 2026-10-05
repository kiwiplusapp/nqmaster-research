"""Apex eval simulator on minute paths (unrealized trailing). Policies (size at each day start from equity eq / peak pk):
 mode 0: fixed k1 | 1: k1 while (pk-eq) < thr else k2 | 2: k1 until eq >= thr then k2 | 3: k1, k2 once eq <= -thr
Optional daily stop: stop the day when day realized <= -dl (0 = off) or >= dg (0 = off)."""
import pickle, numpy as np, pandas as pd
from numba import njit
@njit(cache=True)
def run(day, fav, adv, rel, ndays, start, T, D, maxd, mode, k1, k2, thr, dl, dg):
    # locate first event of start day
    i = np.searchsorted(day, start)
    eq = 0.0; pk = 0.0; d = start
    while d < start + maxd and d < ndays:
        if mode == 0: k = k1
        elif mode == 1: k = k1 if (pk - eq) < thr else k2
        elif mode == 2: k = k1 if eq < thr else k2
        else: k = k1 if eq > -thr else k2
        last = 0.0
        while i < len(day) and day[i] == d:
            w = eq + k * adv[i]
            if w <= pk - D: return -1, d - start + 1
            b = eq + k * fav[i]
            if b > pk: pk = b
            last = rel[i]
            if eq + k * last >= T: return 1, d - start + 1
            if dl > 0 and k * last <= -dl: 
                while i < len(day) and day[i] == d: i += 1
                break
            if dg > 0 and k * last >= dg:
                while i < len(day) and day[i] == d: i += 1
                break
            i += 1
        eq += k * last
        if eq > pk: pk = eq
        d += 1
    return 0, maxd
def stats(P, T=1500, D=1500, maxd=21, mode=0, k1=1, k2=1, thr=0.0, dl=0.0, dg=0.0):
    r = np.array([run(P["day"], P["fav"], P["adv"], P["rel"], P["ndays"], s, T, D, maxd, mode, k1, k2, thr, dl, dg) for s in range(P["ndays"] - maxd)])
    ps = (r[:, 0] == 1).mean(); bs = (r[:, 0] == -1).mean(); to = (r[:, 0] == 0).mean()
    dur = r[:, 1].mean()
    return dict(pass_=round(100 * ps), bust=round(100 * bs), timeout=round(100 * to), med_days=float(np.median(r[r[:, 0] == 1, 1])) if ps > 0 else np.nan,
                evals_per_PA=round(1 / ps, 2) if ps > 0 else np.inf, days_to_PA=round(dur / ps, 1) if ps > 0 else np.inf, cost_to_PA=round(17.70 * np.ceil(1.0) / ps, 0) if ps > 0 else np.inf)
