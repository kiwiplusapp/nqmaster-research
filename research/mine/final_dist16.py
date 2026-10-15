"""2026-10-16 income distribution per MFFU Rapid EOD 50K seat (12-month lifecycle, eval x8 + profit stop 800 -> funded), 1 base contract,
current defaults, starts every 5th day 2020-01..2025-10: today (risk cap below $2,000, no step-up, keep $4,100) vs the new preset
(step-up at $4,000, keep $6,100). Full edge, 35% less edge and ZERO edge (luck + firm economics only). -> final_dist16.json"""
import os, sys, json, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import robust2_build as RB
from robust2_life import full_paths, vectors, SP
from wrq_lib import getD
from mffu_rapid import life_m
from sniper_life import build
if __name__ == "__main__":
    E = RB.setup(); D = getD(RB.NAME)
    days = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb"))[0]; n = len(days); idx = np.arange(n, dtype=np.int64)
    T = build(E, D); T = T[T.date.isin(days)]; S = T["mod"].isin(["MOM1030", "CPI09"]); P = {}
    for cap in (0, 300):
        R0 = T[~S]; S1 = T[S].assign(w=1.0)
        if cap: R0 = R0[R0.risk <= cap]
        P[cap] = (full_paths(R0, days), full_paths(S1, days), R0.w.groupby(R0.date).sum().reindex(days, fill_value=0).to_numpy(), S1.w.groupby(S1.date).sum().reindex(days, fill_value=0).to_numpy())
    d24 = int(np.searchsorted(days, 20240101)); fin = P[0][0][2] + 4 * P[0][1][2]; mu1, mu2 = float(fin[:d24].mean()), float(fin[d24:].mean())
    def vecm(cap, m, G, h, k=1.0):
        a, b, ca, cb = P[cap]; cc = k * (ca + m * cb)
        return vectors(k * (a[0] + m * b[0]) - cc[:, None] - h[:, None], k * (a[1] + m * b[1]) - cc[:, None] - h[:, None], k * (a[2] + m * b[2]) - cc - h, G)
    OUT = {}
    for hc in (0.0, 0.35, 1.0):
        h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2)
        ev = vecm(0, 8, 800.0, h); EL = np.ascontiguousarray(np.array([ev[0], ev[0]])); EC = np.ascontiguousarray(np.array([ev[1], ev[1]]))
        full = vecm(0, 4, 0.0, h); low = vecm(300, 4, 0.0, h); dbl = vecm(0, 4, 0.0, h, 2.0)
        FL = np.ascontiguousarray(np.array([low[0], full[0], dbl[0]])); FC = np.ascontiguousarray(np.array([low[1], full[1], dbl[1]]))
        for name, c2, B in (("today", 1e9, 4100.0), ("new preset", 4000.0, 6100.0)):
            out = np.zeros((n, 9)); k = life_m(EL, EC, -1e9, 3000.0, 2000.0, 0.3, 4, 157.0, FL, FC, 2000.0, c2, B, 0, idx, 252, 5, out)
            o = out[:k]; mo = o[:, 0] / 12; lost = o[:, 1] - o[:, 2] + o[:, 3]; fb = o[:, 3]
            OUT[f"{name} | edge-{int(hc*100)}%"] = dict(seat_years=int(k), usd_month_median=round(float(np.median(mo))), p10=round(float(np.percentile(mo, 10))), p90=round(float(np.percentile(mo, 90))),
                mean=round(float(mo.mean())), P_negative_year=round(100 * float((mo < 0).mean()), 1), P_ge_1200_month=round(100 * float((mo >= 1200).mean()), 1),
                accounts_lost_per_year_mean=round(float(lost.mean()), 2), funded_busts_per_year_mean=round(float(fb.mean()), 2), funded_busts_p90=round(float(np.percentile(fb, 90)), 1))
            print(name, hc, OUT[f"{name} | edge-{int(hc*100)}%"], flush=True)
    json.dump(OUT, open(os.path.join(HERE, "final_dist16.json"), "w"), indent=1)
