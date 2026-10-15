"""2026-10-16 B4 pre-mortem numbers (1 base contract, current defaults, MFFU Rapid EOD 50K funded with the new preset: risk cap $300 below
a $2,000 cushion, step-up at $4,000, keep $6,100). Measured on 2020-26 real days:
  P(funded account lost within 90 trading days) from a fresh funded start, every start day, by period, full edge / 35% less edge
  P(at least one day <= -$1,000 per base contract within 90 trading days) and P(peak-to-trough >= $2,000 within 90 days) from daily
  P&L (20-day block bootstrap, 2,000 paths) -> premortem16.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import robust2_build as RB
from robust2_life import full_paths, vectors, SP
from wrq_lib import getD
from mffu_rapid import fu_m
from sniper_life import build

if __name__ == "__main__":
    E = RB.setup(); D = getD(RB.NAME); rng = np.random.default_rng(7)
    days = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb"))[0]; n = len(days); idx = np.arange(n, dtype=np.int64)
    T = build(E, D); T = T[T.date.isin(days)]; S = T["mod"].isin(["MOM1030", "CPI09"])
    P = {}
    for cap in (0, 300):
        R0 = T[~S]; S1 = T[S].assign(w=1.0)
        if cap: R0 = R0[R0.risk <= cap]
        P[cap] = (full_paths(R0, days), full_paths(S1, days), R0.w.groupby(R0.date).sum().reindex(days, fill_value=0).to_numpy(),
                  S1.w.groupby(S1.date).sum().reindex(days, fill_value=0).to_numpy())
    d24 = int(np.searchsorted(days, 20240101)); fin = P[0][0][2] + 4 * P[0][1][2]; mu1, mu2 = float(fin[:d24].mean()), float(fin[d24:].mean())
    def vecm(cap, m, h, k=1.0):
        a, b, ca, cb = P[cap]; cc = k * (ca + m * cb)
        return vectors(k * (a[0] + m * b[0]) - cc[:, None] - h[:, None], k * (a[1] + m * b[1]) - cc[:, None] - h[:, None], k * (a[2] + m * b[2]) - cc - h, 0.0)
    OUT = {}
    for hc in (0.0, 0.35):
        h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2)
        full = vecm(0, 4, h); low = vecm(300, 4, h); dbl = vecm(0, 4, h, 2.0)
        FL = np.ascontiguousarray(np.array([low[0], full[0], dbl[0]])); FC = np.ascontiguousarray(np.array([low[1], full[1], dbl[1]]))
        rec = {}
        for nm, lo, hi in (("2020-23", 20200101, 20240101), ("2024-26", 20240101, 20260601), ("summer 2026", 20260601, 20260901)):
            st = np.nonzero((days >= lo) & (days < hi))[0]; st = st[st < n - 20]
            lost = [fu_m(FL, FC, 2000.0, 4000.0, idx, int(s), int(min(n, s + 90)), 6100.0, 2000.0, 0)[2] == -1 for s in st]
            rec[nm] = round(100 * float(np.mean(lost)), 1)
        # daily tail at 1 contract (full gear)
        x = full[1]; r2 = []; r1 = []
        for _ in range(2000):
            s0 = rng.integers(0, n - 20, 5); p = np.concatenate([x[s:s + 20] for s in s0])[:90]
            lo_d = np.concatenate([full[0][s:s + 20] for s in s0])[:90]
            r1.append(bool((lo_d <= -1000).any())); eq = np.cumsum(p); r2.append(bool((np.maximum.accumulate(np.r_[0, eq]) - np.r_[0, eq]).max() >= 2000))
        rec["P_day_le_-1000_in_90d"] = round(100 * float(np.mean(r1)), 1); rec["P_drawdown_ge_2000_in_90d"] = round(100 * float(np.mean(r2)), 1)
        OUT[f"edge-{int(hc*100)}%"] = {"P_funded_lost_90d_by_start_period": rec}
        print(hc, rec, flush=True)
    json.dump(OUT, open(os.path.join(HERE, "premortem16.json"), "w"), indent=1)
