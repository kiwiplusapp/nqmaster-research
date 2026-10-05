"""Dynamic sizing policies for the Apex 50K evaluation (target 3000, trailing 2500 on open equity, 21 trading days = 30 calendar).
Size is decided at each day start from the equity state:
  eq >= T - near           -> k_near   (protect the finish)
  cushion < cush           -> k_low    (protect the account)
  day >= d_late & eq < lg  -> k_late   (behind schedule)
  otherwise                -> k0
Optional intraday stops: stop the day after realized <= -dl or >= +dg (dg capped so the day never overshoots the target)."""
import os, sys, pickle, itertools, numpy as np, pandas as pd
from numba import njit

@njit(cache=True)
def run_pol(day, fav, adv, rel, ndays, start, T, D, maxd, k0, near, k_near, cush, k_low, d_late, lg, k_late, dl, dg):
    i = np.searchsorted(day, start); eq = 0.0; pk = 0.0; d = start
    while d < start + maxd and d < ndays:
        dd = d - start; cu = eq - (pk - D)
        if eq >= T - near: k = k_near
        elif cu < cush: k = k_low
        elif dd >= d_late and eq < lg: k = k_late
        else: k = k0
        last = 0.0; stopped = False
        while i < len(day) and day[i] == d:
            if stopped: i += 1; continue
            if eq + k * adv[i] <= pk - D: return -1, dd + 1
            b = eq + k * fav[i]
            if b > pk: pk = b
            last = rel[i]; i += 1
            if eq + k * last >= T: return 1, dd + 1
            if dl > 0 and k * last <= -dl: stopped = True
            if dg > 0 and k * last >= dg: stopped = True
        eq += k * last
        if eq > pk: pk = eq
        d += 1
    return 0, maxd

@njit(cache=True)
def stats_pol(day, fav, adv, rel, ndays, T, D, maxd, k0, near, k_near, cush, k_low, d_late, lg, k_late, dl, dg):
    n = ndays - maxd; npass = 0; nbust = 0; p14 = 0; dsum = 0.0
    for s in range(n):
        r, u = run_pol(day, fav, adv, rel, ndays, s, T, D, maxd, k0, near, k_near, cush, k_low, d_late, lg, k_late, dl, dg)
        dsum += u
        if r == 1:
            npass += 1
            if u <= 14: p14 += 1
        elif r == -1: nbust += 1
    return npass / n, nbust / n, p14 / n, dsum / n

if __name__ == "__main__":
    RES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PROF = {"Ultra": pickle.load(open(os.path.join(RES, "mine", "ultra_paths.pkl"), "rb")), "WR70Plus": pickle.load(open(os.path.join(RES, "mine", "wr70plus_paths.pkl"), "rb"))}
    grid = list(itertools.product((1, 2, 3), (0.0, 1000.0, 1500.0), (1, 2), (0.0, 1000.0, 1500.0), (1,), ((99, 0.0, 1), (8, 1000.0, 3), (8, 1000.0, 4), (12, 2000.0, 3), (12, 2000.0, 4)), (0.0, 800.0, 1200.0), (0.0, 1500.0)))
    grid = [g for g in grid if not (g[1] == 0.0 and g[2] == 2)]
    rows = []
    for prof, PP in PROF.items():
        for gi, (k0, near, kn, cush, kl, (dlate, lg, klate), dl, dg) in enumerate(grid):
            r = dict(prof=prof, k0=k0, near=near, k_near=kn, cush=cush, d_late=dlate, lg=lg, k_late=klate, dl=dl, dg=dg)
            for per in ("IS", "C24", "REAL"):
                P = PP[per]
                p, b, p14, du = stats_pol(P["day"], P["fav"], P["adv"], P["rel"], P["ndays"], 3000.0, 2500.0, 21, k0, near, kn, cush, kl, dlate, lg, klate, dl, dg)
                r.update({per + "_pass": round(100 * p, 1), per + "_bust": round(100 * b, 1), per + "_p14": round(100 * p14, 1), per + "_days": round(du, 2)})
            rows.append(r)
        print(prof, "done", flush=True)
    g = pd.DataFrame(rows); g.to_csv(os.path.join(RES, "mine", "evalpol.csv"), index=False)
    pd.set_option("display.width", 260)
    for prof in PROF:
        x = g[g.prof == prof]
        base = x[(x.k0 == 2) & (x.near == 0) & (x.cush == 0) & (x.d_late == 99) & (x.dl == 0) & (x.dg == 0)]
        print("\n", prof, "BASELINE fixed 2:\n", base[["IS_pass", "C24_pass", "REAL_pass", "IS_p14", "C24_p14", "REAL_p14"]].to_string(index=False))
        top = x.sort_values("IS_pass", ascending=False).head(15)
        print(top[["k0", "near", "k_near", "cush", "d_late", "lg", "k_late", "dl", "dg", "IS_pass", "C24_pass", "REAL_pass", "IS_p14", "C24_p14", "REAL_p14", "REAL_bust", "REAL_days"]].to_string(index=False))
