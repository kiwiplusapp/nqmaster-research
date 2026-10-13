"""Funded-account question (2026-10-13): what if profit is NOT withdrawn, to keep a cushion above the trailing-drawdown floor?
MFFU Rapid EOD 50K, 1 contract (cap $300 below $2,000 cushion), withdraw only what is above B (B = profit kept in the account; MFFU minimum buffer $2,100),
90% split, payouts >= $500. Lucid Flex 50K: payout requested only when profit >= X (X = kept cushion + $500..), cap $2,000 per payout.
Edge 0 / 35% haircut, +1 tick.  $ per month net of eval fees, accounts lost per year, cash lost when a funded account busts (profit sitting in it).  -> smallacct_cushion.json"""
import os, sys, json, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from robust2_life import vectors, SP
from mffu_rapid import life_m
import acct1c_lib as A
H = 252
if __name__ == "__main__":
    days, P = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb")); n = len(days); idx = np.arange(n, dtype=np.int64)
    d24 = int(np.searchsorted(days, 20240101)); mu1 = float(P[("UltraR", 0)][2][:d24].mean()); mu2 = float(P[("UltraR", 0)][2][d24:].mean())
    OUT = {"MFFU Rapid EOD 50K": {}, "Lucid Flex 50K": {}}
    for hc in (0.0, 0.35):
        h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2)
        def vec(key, g):
            low, close, fin = P[key]; cc = P[key + ("cost",)]
            return vectors(low - cc[:, None] - h[:, None], close - cc[:, None] - h[:, None], fin - cc - h, g)
        hi = vec(("UltraR", 0), 800.0); EL = np.ascontiguousarray(np.array([hi[0], hi[0]])); EC = np.ascontiguousarray(np.array([hi[1], hi[1]]))
        hf = vec(("UltraR", 0), 0.0); lf = vec(("UltraR", 300), 0.0)
        FL = np.ascontiguousarray(np.array([lf[0], hf[0], hf[0]])); FC = np.ascontiguousarray(np.array([lf[1], hf[1], hf[1]]))
        for B in (2100.0, 3100.0, 4100.0, 5100.0, 7100.0):
            out = np.zeros((n, 9)); k = life_m(EL, EC, -1e9, 3000.0, 2000.0, 0.3, 4, 157.0, FL, FC, 2000.0, 2000.0, B, 0, idx, H, 5, out)
            o = out[:k]; st = np.arange(k) * 5; a = o[(st + H) < d24]; b = o[st >= d24]
            OUT["MFFU Rapid EOD 50K"].setdefault(f"keep ${int(B-100)} profit", {})[f"edge-{int(hc*100)}%"] = {p: dict(per_month=round(float(x[:, 0].mean() / 12)), lost=round(float((x[:, 1] - x[:, 2] + x[:, 3]).mean()), 2),
                              neg_year=round(100 * float((x[:, 0] < 0).mean()), 1), p10_month=round(float(np.percentile(x[:, 0], 10) / 12))) for p, x in (("T1", a), ("T2", b))}
        hl = vec(("UltraR", 0), 1350.0); EL2 = np.ascontiguousarray(np.array([hl[0], hl[0]])); EC2 = np.ascontiguousarray(np.array([hl[1], hl[1]]))
        FL2 = np.ascontiguousarray(np.array([lf[0], hf[0], hf[0]])); FC2 = np.ascontiguousarray(np.array([lf[1], hf[1], hf[1]]))
        for X in (2500.0, 4000.0, 5000.0, 6000.0, 8000.0):
            out = np.zeros((n, 9)); k = A.life(EL2, EC2, -1e9, 3000.0, 2000.0, 0.5, np.ones(n, np.bool_), 146.0, FL2, FC2, 1000.0, 1000.0, 0, X, 150.0, 2000.0, 2000.0, idx, H, 5, out)
            o = out[:k]; st = np.arange(k) * 5; a = o[(st + H) < d24]; b = o[st >= d24]
            OUT["Lucid Flex 50K"].setdefault(f"request payout at profit {int(X)}", {})[f"edge-{int(hc*100)}%"] = {p: dict(per_month=round(float(x[:, 0].mean() / 12)), lost=round(float((x[:, 1] - x[:, 2] + x[:, 3]).mean()), 2),
                              neg_year=round(100 * float((x[:, 0] < 0).mean()), 1), p10_month=round(float(np.percentile(x[:, 0], 10) / 12))) for p, x in (("T1", a), ("T2", b))}
    for f, d in OUT.items():
        print(f)
        for k, v in d.items(): print("  ", k, {e: (r["T1"]["per_month"], r["T2"]["per_month"], r["T2"]["lost"], r["T2"]["neg_year"]) for e, r in v.items()})
    json.dump(OUT, open(os.path.join(HERE, "smallacct_cushion.json"), "w"), indent=1)
