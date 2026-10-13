"""1-contract study, step 11: MFFU Rapid EOD 50K lifecycle in the same framework as the Lucid seats (UltraR, +1 tick, edge haircut 0/35/60 %).
Eval = full profile, daily profit stop 800 (30% consistency), serial restarts at $157; funded = per-trade risk cap $300 while the cushion < $2,000
(the shipped default) or none, optional step-up to 2 contracts (path x2) from a $3,000 cushion; withdraw down to $4,100 profit (payout every time
balance - 4,100 >= 500, 90% split, no cap).  -> smallacct_mffu.json"""
import os, sys, json, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from robust2_life import vectors, SP
from mffu_rapid import life_m
H = 252
if __name__ == "__main__":
    days, P = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb")); n = len(days); idx = np.arange(n, dtype=np.int64)
    d24 = int(np.searchsorted(days, 20240101)); mu1 = float(P[("UltraR", 0)][2][:d24].mean()); mu2 = float(P[("UltraR", 0)][2][d24:].mean())
    OUT = {}
    for variant, (cap, stepup) in {"1c, risk cap $300 < $2,000": (300, False), "1c, no cap": (0, False), "step-up 2c from $3,000 cushion + cap": (300, True)}.items():
        r = {}
        for hc in (0.0, 0.35, 0.60):
            h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2)
            def vec(key, g, mult=1.0):
                low, close, fin = P[key]; cc = P[key + ("cost",)]
                lo, cl = vectors(low - cc[:, None] - h[:, None], close - cc[:, None] - h[:, None], fin - cc - h, g)
                return lo * mult, cl * mult
            hi = vec(("UltraR", 0), 800.0); EL = np.ascontiguousarray(np.array([hi[0], hi[0]])); EC = np.ascontiguousarray(np.array([hi[1], hi[1]]))
            hf = vec(("UltraR", 0), 0.0); lf = vec(("UltraR", cap), 0.0) if cap else hf; h2 = vec(("UltraR", 0), 0.0, 2.0) if stepup else hf
            FL = np.ascontiguousarray(np.array([lf[0], hf[0], h2[0]])); FC = np.ascontiguousarray(np.array([lf[1], hf[1], h2[1]]))
            out = np.zeros((n, 9)); k = life_m(EL, EC, -1e9, 3000.0, 2000.0, 0.3, 4, 157.0, FL, FC, 2000.0 if cap else 0.0, 3000.0 if stepup else 1e9, 4100.0, 0, idx, H, 5, out)
            o = out[:k]; st = np.arange(k) * 5; a = o[(st + H) < d24]; b = o[st >= d24]
            r[f"edge-{int(hc*100)}%"] = {p: dict(per_month=round(float(x[:, 0].mean() / 12)), p10_month=round(float(np.percentile(x[:, 0], 10) / 12)), accounts_lost=round(float((x[:, 1] - x[:, 2] + x[:, 3]).mean()), 2),
                                                 neg_year_pct=round(100 * float((x[:, 0] < 0).mean()), 1)) for p, x in (("T1", a), ("T2", b))}
        OUT[variant] = r; print(variant, {k: (v["T1"]["per_month"], v["T2"]["per_month"], v["T2"]["accounts_lost"], v["T2"]["neg_year_pct"]) for k, v in r.items()}, flush=True)
    json.dump(OUT, open(os.path.join(HERE, "smallacct_mffu.json"), "w"), indent=1)
